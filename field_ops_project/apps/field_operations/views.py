import json
try:
    import pandas as pd  # legacy; optional
except Exception:  # pragma: no cover
    pd = None
import ast
import re
from datetime import date, datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect # YENİ: Yönlendirme için
from django.db.models import Q
from django.core.paginator import Paginator
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.contrib.auth import get_user_model
from django.db import transaction

from .models import RoutePlan, VisitTask, VisitType
from apps.customers.models import Customer

User = get_user_model()
CYCLE_START_DATE = date(2025, 12, 22)

# --- 1. GÖREV LİSTESİ ---
@login_required
def task_list(request):
    # NOT: Otomatik oluşturma fonksiyonunu buradan kaldırdık. 
    # Artık sildiğin görevler hortlamayacak.

    tasks = VisitTask.objects.all().select_related('customer', 'visit_type').order_by('planned_date')
    
    merchandisers = User.objects.filter(is_active=True).values_list('username', flat=True).order_by('username')
    visit_types = VisitType.objects.all()

    # Filtreleri Al
    f_search = request.GET.get('search', '')
    f_merch = request.GET.get('f_merch', '')
    f_city = request.GET.get('f_city', '')
    f_district = request.GET.get('f_district', '')
    f_status = request.GET.get('f_status', '')
    f_start_date = request.GET.get('f_start_date', '')
    f_end_date = request.GET.get('f_end_date', '')
    f_dateless = request.GET.get('f_dateless', '')
    f_visit_type = request.GET.get('f_visit_type', '')

    # --- VARSAYILAN TARİH AYARI (ÖNEMLİ GÜNCELLEME) ---
    # Eğer hiçbir tarih filtresi seçili değilse ve arama yapılmıyorsa, SADECE BUGÜNÜ getir.
    # (Tarihsizler modu açık değilse)
    is_filtering = any([f_search, f_merch, f_city, f_district, f_status, f_start_date, f_end_date, f_visit_type, f_dateless])
    
    if not is_filtering:
        # Varsayılan mod: Sadece Bugün
        tasks = tasks.filter(planned_date=date.today())
    else:
        # Filtreleme varsa normal mantık
        if f_search:
            tasks = tasks.filter(Q(customer__name__icontains=f_search) | Q(merch_code__icontains=f_search))
        if f_merch:
            tasks = tasks.filter(merch_code__icontains=f_merch)
        if f_city:
            tasks = tasks.filter(customer__city__icontains=f_city)
        if f_district:
            tasks = tasks.filter(customer__district__icontains=f_district)
        if f_status:
            tasks = tasks.filter(status=f_status)
        if f_visit_type:
            tasks = tasks.filter(visit_type__id=f_visit_type)
        
        if f_dateless == 'on':
            tasks = tasks.filter(planned_date__isnull=True)
        else:
            if f_start_date: tasks = tasks.filter(planned_date__gte=f_start_date)
            if f_end_date: tasks = tasks.filter(planned_date__lte=f_end_date)

    # Sayfalama
    paginator = Paginator(tasks, 50)
    page_tasks = paginator.get_page(request.GET.get('page'))

    today = date.today()
    delta = (today - CYCLE_START_DATE).days
    current_cycle_day = (delta % 28) + 1 if delta >= 0 else 0

    context = {
        'tasks': page_tasks,
        'paginator': paginator,
        'today': today,
        'current_cycle_day': current_cycle_day,
        'merchandisers': merchandisers,
        'visit_types': visit_types,
        'f_search': f_search, 'f_merch': f_merch, 'f_city': f_city, 
        'f_district': f_district, 'f_start_date': f_start_date, 
        'f_end_date': f_end_date, 'f_status': f_status, 
        'f_dateless': f_dateless, 'f_visit_type': f_visit_type,
        'is_filtering': is_filtering # Template'de uyarı göstermek istersek diye
    }
    return render(request, 'apps/field_operations/task_list.html', context)

# --- 2. HARİTA GÖRÜNÜMÜ ---
@login_required
@xframe_options_sameorigin
def task_map_view(request):
    selected_ids = request.GET.get('ids', '')
    tasks_data = []
    merchandisers = User.objects.filter(is_active=True).values_list('username', flat=True).order_by('username')

    if selected_ids:
        id_list = selected_ids.split(',')
        tasks = VisitTask.objects.filter(id__in=id_list, customer__latitude__isnull=False).select_related('customer')
        
        for t in tasks:
            if t.customer.latitude and t.customer.longitude:
                try:
                    tasks_data.append({
                        'id': t.id,
                        'sys_id': f"G-{t.id}",
                        'lat': float(t.customer.latitude.replace(',', '.')),
                        'lng': float(t.customer.longitude.replace(',', '.')),
                        'customer': t.customer.name,
                        'merch': t.merch_code,
                        'date': t.planned_date.strftime('%d.%m.%Y') if t.planned_date else "Tarihsiz",
                        'status': t.get_status_display()
                    })
                except: continue

    return render(request, 'apps/field_operations/task_map.html', {
        'tasks_json': json.dumps(tasks_data),
        'merchandisers': merchandisers
    })

