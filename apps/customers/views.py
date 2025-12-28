import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Q
from django.core.paginator import Paginator # Sayfalama Modülü
from .models import Customer, CustomerCari, CustomFieldDefinition
from .forms import CustomerForm, CariForm, CustomFieldForm
from apps.users.hierarchy_access import get_hierarchy_scope_for_user
from django.db.models import Q as DQ

# --- LİSTE VE SAYFALAMA ---
@login_required
def customer_list(request):
    # 1. SIRALAMA (Mevcut Mantık)
    sort_by = request.GET.get('sort', '-created_at')
    direction = request.GET.get('dir', 'desc')
    
    valid_sort_fields = {'id': 'id', 'code': 'customer_code', 'name': 'name', 'cari': 'cari__name', 'city': 'city', 'district': 'district', 'auth': 'authorized_person'}
    db_sort_field = valid_sort_fields.get(sort_by, '-created_at')
    if direction == 'desc' and not db_sort_field.startswith('-'): db_sort_field = f'-{db_sort_field}'
    
    # 2. TEMEL SORGULAR
    customer_qs = Customer.objects.all().order_by(db_sort_field)

    # Hiyerarşi bazlı filtre: Admin değilse sadece kendi/altının müşteri havuzu
    scope = get_hierarchy_scope_for_user(request.user, include_self=True)
    if scope.usernames:
        customer_qs = customer_qs.filter(
            DQ(visittask__merch_code__in=scope.usernames) | DQ(routeplan__merch_code__in=scope.usernames)
        ).distinct()
    cariler = CustomerCari.objects.all()
    custom_fields = CustomFieldDefinition.objects.all() # Özel alan tanımları

    # 3. GELİŞMİŞ FİLTRELEME (Her Sütun İçin Ayrı Filtre)
    
    # A. Standart Alan Filtreleri
    f_search = request.GET.get('search', '')    # Genel Arama (Hala kalsın, hızlı arama için)
    f_code = request.GET.get('f_code', '')      # Müşteri Kodu
    f_name = request.GET.get('f_name', '')      # Müşteri Adı
    f_cari = request.GET.get('f_cari', '')      # Cari ID
    f_city = request.GET.get('f_city', '')      # İl
    f_district = request.GET.get('f_district', '') # İlçe
    f_auth = request.GET.get('f_auth', '')      # Yetkili
    f_phone = request.GET.get('f_phone', '')    # Telefon

    # Filtreleri Uygula
    if f_search:
        customer_qs = customer_qs.filter(Q(name__icontains=f_search) | Q(customer_code__icontains=f_search))
    if f_code: customer_qs = customer_qs.filter(customer_code__icontains=f_code)
    if f_name: customer_qs = customer_qs.filter(name__icontains=f_name)
    if f_cari: customer_qs = customer_qs.filter(cari_id=f_cari)
    if f_city: customer_qs = customer_qs.filter(city__icontains=f_city)
    if f_district: customer_qs = customer_qs.filter(district__icontains=f_district)
    if f_auth: customer_qs = customer_qs.filter(authorized_person__icontains=f_auth)
    if f_phone: customer_qs = customer_qs.filter(phone__icontains=f_phone)

    # B. Özel Alan Filtreleri (Dinamik)
    # URL'den "custom_stant-tipi=123" gibi gelenleri yakalar
    filter_values = {} # Şablonda kutucukların içi boşalmasın diye değerleri saklıyoruz
    
    for cf in custom_fields:
        # Form elemanının adı: custom_slug (Örn: custom_stant-tipi)
        val = request.GET.get(f"custom_{cf.slug}", '')
        if val:
            # JSONField içinde arama yap: extra_data__slug__icontains
            filter_kwargs = {f"extra_data__{cf.slug}__icontains": val}
            customer_qs = customer_qs.filter(**filter_kwargs)
            filter_values[cf.slug] = val

    # 4. SAYFALAMA
    paginator = Paginator(customer_qs, 50)
    page_number = request.GET.get('page')
    customers_page = paginator.get_page(page_number)

    context = {
        'customers': customers_page,
        'paginator': paginator,
        'cariler': cariler,
        'custom_fields': custom_fields,
        
        # Filtre Değerlerini Geri Gönder (Kutular silinmesin)
        'f_search': f_search,
        'f_code': f_code,
        'f_name': f_name,
        'f_cari': int(f_cari) if f_cari.isdigit() else '',
        'f_city': f_city,
        'f_district': f_district,
        'f_auth': f_auth,
        'f_phone': f_phone,
        'filter_values': filter_values, # Özel alan değerleri
        
        'current_sort': sort_by,
        'current_dir': direction
    }
    return render(request, 'apps/customers/customer_list.html', context)

