from django.shortcuts import render, redirect
from django.contrib.auth import login, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import models
from django.core.files.base import ContentFile
from .models import SystemSetting
# VisitTask modelini doğru adresten çağırıyoruz:
from apps.field_operations.models import VisitTask
from .utils import calculate_distance
from datetime import date
import json


# Gerekli Modeller
from apps.field_operations.models import VisitTask
from apps.customers.models import Customer
from apps.forms.models import Survey, SurveyAnswer, Question

from .models import SystemSetting

def init_default_settings():
    """Sistemde hiç ayar yoksa varsayılanları oluşturur."""
    defaults = [
        # --- GENEL AYARLAR ---
        {
            'key': 'app_sync_interval',
            'label': 'Mobil Senkronizasyon Süresi (Dakika)',
            'value': '15',
            'category': 'general',
            'input_type': 'number',
            'description': 'Mobil uygulamanın sunucudan yeni verileri çekme sıklığı.'
        },
        {
            'key': 'maintenance_mode',
            'label': 'Bakım Modu',
            'value': 'False',
            'category': 'general',
            'input_type': 'bool',
            'description': 'Açılırsa sadece yöneticiler sisteme girebilir.'
        },
        
        # --- ZİYARET AYARLARI ---
        {
            'key': 'visit_radius',
            'label': 'Mağaza Giriş Mesafesi (Metre)',
            'value': '300', # 300 metre
            'category': 'visit',
            'input_type': 'number',
            'description': 'Personel mağazaya en fazla ne kadar uzaktayken ziyaret başlatabilir?'
        },
        {
            'key': 'distance_rule',
            'label': 'Mesafe Kuralı',
            'value': 'True',
            'category': 'visit',
            'input_type': 'bool',
            'description': 'Açık: Giriş mesafesi ve gezinme mesafesi kontrolü yapılır. Kapalı: Mesafe kontrolü yapılmaz, herhangi bir mesafeden ziyaret başlatılabilir.'
        },
        {
            'key': 'wander_radius',
            'label': 'Gezinme Sınırı (Metre)',
            'value': '500',
            'category': 'visit',
            'input_type': 'number',
            'description': 'Ziyaret sırasında mağaza konumundan maksimum uzaklaşma mesafesi. Bu mesafeyi aşarsa ziyaret otomatik bitirilir.'
        },
    ]

    for setting in defaults:
        # Eğer bu ayar veritabanında yoksa oluştur
        if not SystemSetting.objects.filter(key=setting['key']).exists():
            SystemSetting.objects.create(**setting)

# --- OTOMATİK GİRİŞ ---
def auto_login(request):
    User = get_user_model()
    user = User.objects.filter(is_superuser=True).first()
    if not user:
        user = User.objects.first()
    
    if user:
        if not user.is_active:
            user.is_active = True
            user.save()
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return redirect('home')
    else:
        return render(request, 'base.html', {'content': 'Kullanıcı yok...'})
    

from .models import SystemSetting