# --- 3. EXCEL IMPORT ---
@login_required
def import_tasks(request):
    # İşlem sonrası geri dönüş adresi
    referer = request.META.get('HTTP_REFERER', 'task_list')

    if request.method == 'POST' and request.FILES.get('excel_file'):
        try:
            if pd is None:
                messages.error(request, "Excel import için pandas gerekli (legacy mod).")
                return HttpResponseRedirect(referer)
            df = pd.read_excel(request.FILES['excel_file'])
            df = df.where(pd.notnull(df), None)
            updated_count = 0
            created_count = 0
            cols = df.columns.tolist()

            for index, row in df.iterrows():
                # ID Temizle
                raw_id = row.get('Sistem ID')
                task_id = None
                if raw_id:
                    clean_id = str(raw_id).upper().replace('G-', '').replace('G', '').strip()
                    if clean_id.isdigit(): task_id = int(clean_id)
                
                # Tarih Oku
                raw_date = row.get('Tarih')
                p_date = None
                c_day = 0
                if raw_date and str(raw_date).strip() not in ['Tarihsiz', '', 'nan', 'NaT']:
                    try:
                        p_date = pd.to_datetime(raw_date, dayfirst=True).date()
                        delta = (p_date - CYCLE_START_DATE).days
                        c_day = (delta % 28) + 1 if delta >= 0 else 0
                    except: p_date = None

                # Güncelle veya Ekle
                if task_id:
                    try:
                        task = VisitTask.objects.get(id=task_id)
                        if 'Tarih' in cols:
                            task.planned_date = p_date
                            task.cycle_day = c_day
                        excel_merch = row.get('Personel') or row.get('Personel Kodu')
                        if excel_merch: task.merch_code = str(excel_merch).strip()
                        if 'Ziyaret Notu' in cols: task.visit_note = row.get('Ziyaret Notu')
                        task.save()
                        updated_count += 1
                    except VisitTask.DoesNotExist: pass
                else:
                    cust_code = row.get('Müşteri Kodu')
                    merch = row.get('Personel') or row.get('Personel Kodu')
                    if cust_code and merch:
                        try:
                            customer = Customer.objects.get(customer_code=str(cust_code).strip())
                            VisitTask.objects.create(
                                customer=customer, merch_code=str(merch).strip(), 
                                planned_date=p_date, cycle_day=c_day, status='pending'
                            )
                            created_count += 1
                        except Customer.DoesNotExist: pass
            
            messages.success(request, f"İşlem Tamam: {created_count} yeni, {updated_count} güncellendi.")
        except Exception as e:
            messages.error(request, f"Hata: {str(e)}")
            
    return HttpResponseRedirect(referer) # Filtreleri koruyarak geri dön

# --- 4. EXCEL EXPORT ---
@login_required
def export_tasks(request):
    # Export zaten GET parametreleriyle çalıştığı için değişime gerek yok
    tasks = VisitTask.objects.all().select_related('customer', 'visit_type').order_by('planned_date')
    
    # Filtreleri tekrar uygula (Aynı mantık)
    f_search = request.GET.get('search', '')
    f_merch = request.GET.get('f_merch', '')
    f_city = request.GET.get('f_city', '')
    f_district = request.GET.get('f_district', '')
    f_status = request.GET.get('f_status', '')
    f_start_date = request.GET.get('f_start_date', '')
    f_end_date = request.GET.get('f_end_date', '')
    f_dateless = request.GET.get('f_dateless', '')
    f_visit_type = request.GET.get('f_visit_type', '')

    # Varsayılan filtre kontrolü (Ekranda ne görüyorsan o inmeli)
    is_filtering = any([f_search, f_merch, f_city, f_district, f_status, f_start_date, f_end_date, f_visit_type, f_dateless])
    if not is_filtering:
         tasks = tasks.filter(planned_date=date.today())

    if f_search: tasks = tasks.filter(Q(customer__name__icontains=f_search) | Q(merch_code__icontains=f_search))
    if f_merch: tasks = tasks.filter(merch_code__icontains=f_merch)
    if f_city: tasks = tasks.filter(customer__city__icontains=f_city)
    if f_district: tasks = tasks.filter(customer__district__icontains=f_district)
    if f_status: tasks = tasks.filter(status=f_status)
    if f_visit_type: tasks = tasks.filter(visit_type__id=f_visit_type)
    
    if f_dateless == 'on': tasks = tasks.filter(planned_date__isnull=True)
    else:
        if f_start_date: tasks = tasks.filter(planned_date__gte=f_start_date)
        if f_end_date: tasks = tasks.filter(planned_date__lte=f_end_date)

    # Sütun Seçimi
    selected_fields = request.GET.get('fields', '')
    field_map = {
        'sys_id': 'Sistem ID', 'visit_type': 'Ziyaret Tipi', 'date': 'Tarih', 'cycle_day': 'Döngü Günü',
        'merch': 'Personel', 'cust_code': 'Müşteri Kodu', 'customer': 'Müşteri Adı', 
        'city': 'İl', 'district': 'İlçe', 'status': 'Durum', 'note': 'Ziyaret Notu'
    }

    if selected_fields: requested_keys = selected_fields.split(',')
    else: requested_keys = field_map.keys()

    data = []
    for t in tasks:
        row = {}
        if 'sys_id' in requested_keys: row[field_map['sys_id']] = f"G-{t.id}"
        if 'visit_type' in requested_keys: row[field_map['visit_type']] = t.visit_type.name if t.visit_type else '-'
        if 'date' in requested_keys: 
            row[field_map['date']] = t.planned_date.strftime('%d.%m.%Y') if t.planned_date else 'Tarihsiz'
        if 'cycle_day' in requested_keys: row[field_map['cycle_day']] = t.cycle_day if t.planned_date else '-'
        if 'merch' in requested_keys: row[field_map['merch']] = t.merch_code
        if 'cust_code' in requested_keys: row[field_map['cust_code']] = t.customer.customer_code
        if 'customer' in requested_keys: row[field_map['customer']] = t.customer.name
        if 'city' in requested_keys: row[field_map['city']] = t.customer.city
        if 'district' in requested_keys: row[field_map['district']] = t.customer.district
        
        status_display = dict(VisitTask.STATUS_CHOICES).get(t.status, t.status)
        if 'status' in requested_keys: row[field_map['status']] = status_display
        if 'note' in requested_keys: row[field_map['note']] = t.visit_note
        data.append(row)

    if not data: return HttpResponse("Veri yok.", content_type="text/plain")
    
    if pd is None:
        return HttpResponse("Excel export için pandas gerekli (legacy mod).", content_type="text/plain", status=500)
    df = pd.DataFrame(data)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=gorev_listesi.xlsx'
    df.to_excel(response, index=False)
    return response