# --- YENİ ÖZEL ALAN EKLEME ---
@login_required
def add_custom_field(request):
    if request.method == 'POST':
        form = CustomFieldForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Yeni alan tüm müşterilere eklendi.")
        else:
            messages.error(request, "Bu alan adı zaten var veya geçersiz.")
    # Nereden geldiyse oraya dön (Listeye veya Detaya)
    return redirect(request.META.get('HTTP_REFERER', 'customer_list'))

# --- DİĞER STANDART İŞLEMLER (Öncekilerin Aynısı - Kısaltılmış) ---
@login_required
def bulk_customer_action(request):
    if request.method == 'POST':
        selected_ids = request.POST.getlist('selected_ids')
        action_type = request.POST.get('action_type')
        if not selected_ids: return redirect('customer_list')

        if action_type == 'delete':
            Customer.objects.filter(id__in=selected_ids).delete()
            messages.success(request, "Silindi.")
        elif action_type == 'bulk_edit':
            target_field = request.POST.get('target_field')
            new_value = request.POST.get('new_value')
            if target_field == 'cari':
                if new_value: Customer.objects.filter(id__in=selected_ids).update(cari_id=new_value)
            else:
                Customer.objects.filter(id__in=selected_ids).update(**{target_field: new_value})
            messages.success(request, "Güncellendi.")
    return redirect('customer_list')

