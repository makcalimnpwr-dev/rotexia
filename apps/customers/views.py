from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.db.models import Q
from .models import Customer, CustomerCari, CustomerFieldDefinition, CustomFieldDefinition
from apps.core.tenant_utils import filter_by_tenant, set_tenant_on_save, get_current_tenant
import json
import csv
import openpyxl
from datetime import datetime
from django.utils.text import slugify
import unicodedata

@login_required
def customer_list(request):
    """Müşteri listesi ve filtreleme"""
    search_query = request.GET.get('search', '')
    sort = request.GET.get('sort', 'name_asc')
    
    # Sıralama
    if sort == 'name_desc':
        db_sort_field = '-name'
    elif sort == 'created_desc':
        db_sort_field = '-created_at'
    elif sort == 'created_asc':
        db_sort_field = 'created_at'
    else:
        db_sort_field = 'name'
        
    # Filtreleme
    if search_query:
        customer_qs = filter_by_tenant(Customer.objects.all(), request).filter(
            Q(name__icontains=search_query) | 
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(customer_code__icontains=search_query)
        ).order_by(db_sort_field)
    else:
        # Tüm müşterileri getir
        customer_qs = filter_by_tenant(Customer.objects.all(), request).order_by(db_sort_field)
        
    context = {
        'customers': customer_qs,
        'search_query': search_query,
        'sort': sort,
        'custom_fields': filter_by_tenant(CustomerFieldDefinition.objects.all(), request)
    }
    return render(request, 'apps/customers/customer_list.html', context)

@login_required
def add_customer(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        city = request.POST.get('city')
        district = request.POST.get('district')
        customer_code = request.POST.get('customer_code')
        
        customer = Customer(
            name=name,
            email=email,
            phone=phone,
            address=address,
            city=city,
            district=district,
            customer_code=customer_code
        )
        set_tenant_on_save(customer, request)
        customer.save()
        
        # Özel alanları kaydet
        custom_data = {}
        for field in filter_by_tenant(CustomerFieldDefinition.objects.all(), request):
            value = request.POST.get(f'custom_field_{field.id}')
            if value:
                custom_data[field.name] = value
        
        if custom_data:
            customer.custom_data = custom_data
            customer.save()
            
        messages.success(request, 'Müşteri başarıyla eklendi.')
        return redirect('customer_list')
        
    return render(request, 'apps/customers/add_customer.html', {
        'custom_fields': filter_by_tenant(CustomerFieldDefinition.objects.all(), request)
    })

@login_required
def edit_customer(request, pk):
    customer = get_object_or_404(filter_by_tenant(Customer.objects.all(), request), pk=pk)
    
    if request.method == 'POST':
        customer.name = request.POST.get('name')
        customer.email = request.POST.get('email')
        customer.phone = request.POST.get('phone')
        customer.address = request.POST.get('address')
        customer.city = request.POST.get('city')
        customer.district = request.POST.get('district')
        customer.customer_code = request.POST.get('customer_code')
        
        # Özel alanları güncelle
        custom_data = customer.custom_data or {}
        for field in filter_by_tenant(CustomerFieldDefinition.objects.all(), request):
            value = request.POST.get(f'custom_field_{field.id}')
            if value:
                custom_data[field.name] = value
            elif field.name in custom_data: # Değer silindiyse
                del custom_data[field.name]
                
        customer.custom_data = custom_data
        customer.save()
        
        messages.success(request, 'Müşteri bilgileri güncellendi.')
        return redirect('customer_list')
        
    return render(request, 'apps/customers/add_customer.html', {
        'customer': customer,
        'is_edit': True,
        'custom_fields': filter_by_tenant(CustomerFieldDefinition.objects.all(), request)
    })

@login_required
def delete_customer(request, pk):
    if request.method == 'POST':
        customer = get_object_or_404(filter_by_tenant(Customer.objects.all(), request), pk=pk)
        customer.delete()
        messages.success(request, 'Müşteri silindi.')
    return redirect('customer_list')

@login_required
def customer_map_view(request):
    customers = filter_by_tenant(Customer.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True), request)
    return render(request, 'apps/customers/map_view.html', {'customers': customers})