# --- 5. TOPLU İŞLEMLER ---
@login_required
def bulk_task_action(request):
    # İşlem sonrası geri dönüş adresi (Filtreleri hatırlar)
    referer = request.META.get('HTTP_REFERER', 'task_list')

    if request.method == 'POST':
        selected_ids = request.POST.getlist('selected_ids')
        action_type = request.POST.get('action_type')
        
        if not selected_ids:
            messages.warning(request, "Seçim yapılmadı.")
            return HttpResponseRedirect(referer)

        tasks = VisitTask.objects.filter(id__in=selected_ids)
        count = tasks.count()

        if action_type == 'delete':
            tasks.delete()
            messages.success(request, f"{count} görev silindi.")
        elif action_type == 'passive':
            tasks.update(status='cancelled')
            messages.warning(request, f"{count} görev pasife alındı.")
        elif action_type == 'active':
            tasks.update(status='pending')
            messages.success(request, f"{count} görev aktif edildi.")
        
        # KOMBİNE GÜNCELLEME
        elif action_type == 'combined_update':
            new_merch = request.POST.get('new_merch')
            new_date_str = request.POST.get('new_date')
            
            updates = {}
            msg_parts = []

            if new_merch:
                updates['merch_code'] = new_merch
                msg_parts.append(f"Personel: {new_merch}")
            
            if new_date_str:
                try:
                    new_date = datetime.strptime(new_date_str, '%Y-%m-%d').date()
                    delta = (new_date - CYCLE_START_DATE).days
                    new_cycle = (delta % 28) + 1 if delta >= 0 else 0
                    updates['planned_date'] = new_date
                    updates['cycle_day'] = new_cycle
                    msg_parts.append(f"Tarih: {new_date}")
                except: pass

            if updates:
                tasks.update(**updates)
                messages.success(request, f"Güncellendi: {', '.join(msg_parts)}")
            else:
                messages.warning(request, "Değişiklik seçilmedi.")

    return HttpResponseRedirect(referer) # Filtreli sayfaya geri dön

# --- 6. MANUEL OLUŞTURMA (KURTARMA / OTO OLUŞTUR) ---
# --- 6. MANUEL OLUŞTURMA (KURTARMA / OTO OLUŞTUR) ---
@login_required
def generate_daily_tasks(request):
    referer = request.META.get('HTTP_REFERER', 'task_list')
    target_date = date.today()
    
    if request.method == 'POST':
        custom_date = request.POST.get('target_date')
        if custom_date:
            try: target_date = datetime.strptime(custom_date, '%Y-%m-%d').date()
            except: pass

    # Gün Hesabı (Örn: 30.12.2025 -> 9. Gün)
    delta = (target_date - CYCLE_START_DATE).days
    if delta < 0:
        messages.error(request, "Hatalı tarih (Döngü öncesi).")
        return HttpResponseRedirect(referer)

    cycle_day = (delta % 28) + 1
    
    # --- DEDEKTİF LOGU BAŞLANGICI ---
    print(f"\n--- GÖREV OLUŞTURMA RAPORU ---")
    print(f"HEDEF TARİH: {target_date}")
    print(f"ARANAN DÖNGÜ GÜNÜ: {cycle_day}")
    # -------------------------------

    all_routes = RoutePlan.objects.all()
    count = 0
    
    for route in all_routes:
        # 1. Veri ne olursa olsun (Liste, Sayı, Yazı) önce String'e çevir
        raw_data_str = str(route.active_days)
        
        # 2. REGEX İLE RAKAMLARI ÇEK: "['1', ' 9']" -> ['1', '9']
        # Bu kod metnin içindeki TÜM sayıları bulur.
        found_days = re.findall(r'\d+', raw_data_str)
        
        # 3. KONTROL ET
        if str(cycle_day) in found_days:
            
            # Sadece EKSİK olanları tamamla
            exists = VisitTask.objects.filter(
                customer=route.customer, 
                planned_date=target_date
            ).exclude(status='cancelled').exists()
            
            if not exists:
                VisitTask.objects.create(
                    customer=route.customer, 
                    merch_code=route.merch_code, 
                    planned_date=target_date, 
                    cycle_day=cycle_day, 
                    status='pending'
                )
                count += 1
                print(f"[EKLEME] Müşteri: {route.customer.name} (Rotasında {found_days} var)")
            else:
                # Zaten varsa loga yaz (Debug için)
                # print(f"[VAR] {route.customer.name} zaten mevcut.")
                pass
                
    print(f"--- İŞLEM BİTTİ: {count} GÖREV EKLENDİ ---\n")
    
    messages.success(request, f"{target_date.strftime('%d.%m.%Y')} ({cycle_day}. Gün) tarandı. {count} eksik görev geri getirildi.")
    return HttpResponseRedirect(referer)