@login_required
def settings_home(request):
    
    # --- 0. ESKİ AYARLARI MİGRATE ET ---
    # Eğer eski require_gps ayarı varsa, distance_rule olarak güncelle
    old_require_gps = SystemSetting.objects.filter(key='require_gps').first()
    if old_require_gps:
        # Yeni ayar zaten var mı kontrol et
        if not SystemSetting.objects.filter(key='distance_rule').exists():
            # Eski ayarı yeni isimle güncelle
            old_require_gps.key = 'distance_rule'
            old_require_gps.label = 'Mesafe Kuralı'
            old_require_gps.description = 'Açık: Giriş mesafesi ve gezinme mesafesi kontrolü yapılır. Kapalı: Mesafe kontrolü yapılmaz, herhangi bir mesafeden ziyaret başlatılabilir.'
            old_require_gps.save()
        else:
            # Yeni ayar zaten varsa, eski ayarı sil
            old_require_gps.delete()
    
    # --- 1. ÖNCE TEMİZLİK (Eski/Bozuk verileri sil) ---
    # Eğer hiç ayar görünmüyorsa, bu satır tabloyu sıfırlar ve temiz kurulum yapar.
    if not SystemSetting.objects.exists() or request.GET.get('reset') == 'true':
        SystemSetting.objects.all().delete()
        
        defaults = [
            {
                'key': 'app_sync_interval', 'label': 'Mobil Senkronizasyon (Dakika)', 'value': '15',
                'category': 'general', 'input_type': 'number', 'description': 'Veri alışverişi kaç dakikada bir yapılsın?'
            },
            {
                'key': 'maintenance_mode', 'label': 'Bakım Modu', 'value': 'False',
                'category': 'general', 'input_type': 'bool', 'description': 'Açılırsa sadece yöneticiler sisteme girebilir.'
            },
            {
                'key': 'visit_radius', 'label': 'Mağaza Giriş Mesafesi (Metre)', 'value': '300',
                'category': 'visit', 'input_type': 'number', 'description': 'Mağazaya kaç metre yaklaşınca buton açılsın?'
            },
            {
                'key': 'distance_rule', 'label': 'Mesafe Kuralı', 'value': 'True',
                'category': 'visit', 'input_type': 'bool', 'description': 'Açık: Giriş mesafesi ve gezinme mesafesi kontrolü yapılır. Kapalı: Mesafe kontrolü yapılmaz, herhangi bir mesafeden ziyaret başlatılabilir.'
            },
            {
                'key': 'wander_radius', 'label': 'Gezinme Sınırı (Metre)', 'value': '500',
                'category': 'visit', 'input_type': 'number', 'description': 'Ziyaret sırasında mağaza konumundan maksimum uzaklaşma mesafesi. Bu mesafeyi aşarsa ziyaret otomatik bitirilir.'
            },
            {
                'key': 'daily_start_hour', 'label': 'Mesai Başlangıç Saati', 'value': '08:00',
                'category': 'user', 'input_type': 'text', 'description': 'Bu saatten önce ziyaret başlatılamaz.'
            }
        ]
        
        for item in defaults:
            SystemSetting.objects.create(**item)
        
        messages.info(request, '🔄 Sistem ayarları fabrika ayarlarına döndürüldü.')

    # --- 2. GÜNCELLEME İŞLEMİ ---
    if request.method == 'POST':
        all_settings = SystemSetting.objects.all()
        for setting in all_settings:
            if setting.input_type == 'bool':
                new_val = 'True' if request.POST.get(setting.key) == 'on' else 'False'
            else:
                new_val = request.POST.get(setting.key)
            
            if new_val is not None:
                setting.value = new_val
                setting.save()
        messages.success(request, '✅ Ayarlar kaydedildi.')
        return redirect('settings_home')
    
    # CASUS KOD BAŞLANGICI
    print("----------------------------------------")
    print("👀 VIEW ÇALIŞIYOR - KONTROL ZAMANI")
    all_count = SystemSetting.objects.count()
    visit_count = SystemSetting.objects.filter(category='visit').count()
    print(f"Toplam Kayıt: {all_count}")
    print(f"Ziyaret Kategorisi Sayısı: {visit_count}")
    
    # Verileri ekrana da basalım
    for s in SystemSetting.objects.all():
        print(f" -> Kayıt: {s.key} | Kategori: '{s.category}'")
    print("----------------------------------------")
    # CASUS KOD BİTİŞİ

    # --- 3. VERİLERİ ÇEK ---
    settings_general = SystemSetting.objects.filter(category='general')
    settings_visit = SystemSetting.objects.filter(category='visit')
    settings_user = SystemSetting.objects.filter(category='user')

    context = {
        'settings_general': settings_general,
        'settings_visit': settings_visit,
        'settings_user': settings_user,
    }
    return render(request, 'apps/core/settings.html', context)

# --- AKILLI ANASAYFA ---
@login_required
def home(request):
    """
    Backend tarafında cihaz kontrolü yapar.
    Ancak asıl işi Login ekranındaki JavaScript yapacak.
    """
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    mobile_keywords = ['mobile', 'android', 'iphone', 'ipad', 'webos', 'ipod']
    
    is_mobile = any(keyword in user_agent for keyword in mobile_keywords)
    
    if is_mobile:
        return redirect('mobile_home')
    else:
        # MASAÜSTÜ DASHBOARD
        total_tasks = VisitTask.objects.count()
        completed_tasks = VisitTask.objects.filter(status='completed').count()
        today_tasks = VisitTask.objects.filter(planned_date=date.today())
        today_done = today_tasks.filter(status='completed').count()
        
        daily_performance = 0
        if today_tasks.count() > 0:
            daily_performance = int((today_done / today_tasks.count()) * 100)

        context = {
            'kpi': {
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'daily_performance': daily_performance,
            }
        }
        return render(request, 'apps/core/home.html', context)


def healthz(request):
    """
    Render/healthcheck endpoint. Always returns 200.
    """
    return HttpResponse("ok", content_type="text/plain")

# --- MOBİL ANASAYFA ---
@login_required
def mobile_home(request):
    today = date.today()
    user = request.user
    
    # Aktif ziyaret var mı kontrol et (check_in_time var ama check_out_time yok)
    active_visit = VisitTask.objects.filter(
        merch_code=user.username,
        check_in_time__isnull=False,
        check_out_time__isnull=True,
        status__in=['pending', 'missed']  # completed değilse aktif
    ).first()
    
    # Eğer aktif ziyaret varsa uyarı göster
    if active_visit:
        from django.contrib import messages
        messages.warning(request, f'Devam eden bir ziyaret var: {active_visit.customer.name}. Lütfen önce bu ziyareti tamamlayın.')
    
    tasks = VisitTask.objects.filter(
        merch_code=user.username,
        planned_date=today
    ).select_related('customer').order_by('status', 'customer__name')
    
    total_tasks = tasks.count()
    completed_tasks = tasks.filter(status='completed').count()
    
    progress_percentage = 0
    if total_tasks > 0:
        progress_percentage = int((completed_tasks / total_tasks) * 100)
    
    context = {
        'tasks': tasks,
        'today': today,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'progress_percentage': progress_percentage,
        'active_visit': active_visit
    }
    return render(request, 'mobile/home.html', context)