@login_required
def bulk_customer_action(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        selected_ids = request.POST.getlist('selected_customers')
        
        if not selected_ids:
            messages.warning(request, 'Lütfen en az bir müşteri seçin.')
            return redirect('customer_list')
            
        if action == 'delete':
            filter_by_tenant(Customer.objects.filter(id__in=selected_ids), request).delete()
            messages.success(request, f'{len(selected_ids)} müşteri silindi.')
            
    return redirect('customer_list')

@login_required
def add_custom_field(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        field_type = request.POST.get('type')
        
        if name and field_type:
            field = CustomerFieldDefinition(name=name, field_type=field_type)
            set_tenant_on_save(field, request)
            field.save()
            messages.success(request, 'Özel alan eklendi.')
            
    return redirect('customer_list')

@login_required
def cari_settings(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        code = request.POST.get('code')
        if name:
            cari = CustomerCari(name=name, code=code)
            set_tenant_on_save(cari, request)
            cari.save()
            messages.success(request, 'Cari eklendi.')
            
    caris = filter_by_tenant(CustomerCari.objects.all(), request)
    return render(request, 'apps/customers/cari_settings.html', {'caris': caris})

@login_required
def delete_cari(request, pk):
    if request.method == 'POST':
        cari = get_object_or_404(filter_by_tenant(CustomerCari.objects.all(), request), pk=pk)
        cari.delete()
        messages.success(request, 'Cari silindi.')
    return redirect('cari_settings')

@login_required
def export_customers(request):
    # CSV export implementation
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="musteriler.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Ad', 'Kod', 'Email', 'Telefon', 'Şehir', 'İlçe', 'Adres'])
    
    customers = filter_by_tenant(Customer.objects.all(), request)
    for c in customers:
        writer.writerow([c.name, c.customer_code, c.email, c.phone, c.city, c.district, c.address])
        
    return response

@login_required
def import_customers(request):
    """
    Excel (.xlsx) ile müşteri import.
    - Zorunlu sütunlar: Kod, Müşteri, İl, İlçe
    - Opsiyonel: Cari/Firma, Adres, Telefon, Yetkili, Enlem, Boylam + Özel Alanlar
    Hata durumunda kullanıcıya eksik/yanlış sütun ve satır bazlı hataları bildirir.
    """
    if request.method != 'POST':
        return redirect('customer_list')

    tenant = get_current_tenant(request)
    if not tenant:
        messages.error(request, "Tenant bilgisi bulunamadı. Lütfen önce firmaya bağlanın.")
        return redirect('customer_list')

    f = request.FILES.get('excel_file')
    if not f:
        messages.error(request, "Lütfen bir Excel dosyası seçin.")
        return redirect('customer_list')

    filename = (getattr(f, "name", "") or "").lower()
    if filename.endswith(".xls") and not filename.endswith(".xlsx"):
        messages.error(request, "Şu an sadece .xlsx dosyaları destekleniyor. Lütfen dosyanızı .xlsx olarak kaydedip tekrar deneyin.")
        return redirect('customer_list')

    # Header normalize (Türkçe/Unicode güvenli)
    # Excel başlıklarında "İl" gibi büyük İ -> lower() sonrası "i̇l" (combining dot) olur.
    # Bunu yakalamak için NFKD + combining mark temizliği + Türkçe harf map uygula.
    tr_map = str.maketrans({"ç": "c", "ğ": "g", "ş": "s", "ü": "u", "ı": "i", "ö": "o"})

    def norm(s: str) -> str:
        s = (s or "").strip()
        # casefold unicode için daha güvenli
        s = s.casefold()
        # NFKD + combining mark temizle (örn: i̇ -> i)
        s = unicodedata.normalize("NFKD", s)
        s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
        # Türkçe map + boşluk/altçizgi/tire temizliği
        s = s.translate(tr_map)
        s = s.replace(" ", "").replace("_", "").replace("-", "")
        return s

    # Excel oku
    try:
        wb = openpyxl.load_workbook(f, data_only=True)
        ws = wb.active
    except Exception as e:
        messages.error(request, f"Excel okunamadı: {e}")
        return redirect('customer_list')

    rows = list(ws.iter_rows(values_only=True))
    if not rows or not rows[0]:
        messages.error(request, "Excel dosyası boş görünüyor.")
        return redirect('customer_list')

    header_row = [str(h).strip() if h is not None else "" for h in rows[0]]
    if not any(header_row):
        messages.error(request, "Excel başlık satırı boş. Lütfen ilk satırda sütun başlıkları olduğundan emin olun.")
        return redirect('customer_list')

    header_map = {norm(h): idx for idx, h in enumerate(header_row) if h}

    # Desteklenen sütun isimleri -> alan
    aliases = {
        "kod": "customer_code",
        "musterikodu": "customer_code",
        "customercode": "customer_code",
        "musteri": "name",
        "musteriadi": "name",
        "ad": "name",
        "il": "city",
        "sehir": "city",
        "city": "city",
        "ilce": "district",
        "district": "district",
        "adres": "address",
        "acikadres": "address",
        "telefon": "phone",
        "tel": "phone",
        "yetkili": "authorized_person",
        "yetkilikisi": "authorized_person",
        "authorizedperson": "authorized_person",
        "cari": "cari",
        "carifirma": "cari",
        "firma": "cari",
        "enlem": "latitude",
        "latitude": "latitude",
        "boylam": "longitude",
        "longitude": "longitude",
        "sysid": "sys_id",
        "sistemid": "sys_id",
    }

    # Header -> field index map
    field_idx = {}
    unknown_headers = []
    for raw_h in header_row:
        key = norm(raw_h)
        if not key:
            continue
        if key in aliases:
            field_idx[aliases[key]] = header_map[key]
        else:
            unknown_headers.append(raw_h)

    required_fields = ["customer_code", "name", "city", "district"]
    missing = [f for f in required_fields if f not in field_idx]
    if missing:
        friendly = {
            "customer_code": "Kod",
            "name": "Müşteri",
            "city": "İl",
            "district": "İlçe",
        }
        missing_names = ", ".join([friendly.get(m, m) for m in missing])
        messages.error(
            request,
            f"❌ Eksik sütun(lar): {missing_names}. Excel başlıkları: {', '.join([h for h in header_row if h])}"
        )
        return redirect('customer_list')

    # Özel alanlar: kalan sütunları extra_data'ya yaz
    # Var olan custom alan tanımları varsa onlarla eşleştir (slug üzerinden)
    custom_defs = list(CustomFieldDefinition.objects.all())
    custom_slug_set = {d.slug: d for d in custom_defs}

    def parse_float(v):
        if v is None or v == "":
            return None
        if isinstance(v, (int, float)):
            return float(v)
        s = str(v).strip().replace(",", ".")
        return float(s)

    created = 0
    updated = 0
    errors = []

    # Data satırları
    for r_i, row in enumerate(rows[1:], start=2):  # Excel satır no = 1-based
        if row is None:
            continue

        def get(field):
            idx = field_idx.get(field)
            return row[idx] if idx is not None and idx < len(row) else None

        code = (get("customer_code") or "").strip() if isinstance(get("customer_code"), str) else str(get("customer_code") or "").strip()
        name = (get("name") or "").strip() if isinstance(get("name"), str) else str(get("name") or "").strip()
        city = (get("city") or "").strip() if isinstance(get("city"), str) else str(get("city") or "").strip()
        district = (get("district") or "").strip() if isinstance(get("district"), str) else str(get("district") or "").strip()

        if not code:
            errors.append(f"Satır {r_i}: Kod boş.")
            continue
        if not name:
            errors.append(f"Satır {r_i}: Müşteri adı boş.")
            continue
        if not city:
            errors.append(f"Satır {r_i}: İl boş.")
            continue
        if not district:
            errors.append(f"Satır {r_i}: İlçe boş.")
            continue

        # Cari
        cari_obj = None
        cari_val = get("cari")
        if cari_val is not None and str(cari_val).strip():
            cari_name = str(cari_val).strip()
            cari_obj, _ = CustomerCari.objects.get_or_create(name=cari_name)

        # Koordinatlar
        try:
            lat = parse_float(get("latitude"))
        except Exception:
            errors.append(f"Satır {r_i}: Enlem (latitude) sayı olmalı.")
            lat = None
        try:
            lng = parse_float(get("longitude"))
        except Exception:
            errors.append(f"Satır {r_i}: Boylam (longitude) sayı olmalı.")
            lng = None

        # Opsiyoneller
        address = get("address")
        phone = get("phone")
        authorized = get("authorized_person")

        # extra_data: bilinen alanlar dışındaki sütunları ekle
        extra = {}
        for col_i, raw_h in enumerate(header_row):
            if not raw_h:
                continue
            k_norm = norm(raw_h)
            if not k_norm:
                continue
            if k_norm in aliases:  # bilinen
                continue

            val = row[col_i] if col_i < len(row) else None
            if val is None or str(val).strip() == "":
                continue

            slug = slugify(str(raw_h).strip().translate(tr_map))
            if slug in custom_slug_set:
                extra[slug] = str(val).strip()
            else:
                # tanım yoksa da slug ile yaz (sonradan alan tanımı eklenince görünür)
                extra[slug] = str(val).strip()

        # Upsert
        existing = Customer.objects.filter(customer_code=code).first()
        if existing and existing.tenant_id and existing.tenant_id != tenant.id:
            errors.append(f"Satır {r_i}: Kod '{code}' başka firmaya ait ({existing.tenant}).")
            continue

        if existing:
            existing.name = name
            existing.city = city
            existing.district = district
            existing.address = str(address).strip() if address is not None else None
            existing.phone = str(phone).strip() if phone is not None else None
            existing.authorized_person = str(authorized).strip() if authorized is not None else None
            existing.cari = cari_obj
            existing.latitude = lat
            existing.longitude = lng
            existing.tenant = tenant
            existing.extra_data = {**(existing.extra_data or {}), **extra}
            existing.save()
            updated += 1
        else:
            c = Customer(
                customer_code=code,
                name=name,
                city=city,
                district=district,
                address=str(address).strip() if address is not None else None,
                phone=str(phone).strip() if phone is not None else None,
                authorized_person=str(authorized).strip() if authorized is not None else None,
                cari=cari_obj,
                latitude=lat,
                longitude=lng,
                tenant=tenant,
                extra_data=extra,
            )
            c.save()
            created += 1

    # Mesajlar
    if unknown_headers:
        # Bilgi amaçlı: import yine de yapıldı, sadece eşleştirilmemiş sütunları bildir
        uniq_unknown = []
        for h in unknown_headers:
            if h and h not in uniq_unknown:
                uniq_unknown.append(h)
        if uniq_unknown:
            messages.info(request, f"ℹ️ Bilinmeyen sütunlar extra_data olarak kaydedildi: {', '.join(uniq_unknown[:10])}" + (" ..." if len(uniq_unknown) > 10 else ""))

    if created or updated:
        messages.success(request, f"✅ Import tamamlandı. Yeni: {created}, Güncellenen: {updated}")

    if errors:
        preview = "<br>".join(errors[:12])
        more = f"<br>... (+{len(errors)-12} hata)" if len(errors) > 12 else ""
        messages.error(request, f"❌ Import sırasında bazı hatalar oluştu:<br>{preview}{more}")

    if not created and not updated and not errors:
        messages.info(request, "ℹ️ Import edilecek satır bulunamadı.")

    return redirect('customer_list')
