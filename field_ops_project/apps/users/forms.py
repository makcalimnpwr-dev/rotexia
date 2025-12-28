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
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label="Şifre")
    
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
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'user_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Örn: TR-001'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'authority': forms.Select(attrs={'class': 'form-select'}),
        }

    # İŞTE SİHİRLİ KOD BURASI (__init__)
    # Form her oluşturulduğunda çalışır ve listeyi günceller
    def __init__(self, *args, **kwargs):
        super(UserCreationForm, self).__init__(*args, **kwargs)
        self.fields['role'].queryset = UserRole.objects.all()

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.username = self.cleaned_data["user_code"]
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
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'authority': forms.Select(attrs={'class': 'form-select'}),
        }

    # BURADA DA AYNISINI YAPIYORUZ
    def __init__(self, *args, **kwargs):
        super(UserEditForm, self).__init__(*args, **kwargs)
        self.fields['role'].queryset = UserRole.objects.all()

    def save(self, commit=True):
        user = super().save(commit=False)
        new_pwd = self.cleaned_data.get('new_password')
        if new_pwd:
            user.set_password(new_pwd)
        if commit:
            user.save()
        return user