# --- MOBİL PROFİL (Hata veren eksik parça buydu) ---
@login_required
def mobile_profile(request):
    return render(request, 'mobile/profile.html')

import pandas as pd
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

@login_required
def download_excel_template(request, template_type):
    """
    İstenilen türe göre (customer, user, task) boş bir Excel şablonu oluşturur ve indirir.
    HATA DÜZELTME: Tüm sütunların uzunluğu eşitlendi.
    """
    filename = "sablon.xlsx"
    columns = []
    
    # 1. Sütun Başlıklarını Belirle
    if template_type == 'customer':
        columns = [
            'Müşteri Kodu', 'Müşteri Adı', 'Cari / Firma', 'İl', 'İlçe', 
            'Adres', 'Telefon', 'Yetkili Kişi', 'Enlem', 'Boylam'
        ]
        filename = "musteri_yukleme_sablonu.xlsx"

    elif template_type == 'user':
        columns = ['Kullanıcı Kodu', 'Ad', 'Soyad', 'Telefon', 'E-posta', 'Rol', 'Şifre']
        filename = "personel_yukleme_sablonu.xlsx"

    elif template_type == 'task':
        columns = ['Müşteri Kodu', 'Personel', 'Tarih', 'Ziyaret Notu']
        filename = "gorev_yukleme_sablonu.xlsx"
        
    elif template_type == 'route':
        columns = ['Saha Kullanıcısı', 'Müşteri Kodu', 'Gün 1', 'Gün 2', 'Gün 3', 'Gün 4', 'Gün 5', 'Gün 6', 'Gün 7']
        filename = "rota_yukleme_sablonu.xlsx"

    # 2. Veri Sözlüğünü Oluştur (HATA BURADAYDI, ŞİMDİ DÜZELTİLDİ)
    # Tüm sütunlara varsayılan olarak 1 tane boş satır ekliyoruz ['']
    # Böylece hepsi eşit uzunlukta oluyor.
    data = {col: [''] for col in columns}

    # 3. Örnek Verileri Doldur (Sadece gerekli olanları)
    if template_type == 'customer':
        data['Müşteri Kodu'] = ['M-001']
        data['Müşteri Adı'] = ['Örnek Market']
        data['İl'] = ['İstanbul']
        
    elif template_type == 'user':
        data['Kullanıcı Kodu'] = ['Merch1']
        data['Ad'] = ['Ahmet']
        data['Rol'] = ['Saha Personeli']
        data['Şifre'] = ['123456']
        
    elif template_type == 'task':
        data['Müşteri Kodu'] = ['M-001']
        data['Personel'] = ['Merch1']
        data['Tarih'] = ['25.12.2025']
        
    elif template_type == 'route':
        data['Saha Kullanıcısı'] = ['Merch1']
        data['Müşteri Kodu'] = ['M-001']
        data['Gün 1'] = ['1']

    # DataFrame oluştur ve Excel olarak döndür
    df = pd.DataFrame(data)
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename={filename}'
    df.to_excel(response, index=False)
    
    return response

from django.shortcuts import get_object_or_404
from apps.forms.models import Survey  # Bunu en üste eklemeyi unutma

