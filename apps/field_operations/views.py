import json
import ast
import re
from io import BytesIO
from datetime import date, datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse # YENİ: Yönlendirme için
from django.db.models import Q, F, OuterRef, Subquery
from django.db.models import Count, Min, Max
from django.core.paginator import Paginator
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.http import require_http_methods
from django.contrib.contenttypes.models import ContentType

from .models import RoutePlan, VisitTask, VisitType
from .models import ReportRecord
from apps.forms.models import Survey, Question, SurveyAnswer
from apps.core.models import SystemSetting
from apps.customers.models import Customer
from apps.customers.models import CustomFieldDefinition
from apps.users.hierarchy_access import get_hierarchy_scope_for_user
from apps.users.models import AuthorityNode
from apps.core.excel_utils import xlsx_from_rows, xlsx_to_rows

User = get_user_model()
CYCLE_START_DATE = date(2025, 12, 22)

def _truthy_qp(val: str | None) -> bool:
    """
    Parse truthy query param values (e.g. ?x=1, ?x=on, ?x=true).
    """
    if val is None:
        return False
    v = str(val).strip().lower()
    return v in {"1", "true", "on", "yes"}


def _apply_latest_only_per_customer(
    *,
    base_qs,
    survey: Survey,
    scope_usernames: list[str] | None,
    start_date: date | None,
    end_date: date | None,
):
    """
    For survey reports: keep only the latest VisitTask per customer within the filtered queryset.
    This ensures repeating stores (customers) appear once with their most recent filled survey.
    """
    inner = (
        VisitTask.objects.filter(customer_id=OuterRef("customer_id"))
        .filter(answers__question__survey=survey)
        .exclude(check_in_time__isnull=True)
    )
    if scope_usernames:
        inner = inner.filter(merch_code__in=scope_usernames)
    if start_date and end_date:
        inner = inner.filter(check_in_time__date__gte=start_date, check_in_time__date__lte=end_date)

    inner = inner.order_by("-check_in_time", "-id").values("id")[:1]

    return (
        base_qs.annotate(_latest_task_id=Subquery(inner))
        .filter(id=F("_latest_task_id"))
        .distinct()
        .order_by("-check_in_time", "-id")
    )