# --- 7. TEKİL MANUEL OLUŞTURMA ---
@login_required
def create_manual_task(request):
    referer = request.META.get('HTTP_REFERER', 'task_list')
    if request.method == 'POST':
        customer_code = request.POST.get('customer_code')
        merch_code = request.POST.get('merch_code')
        planned_date = request.POST.get('planned_date')
        visit_type_id = request.POST.get('visit_type')
        
        try:
            customer = Customer.objects.get(customer_code=customer_code)
            p_date = None
            c_day = 0
            if planned_date:
                p_date = datetime.strptime(planned_date, '%Y-%m-%d').date()
                delta = (p_date - CYCLE_START_DATE).days
                c_day = (delta % 28) + 1 if delta >= 0 else 0
            
            v_type = None
            if visit_type_id: v_type = VisitType.objects.get(id=visit_type_id)

            VisitTask.objects.create(customer=customer, merch_code=merch_code, planned_date=p_date, cycle_day=c_day, status='pending', visit_type=v_type)
            messages.success(request, "Görev oluşturuldu.")
        except Exception as e: messages.error(request, str(e))
    return HttpResponseRedirect(referer)

# --- 8. TEKİL DÜZENLEME ---
@login_required
def edit_task(request, pk):
    task = get_object_or_404(VisitTask, pk=pk)
    # Edit sayfası GET olduğu için referer'ı form içinde hidden input olarak tutmak gerekir.
    # Basitlik için burada normal redirect kullanıyoruz ama silme/pasif butonları POST olduğu için onlar referer'ı kullanabilir.
    
    if request.method == 'POST':
        action = request.POST.get('action')
        # Geri dönüş adresi (Formda hidden olarak gelirse onu al, yoksa task_list)
        # Şimdilik task_list'e dönmesi normal, çünkü edit sayfası ayrı bir sayfa.
        
        if action == 'delete':
            task.delete()
            return redirect('task_list')
        elif action == 'passive':
            task.status = 'cancelled'
            task.save()
            return redirect('task_list')
        elif action == 'save':
            task.merch_code = request.POST.get('merch_code')
            task.visit_note = request.POST.get('visit_note')
            p_date = request.POST.get('planned_date')
            if p_date:
                new_date = datetime.strptime(p_date, '%Y-%m-%d').date()
                task.planned_date = new_date
                delta = (new_date - CYCLE_START_DATE).days
                task.cycle_day = (delta % 28) + 1 if delta >= 0 else 0
            else:
                task.planned_date = None
                task.cycle_day = 0
            task.save()
            return redirect('task_list')
            
    return render(request, 'apps/field_operations/edit_task.html', {'task': task})

# --- 9. AYARLAR VE ROTA ---
@login_required
def settings_visit_types(request):
    if request.method == 'POST':
        if 'add_type' in request.POST:
            name = request.POST.get('type_name')
            if name: VisitType.objects.create(name=name)
        elif 'delete_type' in request.POST:
            VisitType.objects.filter(id=request.POST.get('type_id')).delete()
        return redirect('settings_visit_types')
    return render(request, 'apps/field_operations/settings_types.html', {'types': VisitType.objects.all()})

# --- 9. ROTA PLANLAMA VE YÖNETİMİ ---

@login_required
def route_plan_list(request):
    routes = RoutePlan.objects.all().select_related('customer')
    
    # --- 1. FİLTRELEME ---
    f_search = request.GET.get('search', '')     # Genel Arama (Müşteri)
    f_merch = request.GET.get('merch', '')       # Personel
    f_day = request.GET.get('day', '')           # Gün (1-28)

    if f_search:
        routes = routes.filter(customer__name__icontains=f_search)
    if f_merch:
        routes = routes.filter(merch_code__icontains=f_merch)
    
    # Gün Filtresi (Zor Kısım: Veritabanında [1, 3] veya "1, 3" yazıyor olabilir)
    # Performans için Python tarafında filtreliyoruz (Regex ile)
    if f_day:
        filtered_ids = []
        for r in routes:
            raw = str(r.active_days)
            found = re.findall(r'\d+', raw)
            if str(f_day) in found:
                filtered_ids.append(r.id)
        routes = routes.filter(id__in=filtered_ids)

    # Gruplama (Personel Bazlı)
    grouped_routes = {}
    for r in routes:
        grouped_routes.setdefault(r.merch_code, []).append(r)

    # Dropdown için personel listesi
    merchandisers = User.objects.filter(is_active=True).values_list('username', flat=True).order_by('username')

    context = {
        'grouped_routes': grouped_routes,
        'merchandisers': merchandisers,
        # Filtreleri template'e geri gönder
        'f_search': f_search, 'f_merch': f_merch, 'f_day': f_day
    }
    return render(request, 'apps/field_operations/route_plan.html', context)

