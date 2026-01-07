from django.db import models
from apps.field_operations.models import VisitTask 
from apps.customers.models import Customer, CustomerCari

# 1. ANKET MODELİ
class Survey(models.Model):
    title = models.CharField(max_length=200, verbose_name="Anket Başlığı")
    description = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    
    # --- AYARLAR ---
    start_date = models.DateField(null=True, blank=True, verbose_name="Başlangıç")
    end_date = models.DateField(null=True, blank=True, verbose_name="Bitiş")
    is_active = models.BooleanField(default=True, verbose_name="Aktif mi?")

    # --- FİLTRELER ---
    # 1. Müşteri (Firma) Filtresi
    filter_customers = models.ManyToManyField(Customer, blank=True, related_name='surveys_as_customer', verbose_name="Müşteri Filtresi")
    
    # 2. Cari (Şube) Filtresi
    filter_caris = models.ManyToManyField(CustomerCari, blank=True, related_name='surveys_as_cari', verbose_name="Cari Filtresi")
    
    # 3. Kullanıcı Filtreleri
    filter_users = models.ManyToManyField('users.CustomUser', blank=True, related_name='surveys_as_user', verbose_name="Kullanıcı Filtresi")
    target_roles = models.ManyToManyField('users.UserRole', blank=True, verbose_name="Rol Filtresi")
    
    # 4. Müşteri Özel Alan Filtreleri (JSON)
    custom_filters = models.JSONField(default=dict, blank=True, null=True)
    
    # 5. Kullanıcı Özel Alan Filtreleri (JSON)
    user_custom_filters = models.JSONField(default=dict, blank=True, null=True, verbose_name="Kullanıcı Özel Alan Filtreleri")

    # (Eski alanlar, veritabanı hatası vermesin diye tutuyoruz ama kullanmıyoruz)
    target_customers = models.ManyToManyField(CustomerCari, blank=True, related_name='old_targets') 
    
    # Multi-Tenancy: Her anket bir tenant'a ait
    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        verbose_name="Firma",
        null=True,
        blank=True,
        related_name='surveys'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

# 2. SORU MODELİ
class Question(models.Model):
    INPUT_TYPES = [
        ('text', 'Kısa Yazı'),
        ('textarea', 'Uzun Yazı'),
        ('photo', 'Fotoğraf'),
        ('select', 'Seçim Kutusu'),
        ('video', 'Video'),
        ('location', 'Konum'),
    ]

    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='questions')
    label = models.CharField(max_length=500, verbose_name="Soru Metni")
    input_type = models.CharField(max_length=20, choices=INPUT_TYPES, default='text')
    order = models.IntegerField(default=0)
    required = models.BooleanField(default=False)
    
    # Fotoğraf Limitleri
    min_photos = models.IntegerField(default=1, blank=True, null=True)
    max_photos = models.IntegerField(default=5, blank=True, null=True)

    # Bağlantı Ayarları
    parent_question = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='child_questions')
    trigger_answer = models.CharField(max_length=200, blank=True, null=True)

    dependency_question = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='dependent_questions',
        verbose_name="Bağlı Olduğu Soru"
    )

    dependency_value = models.CharField(
        max_length=255, 
        null=True, 
        blank=True, 
        verbose_name="Tetikleyen Cevap Değeri"
    )

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.label

# 3. SEÇENEKLER
class QuestionOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=200)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

# 4. CEVAPLAR
class SurveyAnswer(models.Model):
    task = models.ForeignKey(VisitTask, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer_text = models.TextField(blank=True, null=True)
    answer_photo = models.ImageField(upload_to='survey_photos/', blank=True, null=True)
    answer_video = models.FileField(upload_to='survey_videos/', blank=True, null=True, verbose_name="Video")
    
    # Konum Bilgileri (enlem, boylam)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True, verbose_name="Enlem")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True, verbose_name="Boylam")
    
    # Multi-Tenancy: Her cevap bir tenant'a ait
    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        verbose_name="Firma",
        null=True,
        blank=True,
        related_name='survey_answers'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)