@login_required
def mobile_task_detail(request, pk):
    """
    Seçilen görevin detay ekranı.
    Mağaza bilgisi + Formlar + Başlat Butonu
    Filtreleme: Tüm filtreler AND mantığıyla çalışır (şartlı)
    """
    task = get_object_or_404(VisitTask, pk=pk)
    user = request.user
    customer = task.customer
    
    # Aktif anketleri başlangıç olarak al
    surveys = Survey.objects.filter(is_active=True)
    
    # Tarih kontrolü
    from datetime import date
    today = date.today()
    surveys = surveys.filter(
        models.Q(start_date__isnull=True) | models.Q(start_date__lte=today)
    ).filter(
        models.Q(end_date__isnull=True) | models.Q(end_date__gte=today)
    )
    
    # FİLTRELEME (AND MANTIĞI - TÜM ŞARTLAR SAĞLANMALI)
    filtered_surveys = []
    
    for survey in surveys:
        should_show = True  # Varsayılan olarak göster
        
        # 1. KULLANICI FİLTRESİ
        if survey.filter_users.exists():
            # Eğer kullanıcı filtresi varsa, kullanıcı listede olmalı
            if user not in survey.filter_users.all():
                should_show = False
        
        # 2. ROL FİLTRESİ
        if survey.target_roles.exists():
            # Eğer rol filtresi varsa, kullanıcının rolü listede olmalı
            if not user.role or user.role not in survey.target_roles.all():
                should_show = False
        
        # 3. KULLANICI ÖZEL ALAN FİLTRELERİ
        if survey.user_custom_filters:
            for field_slug, allowed_values in survey.user_custom_filters.items():
                if allowed_values:  # Eğer değer seçilmişse
                    user_value_str = user.extra_data.get(field_slug, '') if user.extra_data else ''
                    # Tag sistemi: Değerler virgülle ayrılmış (örn: "Lansman,Stok Takibi")
                    user_tags = [tag.strip() for tag in str(user_value_str).split(',') if tag.strip()]
                    # Kullanıcının tag'lerinden en az biri, izin verilen değerlerden biri olmalı
                    if not any(tag in allowed_values for tag in user_tags):
                        should_show = False
                        break
        
        # 4. MÜŞTERİ FİLTRESİ
        if survey.filter_customers.exists():
            # Eğer müşteri filtresi varsa, müşteri listede olmalı
            if customer not in survey.filter_customers.all():
                should_show = False
        
        # 5. CARİ FİLTRESİ
        if survey.filter_caris.exists():
            # Eğer cari filtresi varsa, müşterinin carisi listede olmalı
            if not customer.cari or customer.cari not in survey.filter_caris.all():
                should_show = False
        
        # 6. MÜŞTERİ ÖZEL ALAN FİLTRELERİ
        if survey.custom_filters:
            for field_slug, allowed_values in survey.custom_filters.items():
                if allowed_values:  # Eğer değer seçilmişse
                    customer_value = customer.extra_data.get(field_slug, '') if customer.extra_data else ''
                    # Müşterinin bu alandaki değeri, izin verilen değerlerden biri olmalı
                    if customer_value not in allowed_values:
                        should_show = False
                        break
        
        # Tüm şartlar sağlandıysa listeye ekle
        if should_show:
            filtered_surveys.append(survey)
    
    # --- Anket durumları (Yapıldı / Yapılmadı) ---
    # Kural:
    # - Anketin zorunlu soruları varsa: tüm zorunlular cevaplandıysa "Yapıldı"
    # - Zorunlu soru yoksa: ankete ait en az 1 soru cevaplandıysa "Yapıldı"
    survey_ids = [s.id for s in filtered_surveys]
    answered_q_ids = set(
        SurveyAnswer.objects.filter(task=task, question__survey_id__in=survey_ids)
        .exclude(answer_text__isnull=True, answer_photo__isnull=True)
        .values_list('question_id', flat=True)
    )

    questions = list(
        Question.objects.filter(survey_id__in=survey_ids).values('id', 'survey_id', 'required')
    )
    req_map = {}
    all_map = {}
    for q in questions:
        sid = q['survey_id']
        all_map.setdefault(sid, []).append(q['id'])
        if q['required']:
            req_map.setdefault(sid, []).append(q['id'])

    for s in filtered_surveys:
        req_ids = req_map.get(s.id, [])
        all_ids = all_map.get(s.id, [])
        if req_ids:
            done_required = sum(1 for qid in req_ids if qid in answered_q_ids)
            s.is_done = done_required == len(req_ids)
            s.required_done = done_required
            s.required_total = len(req_ids)
        else:
            any_done = any(qid in answered_q_ids for qid in all_ids)
            s.is_done = any_done
            s.required_done = 1 if any_done else 0
            s.required_total = 1 if all_ids else 0

    context = {
        'task': task,
        'surveys': filtered_surveys,
    }
    return render(request, 'mobile/task_detail.html', context)