@login_required
def get_route_day_details(request):
    """AJAX: Belirli bir personel ve gün (1-28) için harita/liste verisi döner"""
    try:
        merch = request.GET.get('merch')
        day = request.GET.get('day')

        print(f"--- AJAX İSTEĞİ GELDİ: Personel={merch}, Gün={day} ---") # Log

        if not merch or not day:
            return HttpResponse(json.dumps({'error': 'Eksik parametre'}), content_type='application/json', status=400)

        data = []
        routes = RoutePlan.objects.filter(merch_code=merch).select_related('customer')

        for r in routes:
            # Regex ile gün kontrolü (Zırhlı)
            raw = str(r.active_days)
            found = re.findall(r'\d+', raw)

            if str(day) in found:
                # Koordinat güvenli çeviri
                lat, lng = None, None
                if r.customer.latitude and r.customer.longitude:
                    try:
                        # Virgül/Nokta değişimi ve boşluk temizliği
                        clean_lat = str(r.customer.latitude).replace(',', '.').strip()
                        clean_lng = str(r.customer.longitude).replace(',', '.').strip()
                        if clean_lat and clean_lng:
                            lat = float(clean_lat)
                            lng = float(clean_lng)
                    except: 
                        pass # Koordinat bozuksa boş geç

                data.append({
                    'route_id': r.id,
                    'customer_name': r.customer.name,
                    'customer_code': r.customer.customer_code,
                    'lat': lat,
                    'lng': lng,
                    'district': r.customer.district or '-',
                    'city': r.customer.city or '-'
                })

        print(f"--- SONUÇ: {len(data)} mağaza bulundu. ---")
        return HttpResponse(json.dumps(data), content_type='application/json')

    except Exception as e:
        print(f"!!! HATA OLUŞTU: {str(e)}")
        return HttpResponse(json.dumps({'error': str(e)}), content_type='application/json', status=500)

@login_required
def action_route_day(request):
    """AJAX/FORM: Rota üzerindeki bir günü siler, transfer eder veya pasife alır"""
    if request.method == 'POST':
        route_id = request.POST.get('route_id')
        current_day = request.POST.get('current_day') # Şu anki gün (Örn: 1)
        action = request.POST.get('action') # delete, assign, passive
        
        target_merch = request.POST.get('target_merch')
        target_day = request.POST.get('target_day') # Yeni gün (Örn: 5)
        
        try:
            route = RoutePlan.objects.get(id=route_id)
            
            # 1. MEVCUT GÜNÜ LİSTEDEN ÇIKAR
            # Veriyi temizle ve listeye çevir
            raw = str(route.active_days)
            # Regex ile sadece sayıları al
            days_list = re.findall(r'\d+', raw)
            
            if str(current_day) in days_list:
                days_list.remove(str(current_day))
                
                # Listeyi veritabanına geri kaydet (Temiz formatta: [1, 3])
                # Sayıya çevirip kaydedelim ki düzgün olsun
                int_days = sorted([int(x) for x in days_list])
                route.active_days = int_days
                route.save()
                
                # --- İŞLEM TÜRÜNE GÖRE DEVAM ET ---
                
                if action == 'assign':
                    # Başka bir güne/personele ekle
                    # Hedef personel için rota var mı?
                    target_route, created = RoutePlan.objects.get_or_create(
                        customer=route.customer,
                        merch_code=target_merch,
                        defaults={'active_days': []}
                    )
                    
                    # Hedefin günlerini al
                    target_raw = str(target_route.active_days)
                    target_days = re.findall(r'\d+', target_raw)
                    
                    if str(target_day) not in target_days:
                        target_days.append(str(target_day))
                        
                    # Kaydet
                    final_days = sorted([int(x) for x in target_days])
                    target_route.active_days = final_days
                    target_route.save()
                    
                    messages.success(request, f"Transfer Başarılı: {target_merch} - {target_day}. Gün")

                elif action == 'delete':
                    messages.warning(request, "Rota o günden silindi.")
                    
                # Pasif işlemi için Customer modelinde status alanı lazım, 
                # şimdilik sadece rotadan siliyoruz.
                
            else:
                messages.error(request, "Hata: O gün zaten listede yok.")

        except Exception as e:
            messages.error(request, f"Hata oluştu: {str(e)}")
            
    return redirect('route_plan_list')

# apps/field_operations/views.py

