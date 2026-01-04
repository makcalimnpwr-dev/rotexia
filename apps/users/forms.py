from django import forms
from .models import CustomUser, UserRole

# --- ROL YÖNETİMİ FORMU ---
class RoleForm(forms.ModelForm):
    class Meta:
        model = UserRole
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Örn: Depo Sorumlusu'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
        }

# --- YENİ KULLANICI EKLEME FORMU ---
class UserCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password', 'value': ''}), label="Şifre")
    
    # Rol alanı tanımı
    role = forms.ModelChoiceField(
        queryset=UserRole.objects.none(), # Başlangıçta boş bırakıyoruz, aşağıda dolduracağız
        empty_label="Rol Seçiniz", 
        required=True, 
        label="Rol / Görev",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'user_code', 'password', 'phone', 'email', 'role', 'authority']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'user_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Örn: TR-001', 'autocomplete': 'off', 'value': ''}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'authority': forms.Select(attrs={'class': 'form-select'}),
        }

    # İŞTE SİHİRLİ KOD BURASI (__init__)
    # Form her oluşturulduğunda çalışır ve listeyi günceller
    def __init__(self, *args, **kwargs):
        # Request'i al (tenant kontrolü için)
        self.request = kwargs.pop('request', None)
        super(UserCreationForm, self).__init__(*args, **kwargs)
        # Tenant'a göre rolleri filtrele - HER ZAMAN GÜNCEL OLSUN
        if self.request:
            from apps.core.tenant_utils import get_current_tenant
            tenant = get_current_tenant(self.request)
            if tenant:
                # Sadece bu tenant'ın rolleri - DEBUG: Queryset'i kontrol et
                queryset = UserRole.objects.filter(tenant=tenant).order_by('name')
                self.fields['role'].queryset = queryset
                # Debug: Roller var mı kontrol et
                if queryset.count() == 0:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"UserCreationForm: Tenant '{tenant.name}' (ID: {tenant.id}) için hiç rol yok!")
            else:
                # Tenant yoksa boş queryset (güvenlik)
                self.fields['role'].queryset = UserRole.objects.none()
        else:
            # Request yoksa tüm rolleri göster (fallback)
            self.fields['role'].queryset = UserRole.objects.all()

    def clean_user_code(self):
        """User code'un tenant bazında unique olup olmadığını kontrol et"""
        user_code = self.cleaned_data.get('user_code')
        if not user_code:
            return user_code
        
        # Request'ten tenant'ı al
        tenant = None
        if self.request:
            from apps.core.tenant_utils import get_current_tenant
            tenant = get_current_tenant(self.request)
        
        # Eğer tenant yoksa hata ver
        if not tenant:
            raise forms.ValidationError("Firma seçimi yapılmamış. Lütfen bir firma seçin.")
        
        # Aynı tenant içinde bu user_code var mı kontrol et
        queryset = CustomUser.objects.filter(user_code=user_code, tenant=tenant)
        # Eğer form'da bir instance varsa (düzenleme), kendisini hariç tut
        if self.instance and self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise forms.ValidationError(
                f"Bu kullanıcı kodu '{tenant.name}' firmasında zaten kullanılıyor. "
                f"Farklı firmalarda aynı kod kullanılabilir."
            )
        
        return user_code
    
    # clean() metodunu kaldırdık - username otomatik oluşturulacak ve global unique olacak

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        
        # Tenant'ı ata
        tenant = None
        if self.request:
            from apps.core.tenant_utils import get_current_tenant, set_tenant_on_save
            tenant = get_current_tenant(self.request)
            set_tenant_on_save(user, self.request)
        
        # Username'i tenant slug + user_code formatında oluştur
        user_code = self.cleaned_data.get("user_code", "")
        if tenant and tenant.slug:
            # Format: {tenant_slug}_{user_code} (örn: pastel_merch1)
            user.username = f"{tenant.slug}_{user_code}"
        else:
            # Tenant yoksa sadece user_code (root admin için)
            user.username = user_code
        
        if commit:
            user.save()
        return user

# --- KULLANICI DÜZENLEME FORMU ---
class UserEditForm(forms.ModelForm):
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}), 
        required=False, 
        label="Yeni Şifre"
    )
    
    role = forms.ModelChoiceField(
        queryset=UserRole.objects.none(), 
        empty_label="Rol Seçiniz", 
        required=True, 
        label="Rol / Görev",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'user_code', 'phone', 'email', 'is_active', 'role', 'authority']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'user_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Örn: TR-001'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'activeCheck'}),
            'authority': forms.Select(attrs={'class': 'form-select'}),
        }

    # BURADA DA AYNISINI YAPIYORUZ
    def __init__(self, *args, **kwargs):
        # Request'i al (tenant kontrolü için)
        self.request = kwargs.pop('request', None)
        super(UserEditForm, self).__init__(*args, **kwargs)
        # Tenant'a göre rolleri filtrele - HER ZAMAN GÜNCEL OLSUN
        if self.request:
            from apps.core.tenant_utils import get_current_tenant
            tenant = get_current_tenant(self.request)
            if tenant:
                # Sadece bu tenant'ın rolleri - DEBUG: Queryset'i kontrol et
                queryset = UserRole.objects.filter(tenant=tenant).order_by('name')
                self.fields['role'].queryset = queryset
                # Debug: Roller var mı kontrol et
                if queryset.count() == 0:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"UserEditForm: Tenant '{tenant.name}' (ID: {tenant.id}) için hiç rol yok!")
            else:
                # Tenant yoksa boş queryset (güvenlik)
                self.fields['role'].queryset = UserRole.objects.none()
        else:
            # Request yoksa tüm rolleri göster (fallback)
            self.fields['role'].queryset = UserRole.objects.all()
        # Kullanıcı kodu oluşturulduktan sonra değiştirilemez olmalı
        if getattr(self.instance, "pk", None):
            self.fields['user_code'].disabled = True
            self.fields['user_code'].help_text = "Kullanıcı kodu oluşturulduktan sonra değiştirilemez."

    def clean_user_code(self):
        """
        user_code alanı edit ekranında değiştirilemez.
        Template manipülasyonu olsa bile instance değerini koru.
        """
        if getattr(self.instance, "pk", None):
            return self.instance.user_code
        return self.cleaned_data.get('user_code')

    def save(self, commit=True):
        user = super().save(commit=False)
        # Username'i tenant slug + user_code formatında güncelle
        if user.user_code:
            tenant = getattr(user, 'tenant', None)
            if tenant and tenant.slug:
                # Format: {tenant_slug}_{user_code} (örn: pastel_merch1)
                expected_username = f"{tenant.slug}_{user.user_code}"
                if user.username != expected_username:
                    user.username = expected_username
            else:
                # Tenant yoksa sadece user_code (root admin için)
                if user.username != user.user_code:
                    user.username = user.user_code
        new_pwd = self.cleaned_data.get('new_password')
        if new_pwd:
            user.set_password(new_pwd)
        if commit:
            user.save()
        return user