@login_required
def mobile_fill_survey(request, task_id, survey_id):
    task = get_object_or_404(VisitTask, pk=task_id)
    survey = get_object_or_404(Survey, pk=survey_id)
    
    # Ana soruları al (parent_question veya dependency_question olmayanlar)
    main_questions = survey.questions.filter(
        models.Q(parent_question__isnull=True) & models.Q(dependency_question__isnull=True)
    ).order_by('order')
    
    # Tüm soruları al (alt sorular dahil)
    all_questions = survey.questions.all().order_by('order')

    if request.method == 'POST':
        try:
            # Her soru için döngüye girip cevabı alalım
            for q in all_questions:
                # HTML formundaki input ismi: "q_1", "q_2" şeklinde ayarlamıştık
                input_name = f"q_{q.id}"
                
                text_val = request.POST.get(input_name)
                photo_val = request.FILES.get(input_name)
                photo_b64 = request.POST.get(f"{input_name}_base64") if q.input_type == 'photo' else None

                # WebView fallback: base64 geldiyse dosyaya çevir
                if not photo_val and photo_b64 and photo_b64.startswith('data:image/'):
                    try:
                        header, b64data = photo_b64.split(',', 1)
                        # data:image/jpeg;base64
                        ext = 'jpg'
                        if 'image/png' in header:
                            ext = 'png'
                        elif 'image/webp' in header:
                            ext = 'webp'
                        elif 'image/jpeg' in header or 'image/jpg' in header:
                            ext = 'jpg'

                        import base64
                        decoded = base64.b64decode(b64data)
                        photo_val = ContentFile(decoded, name=f"survey_{task_id}_{q.id}.{ext}")
                    except Exception:
                        photo_val = None
                
                # Eğer soruya bir cevap verilmişse (Yazı veya Fotoğraf)
                if text_val or photo_val:
                    # Önce eski cevap varsa silelim (Güncelleme mantığı)
                    SurveyAnswer.objects.filter(task=task, question=q).delete()
                    
                    # Yeni cevabı kaydet
                    SurveyAnswer.objects.create(
                        task=task,
                        question=q,
                        answer_text=text_val,
                        answer_photo=photo_val
                    )
            
            messages.success(request, '✅ Form başarıyla kaydedildi.')
            return redirect('mobile_task_detail', pk=task_id)
            
        except Exception as e:
            messages.error(request, f'Hata oluştu: {str(e)}')

    # Soruları ve alt sorularını hazırla
    questions_data = []
    for q in main_questions:
        # Alt soruları al (parent_question veya dependency_question ile bağlı olanlar)
        child_questions = survey.questions.filter(
            models.Q(parent_question=q) | models.Q(dependency_question=q)
        ).distinct().order_by('order')
        
        # Alt soruları detaylı bilgilerle hazırla
        child_questions_list = []
        for child in child_questions:
            # Hangi alan kullanılmış? (parent_question veya dependency_question)
            trigger_value = ''
            if child.parent_question == q:
                trigger_value = child.trigger_answer or ''
            elif child.dependency_question == q:
                trigger_value = child.dependency_value or ''
            
            child_questions_list.append({
                'id': child.id,
                'label': child.label,
                'input_type': child.input_type,
                'required': child.required,
                'trigger_answer': trigger_value,
                'parent_id': q.id,
                'options': [{'text': opt.text, 'id': opt.id} for opt in child.options.all()],
                'min_photos': child.min_photos,
                'max_photos': child.max_photos,
            })
        
        # Sorunun seçeneklerini al (select tipi sorular için)
        question_options = [{'text': opt.text, 'id': opt.id} for opt in q.options.all()] if q.input_type == 'select' else []
        
        questions_data.append({
            'question': q,
            'child_questions': child_questions_list,
            'options': question_options,
        })
    
    # Zorunlu soruları kontrol et
    required_questions = [q for q in all_questions if q.required]
    answered_questions = SurveyAnswer.objects.filter(task=task, question__in=required_questions).values_list('question_id', flat=True)
    missing_required = [q for q in required_questions if q.id not in answered_questions]

    context = {
        'task': task,
        'survey': survey,
        'questions_data': questions_data,
        'required_questions': required_questions,
        'missing_required': missing_required,
    }
    return render(request, 'mobile/survey_form.html', context)