@login_required
def import_route_plan(request):
    referer = request.META.get('HTTP_REFERER', 'route_plan_list')
    
    if request.method == 'POST' and request.FILES.get('excel_file'):
        print("\n=== DETAYLI EXCEL ANALİZİ (TRANSFER MODU) ===") 
        try:
            # ADIM 1: Excel'i Oku
            if pd is None:
                messages.error(request, "Rota excel import için pandas gerekli (legacy mod).")
                return HttpResponseRedirect(referer)
            df = pd.read_excel(request.FILES['excel_file'], dtype=str)
            df.columns = df.columns.str.strip()
            
            # Sütunları Bul
            day_columns = {} 
            for col in df.columns:
                match = re.search(r'(?:G[uü]n)\s*(\d+)', col, re.IGNORECASE)
                if match:
                    day_num = int(match.group(1))
                    if 1 <= day_num <= 28:
                        day_columns[col] = day_num
            
            if not day_columns:
                messages.error(request, "Excel'de 'Gün X' sütunları bulunamadı.")
                return HttpResponseRedirect(referer)

            merch_col = next((c for c in df.columns if 'Saha' in c or 'Personel' in c or 'Merch' in c), None)
            if not merch_col:
                messages.error(request, "Personel sütunu bulunamadı.")
                return HttpResponseRedirect(referer)

            unique_merchs = df[merch_col].dropna().unique()
            success_count = 0
            task_action_count = 0
            
            # --- VERİTABANI İŞLEMİ ---
            with transaction.atomic():
                for merch_raw in unique_merchs:
                    merch_name = str(merch_raw).strip()
                    if merch_name.lower() == 'nan': continue
                    
                    print(f"-> Personel: {merch_name}")

                    # 1. TEMİZLİK (Mevcut günleri temizle - Sadece Excel'dekileri)
                    routes = RoutePlan.objects.filter(merch_code=merch_name)
                    target_days = list(day_columns.values())
                    for r in routes:
                        current = set()
                        for d in re.findall(r'\d+', str(r.active_days)): current.add(int(d))
                        for td in target_days:
                            if td in current: current.remove(td)
                        r.active_days = sorted(list(current))
                        r.save()

                    # 2. EKLEME VE GÖREV YÖNETİMİ
                    merch_df = df[df[merch_col] == merch_raw]
                    
                    for idx, row in merch_df.iterrows():
                        # Müşteriyi Bul
                        customer = None
                        raw_sys_id = str(row.get('Sistem ID') or row.get('Sys ID') or '').replace('nan', '').strip()
                        raw_code = str(row.get('Kod') or row.get('Müşteri Kodu') or '').replace('nan', '').strip()

                        if raw_sys_id:
                            clean_id = raw_sys_id.replace('G-', '').split('.')[0]
                            if clean_id.isdigit():
                                customer = Customer.objects.filter(id=int(clean_id)).first()
                        
                        if not customer and raw_code:
                            clean_code = raw_code.split('.')[0]
                            customer = Customer.objects.filter(customer_code=clean_code).first()

                        if customer:
                            route, created = RoutePlan.objects.get_or_create(
                                merch_code=merch_name,
                                customer=customer,
                                defaults={'active_days': []}
                            )
                            
                            current_days = set()
                            for d in re.findall(r'\d+', str(route.active_days)): current_days.add(int(d))
                            
                            added_days = [] # Yeni eklenen veya teyit edilen günler
                            
                            for col_name, day_num in day_columns.items():
                                val = str(row.get(col_name, '')).lower().strip()
                                if val not in ['nan', '', '0', '0.0', 'false', 'none']:
                                    current_days.add(day_num)
                                    added_days.append(day_num)
                            
                            route.active_days = sorted(list(current_days))
                            route.save()
                            success_count += 1
                            
                            # --- 3. GÖREV SENKRONİZASYONU (TRANSFER/OLUŞTUR) ---
                            today = date.today()
                            for d_num in added_days:
                                # Bugünün döngü günü
                                delta_today = (today - CYCLE_START_DATE).days
                                cycle_today = (delta_today % 28) + 1
                                
                                # Hedef gün farkı
                                diff = d_num - cycle_today
                                if diff < 0: diff += 28 
                                
                                task_date = today + timedelta(days=diff)
                                
                                # A) GÖREV VAR MI? (Kimin üzerinde olduğuna bakmaksızın)
                                existing_task = VisitTask.objects.filter(
                                    customer=customer, 
                                    planned_date=task_date
                                ).exclude(status='cancelled').first()
                                
                                if existing_task:
                                    # Görev var. Peki sahibi doğru mu?
                                    if existing_task.merch_code != merch_name:
                                        # SAHİBİ YANLIŞ -> TRANSFER ET
                                        old_merch = existing_task.merch_code
                                        existing_task.merch_code = merch_name
                                        existing_task.cycle_day = d_num
                                        existing_task.save()
                                        task_action_count += 1
                                        print(f"      [TRANSFER] {customer.name}: {old_merch} -> {merch_name} ({task_date})")
                                    else:
                                        # Sahibi zaten doğru, bir şey yapma
                                        pass
                                else:
                                    # B) GÖREV YOK -> OLUŞTUR
                                    VisitTask.objects.create(
                                        customer=customer,
                                        merch_code=merch_name,
                                        planned_date=task_date,
                                        cycle_day=d_num,
                                        status='pending'
                                    )
                                    task_action_count += 1
                                    print(f"      [YENİ] {customer.name} -> {merch_name} ({task_date})")

            print(f"=== RAPOR: {success_count} Rota Güncellendi, {task_action_count} Görev İşlendi (Yeni/Transfer) ===")
            
            if task_action_count > 0:
                messages.success(request, f"İşlem Başarılı: {success_count} rota güncellendi. {task_action_count} adet görev oluşturuldu veya yeni personele transfer edildi.")
            elif success_count > 0:
                 messages.warning(request, f"{success_count} rota güncellendi. Görevler zaten bu personelin üzerindeydi.")
            else:
                 messages.error(request, "Hiçbir kayıt güncellenemedi.")

        except Exception as e:
            print(f"HATA: {str(e)}")
            messages.error(request, f"Hata: {str(e)}")
            
    return HttpResponseRedirect(referer)

