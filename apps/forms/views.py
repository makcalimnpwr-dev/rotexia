from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import models
import json

from .models import Survey, Question, QuestionOption
from apps.users.models import UserRole, CustomUser, UserFieldDefinition
from apps.users.decorators import tenant_required
# --- HATAYI ÇÖZEN SATIR ---
from apps.customers.models import Customer, CustomerCari, CustomerFieldDefinition, CustomFieldDefinition
# --------------------------
from apps.core.tenant_utils import filter_by_tenant, set_tenant_on_save
from apps.core.models import Tenant

# 1. ANKET LİSTESİ
@login_required
def survey_list(request):
    # Admin panel kontrolü - Admin panelindeyken tenant kontrolünü atla
    from apps.users.utils import is_root_admin
    
    is_admin_panel_path = (
        request.path.startswith('/admin-home') or
        request.path.startswith('/admin/') or
        request.path.startswith('/admin-panel/') or
        request.path.startswith('/admin-login') or
        'admin_mode=1' in request.GET or
        'admin_mode=1' in request.META.get('QUERY_STRING', '')
    )
    
    # Admin panelindeyken tüm formları göster (tenant filtresi yok)
    base_qs = Survey.objects.all()
    if not (is_root_admin(request.user) and is_admin_panel_path):
        base_qs = filter_by_tenant(base_qs, request)
    surveys = base_qs.order_by('-created_at')
    return render(request, 'forms/list.html', {'surveys': surveys})

# 2. YENİ ANKET OLUŞTURMA
@login_required
def survey_create(request):
    from apps.users.utils import is_root_admin

    is_admin_panel_path = (
        request.path.startswith('/admin-home') or
        request.path.startswith('/admin/') or
        request.path.startswith('/admin-panel/') or
        request.path.startswith('/admin-login') or
        'admin_mode=1' in request.GET or
        'admin_mode=1' in request.META.get('QUERY_STRING', '')
    )

    if request.method == 'POST':
        title = request.POST.get('title')
        desc = request.POST.get('description')
        if title:
            survey = Survey(title=title, description=desc)
            # Root admin admin panelde tenant yok → firmayı formdan seçtir
            if is_root_admin(request.user) and is_admin_panel_path:
                tenant_id = (request.POST.get('tenant_id') or '').strip()
                if not tenant_id.isdigit():
                    messages.error(request, 'Lütfen firma seçin.')
                    return redirect('survey_create')
                tenant = Tenant.objects.filter(id=int(tenant_id), is_active=True).first()
                if not tenant:
                    messages.error(request, 'Seçilen firma bulunamadı.')
                    return redirect('survey_create')
                survey.tenant = tenant
            else:
                set_tenant_on_save(survey, request)
            survey.save()
            messages.success(request, 'Anket oluşturuldu, şimdi soruları ekleyin.')
            return redirect('survey_builder', pk=survey.id)
    return render(request, 'forms/create.html')

# 3. ANKET SİLME
@login_required
def survey_delete(request, pk):
    survey = get_object_or_404(filter_by_tenant(Survey.objects.all(), request), pk=pk)
    survey.delete()
    messages.success(request, 'Anket silindi.')
    return redirect('survey_list')

# 4. SORU EKLEME
@login_required
def question_create(request, survey_id):
    survey = get_object_or_404(filter_by_tenant(Survey.objects.all(), request), pk=survey_id)
    if request.method == 'POST':
        label = request.POST.get('label')
        input_type = request.POST.get('input_type')
        required = request.POST.get('required') == 'on'
        min_p = request.POST.get('min_photos') or 1
        max_p = request.POST.get('max_photos') or 1
        
        # Bağlantı Verileri
        parent_id = request.POST.get('parent_question')
        trigger = request.POST.get('trigger_answer')
        
        parent_q = None
        if parent_id:
            parent_q = Question.objects.get(id=parent_id)

        q = Question.objects.create(
            survey=survey,
            label=label,
            input_type=input_type,
            required=required,
            min_photos=int(min_p),
            max_photos=int(max_p),
            parent_question=parent_q,
            trigger_answer=trigger,
            order=survey.questions.count() + 1
        )
        
        # Seçenekler
        options_text = request.POST.get('options_hidden_input')
        if input_type == 'select' and options_text:
            opts = [o.strip() for o in options_text.split(',')]
            for i, opt_text in enumerate(opts):
                if opt_text:
                    QuestionOption.objects.create(question=q, text=opt_text, order=i)

        messages.success(request, 'Soru eklendi.')
    return redirect('survey_builder', pk=survey_id)