@csrf_exempt
def start_visit_check(request, task_id):
    # Debug için print ekleyelim (production'da kaldırılabilir)
    print(f"[DEBUG] start_visit_check çağrıldı - Method: {request.method}, Task ID: {task_id}")
    print(f"[DEBUG] User: {request.user if hasattr(request, 'user') else 'Anonymous'}")
    print(f"[DEBUG] Body: {request.body}")
    print(f"[DEBUG] Headers: {dict(request.headers)}")
    
    # GET isteği için test endpoint
    if request.method == 'GET':
        return JsonResponse({
            'success': True,
            'message': 'API çalışıyor',
            'task_id': task_id,
            'method': 'GET'
        })
    
    if request.method == 'POST':
        try:
            # 1. Mobilden gelen body
            body_text = request.body.decode('utf-8')
            data = json.loads(body_text)

            # 2. Görevi ve Müşteriyi Bul
            task = VisitTask.objects.get(id=task_id)
            customer = task.customer

            # 3. Mesafe kuralı kontrolü (distance_rule) - kapalıysa konum ve mesafe kontrolü yapılmaz
            distance_rule_setting = SystemSetting.objects.filter(key='distance_rule').first()
            # Eski require_gps ayarını migrate et
            if not distance_rule_setting:
                old_setting = SystemSetting.objects.filter(key='require_gps').first()
                if old_setting:
                    old_setting.key = 'distance_rule'
                    old_setting.label = 'Mesafe Kuralı'
                    old_setting.description = 'Açık: Giriş mesafesi ve gezinme mesafesi kontrolü yapılır. Kapalı: Mesafe kontrolü yapılmaz, herhangi bir mesafeden ziyaret başlatılabilir.'
                    old_setting.save()
                    distance_rule_setting = old_setting

            distance_rule_enabled = True
            if distance_rule_setting:
                try:
                    distance_rule_enabled = distance_rule_setting.value.lower() == 'true'
                except:
                    distance_rule_enabled = True

            # Mesafe kuralı kapalıysa: konum zorunlu değil, doğrudan başlat
            if not distance_rule_enabled:
                from datetime import datetime
                task.check_in_time = datetime.now()
                task.save()
                return JsonResponse({
                    'success': True,
                    'message': 'Ziyaret başlatıldı. (Mesafe kuralı kapalı olduğu için konum ve mesafe kontrolü yapılmadı.)'
                })

            # 4. Kullanıcı koordinatları - mesafe kuralı açıkken zorunlu
            user_lat_raw = data.get('latitude')
            user_lon_raw = data.get('longitude')

            if user_lat_raw is None or user_lon_raw is None:
                return JsonResponse({
                    'success': False, 
                    'message': 'Konum bilgisi alınamadı. Lütfen GPS\'in açık olduğundan ve konum izninin verildiğinden emin olun.'
                })

            try:
                user_lat = float(user_lat_raw)
                user_lon = float(user_lon_raw)
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False, 
                    'message': 'Geçersiz konum bilgisi. Lütfen tekrar deneyin.'
                })

            # Koordinatlar geçerli aralıkta mı?
            if not (-90 <= user_lat <= 90) or not (-180 <= user_lon <= 180):
                return JsonResponse({
                    'success': False, 
                    'message': 'Geçersiz konum koordinatları. Lütfen tekrar deneyin.'
                })

            try:
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Koordinat alındı - Lat: {user_lat}, Lon: {user_lon}")
            except:
                pass

            try:
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Task ve Customer bulundu - Customer: {customer.name}, Lat: {customer.latitude}, Lon: {customer.longitude}")
            except:
                pass
            
            # Müşterinin koordinatı yoksa mesafe kontrolü yapmadan ziyareti başlat
            # latitude ve longitude FloatField, None veya 0.0 olabilir
            cust_lat_val = customer.latitude
            cust_lng_val = customer.longitude
            
            # Koordinat kontrolü - None veya 0.0 ise mesafe kontrolü yapma
            if (cust_lat_val is None or cust_lng_val is None or 
                cust_lat_val == 0.0 or cust_lng_val == 0.0):
                from datetime import datetime
                task.check_in_time = datetime.now()
                task.save()
                return JsonResponse({
                    'success': True, 
                    'message': 'Ziyaret başlatıldı. (Müşteri konumu sistemde olmadığı için mesafe kontrolü yapılmadı.)'
                })

            # 3. Mesafeyi Hesapla - None kontrolü ile
            try:
                # None kontrolü
                if cust_lat_val is None or cust_lng_val is None:
                    raise ValueError("Müşteri koordinatları None")
                
                cust_lat = float(cust_lat_val)
                cust_lon = float(cust_lng_val)
                
                # Koordinatlar geçerli mi kontrol et (enlem: -90 ile 90, boylam: -180 ile 180)
                if not (-90 <= cust_lat <= 90) or not (-180 <= cust_lon <= 180):
                    raise ValueError("Koordinatlar geçersiz aralıkta")
                
                distance = calculate_distance(user_lat, user_lon, cust_lat, cust_lon)
            except (ValueError, TypeError) as e:
                # Koordinat geçersizse mesafe kontrolü yapmadan başlat
                from datetime import datetime
                task.check_in_time = datetime.now()
                task.save()
                return JsonResponse({
                    'success': True, 
                    'message': 'Ziyaret başlatıldı. (Müşteri konumu geçersiz olduğu için mesafe kontrolü yapılmadı.)'
                })
            
            # 4. Mesafe Kuralı kontrolü - Eğer kapalıysa mesafe kontrolü yapma
            distance_rule_setting = SystemSetting.objects.filter(key='distance_rule').first()
            # Eğer yeni ayar yoksa, eski require_gps ayarını kontrol et
            if not distance_rule_setting:
                old_setting = SystemSetting.objects.filter(key='require_gps').first()
                if old_setting:
                    # Eski ayarı yeni isimle güncelle
                    old_setting.key = 'distance_rule'
                    old_setting.label = 'Mesafe Kuralı'
                    old_setting.description = 'Açık: Giriş mesafesi ve gezinme mesafesi kontrolü yapılır. Kapalı: Mesafe kontrolü yapılmaz, herhangi bir mesafeden ziyaret başlatılabilir.'
                    old_setting.save()
                    distance_rule_setting = old_setting
            
            distance_rule_enabled = True  # Varsayılan: açık
            if distance_rule_setting:
                try:
                    distance_rule_enabled = distance_rule_setting.value.lower() == 'true'
                except:
                    distance_rule_enabled = True
            
            # Eğer mesafe kuralı kapalıysa, direkt ziyareti başlat
            if not distance_rule_enabled:
                from datetime import datetime
                task.check_in_time = datetime.now()
                task.save()
                return JsonResponse({
                    'success': True, 
                    'message': 'Ziyaret başlatıldı. (Mesafe kuralı kapalı olduğu için mesafe kontrolü yapılmadı.)'
                })
            
            # 5. Admin Panelindeki Sınırı Çek (Mesafe kuralı açıksa)
            # Eğer ayar yoksa varsayılan 300 metre olsun
            setting = SystemSetting.objects.filter(key='visit_radius').first()
            try:
                limit = float(setting.value) if setting and setting.value else 300.0
            except (ValueError, TypeError):
                limit = 300.0

            # 6. KARAR ANI - Mesafe kontrolü (>= kullanarak sıkı kontrol)
            # Eğer mesafe limit'e eşit veya fazlaysa ziyaret başlatılmamalı
            if distance >= limit:
                # Mesafe UZAK veya EŞİT - Ziyaret başlatılmamalı
                distance_diff = int(distance - limit)
                return JsonResponse({
                    'success': False, 
                    'message': f"Ziyaret mesafesi uyarısı!\nTespit Edilen Mesafe: {int(distance)}m\nİzin Verilen: {int(limit)}m\nFark: {distance_diff}m fazla"
                })
            
            # Mesafe uygun (limit'ten küçük), ziyaret başlatıldı
            from datetime import datetime
            task.check_in_time = datetime.now()
            task.save()
            return JsonResponse({'success': True, 'message': 'Konum doğrulandı. Ziyaret başladı.'})

        except json.JSONDecodeError as e:
            import logging
            logger = logging.getLogger(__name__)
            try:
                logger.error(f"JSON decode hatası: {str(e)}, Body: {request.body}")
            except:
                pass
            return JsonResponse({'success': False, 'message': 'Geçersiz veri formatı. Lütfen tekrar deneyin.'})
        except ValueError as e:
            import logging
            logger = logging.getLogger(__name__)
            try:
                logger.error(f"ValueError: {str(e)}")
            except:
                pass
            return JsonResponse({'success': False, 'message': 'Koordinat bilgisi geçersiz. Lütfen konum iznini kontrol edin.'})
        except VisitTask.DoesNotExist:
            import logging
            logger = logging.getLogger(__name__)
            try:
                logger.error(f"VisitTask bulunamadı - Task ID: {task_id}")
            except:
                pass
            return JsonResponse({'success': False, 'message': 'Ziyaret görevi bulunamadı.'})
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            try:
                logger.error(f"Genel hata: {str(e)}", exc_info=True)
            except:
                pass
            return JsonResponse({'success': False, 'message': f'Bir hata oluştu: {str(e)}'})

    return JsonResponse({'success': False, 'message': 'Hatalı İstek - POST metodu bekleniyor.'})

