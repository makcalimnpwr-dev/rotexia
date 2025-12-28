from django.db import migrations, models
import django.db.models.deletion


def seed_authority_nodes(apps, schema_editor):
    CustomUser = apps.get_model('users', 'CustomUser')
    AuthorityNode = apps.get_model('users', 'AuthorityNode')

    # Create nodes for all authorities
    choices = [c[0] for c in getattr(CustomUser, 'AUTHORITY_CHOICES', [])] or [
        'Admin',
        'Proje Müdürü',
        'Proje Sorumlusu',
        'Bölge Sorumlusu',
        'Supervisor',
        'Satış Sorumlusu',
        'Müşteri',
        'Saha Ekibi',
        'Uzman',
        'Günlükçü Personel',
    ]

    nodes = {}
    for idx, auth in enumerate(choices):
        node, _ = AuthorityNode.objects.get_or_create(authority=auth, defaults={'sort_order': idx})
        nodes[auth] = node

    # Ensure Admin is root by default; others start unlinked (parent=None)
    admin_node = nodes.get('Admin')
    if admin_node and admin_node.parent_id is not None:
        admin_node.parent = None
        admin_node.save(update_fields=['parent'])

    # Set existing superusers/staff to Admin authority if empty/default
    CustomUser.objects.filter(is_superuser=True).update(authority='Admin')


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_userfielddefinition_customuser_extra_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='authority',
            field=models.CharField(choices=[('Admin', 'Admin'), ('Proje Müdürü', 'Proje Müdürü'), ('Proje Sorumlusu', 'Proje Sorumlusu'), ('Bölge Sorumlusu', 'Bölge Sorumlusu'), ('Supervisor', 'Supervisor'), ('Satış Sorumlusu', 'Satış Sorumlusu'), ('Müşteri', 'Müşteri'), ('Saha Ekibi', 'Saha Ekibi'), ('Uzman', 'Uzman'), ('Günlükçü Personel', 'Günlükçü Personel')], default='Saha Ekibi', max_length=30, verbose_name='Yetki'),
        ),
        migrations.CreateModel(
            name='AuthorityNode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('authority', models.CharField(choices=[('Admin', 'Admin'), ('Proje Müdürü', 'Proje Müdürü'), ('Proje Sorumlusu', 'Proje Sorumlusu'), ('Bölge Sorumlusu', 'Bölge Sorumlusu'), ('Supervisor', 'Supervisor'), ('Satış Sorumlusu', 'Satış Sorumlusu'), ('Müşteri', 'Müşteri'), ('Saha Ekibi', 'Saha Ekibi'), ('Uzman', 'Uzman'), ('Günlükçü Personel', 'Günlükçü Personel')], max_length=30, unique=True, verbose_name='Yetki')),
                ('sort_order', models.IntegerField(default=0, verbose_name='Sıra')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='children', to='users.authoritynode', verbose_name='Üst Yetki')),
            ],
            options={
                'verbose_name': 'Yetki Hiyerarşisi Düğümü',
                'verbose_name_plural': 'Yetki Hiyerarşisi Düğümleri',
                'ordering': ['sort_order', 'authority'],
            },
        ),
        migrations.RunPython(seed_authority_nodes, migrations.RunPython.noop),
    ]