# --- 1. GÖREV LİSTESİ ---
@login_required
def task_list(request):
    # NOT: Otomatik oluşturma fonksiyonunu buradan kaldırdık. 
    # Artık sildiğin görevler hortlamayacak.

    tasks = VisitTask.objects.all().select_related('customer', 'visit_type').order_by('planned_date')

    # Hiyerarşi bazlı yetkilendirme: Admin değilse sadece kendi + altının görevleri
    scope = get_hierarchy_scope_for_user(request.user, include_self=True)
    if scope.usernames:
        tasks = tasks.filter(merch_code__in=scope.usernames)
    
    merchandisers_qs = User.objects.filter(is_active=True)
    if scope.usernames:
        merchandisers_qs = merchandisers_qs.filter(username__in=scope.usernames)
    merchandisers = merchandisers_qs.values_list('username', flat=True).order_by('username')
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

    # --- ALT ÖZET (Filtrelenmiş toplamlar) ---
    # Not: toplamlar sayfalanmış listeye göre değil, filtrelenmiş tüm queryset'e göre hesaplanır.
    task_summary = tasks.aggregate(
        total=Count('id'),
        completed=Count('id', filter=Q(status='completed')),
        pending=Count('id', filter=Q(status='pending')),
        passive=Count('id', filter=Q(status='cancelled')),
        missed=Count('id', filter=Q(status='missed')),
    )

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
        'task_summary': task_summary,
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
            rows = xlsx_to_rows(request.FILES['excel_file'])
            updated_count = 0
            created_count = 0
            cols = list(rows[0].keys()) if rows else []

            for row in rows:
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
                        if isinstance(raw_date, datetime):
                            p_date = raw_date.date()
                        elif isinstance(raw_date, date):
                            p_date = raw_date
                        else:
                            # try parse dd.mm.yyyy or yyyy-mm-dd
                            s = str(raw_date).strip()
                            try:
                                p_date = datetime.strptime(s, "%d.%m.%Y").date()
                            except Exception:
                                p_date = datetime.strptime(s, "%Y-%m-%d").date()
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

    content = xlsx_from_rows(data, sheet_name="Görevler")
    response = HttpResponse(
        content,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=gorev_listesi.xlsx'
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

    # Hiyerarşi bazlı yetkilendirme: Admin değilse sadece kendi + altının rotaları
    scope = get_hierarchy_scope_for_user(request.user, include_self=True)
    if scope.usernames:
        routes = routes.filter(merch_code__in=scope.usernames)
    
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
    merchandisers_qs = User.objects.filter(is_active=True)
    if scope.usernames:
        merchandisers_qs = merchandisers_qs.filter(username__in=scope.usernames)
    merchandisers = merchandisers_qs.values_list('username', flat=True).order_by('username')

    # --- KPI: Bugünün (veya seçilen günün) toplam görevleri / yüzde ---
    today = date.today()
    delta_today = (today - CYCLE_START_DATE).days
    today_cycle_day = (delta_today % 28) + 1 if delta_today >= 0 else 0

    selected_day = None
    try:
        selected_day = int(f_day) if str(f_day).strip() else today_cycle_day
    except Exception:
        selected_day = today_cycle_day
    if selected_day < 1 or selected_day > 28:
        selected_day = today_cycle_day

    # Seçilen döngü gününe denk gelen en yakın tarih (bugün veya gelecekte)
    target_date = today
    if selected_day and selected_day != today_cycle_day and today_cycle_day:
        diff = selected_day - today_cycle_day
        if diff < 0:
            diff += 28
        target_date = today + timedelta(days=diff)

    # KPI, rota kaydı olmayan personelde bile doğru olmalı (görev elle taşınmış olabilir).
    # Bu yüzden scope içindeki aktif personelleri baz al.
    visible_merchs = list(merchandisers)
    if f_merch:
        # Filtre seçildiyse KPI da sadece o personel için hesaplanmalı
        visible_merchs = [m for m in visible_merchs if f_merch.lower() in str(m).lower()]
    task_stats = {}
    scope_total = 0
    scope_completed = 0
    if selected_day and visible_merchs:
        stats_qs = (
            VisitTask.objects.filter(planned_date=target_date, merch_code__in=visible_merchs)
            .exclude(status='cancelled')
            .values('merch_code')
            .annotate(
                total=Count('id'),
                completed=Count('id', filter=Q(status='completed')),
            )
        )
        for row in stats_qs:
            total = int(row.get('total') or 0)
            completed = int(row.get('completed') or 0)
            pct = int((completed / total) * 100) if total > 0 else 0
            task_stats[row['merch_code']] = {'total': total, 'completed': completed, 'percent': pct}
            scope_total += total
            scope_completed += completed
    scope_percent = int((scope_completed / scope_total) * 100) if scope_total > 0 else 0

    context = {
        'grouped_routes': grouped_routes,
        'merchandisers': merchandisers,
        'today_cycle_day': today_cycle_day,
        'selected_day': selected_day,
        'target_date': target_date,
        'merch_task_stats': task_stats,
        'scope_total_tasks': scope_total,
        'scope_completed_tasks': scope_completed,
        'scope_percent': scope_percent,
        # Filtreleri template'e geri gönder
        'f_search': f_search, 'f_merch': f_merch, 'f_day': f_day
    }
    return render(request, 'apps/field_operations/route_plan.html', context)


# --- 10. RAPORLAR ---
@login_required
def reports_home(request):
    return render(request, "apps/reports/home.html")


def _parse_date_yyyy_mm_dd(val: str | None) -> date | None:
    if not val:
        return None
    try:
        return datetime.strptime(str(val).strip(), "%Y-%m-%d").date()
    except Exception:
        return None


VISIT_DETAIL_REPORT_COLS_SESSION_KEY = "report_visit_detail_cols"
DAILY_SUMMARY_PREFS_SESSION_KEY = "report_daily_summary_prefs"
SURVEY_REPORT_COLS_SESSION_PREFIX = "report_survey_cols_"
REPORT_TRASH_RETENTION_KEY = "report_trash_retention_days"
DEFAULT_REPORT_TRASH_RETENTION_DAYS = 30


def _get_saved_cols_from_session(request) -> list[str]:
    raw = request.session.get(VISIT_DETAIL_REPORT_COLS_SESSION_KEY)
    if not raw:
        return []
    if isinstance(raw, list):
        return [str(x) for x in raw if x]
    if isinstance(raw, str):
        return [c for c in raw.split(",") if c]
    return []


def _save_cols_to_session(request, cols: list[str]) -> None:
    request.session[VISIT_DETAIL_REPORT_COLS_SESSION_KEY] = cols
    request.session.modified = True


def _get_daily_summary_prefs(request) -> dict:
    raw = request.session.get(DAILY_SUMMARY_PREFS_SESSION_KEY) or {}
    return raw if isinstance(raw, dict) else {}


def _save_daily_summary_prefs(request, prefs: dict) -> None:
    request.session[DAILY_SUMMARY_PREFS_SESSION_KEY] = prefs
    request.session.modified = True


def _get_survey_saved_cols_from_session(request, survey_id: int) -> list[str]:
    key = f"{SURVEY_REPORT_COLS_SESSION_PREFIX}{int(survey_id)}"
    raw = request.session.get(key)
    if not raw:
        return []
    if isinstance(raw, list):
        return [str(x) for x in raw if x]
    if isinstance(raw, str):
        return [c for c in raw.split(",") if c]
    return []


def _save_survey_cols_to_session(request, survey_id: int, cols: list[str]) -> None:
    key = f"{SURVEY_REPORT_COLS_SESSION_PREFIX}{int(survey_id)}"
    request.session[key] = cols
    request.session.modified = True


def _survey_report_columns(survey: Survey):
    """
    Builds columns for a survey report:
      - same base columns as visit detail report
      - plus question columns appended at the end
    Returns (columns, label_by_key)
    """
    cols, label_by_key = _visit_detail_report_columns()

    # Append question columns at the end (order matters)
    for q in Question.objects.filter(survey=survey).order_by("order", "id"):
        key = f"q_{q.id}"
        cols.append({"key": key, "label": q.label, "group": "Anket"})
        label_by_key[key] = q.label

    return cols, label_by_key


def _build_answer_map_for_tasks(tasks: list[VisitTask], survey: Survey) -> dict[tuple[int, int], str]:
    """
    Returns mapping: (task_id, question_id) -> "answer1 | answer2 | ..."
    """
    task_ids = [t.id for t in tasks if t and t.id]
    if not task_ids:
        return {}

    answers = (
        SurveyAnswer.objects.select_related("question")
        .filter(task_id__in=task_ids, question__survey=survey)
        .order_by("task_id", "question_id", "id")
    )

    bucket: dict[tuple[int, int], list[str]] = {}
    for a in answers:
        qid = getattr(a, "question_id", None)
        tid = getattr(a, "task_id", None)
        if not qid or not tid:
            continue

        val = ""
        if getattr(a, "answer_text", None):
            val = str(a.answer_text).strip()
        elif getattr(a, "answer_photo", None):
            try:
                val = a.answer_photo.url
            except Exception:
                val = str(a.answer_photo)

        if not val:
            continue
        bucket.setdefault((tid, qid), []).append(val)

    out: dict[tuple[int, int], str] = {}
    for k, vals in bucket.items():
        out[k] = " | ".join([v for v in vals if v])
    return out


def _task_to_survey_report_value(
    task: VisitTask,
    col_key: str,
    *,
    answers_map: dict[tuple[int, int], str],
    user_fullname_by_username: dict[str, str] | None = None,
    hierarchy_parent_by_username: dict[str, str] | None = None,
) -> str:
    if col_key.startswith("q_"):
        try:
            qid = int(col_key.replace("q_", "", 1))
        except Exception:
            return ""
        return answers_map.get((task.id, qid), "")

    # Reuse base mapping from visit report for all other columns
    return _task_to_report_value(
        task,
        col_key,
        user_fullname_by_username=user_fullname_by_username,
        hierarchy_parent_by_username=hierarchy_parent_by_username,
    )

def _default_daily_summary_colors() -> dict:
    return {
        "donut_completed": "#ff0066",
        "donut_remaining": "#ffd1e3",
        "bar_planned": "#ff5a97",
        "bar_completed": "#ff0066",
    }


def _default_daily_summary_headers() -> dict:
    return {
        "user": "Kullanıcı Adı",
        "completed": "Bugün Gerçekleşen Planlı Görev Sayısı",
        "planned": "Planlanan Görev Sayısı",
        "stores": "Toplam Planlı Personel Mağaza Sayısı",
        "percent": "Planlı Gerçekleşen Ziyaret %",
        "first_in": "İlk Noktaya Giriş Saati",
        "last_out": "Son Noktadan Çıkış Saati",
    }


def _get_report_trash_retention_days() -> int:
    """
    Global retention days (stored in SystemSetting as a number).
    """
    s, _ = SystemSetting.objects.get_or_create(
        key=REPORT_TRASH_RETENTION_KEY,
        defaults={
            "label": "Silinecek Gün Sayısı",
            "value": str(DEFAULT_REPORT_TRASH_RETENTION_DAYS),
            "category": "general",
            "input_type": "number",
            "description": "Çöp kutusunda raporların kaç gün tutulacağı.",
        },
    )
    try:
        v = int(str(s.value).strip())
        return v if v >= 0 else DEFAULT_REPORT_TRASH_RETENTION_DAYS
    except Exception:
        return DEFAULT_REPORT_TRASH_RETENTION_DAYS


def _set_report_trash_retention_days(days: int) -> int:
    if days < 0:
        days = 0
    if days > 3650:
        days = 3650
    SystemSetting.objects.update_or_create(
        key=REPORT_TRASH_RETENTION_KEY,
        defaults={
            "label": "Silinecek Gün Sayısı",
            "value": str(days),
            "category": "general",
            "input_type": "number",
            "description": "Çöp kutusunda raporların kaç gün tutulacağı.",
        },
    )
    return days


def _purge_old_deleted_reports() -> int:
    """
    Deletes report records from DB if they stayed in trash longer than retention days.
    Returns number of deleted records.
    """
    retention = _get_report_trash_retention_days()
    if retention <= 0:
        # 0 => keep none in trash; allow immediate purge of already deleted
        cutoff = timezone.now()
    else:
        cutoff = timezone.now() - timedelta(days=retention)

    qs = ReportRecord.objects.filter(deleted_at__isnull=False, deleted_at__lte=cutoff)
    count = qs.count()
    if count:
        qs.delete()
    return count
def _visit_detail_report_columns():
    """
    Returns (columns, label_by_key) where columns is a list of dicts:
    {key, label, group}
    """
    cols = []

    # System / row identifier (required in all reports)
    cols.append({"key": "answer_id", "label": "Cevap ID", "group": "Sistem"})

    # Customer fixed fields (Müşteriler ekranındaki başlıklar)
    customer_fixed = [
        ("customer_code", "Müşteri Kodu"),
        ("customer_name", "Müşteri Adı"),
        ("cari", "Cari / Firma"),
        ("city", "İl"),
        ("district", "İlçe"),
        ("address", "Adres"),
        ("phone", "Telefon"),
        ("authorized_person", "Yetkili Kişi"),
        ("latitude", "Enlem"),
        ("longitude", "Boylam"),
    ]
    for key, label in customer_fixed:
        cols.append({"key": key, "label": label, "group": "Müşteri"})

    # Customer dynamic custom fields (otomatik gelir)
    for cf in CustomFieldDefinition.objects.all().order_by("id"):
        cols.append({"key": f"custom_{cf.slug}", "label": cf.name, "group": "Müşteri (Özel)"})

    # Visit/task fields (ekstra)
    visit_cols = [
        ("personel", "Personel"),
        ("user_full_name", "Kullanıcı Ad Soyad"),
        ("hierarchy_parent", "Hiyerarşi (Bağlı Olduğu)"),
        ("task_status", "Görev Durumu"),
        ("task_weekday", "Görev Günü"),
        ("task_month", "Görev Ayı"),
        ("visit_start_date", "Ziyaret Başlattığı Tarih"),
        ("visit_start_time", "Ziyaret Başlattığı Saat"),
        ("visit_end_date", "Ziyareti Bitirdiği Tarih"),
        ("visit_end_time", "Ziyareti Bitirdiği Saat"),
        ("visit_duration_min", "Mağaza İçi Süre (dk)"),
    ]
    for key, label in visit_cols:
        cols.append({"key": key, "label": label, "group": "Ziyaret"})

    label_by_key = {c["key"]: c["label"] for c in cols}
    return cols, label_by_key


def _task_to_report_value(
    task: VisitTask,
    col_key: str,
    *,
    user_fullname_by_username: dict[str, str] | None = None,
    hierarchy_parent_by_username: dict[str, str] | None = None,
) -> str:
    c = task.customer
    if col_key == "answer_id":
        # Stable unique ID for this report row (VisitTask-based submission ID)
        return f"A-{task.id}"
    if col_key == "customer_code":
        return c.customer_code or ""
    if col_key == "customer_name":
        return c.name or ""
    if col_key == "cari":
        return c.cari.name if getattr(c, "cari", None) else ""
    if col_key == "city":
        return c.city or ""
    if col_key == "district":
        return c.district or ""
    if col_key == "address":
        return c.address or ""
    if col_key == "phone":
        return c.phone or ""
    if col_key == "authorized_person":
        return c.authorized_person or ""
    if col_key == "latitude":
        return "" if c.latitude is None else str(c.latitude)
    if col_key == "longitude":
        return "" if c.longitude is None else str(c.longitude)
    if col_key.startswith("custom_"):
        slug = col_key.replace("custom_", "", 1)
        return (c.extra_data or {}).get(slug, "") if hasattr(c, "extra_data") else ""
    if col_key == "personel":
        return task.merch_code or ""
    if col_key == "user_full_name":
        if user_fullname_by_username is None:
            return ""
        return user_fullname_by_username.get(task.merch_code or "", "")
    if col_key == "hierarchy_parent":
        if hierarchy_parent_by_username is None:
            return ""
        return hierarchy_parent_by_username.get(task.merch_code or "", "")
    if col_key == "task_status":
        status_map = {
            "pending": "Beklemede",
            "completed": "Tamamlandı",
            "cancelled": "Pasif",
            "missed": "Ziyaret Edilmedi",
        }
        return status_map.get(getattr(task, "status", "") or "", getattr(task, "status", "") or "")

    # Visit start/end and duration
    cin = task.check_in_time
    cout = task.check_out_time
    # Ziyaret raporunda "yapılan tarih" = ziyaretin başlatıldığı tarih
    visit_day = timezone.localtime(cin).date() if cin else None
    if col_key == "task_weekday":
        if not visit_day:
            return ""
        dow = visit_day.weekday()  # 0=Mon
        names = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
        return names[dow] if 0 <= dow <= 6 else ""
    if col_key == "task_month":
        if not visit_day:
            return ""
        month_names = [
            "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
            "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık",
        ]
        mname = month_names[visit_day.month - 1] if 1 <= visit_day.month <= 12 else ""
        return f"{visit_day.year}/{visit_day.month:02d} - {mname}".strip(" -")
    if col_key == "visit_start_date":
        return timezone.localtime(cin).strftime("%d.%m.%Y") if cin else ""
    if col_key == "visit_start_time":
        return timezone.localtime(cin).strftime("%H:%M:%S") if cin else ""
    if col_key == "visit_end_date":
        return timezone.localtime(cout).strftime("%d.%m.%Y") if cout else ""
    if col_key == "visit_end_time":
        return timezone.localtime(cout).strftime("%H:%M:%S") if cout else ""
    if col_key == "visit_duration_min":
        if cin and cout:
            delta = cout - cin
            return str(int(delta.total_seconds() // 60))
        return ""
    return ""


def _build_user_and_hierarchy_maps(usernames: list[str]) -> tuple[dict[str, str], dict[str, str]]:
    """
    Returns:
    - user_fullname_by_username: merch_code -> "Ad Soyad"
    - hierarchy_parent_by_username: merch_code -> "Üst Ad Soyad" (ilk bağlı kişi)
    """
    usernames = [u for u in usernames if u]
    if not usernames:
        return {}, {}

    # Users map
    user_fullname_by_username: dict[str, str] = {}
    for u in User.objects.filter(username__in=usernames).only("username", "first_name", "last_name", "user_code"):
        full = (f"{u.first_name} {u.last_name}").strip()
        user_fullname_by_username[u.username] = full or getattr(u, "user_code", "") or u.username

    # Hierarchy parent map (assigned node -> parent.assigned_user)
    hierarchy_parent_by_username: dict[str, str] = {}
    nodes = (
        AuthorityNode.objects.select_related("assigned_user", "parent__assigned_user")
        .filter(assigned_user__username__in=usernames)
    )
    for n in nodes:
        uname = getattr(n.assigned_user, "username", None)
        if not uname:
            continue
        parent_user = getattr(getattr(n, "parent", None), "assigned_user", None)
        if parent_user:
            full = (f"{parent_user.first_name} {parent_user.last_name}").strip()
            hierarchy_parent_by_username[uname] = full or getattr(parent_user, "user_code", "") or parent_user.username
        else:
            hierarchy_parent_by_username[uname] = ""

    return user_fullname_by_username, hierarchy_parent_by_username


@login_required
def visit_detail_report(request):
    # Filters
    start_date = _parse_date_yyyy_mm_dd(request.GET.get("start_date"))
    end_date = _parse_date_yyyy_mm_dd(request.GET.get("end_date"))
    if not start_date and not end_date:
        start_date = date.today()
        end_date = date.today()
    if start_date and not end_date:
        end_date = start_date
    if end_date and not start_date:
        start_date = end_date

    cols, label_by_key = _visit_detail_report_columns()
    available_keys = set(label_by_key.keys())

    # Selected columns (order matters)
    raw_cols = (request.GET.get("cols") or "").strip()
    if raw_cols:
        selected_cols = [c for c in raw_cols.split(",") if c]
        selected_cols = [c for c in selected_cols if c in available_keys]
        _save_cols_to_session(request, selected_cols)
    else:
        selected_cols = [c for c in _get_saved_cols_from_session(request) if c in available_keys]

    if not selected_cols:
        selected_cols = [
            "answer_id",
            "customer_code",
            "customer_name",
            "visit_start_date",
            "visit_start_time",
            "visit_end_date",
            "visit_end_time",
            "visit_duration_min",
        ]
    # Force required ID column to always be present and first
    if "answer_id" not in selected_cols:
        selected_cols = ["answer_id"] + [c for c in selected_cols if c != "answer_id"]
        _save_cols_to_session(request, selected_cols)

    # Queryset (hierarchy scope + date filter)
    qs = VisitTask.objects.select_related("customer", "customer__cari").all()
    scope = get_hierarchy_scope_for_user(request.user, include_self=True)
    if scope.usernames:
        qs = qs.filter(merch_code__in=scope.usernames)

    # Only visits that were started
    qs = qs.exclude(check_in_time__isnull=True)

    if start_date and end_date:
        qs = qs.filter(check_in_time__date__gte=start_date, check_in_time__date__lte=end_date)

    qs = qs.order_by("-check_in_time", "-id")

    # Preview rows (large table, but cap for performance)
    preview_limit = 500
    tasks = list(qs[:preview_limit])
    usernames = list({t.merch_code for t in tasks if t.merch_code})
    user_fullname_by_username, hierarchy_parent_by_username = _build_user_and_hierarchy_maps(usernames)

    headers = [{"key": k, "label": label_by_key.get(k, k)} for k in selected_cols]
    rows = []
    for t in tasks:
        rows.append(
            {
                k: _task_to_report_value(
                    t,
                    k,
                    user_fullname_by_username=user_fullname_by_username,
                    hierarchy_parent_by_username=hierarchy_parent_by_username,
                )
                for k in selected_cols
            }
        )

    total_count = qs.count()

    return render(
        request,
        "apps/reports/visit_detail_report.html",
        {
            "start_date": start_date,
            "end_date": end_date,
            "columns": cols,
            "selected_cols": selected_cols,
            "headers": headers,
            "rows": rows,
            "total_count": total_count,
            "preview_limit": preview_limit,
        },
    )


@login_required
def daily_visit_summary_report(request):
    """
    Günlük Ziyaret Özeti:
    Seçilen gün için planlanan görevler (planned_date) üzerinden personel bazlı özet + grafik.
    """
    summary_date = _parse_date_yyyy_mm_dd(request.GET.get("date")) or date.today()

    scope = get_hierarchy_scope_for_user(request.user, include_self=True)
    qs = VisitTask.objects.select_related("customer").filter(planned_date=summary_date).exclude(planned_date__isnull=True)
    if scope.usernames:
        qs = qs.filter(merch_code__in=scope.usernames)

    stats_qs = (
        qs.values("merch_code")
        .annotate(
            planned=Count("id"),
            completed=Count("id", filter=Q(status="completed")),
            store_count=Count("customer_id", distinct=True),
            first_in=Min("check_in_time"),
            last_out=Max("check_out_time"),
        )
        .order_by("merch_code")
    )

    rows = []
    total_planned = 0
    total_completed = 0
    total_stores = 0

    all_merchs = [r["merch_code"] for r in stats_qs if r.get("merch_code")]
    full_by_username, _ = _build_user_and_hierarchy_maps(all_merchs)

    for r in stats_qs:
        merch = r.get("merch_code") or ""
        planned = int(r.get("planned") or 0)
        completed = int(r.get("completed") or 0)
        stores = int(r.get("store_count") or 0)
        pct = int((completed / planned) * 100) if planned > 0 else 0
        first_in = r.get("first_in")
        last_out = r.get("last_out")
        first_in_time = timezone.localtime(first_in).strftime("%H:%M:%S") if first_in else ""
        last_out_time = timezone.localtime(last_out).strftime("%H:%M:%S") if last_out else ""
        rows.append(
            {
                "merch_code": merch,
                "user_name": full_by_username.get(merch, "") or merch,
                "planned": planned,
                "completed": completed,
                "stores": stores,
                "percent": pct,
                "first_in_time": first_in_time,
                "last_out_time": last_out_time,
            }
        )
        total_planned += planned
        total_completed += completed
        total_stores += stores

    total_percent = int((total_completed / total_planned) * 100) if total_planned > 0 else 0

    charts_json = json.dumps(
        {
            "labels": [x["user_name"] for x in rows],
            "planned": [x["planned"] for x in rows],
            "completed": [x["completed"] for x in rows],
            "total_planned": total_planned,
            "total_completed": total_completed,
            "total_percent": total_percent,
        },
        ensure_ascii=False,
    )

    prefs = _get_daily_summary_prefs(request)
    colors = _default_daily_summary_colors() | (prefs.get("colors") or {})
    headers = _default_daily_summary_headers() | (prefs.get("headers") or {})

    return render(
        request,
        "apps/reports/daily_visit_summary.html",
        {
            "summary_date": summary_date,
            "rows": rows,
            "totals": {
                "planned": total_planned,
                "completed": total_completed,
                "stores": total_stores,
                "percent": total_percent,
            },
            "charts_json": charts_json,
            "chart_colors_json": json.dumps(colors, ensure_ascii=False),
            "table_headers": headers,
        },
    )


@login_required
@require_POST
def daily_visit_summary_save_prefs(request):
    """
    Save per-user daily summary preferences (colors, header labels) into session.
    Payload JSON:
      { colors?: {...}, headers?: {...} }
    """
    try:
        data = json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        return JsonResponse({"success": False, "message": "Geçersiz veri."}, status=400)

    prefs = _get_daily_summary_prefs(request)
    prefs = prefs if isinstance(prefs, dict) else {}

    if isinstance(data.get("colors"), dict):
        # Only accept known keys
        allowed = set(_default_daily_summary_colors().keys())
        incoming = {k: v for k, v in data["colors"].items() if k in allowed and isinstance(v, str)}
        prefs["colors"] = (_default_daily_summary_colors() | (prefs.get("colors") or {})) | incoming

    if isinstance(data.get("headers"), dict):
        allowed = set(_default_daily_summary_headers().keys())
        incoming = {k: v for k, v in data["headers"].items() if k in allowed and isinstance(v, str)}
        prefs["headers"] = (_default_daily_summary_headers() | (prefs.get("headers") or {})) | incoming

    _save_daily_summary_prefs(request, prefs)
    return JsonResponse({"success": True})


@login_required
def survey_reports_home(request):
    _purge_old_deleted_reports()

    ct = ContentType.objects.get_for_model(Survey)
    reports = (
        ReportRecord.objects.filter(report_type="survey", content_type=ct, deleted_at__isnull=True)
        .order_by("-created_at")
    )
    survey_ids = [r.object_id for r in reports]
    surveys_by_id = {s.id: s for s in Survey.objects.filter(id__in=survey_ids)}

    rows = []
    for r in reports:
        s = surveys_by_id.get(r.object_id)
        rows.append({"report": r, "survey": s})

    return render(request, "apps/reports/survey_reports_home.html", {"rows": rows})


@login_required
def survey_report_create(request, survey_id: int):
    """
    Creates (or restores) the report entry for a survey and redirects to its report page.
    """
    survey = get_object_or_404(Survey, pk=survey_id)
    ct = ContentType.objects.get_for_model(Survey)
    rec, _ = ReportRecord.objects.get_or_create(
        report_type="survey",
        content_type=ct,
        object_id=survey.id,
        defaults={"title": survey.title, "created_by": request.user},
    )
    # If it was in trash, restore
    if rec.deleted_at:
        rec.restore_from_trash()
    # Keep title in sync
    if rec.title != survey.title:
        rec.title = survey.title
        rec.save(update_fields=["title"])

    return redirect("survey_report", survey_id=survey.id)


@login_required
def survey_report(request, survey_id: int):
    survey = get_object_or_404(Survey, pk=survey_id)
    ct = ContentType.objects.get_for_model(Survey)
    rec = ReportRecord.objects.filter(report_type="survey", content_type=ct, object_id=survey.id).first()
    if rec and rec.deleted_at:
        messages.warning(request, "Bu rapor çöp kutusunda. Geri yüklemek için Çöp Kutusu'ndan geri yükleyin.")
        return redirect("reports_trash")
    if not rec:
        messages.info(request, "Bu anket için rapor kaydı yok. Lütfen 'Rapor Oluştur' ile oluşturun.")
        return redirect("survey_reports_home")

    # Filters (same behavior as visit detail report)
    start_date = _parse_date_yyyy_mm_dd(request.GET.get("start_date"))
    end_date = _parse_date_yyyy_mm_dd(request.GET.get("end_date"))
    if not start_date and not end_date:
        start_date = date.today()
        end_date = date.today()
    if start_date and not end_date:
        end_date = start_date
    if end_date and not start_date:
        start_date = end_date

    cols, label_by_key = _survey_report_columns(survey)
    available_keys = set(label_by_key.keys())

    latest_only = _truthy_qp(request.GET.get("latest_only"))

    raw_cols = (request.GET.get("cols") or "").strip()
    if raw_cols:
        selected_cols = [c for c in raw_cols.split(",") if c]
        selected_cols = [c for c in selected_cols if c in available_keys]
        _save_survey_cols_to_session(request, survey_id, selected_cols)
    else:
        selected_cols = [c for c in _get_survey_saved_cols_from_session(request, survey_id) if c in available_keys]

    if not selected_cols:
        # Default = visit essentials + all survey questions appended
        default_base = [
            "answer_id",
            "customer_code",
            "customer_name",
            "personel",
            "user_full_name",
            "task_status",
            "visit_start_date",
            "visit_start_time",
            "visit_end_date",
            "visit_end_time",
            "visit_duration_min",
        ]
        q_cols = [c["key"] for c in cols if c["key"].startswith("q_")]
        selected_cols = [k for k in default_base if k in available_keys] + q_cols
    # Force required ID column to always be present and first
    if "answer_id" not in selected_cols:
        selected_cols = ["answer_id"] + [c for c in selected_cols if c != "answer_id"]
        _save_survey_cols_to_session(request, survey_id, selected_cols)

    # Queryset (hierarchy scope + date filter + survey answers)
    qs = (
        VisitTask.objects.select_related("customer", "customer__cari")
        .filter(answers__question__survey=survey)
        .exclude(check_in_time__isnull=True)
        .distinct()
    )
    scope = get_hierarchy_scope_for_user(request.user, include_self=True)
    if scope.usernames:
        qs = qs.filter(merch_code__in=scope.usernames)

    if start_date and end_date:
        qs = qs.filter(check_in_time__date__gte=start_date, check_in_time__date__lte=end_date)

    qs = qs.order_by("-check_in_time", "-id")
    if latest_only:
        qs = _apply_latest_only_per_customer(
            base_qs=qs,
            survey=survey,
            scope_usernames=list(scope.usernames) if scope.usernames else None,
            start_date=start_date,
            end_date=end_date,
        )

    preview_limit = 500
    tasks = list(qs[:preview_limit])
    usernames = list({t.merch_code for t in tasks if t.merch_code})
    user_fullname_by_username, hierarchy_parent_by_username = _build_user_and_hierarchy_maps(usernames)
    answers_map = _build_answer_map_for_tasks(tasks, survey)

    headers = [{"key": k, "label": label_by_key.get(k, k)} for k in selected_cols]
    rows = []
    for t in tasks:
        row = {
            k: _task_to_survey_report_value(
                t,
                k,
                answers_map=answers_map,
                user_fullname_by_username=user_fullname_by_username,
                hierarchy_parent_by_username=hierarchy_parent_by_username,
            )
            for k in selected_cols
        }
        # For UI actions (edit/delete)
        row["__task_id"] = t.id
        rows.append(row)

    total_count = qs.count()
    return render(
        request,
        "apps/reports/survey_report.html",
        {
            "survey": survey,
            "report_id": rec.id,
            "start_date": start_date,
            "end_date": end_date,
            "latest_only": latest_only,
            "columns": cols,
            "selected_cols": selected_cols,
            "headers": headers,
            "rows": rows,
            "total_count": total_count,
            "preview_limit": preview_limit,
        },
    )


@login_required
def survey_report_export(request, survey_id: int):
    survey = get_object_or_404(Survey, pk=survey_id)
    ct = ContentType.objects.get_for_model(Survey)
    rec = ReportRecord.objects.filter(report_type="survey", content_type=ct, object_id=survey.id).first()
    if rec and rec.deleted_at:
        return HttpResponse("Bu rapor çöp kutusunda.", content_type="text/plain", status=400)
    if not rec:
        return HttpResponse("Bu anket için rapor kaydı yok.", content_type="text/plain", status=400)

    start_date = _parse_date_yyyy_mm_dd(request.GET.get("start_date"))
    end_date = _parse_date_yyyy_mm_dd(request.GET.get("end_date"))
    if not start_date and not end_date:
        start_date = date.today()
        end_date = date.today()
    if start_date and not end_date:
        end_date = start_date
    if end_date and not start_date:
        start_date = end_date

    cols, label_by_key = _survey_report_columns(survey)
    available_keys = set(label_by_key.keys())

    latest_only = _truthy_qp(request.GET.get("latest_only"))

    raw_cols = (request.GET.get("cols") or "").strip()
    if raw_cols:
        selected_cols = [c for c in raw_cols.split(",") if c]
        selected_cols = [c for c in selected_cols if c in available_keys]
        _save_survey_cols_to_session(request, survey_id, selected_cols)
    else:
        selected_cols = [c for c in _get_survey_saved_cols_from_session(request, survey_id) if c in available_keys]

    if not selected_cols:
        default_base = [
            "answer_id",
            "customer_code",
            "customer_name",
            "personel",
            "user_full_name",
            "task_status",
            "visit_start_date",
            "visit_start_time",
            "visit_end_date",
            "visit_end_time",
            "visit_duration_min",
        ]
        q_cols = [c["key"] for c in cols if c["key"].startswith("q_")]
        selected_cols = [k for k in default_base if k in available_keys] + q_cols
    # Force required ID column to always be present and first
    if "answer_id" not in selected_cols:
        selected_cols = ["answer_id"] + [c for c in selected_cols if c != "answer_id"]
        _save_survey_cols_to_session(request, survey_id, selected_cols)

    qs = (
        VisitTask.objects.select_related("customer", "customer__cari")
        .filter(answers__question__survey=survey)
        .exclude(check_in_time__isnull=True)
        .distinct()
    )
    scope = get_hierarchy_scope_for_user(request.user, include_self=True)
    if scope.usernames:
        qs = qs.filter(merch_code__in=scope.usernames)
    if start_date and end_date:
        qs = qs.filter(check_in_time__date__gte=start_date, check_in_time__date__lte=end_date)
    qs = qs.order_by("-check_in_time", "-id")
    if latest_only:
        qs = _apply_latest_only_per_customer(
            base_qs=qs,
            survey=survey,
            scope_usernames=list(scope.usernames) if scope.usernames else None,
            start_date=start_date,
            end_date=end_date,
        )

    # Build maps for all usernames in export queryset
    usernames = list(qs.values_list("merch_code", flat=True).distinct())
    user_fullname_by_username, hierarchy_parent_by_username = _build_user_and_hierarchy_maps(usernames)

    # For export, compute answers for all tasks in one go
    task_ids = list(qs.values_list("id", flat=True))
    answers = (
        SurveyAnswer.objects.select_related("question")
        .filter(task_id__in=task_ids, question__survey=survey)
        .order_by("task_id", "question_id", "id")
    )
    bucket: dict[tuple[int, int], list[str]] = {}
    for a in answers:
        tid = a.task_id
        qid = a.question_id
        val = ""
        if getattr(a, "answer_text", None):
            val = str(a.answer_text).strip()
        elif getattr(a, "answer_photo", None):
            try:
                val = a.answer_photo.url
            except Exception:
                val = str(a.answer_photo)
        if val:
            bucket.setdefault((tid, qid), []).append(val)
    answers_map: dict[tuple[int, int], str] = {k: " | ".join(v) for k, v in bucket.items()}

    data = []
    for t in qs:
        row = {}
        for k in selected_cols:
            row[label_by_key.get(k, k)] = _task_to_survey_report_value(
                t,
                k,
                answers_map=answers_map,
                user_fullname_by_username=user_fullname_by_username,
                hierarchy_parent_by_username=hierarchy_parent_by_username,
            )
        data.append(row)

    filename = f"anket_raporu_{survey.id}_{(start_date or date.today()).strftime('%Y%m%d')}_{(end_date or date.today()).strftime('%Y%m%d')}.xlsx"
    content = xlsx_from_rows(data, sheet_name="Anket Raporu")
    response = HttpResponse(
        content,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f"attachment; filename={filename}"
    return response


def _get_accessible_survey_task_or_404(request, *, survey: Survey, task_id: int) -> VisitTask:
    """
    Returns a VisitTask that:
    - is within user's hierarchy scope
    - has at least one answer for the given survey
    """
    qs = (
        VisitTask.objects.select_related("customer", "customer__cari")
        .filter(id=task_id, answers__question__survey=survey)
        .exclude(check_in_time__isnull=True)
        .distinct()
    )
    scope = get_hierarchy_scope_for_user(request.user, include_self=True)
    if scope.usernames:
        qs = qs.filter(merch_code__in=scope.usernames)
    return get_object_or_404(qs, id=task_id)


@login_required
@require_http_methods(["GET", "POST"])
def survey_submission_edit(request, survey_id: int, task_id: int):
    """
    Edit a single survey submission (answers) identified by VisitTask.id (Cevap ID).
    Allows updating text answers and replacing photo answers.
    """
    survey = get_object_or_404(Survey, pk=survey_id)
    task = _get_accessible_survey_task_or_404(request, survey=survey, task_id=task_id)
    questions = list(Question.objects.filter(survey=survey).order_by("order", "id"))

    # Build latest answer per question
    latest_answers = {}
    for a in (
        SurveyAnswer.objects.select_related("question")
        .filter(task=task, question__survey=survey)
        .order_by("-id")
    ):
        qid = a.question_id
        if qid not in latest_answers:
            latest_answers[qid] = a

    if request.method == "POST":
        with transaction.atomic():
            for q in questions:
                field = f"q_{q.id}"
                existing = latest_answers.get(q.id)

                # Photo update
                if q.input_type == "photo":
                    uploaded = request.FILES.get(field)
                    if uploaded:
                        if not existing:
                            existing = SurveyAnswer.objects.create(task=task, question=q)
                            latest_answers[q.id] = existing
                        existing.answer_photo = uploaded
                        existing.answer_text = None
                        existing.save(update_fields=["answer_photo", "answer_text"])
                    continue

                # Text/select update
                incoming = (request.POST.get(field) or "").strip()
                if not existing:
                    existing = SurveyAnswer.objects.create(task=task, question=q)
                    latest_answers[q.id] = existing
                existing.answer_text = incoming
                # Don't touch photo for non-photo questions
                existing.save(update_fields=["answer_text"])

        messages.success(request, "Cevap güncellendi.")
        nxt = (request.POST.get("next") or "").strip()
        return redirect(nxt or "survey_report", survey_id=survey.id)

    # Build view model for template
    q_rows = []
    for q in questions:
        a = latest_answers.get(q.id)
        photo_url = ""
        if a and getattr(a, "answer_photo", None):
            try:
                photo_url = a.answer_photo.url
            except Exception:
                photo_url = ""
        q_rows.append(
            {
                "question": q,
                "field": f"q_{q.id}",
                "value": (a.answer_text if a else "") or "",
                "photo_url": photo_url,
            }
        )

    return render(
        request,
        "apps/reports/survey_submission_edit.html",
        {
            "survey": survey,
            "task": task,
            "answer_id": f"A-{task.id}",
            "questions": q_rows,
            "next": (request.GET.get("next") or "").strip(),
        },
    )


@login_required
@require_POST
def survey_submission_delete(request, survey_id: int, task_id: int):
    """
    Delete a survey submission from reports by deleting its SurveyAnswer rows
    (does NOT delete the VisitTask itself).
    """
    survey = get_object_or_404(Survey, pk=survey_id)
    task = _get_accessible_survey_task_or_404(request, survey=survey, task_id=task_id)
    SurveyAnswer.objects.filter(task=task, question__survey=survey).delete()
    messages.success(request, "Cevap silindi.")
    nxt = (request.GET.get("next") or request.POST.get("next") or "").strip()
    return redirect(nxt or "survey_report", survey_id=survey.id)


@login_required
@require_POST
def survey_report_import(request, survey_id: int):
    """
    Import survey answers from an Excel file using 'Cevap ID' column (A-<task_id>).
    - Updates only provided non-empty cells for text/select questions (photo questions are ignored).
    - If a row has Cevap ID but all other provided columns are empty => delete that submission (answers).
    Shows a summary like: '34 revize edildi, 1 silindi'.
    """
    survey = get_object_or_404(Survey, pk=survey_id)
    upload = request.FILES.get("file")
    if not upload:
        messages.error(request, "Dosya seçilmedi.")
        return redirect("survey_report", survey_id=survey.id)

    try:
        rows = xlsx_to_rows(upload)
    except Exception:
        messages.error(request, "Excel okunamadı. Lütfen .xlsx formatında yükleyin.")
        return redirect("survey_report", survey_id=survey.id)

    cols, label_by_key = _survey_report_columns(survey)
    reverse_label = {v: k for k, v in label_by_key.items() if v}

    # Identify ID column
    id_col = None
    for cand in ["Cevap ID", "cevap id", "Answer ID", "answer_id"]:
        for c in (rows[0].keys() if rows else []):
            if str(c).strip().lower() == str(cand).strip().lower():
                id_col = c
                break
        if id_col is not None:
            break
    if id_col is None:
        messages.error(request, "Excel'de 'Cevap ID' sütunu bulunamadı.")
        return redirect("survey_report", survey_id=survey.id)

    # Which columns can be imported? Only survey question columns and only non-photo questions.
    q_by_key = {f"q_{q.id}": q for q in Question.objects.filter(survey=survey).order_by("order", "id")}
    import_keys = []
    for c in (rows[0].keys() if rows else []):
        if c == id_col:
            continue
        key = reverse_label.get(str(c))
        if key and key in q_by_key and q_by_key[key].input_type != "photo":
            import_keys.append(key)

    if not import_keys:
        messages.error(request, "Excel'de güncellenecek soru kolonu bulunamadı (fotoğraf kolonları hariç).")
        return redirect("survey_report", survey_id=survey.id)

    def _parse_task_id(v) -> int | None:
        if v is None:
            return None
        s = str(v).strip()
        if not s:
            return None
        m = re.search(r"(\\d+)", s)
        if not m:
            return None
        try:
            return int(m.group(1))
        except Exception:
            return None

    task_ids = []
    for row in rows:
        tid = _parse_task_id(row.get(id_col))
        if tid:
            task_ids.append(tid)
    task_ids = list({t for t in task_ids if t})

    scope = get_hierarchy_scope_for_user(request.user, include_self=True)
    accessible_tasks = VisitTask.objects.filter(id__in=task_ids, answers__question__survey=survey).distinct()
    if scope.usernames:
        accessible_tasks = accessible_tasks.filter(merch_code__in=scope.usernames)
    accessible_by_id = {t.id: t for t in accessible_tasks}

    # Preload existing latest answers per (task_id, question_id)
    q_ids = [int(k.replace("q_", "", 1)) for k in import_keys]
    existing_answers = (
        SurveyAnswer.objects.filter(task_id__in=accessible_by_id.keys(), question_id__in=q_ids)
        .order_by("task_id", "question_id", "-id")
    )
    latest_answer_by_pair = {}
    for a in existing_answers:
        pair = (a.task_id, a.question_id)
        if pair not in latest_answer_by_pair:
            latest_answer_by_pair[pair] = a

    revised = 0
    deleted = 0
    skipped = 0

    with transaction.atomic():
        for row in rows:
            tid = _parse_task_id(row.get(id_col))
            if not tid:
                continue
            task = accessible_by_id.get(tid)
            if not task:
                skipped += 1
                continue

            # Determine if this row is a delete instruction (all provided import cells empty)
            any_value = False
            for k in import_keys:
                label = label_by_key.get(k, k)
                v = row.get(label)
                if v is None:
                    continue
                if str(v).strip() != "":
                    any_value = True
                    break

            if not any_value:
                SurveyAnswer.objects.filter(task=task, question__survey=survey).delete()
                deleted += 1
                continue

            did_update = False
            for k in import_keys:
                q = q_by_key.get(k)
                if not q:
                    continue
                label = label_by_key.get(k, k)
                v = row.get(label)
                if v is None:
                    continue
                s = str(v).strip()
                if s == "":
                    # If cell is blank, do not change existing value (safe behavior)
                    continue

                pair = (task.id, q.id)
                a = latest_answer_by_pair.get(pair)
                if not a:
                    a = SurveyAnswer.objects.create(task=task, question=q, answer_text=s)
                    latest_answer_by_pair[pair] = a
                else:
                    a.answer_text = s
                    a.save(update_fields=["answer_text"])
                did_update = True

            if did_update:
                revised += 1

    messages.success(request, f"{revised} cevap revize edildi, {deleted} cevap silindi. (Atlanan: {skipped})")
    nxt = (request.POST.get("next") or "").strip()
    return redirect(nxt or "survey_report", survey_id=survey.id)


# ----------------------------------------------------------------------------
# Trash (Reports)
# ----------------------------------------------------------------------------
@login_required
def reports_trash(request):
    purged = _purge_old_deleted_reports()
    retention = _get_report_trash_retention_days()

    qs = ReportRecord.objects.filter(deleted_at__isnull=False).order_by("-deleted_at")
    rows = []
    now = timezone.now()
    for r in qs:
        deleted_at = r.deleted_at or now
        age_days = (now - deleted_at).days
        days_left = max(0, retention - age_days) if retention > 0 else 0
        rows.append(
            {
                "report": r,
                "deleted_at": deleted_at,
                "days_left": days_left,
            }
        )

    return render(
        request,
        "apps/reports/trash.html",
        {"rows": rows, "retention_days": retention, "purged_count": purged},
    )


@login_required
@require_POST
def reports_trash_settings(request):
    raw = (request.POST.get("retention_days") or "").strip()
    try:
        days = int(raw)
    except Exception:
        days = DEFAULT_REPORT_TRASH_RETENTION_DAYS
    _set_report_trash_retention_days(days)
    messages.success(request, "Silinecek gün sayısı güncellendi.")
    return redirect("reports_trash")


@login_required
@require_POST
def reports_trash_restore(request, report_id: int):
    r = get_object_or_404(ReportRecord, pk=report_id)
    r.restore_from_trash()
    messages.success(request, "Rapor geri yüklendi.")
    # Redirect to its report page if it's a survey report
    if r.report_type == "survey":
        return redirect("survey_report", survey_id=r.object_id)
    return redirect("reports_trash")


@login_required
@require_POST
def reports_trash_delete_now(request, report_id: int):
    r = get_object_or_404(ReportRecord, pk=report_id)
    r.delete()
    messages.success(request, "Rapor kalıcı olarak silindi.")
    return redirect("reports_trash")


@login_required
@require_POST
def report_move_to_trash(request, report_id: int):
    r = get_object_or_404(ReportRecord, pk=report_id)
    r.move_to_trash()
    messages.warning(request, "Rapor çöp kutusuna taşındı.")
    return redirect("survey_reports_home")


@login_required
def visit_detail_report_export(request):
    # Reuse same logic as preview
    start_date = _parse_date_yyyy_mm_dd(request.GET.get("start_date"))
    end_date = _parse_date_yyyy_mm_dd(request.GET.get("end_date"))
    if not start_date and not end_date:
        start_date = date.today()
        end_date = date.today()
    if start_date and not end_date:
        end_date = start_date
    if end_date and not start_date:
        start_date = end_date

    cols, label_by_key = _visit_detail_report_columns()
    available_keys = set(label_by_key.keys())

    raw_cols = (request.GET.get("cols") or "").strip()
    if raw_cols:
        selected_cols = [c for c in raw_cols.split(",") if c]
        selected_cols = [c for c in selected_cols if c in available_keys]
        _save_cols_to_session(request, selected_cols)
    else:
        selected_cols = [c for c in _get_saved_cols_from_session(request) if c in available_keys]
    if not selected_cols:
        selected_cols = [
            "answer_id",
            "customer_code",
            "customer_name",
            "visit_start_date",
            "visit_start_time",
            "visit_end_date",
            "visit_end_time",
            "visit_duration_min",
        ]
    # Force required ID column to always be present and first
    if "answer_id" not in selected_cols:
        selected_cols = ["answer_id"] + [c for c in selected_cols if c != "answer_id"]
        _save_cols_to_session(request, selected_cols)

    qs = VisitTask.objects.select_related("customer", "customer__cari").all()
    scope = get_hierarchy_scope_for_user(request.user, include_self=True)
    if scope.usernames:
        qs = qs.filter(merch_code__in=scope.usernames)
    qs = qs.exclude(check_in_time__isnull=True)
    if start_date and end_date:
        qs = qs.filter(check_in_time__date__gte=start_date, check_in_time__date__lte=end_date)
    qs = qs.order_by("-check_in_time", "-id")

    usernames = list(qs.values_list("merch_code", flat=True).distinct())
    user_fullname_by_username, hierarchy_parent_by_username = _build_user_and_hierarchy_maps(usernames)

    data = []
    for t in qs:
        row = {}
        for k in selected_cols:
            row[label_by_key.get(k, k)] = _task_to_report_value(
                t,
                k,
                user_fullname_by_username=user_fullname_by_username,
                hierarchy_parent_by_username=hierarchy_parent_by_username,
            )
        data.append(row)

    filename = f"detayli_ziyaret_raporu_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.xlsx"
    content = xlsx_from_rows(data, sheet_name="Detaylı Ziyaret")
    response = HttpResponse(
        content,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f"attachment; filename={filename}"
    return response

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
            rows = xlsx_to_rows(request.FILES['excel_file'])
            if not rows:
                messages.error(request, "Excel boş veya okunamadı.")
                return HttpResponseRedirect(referer)
            columns = list(rows[0].keys())
            
            # Sütunları Bul
            day_columns = {} 
            for col in columns:
                match = re.search(r'(?:G[uü]n)\s*(\d+)', col, re.IGNORECASE)
                if match:
                    day_num = int(match.group(1))
                    if 1 <= day_num <= 28:
                        day_columns[col] = day_num
            
            if not day_columns:
                messages.error(request, "Excel'de 'Gün X' sütunları bulunamadı.")
                return HttpResponseRedirect(referer)

            merch_col = next((c for c in columns if 'Saha' in c or 'Personel' in c or 'Merch' in c), None)
            if not merch_col:
                messages.error(request, "Personel sütunu bulunamadı.")
                return HttpResponseRedirect(referer)

            unique_merchs = []
            seen_merchs = set()
            for r in rows:
                v = r.get(merch_col)
                if v is None:
                    continue
                s = str(v).strip()
                if not s or s.lower() == "nan":
                    continue
                if s not in seen_merchs:
                    unique_merchs.append(s)
                    seen_merchs.add(s)
            success_count = 0
            task_action_count = 0
            
            # --- VERİTABANI İŞLEMİ ---
            with transaction.atomic():
                for merch_name in unique_merchs:
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
                    merch_rows = [r for r in rows if str(r.get(merch_col) or "").strip() == merch_name]
                    
                    for row in merch_rows:
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