# 5. SORU SİLME
@login_required
def question_delete(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    # Tenant kontrolü: Sadece mevcut tenant'ın sorusunu silebilir
    survey = question.survey
    if hasattr(survey, 'tenant'):
        from apps.core.tenant_utils import get_current_tenant, require_tenant_for_action
        tenant = get_current_tenant(request)
        if tenant and survey.tenant != tenant:
            from django.contrib import messages
            messages.error(request, 'Bu işlem için yetkiniz yok.')
            return redirect('survey_list')
    survey_id = survey.id
    question.delete()
    messages.success(request, 'Soru silindi.')
    return redirect('survey_builder', pk=survey_id)

# 6. SORU DÜZENLEME
@login_required
def question_edit(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    survey_id = question.survey.id

    if request.method == 'POST':
        question.label = request.POST.get('label')
        question.required = request.POST.get('required') == 'on'
        
        min_p = request.POST.get('min_photos') or 1
        max_p = request.POST.get('max_photos') or 1
        question.min_photos = int(min_p)
        question.max_photos = int(max_p)
        
        parent_id = request.POST.get('parent_question')
        trigger = request.POST.get('trigger_answer')
        
        if parent_id:
            question.parent_question = Question.objects.get(id=parent_id)
        else:
            question.parent_question = None
        question.trigger_answer = trigger
        
        question.save()

        if question.input_type == 'select':
            new_options = request.POST.get('options_hidden_input_edit')
            if new_options:
                question.options.all().delete()
                opts = [o.strip() for o in new_options.split(',')]
                for i, opt_text in enumerate(opts):
                    if opt_text:
                        QuestionOption.objects.create(question=question, text=opt_text, order=i)

        messages.success(request, 'Soru güncellendi.')
    return redirect('survey_builder', pk=survey_id)

# 7. SEÇENEKLERİ GETİREN API (JS İÇİN)
@login_required
def get_question_options(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    options = list(question.options.values('text'))
    return JsonResponse({'options': options})

# 8. ANKET TASARIMCISI (BUILDER) - HATA VEREN FONKSİYON BUYDU
@login_required
def survey_builder(request, pk):
    survey = get_object_or_404(filter_by_tenant(Survey.objects.all(), request), pk=pk)
    questions = survey.questions.all().order_by('order')
    
    # --- VERİLERİ ÇEK ---
    all_roles = UserRole.objects.all()
    all_users = CustomUser.objects.filter(is_active=True).order_by('first_name', 'last_name')
    all_customers = Customer.objects.all()      # ARTIK HATA VERMEZ
    all_caris = CustomerCari.objects.all()
    
    # Müşterilerde açılan özel alanları çek (CustomFieldDefinition)
    custom_field_defs = CustomFieldDefinition.objects.all()
    customer_fields_data = []
    
    for cf_def in custom_field_defs:
        # Bu özel alanın müşterilerde kullanılan değerlerini topla
        # Müşterilerin extra_data JSONField'ından bu alanın değerlerini çıkar
        used_values = set()
        for customer in Customer.objects.exclude(extra_data__isnull=True):
            if customer.extra_data and cf_def.slug in customer.extra_data:
                value = customer.extra_data[cf_def.slug]
                if value and str(value).strip():  # Boş değilse
                    used_values.add(str(value).strip())
        
        # Değerleri sıralı listeye çevir
        options_list = sorted(list(used_values))
        
        customer_fields_data.append({
            'key': cf_def.slug,  # Slug kullan (ID değil)
            'label': cf_def.name,
            'options': options_list
        })
    
    # Kullanıcılarda açılan özel alanları çek (UserFieldDefinition)
    user_field_defs = UserFieldDefinition.objects.all()
    user_fields_data = []
    
    for uf_def in user_field_defs:
        # Bu özel alanın kullanıcılarda kullanılan değerlerini topla
        # Tag sistemi: Değerler virgülle ayrılmış string olarak tutulur (örn: "Lansman,Stok Takibi")
        used_values = set()
        for user in CustomUser.objects.exclude(extra_data__isnull=True):
            if user.extra_data and uf_def.slug in user.extra_data:
                value = user.extra_data[uf_def.slug]
                if value and str(value).strip():
                    # Virgülle ayrılmış değerleri parse et
                    tags = [tag.strip() for tag in str(value).split(',') if tag.strip()]
                    used_values.update(tags)
        
        options_list = sorted(list(used_values))
        
        user_fields_data.append({
            'key': uf_def.slug,
            'label': uf_def.name,
            'options': options_list
        })

    if request.method == 'POST':
        if request.POST.get('action') == 'save_settings':
            # Kullanıcı Filtreleri
            survey.filter_users.set(request.POST.getlist('filter_users'))
            survey.target_roles.set(request.POST.getlist('target_roles'))
            
            # Müşteri Filtreleri
            survey.filter_customers.set(request.POST.getlist('filter_customers'))
            survey.filter_caris.set(request.POST.getlist('filter_caris'))
            
            # Tarih ve Durum
            survey.start_date = request.POST.get('start_date') or None
            survey.end_date = request.POST.get('end_date') or None
            survey.is_active = request.POST.get('is_active') == 'on'
            
            # Dinamik Filtreler (JSON) - Müşteri Özel Alanlar
            # Her satır için: custom_filter_key_0, custom_filter_value_0[] formatında gelir
            filter_data = {}
            i = 0
            while True:
                key = request.POST.get(f'custom_filter_key_{i}')
                if not key:
                    break
                # Multiple select'ten gelen tüm değerleri al
                values = request.POST.getlist(f'custom_filter_value_{i}[]')
                if key and values:
                    # Boş değerleri filtrele
                    filter_data[key] = [v for v in values if v.strip()]
                i += 1
            
            # Eğer yukarıdaki format yoksa, eski formatı dene (backward compatibility)
            if not filter_data:
                custom_keys = request.POST.getlist('custom_filter_key[]')
                custom_vals = request.POST.getlist('custom_filter_value[]')
                for k, v in zip(custom_keys, custom_vals):
                    if k and v:
                        if k in filter_data:
                            if v not in filter_data[k]:
                                filter_data[k].append(v)
                        else:
                            filter_data[k] = [v]
            
            survey.custom_filters = filter_data
            
            # Kullanıcı Özel Alan Filtreleri (JSON)
            user_filter_data = {}
            i = 0
            while True:
                key = request.POST.get(f'user_filter_key_{i}')
                if not key:
                    break
                values = request.POST.getlist(f'user_filter_value_{i}[]')
                if key and values:
                    user_filter_data[key] = [v for v in values if v.strip()]
                i += 1
            
            # Backward compatibility
            if not user_filter_data:
                user_keys = request.POST.getlist('user_filter_key[]')
                user_vals = request.POST.getlist('user_filter_value[]')
                for k, v in zip(user_keys, user_vals):
                    if k and v:
                        if k in user_filter_data:
                            if v not in user_filter_data[k]:
                                user_filter_data[k].append(v)
                        else:
                            user_filter_data[k] = [v]
            
            survey.user_custom_filters = user_filter_data
            survey.save()
            messages.success(request, 'Filtreler ve ayarlar güncellendi.')
            return redirect('survey_builder', pk=pk)

    # Her soru için alt soruları ve seçeneklerini hazırla
    questions_data = []
    for q in questions:
        # Alt soruları al (parent_question veya dependency_question ile bağlı olanlar)
        # parent_question eski sistem, dependency_question yeni sistem
        child_questions = Question.objects.filter(
            survey=survey
        ).filter(
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
                'input_type': child.get_input_type_display(),
                'trigger_answer': trigger_value,
                'parent_id': q.id,
                'options': [opt.text for opt in child.options.all()] if child.input_type == 'select' else []
            })
        
        # Sorunun seçeneklerini al (select tipi sorular için)
        question_options = [opt.text for opt in q.options.all()] if q.input_type == 'select' else []
        
        questions_data.append({
            'question': q,
            'child_questions': child_questions_list,
            'options': question_options,
        })
    
    # Context
    context = {
        'survey': survey,
        'questions': questions,
        'questions_data': questions_data,  # Detaylı soru verileri
        'all_roles': all_roles,
        'all_users': all_users,
        'all_customers': all_customers,
        'all_caris': all_caris,
        'customer_fields': customer_fields_data,
        'user_fields': user_fields_data,
        
        'selected_roles': list(survey.target_roles.values_list('id', flat=True)),
        'selected_users': list(survey.filter_users.values_list('id', flat=True)),
        'selected_customers': list(survey.filter_customers.values_list('id', flat=True)),
        'selected_caris': list(survey.filter_caris.values_list('id', flat=True)),
    }
    return render(request, 'forms/builder.html', context)