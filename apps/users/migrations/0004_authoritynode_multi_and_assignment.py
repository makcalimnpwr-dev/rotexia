from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_customuser_authority_authoritynode'),
    ]

    operations = [
        migrations.AlterField(
            model_name='authoritynode',
            name='authority',
            field=models.CharField(choices=[('Admin', 'Admin'), ('Proje Müdürü', 'Proje Müdürü'), ('Proje Sorumlusu', 'Proje Sorumlusu'), ('Bölge Sorumlusu', 'Bölge Sorumlusu'), ('Supervisor', 'Supervisor'), ('Satış Sorumlusu', 'Satış Sorumlusu'), ('Müşteri', 'Müşteri'), ('Saha Ekibi', 'Saha Ekibi'), ('Uzman', 'Uzman'), ('Günlükçü Personel', 'Günlükçü Personel')], max_length=30, verbose_name='Yetki'),
        ),
        migrations.AddField(
            model_name='authoritynode',
            name='label',
            field=models.CharField(blank=True, default='', max_length=50, verbose_name='Etiket (opsiyonel)'),
        ),
        migrations.AddField(
            model_name='authoritynode',
            name='assigned_user',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_hierarchy_node', to=settings.AUTH_USER_MODEL, verbose_name='Atanan Kullanıcı'),
        ),
        migrations.AlterModelOptions(
            name='authoritynode',
            options={'ordering': ['sort_order', 'id'], 'verbose_name': 'Yetki Hiyerarşisi Düğümü', 'verbose_name_plural': 'Yetki Hiyerarşisi Düğümleri'},
        ),
    ]