# Zorunlu anketleri kontrol et
@csrf_exempt
@login_required
def check_required_surveys(request, task_id):
    """Ziyareti bitirmeden önce zorunlu anketlerin tamamlanıp tamamlanmadığını kontrol eder"""
    task = get_object_or_404(VisitTask, pk=task_id)
    
    # Bu görev için gösterilen tüm anketleri al
    surveys = Survey.objects.filter(is_active=True)
    from datetime import date
    today = date.today()
    surveys = surveys.filter(
        models.Q(start_date__isnull=True) | models.Q(start_date__lte=today)
    ).filter(
        models.Q(end_date__isnull=True) | models.Q(end_date__gte=today)
    )
    
    # Filtreleme (mobile_task_detail ile aynı mantık)
    user = request.user
    customer = task.customer
    filtered_surveys = []
    
    for survey in surveys:
        should_show = True
        
        if survey.filter_users.exists():
            if user not in survey.filter_users.all():
                should_show = False
        
        if survey.target_roles.exists():
            if not user.role or user.role not in survey.target_roles.all():
                should_show = False
        
        if survey.user_custom_filters:
            for field_slug, allowed_values in survey.user_custom_filters.items():
                if allowed_values:
                    user_value_str = user.extra_data.get(field_slug, '') if user.extra_data else ''
                    user_tags = [tag.strip() for tag in str(user_value_str).split(',') if tag.strip()]
                    if not any(tag in allowed_values for tag in user_tags):
                        should_show = False
                        break
        
        if survey.filter_customers.exists():
            if customer not in survey.filter_customers.all():
                should_show = False
        
        if survey.filter_caris.exists():
            if not customer.cari or customer.cari not in survey.filter_caris.all():
                should_show = False
        
        if survey.custom_filters:
            for field_slug, allowed_values in survey.custom_filters.items():
                if allowed_values:
                    customer_value = customer.extra_data.get(field_slug, '') if customer.extra_data else ''
                    if customer_value not in allowed_values:
                        should_show = False
                        break
        
        if should_show:
            filtered_surveys.append(survey)
    
    # Zorunlu soruları kontrol et
    missing_required = []
    for survey in filtered_surveys:
        # Bu anketin tüm zorunlu sorularını al
        all_questions = survey.questions.all()
        required_questions = [q for q in all_questions if q.required]
        
        # Bu görev için bu anketin sorularına verilen cevapları kontrol et
        for req_q in required_questions:
            answer = SurveyAnswer.objects.filter(task=task, question=req_q).first()
            if not answer or (not answer.answer_text and not answer.answer_photo):
                missing_required.append(survey)
                break  # Bu anket eksik, diğer sorularına bakmaya gerek yok
    
    return JsonResponse({
        'missing_required': [{'id': s.id, 'title': s.title} for s in missing_required],
        'all_completed': len(missing_required) == 0
    })

