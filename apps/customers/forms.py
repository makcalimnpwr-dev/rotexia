from django import forms
from django.utils.text import slugify
from .models import Customer, CustomerCari, CustomFieldDefinition

class CariForm(forms.ModelForm):
    class Meta:
        model = CustomerCari
        fields = ['name']
        widgets = {'name': forms.TextInput(attrs={'class': 'form-control'})}

class CustomFieldForm(forms.ModelForm):
    class Meta:
        model = CustomFieldDefinition
        fields = ['name']
        widgets = {'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Örn: Raf Sayısı, Mağaza Tipi'})}
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        # İsmi slug'a çevir (Raf Sayısı -> raf-sayisi)
        instance.slug = slugify(instance.name.replace('ı', 'i').replace('ğ', 'g').replace('ü', 'u').replace('ş', 's').replace('ö', 'o').replace('ç', 'c'))
        if commit:
            instance.save()
        return instance

class CustomerForm(forms.ModelForm):
    customer_code = forms.CharField(label="Müşteri Kodu", required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    cari = forms.ModelChoiceField(queryset=CustomerCari.objects.all(), empty_label="Firma Seçiniz", required=False, widget=forms.Select(attrs={'class': 'form-select'}))
    latitude = forms.CharField(required=False, label="Enlem", widget=forms.TextInput(attrs={'class': 'form-control'}))
    longitude = forms.CharField(required=False, label="Boylam", widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Customer
        fields = ['customer_code', 'name', 'cari', 'city', 'district', 'address', 'latitude', 'longitude', 'phone', 'authorized_person']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'district': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'authorized_person': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    # --- SİHİRLİ KISIM: DİNAMİK ALANLARI YÜKLE ---
    def __init__(self, *args, **kwargs):
        super(CustomerForm, self).__init__(*args, **kwargs)
        
        # 1. Tanımlı özel alanları çek
        custom_fields = CustomFieldDefinition.objects.all()
        
        # 2. Eğer düzenleme modundaysak mevcut veriyi al
        current_extra_data = {}
        if self.instance and self.instance.pk and self.instance.extra_data:
            current_extra_data = self.instance.extra_data

        # 3. Form alanlarını yarat
        for cf in custom_fields:
            field_name = f"custom_{cf.slug}"
            self.fields[field_name] = forms.CharField(
                label=cf.name,
                required=False,
                initial=current_extra_data.get(cf.slug, ''), # Varsa değerini getir
                widget=forms.TextInput(attrs={'class': 'form-control bg-light border-info'})
            )

    # --- KAYDEDERKEN DİNAMİK ALANLARI JSON'A PAKETLE ---
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Formdaki custom_ ile başlayan alanları bul
        custom_data = {}
        for key, value in self.cleaned_data.items():
            if key.startswith("custom_"):
                slug_name = key.replace("custom_", "")
                custom_data[slug_name] = value
        
        # JSON alanına yaz
        instance.extra_data = custom_data
        
        if commit:
            instance.save()
        return instance
    
    def clean_latitude(self):
        data = self.cleaned_data['latitude']
        if data: return float(str(data).replace(',', '.'))
        return None

    def clean_longitude(self):
        data = self.cleaned_data['longitude']
        if data: return float(str(data).replace(',', '.'))
        return None