@login_required
def sync_merch_routes(request):
    """
    Belirli bir personel için bugünden itibaren gelecek 28 günü (1 döngü) tarar
    ve eksik görevleri Rota Planına göre tamamlar.
    """
    referer = request.META.get('HTTP_REFERER', 'route_plan_list')
    
    if request.method == 'POST':
        merch_code = request.POST.get('merch_code')
        
        if merch_code:
            today = date.today()
            # 28 Günlük (1 Aylık) tam tarama yapalım
            RANGE_DAYS = 28 
            
            # Sadece bu personelin rotalarını çek
            merch_routes = RoutePlan.objects.filter(merch_code=merch_code)
            count = 0
            
            # Bugünden başla, 28 gün ileri git
            for i in range(RANGE_DAYS):
                target_date = today + timedelta(days=i)
                
                # Döngü gününü hesapla
                delta = (target_date - CYCLE_START_DATE).days
                if delta < 0: continue # Döngü başlamadıysa atla
                
                cycle_day = (delta % 28) + 1
                
                for route in merch_routes:
                    # --- ZIRHLI VERİ OKUYUCU (Regex ile) ---
                    raw_data_str = str(route.active_days)
                    found_days = re.findall(r'\d+', raw_data_str)
                    
                    # Eğer bugünün döngü günü (Örn: 3) rotada varsa
                    if str(cycle_day) in found_days:
                        
                        # Görev var mı kontrol et (İptal edilenler hariç)
                        exists = VisitTask.objects.filter(
                            customer=route.customer,
                            planned_date=target_date
                        ).exclude(status='cancelled').exists()
                        
                        # Yoksa oluştur
                        if not exists:
                            VisitTask.objects.create(
                                customer=route.customer,
                                merch_code=merch_code,
                                planned_date=target_date,
                                cycle_day=cycle_day,
                                status='pending'
                            )
                            count += 1
            
            if count > 0:
                messages.success(request, f"{merch_code} için plan revize edildi: {count} eksik görev tamamlandı.")
            else:
                messages.info(request, f"{merch_code} için plan güncel, eksik görev bulunamadı.")
                
    return HttpResponseRedirect(referer)

# apps/field_operations/views.py EN ALTA EKLE:

@login_required
def route_bulk_add_day(request):
    """Seçili Rota Kayıtlarına (Mağazalara) yeni bir gün ekler (Mevcutları bozmadan)"""
    referer = request.META.get('HTTP_REFERER', 'route_plan_list')
    if request.method == 'POST':
        route_ids = request.POST.getlist('selected_routes')
        day_to_add = request.POST.get('day_to_add')
        
        if route_ids and day_to_add:
            routes = RoutePlan.objects.filter(id__in=route_ids)
            count = 0
            
            for route in routes:
                # 1. Mevcut günleri temizle ve kümeye (set) al
                current_days = set()
                raw_data = str(route.active_days)
                found = re.findall(r'\d+', raw_data)
                for d in found: current_days.add(int(d))
                
                # 2. Yeni günü ekle
                current_days.add(int(day_to_add))
                
                # 3. Sıralı listeye çevir ve kaydet
                route.active_days = sorted(list(current_days))
                route.save()
                count += 1
            
            messages.success(request, f"{count} mağazaya {day_to_add}. gün başarıyla eklendi.")
        else:
            messages.error(request, "Seçim yapılmadı veya gün girilmedi.")
            
    return HttpResponseRedirect(referer)

@login_required
def search_customer_api(request):
    """AJAX: İsim veya koda göre müşteri arar"""
    query = request.GET.get('q', '')
    if len(query) < 2:
        return HttpResponse(json.dumps([]), content_type='application/json')
    
    customers = Customer.objects.filter(
        Q(name__icontains=query) | Q(customer_code__icontains=query)
    )[:20] # En fazla 20 sonuç getir
    
    data = [{'id': c.id, 'name': c.name, 'code': c.customer_code, 'district': c.district} for c in customers]
    return HttpResponse(json.dumps(data), content_type='application/json')

@login_required
def add_store_to_route(request):
    """Belirli bir personelin rotasına veritabanından müşteri ekler"""
    referer = request.META.get('HTTP_REFERER', 'route_plan_list')
    if request.method == 'POST':
        merch_code = request.POST.get('merch_code')
        customer_id = request.POST.get('customer_id')
        day = request.POST.get('day')
        
        if merch_code and customer_id and day:
            try:
                customer = Customer.objects.get(id=customer_id)
                
                # Bu personel ve müşteri için zaten kayıt var mı?
                route, created = RoutePlan.objects.get_or_create(
                    merch_code=merch_code,
                    customer=customer,
                    defaults={'active_days': []}
                )
                
                # Günleri güncelle
                current_days = set()
                raw_data = str(route.active_days)
                found = re.findall(r'\d+', raw_data)
                for d in found: current_days.add(int(d))
                
                current_days.add(int(day))
                route.active_days = sorted(list(current_days))
                route.save()
                
                messages.success(request, f"{customer.name}, {merch_code} listesine eklendi (Gün: {day}).")
            except Exception as e:
                messages.error(request, f"Hata: {str(e)}")
                
    return HttpResponseRedirect(referer)