# Ziyareti bitir
@csrf_exempt
@login_required
def finish_visit(request, task_id):
    """Ziyareti tamamla - Sadece buton ile bitirilebilir, zorunlu formlar kontrol edilir"""
    task = get_object_or_404(VisitTask, pk=task_id)
    
    # Zorunlu anketleri kontrol et
    surveys = Survey.objects.filter(is_active=True)
    from datetime import date
    today = date.today()
    surveys = surveys.filter(
        models.Q(start_date__isnull=True) | models.Q(start_date__lte=today)
    ).filter(
        models.Q(end_date__isnull=True) | models.Q(end_date__gte=today)
    )
    
    user = request.user
    customer = task.customer
    filtered_surveys = []
    
    for survey in surveys:
        should_show = True
        
        if survey.filter_users.exists():
            if user not in survey.filter_users.all():
                should_show = False
        
        if survey.target_roles.exists():
            if not user.role or user.role not in survey.target_roles.all():
                should_show = False
        
        if survey.user_custom_filters:
            for field_slug, allowed_values in survey.user_custom_filters.items():
                if allowed_values:
                    user_value_str = user.extra_data.get(field_slug, '') if user.extra_data else ''
                    user_tags = [tag.strip() for tag in str(user_value_str).split(',') if tag.strip()]
                    if not any(tag in allowed_values for tag in user_tags):
                        should_show = False
                        break
        
        if survey.filter_customers.exists():
            if customer not in survey.filter_customers.all():
                should_show = False
        
        if survey.filter_caris.exists():
            if not customer.cari or customer.cari not in survey.filter_caris.all():
                should_show = False
        
        if survey.custom_filters:
            for field_slug, allowed_values in survey.custom_filters.items():
                if allowed_values:
                    customer_value = customer.extra_data.get(field_slug, '') if customer.extra_data else ''
                    if customer_value not in allowed_values:
                        should_show = False
                        break
        
        if should_show:
            filtered_surveys.append(survey)
    
    # Zorunlu soruları kontrol et
    missing_required = []
    for survey in filtered_surveys:
        all_questions = survey.questions.all()
        required_questions = [q for q in all_questions if q.required]
        
        for req_q in required_questions:
            answer = SurveyAnswer.objects.filter(task=task, question=req_q).first()
            if not answer or (not answer.answer_text and not answer.answer_photo):
                missing_required.append(survey)
                break
    
    if missing_required:
        return JsonResponse({
            'success': False,
            'message': 'Zorunlu anketler tamamlanmadan ziyaret bitirilemez.',
            'missing_required': [{'id': s.id, 'title': s.title} for s in missing_required]
        })
    
    # Tüm kontroller geçildi, ziyareti bitir
    from datetime import datetime
    task.status = 'completed'
    task.check_out_time = datetime.now()
    task.save()
    
    return JsonResponse({
        'success': True,
        'message': 'Ziyaret başarıyla tamamlandı.'
    })

# Gezinme sınırını getir
@csrf_exempt
def get_wander_radius(request):
    """Gezinme sınırı ayarını döndürür"""
    setting = SystemSetting.objects.filter(key='wander_radius').first()
    wander_radius = float(setting.value) if setting else 500.0  # Varsayılan 500m
    return JsonResponse({'wander_radius': wander_radius})

@csrf_exempt
@login_required
def get_distance_rule(request):
    """Mesafe kuralı ayarını döndürür"""
    setting = SystemSetting.objects.filter(key='distance_rule').first()
    # Eğer eski require_gps ayarı varsa, onu distance_rule olarak kullan
    if not setting:
        old_setting = SystemSetting.objects.filter(key='require_gps').first()
        if old_setting:
            # Eski ayarı yeni isimle güncelle
            old_setting.key = 'distance_rule'
            old_setting.label = 'Mesafe Kuralı'
            old_setting.description = 'Açık: Giriş mesafesi ve gezinme mesafesi kontrolü yapılır. Kapalı: Mesafe kontrolü yapılmaz, herhangi bir mesafeden ziyaret başlatılabilir.'
            old_setting.save()
            setting = old_setting
    
    distance_rule = True  # Varsayılan: açık
    if setting:
        try:
            distance_rule = setting.value.lower() == 'true'
        except:
            distance_rule = True
    
    return JsonResponse({'distance_rule': distance_rule})

@csrf_exempt
@login_required
def check_visit_status(request, task_id):
    """Ziyaretin başlatılıp başlatılmadığını kontrol eder"""
    task = get_object_or_404(VisitTask, pk=task_id)
    
    # Ziyaret başlatılmışsa check_in_time dolu olur, bitirilmişse check_out_time dolu olur
    is_started = task.check_in_time is not None
    is_finished = task.check_out_time is not None and task.status == 'completed'
    
    return JsonResponse({
        'is_started': is_started and not is_finished,
        'is_finished': is_finished,
        'check_in_time': task.check_in_time.isoformat() if task.check_in_time else None,
        'check_out_time': task.check_out_time.isoformat() if task.check_out_time else None
    })
    
    return JsonResponse({'distance_rule': distance_rule})