@login_required
def add_customer(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Müşteri eklendi.")
            return redirect('customer_list')
    else: form = CustomerForm()
    return render(request, 'apps/customers/add_customer.html', {'form': form})

@login_required
def edit_customer(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, "Güncellendi.")
            return redirect('customer_list')
    else: form = CustomerForm(instance=customer)
    return render(request, 'apps/customers/add_customer.html', {'form': form, 'title': f"{customer.name} - Düzenle"})

@login_required
def delete_customer(request, pk):
    get_object_or_404(Customer, pk=pk).delete()
    return redirect('customer_list')

@login_required
def cari_settings(request):
    cariler = CustomerCari.objects.all().order_by('name')
    if request.method == 'POST':
        form = CariForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('cari_settings')
    else: form = CariForm()
    return render(request, 'apps/customers/cari_settings.html', {'cariler': cariler, 'form': form})

@login_required
def delete_cari(request, pk):
    get_object_or_404(CustomerCari, pk=pk).delete()
    return redirect('cari_settings')

# Excel kısımları aynı kalacak, sadece JSON desteği eklenecek (uzun olmasın diye buraya yazmadım ama import/export içinde extra_data okunmalı)
# Şimdilik temel fonksiyonları veriyorum.
# apps/customers/views.py içindeki export_customers GÜNCELLENMİŞ HALİ

@login_required
def export_customers(request):
    customers = Customer.objects.all()
    selected_fields = request.GET.get('fields', '')
    
    # TAM SÜTUN HARİTASI (Checkbox Value -> Excel Başlığı)
    field_map = {
        'sys_id': 'Sistem ID',
        'code': 'Müşteri Kodu',
        'name': 'Müşteri Adı',
        'cari': 'Cari / Firma',
        'city': 'İl',
        'district': 'İlçe',
        'phone': 'Telefon',
        'auth': 'Yetkili Kişi',
        'address': 'Adres',
        'latitude': 'Enlem',   # Artık seçilebilir
        'longitude': 'Boylam'  # Artık seçilebilir
    }

    # Özel alanları da haritaya ekle
    custom_fields = CustomFieldDefinition.objects.all()
    for cf in custom_fields:
        field_map[f"custom_{cf.slug}"] = cf.name

    if selected_fields: requested_keys = selected_fields.split(',')

    else:
        requested_keys = field_map.keys()

    data = []
    for c in customers:
        row = {}
        # Standart Alanlar
        if 'sys_id' in requested_keys: row[field_map['sys_id']] = f"M-{c.id}"
        if 'code' in requested_keys: row[field_map['code']] = c.customer_code
        if 'name' in requested_keys: row[field_map['name']] = c.name
        if 'cari' in requested_keys: row[field_map['cari']] = c.cari.name if c.cari else ''
        if 'city' in requested_keys: row[field_map['city']] = c.city
        if 'district' in requested_keys: row[field_map['district']] = c.district
        if 'phone' in requested_keys: row[field_map['phone']] = c.phone
        if 'auth' in requested_keys: row[field_map['auth']] = c.authorized_person
        if 'address' in requested_keys: row[field_map['address']] = c.address
        
        # Koordinatlar (Formatlı)
        if 'latitude' in requested_keys: 
            row[field_map['latitude']] = str(c.latitude).replace('.', ',') if c.latitude else ''
        if 'longitude' in requested_keys: 
            row[field_map['longitude']] = str(c.longitude).replace('.', ',') if c.longitude else ''
        
        # Özel Alanlar
        for cf in custom_fields:
            key = f"custom_{cf.slug}"
            if key in requested_keys:
                row[field_map[key]] = c.extra_data.get(cf.slug, '')
        
        data.append(row)
    
    df = pd.DataFrame(data)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=musteri_listesi.xlsx'
    df.to_excel(response, index=False)
    return response

# Bu fonksiyonu views.py içindeki boş olanla değiştir:

@login_required
def import_customers(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        try:
            df = pd.read_excel(request.FILES['excel_file'])
            df = df.where(pd.notnull(df), None)
            
            # 2. Standart Sütun Eşleştirmesi
            col_map = {
                'Müşteri Kodu': 'customer_code',
                'Müşteri Adı': 'name',
                'İl': 'city',
                'İlçe': 'district',
                'Enlem': 'latitude',
                'Boylam': 'longitude',
                'Telefon': 'phone',
                'Yetkili Kişi': 'authorized_person',
                'Adres': 'address'
            }

            # 3. Özel Alanları Hazırla
            custom_field_defs = CustomFieldDefinition.objects.all()
            custom_map = {cf.name: cf.slug for cf in custom_field_defs}

            updated_count = 0
            created_count = 0
            excel_columns = df.columns.tolist()

            for index, row in df.iterrows():
                # --- A. ID KONTROLÜ ---
                raw_id = row.get('Sistem ID')
                sys_id = None
                if raw_id:
                    clean_id = str(raw_id).upper().replace('M-', '').replace('M', '').strip()
                    if clean_id.isdigit():
                        sys_id = int(clean_id)

                # --- B. VERİ HAZIRLIĞI ---
                update_data = {}
                extra_data_update = {} 

                # 1. Cari / Firma İşlemi
                if 'Cari / Firma' in excel_columns:
                    cari_val = row.get('Cari / Firma')
                    if cari_val:
                        cari_obj, _ = CustomerCari.objects.get_or_create(name=str(cari_val).strip())
                        update_data['cari'] = cari_obj

                # 2. Standart Alanları Doldur
                for excel_col, db_field in col_map.items():
                    if excel_col in excel_columns:
                        val = row.get(excel_col)
                        # Koordinat Düzeltme
                        if db_field in ['latitude', 'longitude'] and val is not None:
                            try: val = float(str(val).replace(',', '.'))
                            except: val = None
                        update_data[db_field] = val

                # 3. Özel Alanları (JSON) Doldur
                for cf_name, cf_slug in custom_map.items():
                    if cf_name in excel_columns:
                        val = row.get(cf_name)
                        if val is not None:
                            extra_data_update[cf_slug] = str(val)

                # --- C. KAYIT / GÜNCELLEME ---
                if sys_id:
                    # GÜNCELLEME
                    customer = Customer.objects.filter(id=sys_id).first()
                    if customer:
                        for k, v in update_data.items():
                            setattr(customer, k, v)
                        
                        if extra_data_update:
                            if not customer.extra_data: customer.extra_data = {}
                            customer.extra_data.update(extra_data_update)
                        
                        customer.save()
                        updated_count += 1
                else:
                    # YENİ KAYIT
                    if 'name' in update_data and update_data['name']:
                        if 'customer_code' not in update_data:
                            import random
                            update_data['customer_code'] = f"AUTO-{random.randint(10000,99999)}"
                        
                        customer = Customer(**update_data)
                        customer.extra_data = extra_data_update
                        customer.save()
                        created_count += 1

            messages.success(request, f"✅ İşlem Tamamlandı: {updated_count} güncellendi, {created_count} yeni eklendi.")
            
        except Exception as e:
            messages.error(request, f"❌ Hata oluştu: {str(e)}")
            
    # İŞTE EKSİK OLAN SATIR BUYDU:
    return redirect('customer_list')

            # apps/customers/views.py dosyasının en altina ekle:

import json
from django.core.serializers.json import DjangoJSONEncoder

@login_required
def customer_map_view(request):
    # URL'den gelen ID'leri al (Örn: ?ids=1,5,8)
    selected_ids = request.GET.get('ids', '')
    
    locations = []
    if selected_ids:
        id_list = selected_ids.split(',')
        # Sadece koordinatı olanları seç
        customers = Customer.objects.filter(id__in=id_list).exclude(latitude__isnull=True).exclude(longitude__isnull=True)
        
        for c in customers:
            locations.append({
                'name': c.name,
                'lat': c.latitude,
                'lng': c.longitude,
                'cari': c.cari.name if c.cari else '',
                'city': c.city
            })
    
    context = {
        'locations_json': json.dumps(locations, cls=DjangoJSONEncoder)
    }
    return render(request, 'apps/customers/map_view.html', context)