# --- apps/field_operations/views.py EN ALTINA EKLE ---

@login_required
def route_bulk_delete(request):
    """Ana ekrandan seçilen rotaları ve bekleyen görevlerini siler"""
    referer = request.META.get('HTTP_REFERER', 'route_plan_list')
    if request.method == 'POST':
        selected_ids = request.POST.getlist('selected_routes')
        if selected_ids:
            with transaction.atomic():
                # 1. Önce bu rotalara ait BEKLEYEN görevleri temizle
                # (Tamamlananlar tarihçe olarak kalmalı)
                routes = RoutePlan.objects.filter(id__in=selected_ids)
                for route in routes:
                    VisitTask.objects.filter(
                        customer=route.customer,
                        merch_code=route.merch_code,
                        status='pending'
                    ).delete()
                
                # 2. Rotaları sil
                count = routes.count()
                routes.delete()
                
            messages.success(request, f"{count} rota ve ilişkili bekleyen görevler silindi.")
        else:
            messages.warning(request, "Silinecek kayıt seçilmedi.")
            
    return HttpResponseRedirect(referer)

@login_required
def route_remove_day_api(request):
    """Modal içinden tek bir günden mağazayı düşürür"""
    if request.method == 'POST':
        route_id = request.POST.get('route_id')
        day_to_remove = request.POST.get('day')
        
        try:
            route = RoutePlan.objects.get(id=route_id)
            
            # 1. Günü listeden çıkar
            current_days = set()
            for d in re.findall(r'\d+', str(route.active_days)): current_days.add(int(d))
            
            if int(day_to_remove) in current_days:
                current_days.remove(int(day_to_remove))
                route.active_days = sorted(list(current_days))
                route.save()
                
                # 2. O güne denk gelen BEKLEYEN görevleri sil
                # (Döngü gününe göre hesaplananlar)
                VisitTask.objects.filter(
                    customer=route.customer,
                    merch_code=route.merch_code,
                    cycle_day=day_to_remove,
                    status='pending'
                ).delete()
                
                return HttpResponse(json.dumps({'status': 'success', 'msg': 'Mağaza o günden çıkarıldı.'}), content_type='application/json')
            else:
                return HttpResponse(json.dumps({'status': 'error', 'msg': 'O gün zaten listede yok.'}), content_type='application/json')
                
        except Exception as e:
            return HttpResponse(json.dumps({'status': 'error', 'msg': str(e)}), content_type='application/json')
    return HttpResponse(status=400)

@login_required
def route_replace_store_api(request):
    """Bir mağazayı o gün için başka bir mağazayla değiştirir"""
    if request.method == 'POST':
        route_id = request.POST.get('route_id')
        day = int(request.POST.get('day'))
        new_customer_id = request.POST.get('new_customer_id')
        
        try:
            with transaction.atomic():
                # A. ESKİ ROTA İŞLEMLERİ
                old_route = RoutePlan.objects.get(id=route_id)
                merch = old_route.merch_code
                
                # Günlerden çıkar
                old_days = set()
                for d in re.findall(r'\d+', str(old_route.active_days)): old_days.add(int(d))
                if day in old_days:
                    old_days.remove(day)
                    old_route.active_days = sorted(list(old_days))
                    old_route.save()
                    
                    # Eski görevleri sil
                    VisitTask.objects.filter(
                        customer=old_route.customer,
                        merch_code=merch,
                        cycle_day=day,
                        status='pending'
                    ).delete()

                # B. YENİ ROTA İŞLEMLERİ
                new_customer = Customer.objects.get(id=new_customer_id)
                
                # Yeni müşteri için bu personelde rota var mı? Yoksa oluştur.
                new_route, created = RoutePlan.objects.get_or_create(
                    merch_code=merch,
                    customer=new_customer,
                    defaults={'active_days': []}
                )
                
                # Güne ekle
                new_days = set()
                for d in re.findall(r'\d+', str(new_route.active_days)): new_days.add(int(d))
                new_days.add(day)
                new_route.active_days = sorted(list(new_days))
                new_route.save()
                
                # C. YENİ GÖREVLERİ OLUŞTUR (Bugünden itibaren döngüyü tara)
                today = date.today()
                # Gelecek 28 gün içinde bu döngü gününe denk gelen tarihleri bul
                for i in range(28):
                    target_date = today + timedelta(days=i)
                    delta = (target_date - CYCLE_START_DATE).days
                    if delta < 0: continue
                    current_cycle = (delta % 28) + 1
                    
                    if current_cycle == day:
                        # Görev oluştur
                        VisitTask.objects.get_or_create(
                            customer=new_customer,
                            merch_code=merch,
                            planned_date=target_date,
                            cycle_day=day,
                            defaults={'status': 'pending'}
                        )

            return HttpResponse(json.dumps({'status': 'success'}), content_type='application/json')
            
        except Exception as e:
            return HttpResponse(json.dumps({'status': 'error', 'msg': str(e)}), content_type='application/json')
            
    return HttpResponse(status=400)