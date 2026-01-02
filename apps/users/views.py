from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import CustomUser, UserRole, UserFieldDefinition, AuthorityNode, UserMenuPermission
from apps.forms.models import Survey
from .forms import UserCreationForm, UserEditForm, RoleForm
from .decorators import root_admin_required
from .utils import ensure_root_admin_configured, get_admin_node, get_root_admin_user, is_root_admin
from django.contrib import messages
from django.db.models import Q
from django.utils.text import slugify
from django.views.decorators.http import require_POST
import json
from apps.core.excel_utils import xlsx_from_rows, xlsx_to_rows

# --- AYARLAR ANA SAYFASI ---
@login_required
@root_admin_required
def settings_home(request):
    return render(request, 'apps/core/settings.html')

# --- ROL YÖNETİMİ ---
@login_required
@root_admin_required
def role_list(request):
    roles = UserRole.objects.all()
    
    # Yeni Rol Ekleme İşlemi
    if request.method == 'POST':
        form = RoleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Yeni rol eklendi.")
            return redirect('role_list')
    else:
        form = RoleForm()
        
    return render(request, 'apps/users/role_list.html', {'roles': roles, 'form': form})

@login_required
@root_admin_required
def role_delete(request, pk):
    role = get_object_or_404(UserRole, pk=pk)
    role.delete()
    messages.success(request, "Rol silindi.")
    return redirect('role_list')

# --- MEVCUT KULLANICI LİSTELEME ---
# apps/users/views.py içindeki user_list fonksiyonu:

# apps/users/views.py dosyasında user_list fonksiyonu:

@login_required
@root_admin_required
def user_list(request):
    users = CustomUser.objects.all().order_by('-date_joined')
    
    # BU SATIR SAYESİNDE FİLTRE KUTUSU HER ZAMAN GÜNCEL OLUR
    roles = UserRole.objects.all() 

    # ... filtreleme kodları (search, role_filter vb.) ...
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            Q(first_name__icontains=search_query) | 
            Q(last_name__icontains=search_query) |
            Q(user_code__icontains=search_query)
        )

    role_filter = request.GET.get('role', '')
    if role_filter:
        users = users.filter(role__id=role_filter)

    show_passive = request.GET.get('show_passive')
    if not show_passive:
        users = users.filter(is_active=True)

    context = {
        'users': users,
        'roles': roles, # HTML'e güncel rol listesini gönderiyoruz
        'search_query': search_query,
        'role_filter': int(role_filter) if role_filter and role_filter.isdigit() else '',
        'show_passive': show_passive
    }
    return render(request, 'apps/users/user_list.html', context)

# --- EKLEME / DÜZENLEME / SİLME ---
@login_required
@root_admin_required
def add_user(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Kullanıcı oluşturuldu.")
            return redirect('user_list')
    else:
        form = UserCreationForm()
    return render(request, 'apps/users/add_user.html', {'form': form})

@login_required
@root_admin_required
def edit_user(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)

    # Root admin düzenlenemez (hiyerarşi tutarlılığı için)
    if is_root_admin(user):
        messages.error(request, "Root Admin kullanıcısı değiştirilemez.")
        return redirect('user_list')
    
    # Özel alan tanımlarını çek
    user_field_defs = UserFieldDefinition.objects.all()
    
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save(commit=False)
            
            # Özel alanları extra_data'ya kaydet
            if not user.extra_data:
                user.extra_data = {}
            
            for uf_def in user_field_defs:
                field_name = f"user_custom_{uf_def.slug}"
                value = request.POST.get(field_name, '').strip()
                if value:
                    user.extra_data[uf_def.slug] = value
                elif uf_def.slug in user.extra_data:
                    # Boş değer gelirse sil
                    del user.extra_data[uf_def.slug]
            
            user.save()
            messages.success(request, "Güncellendi.")
            return redirect('user_list')
    else:
        form = UserEditForm(instance=user)
    
    return render(request, 'apps/users/edit_user.html', {
        'form': form, 
        'user': user,
        'user_field_defs': user_field_defs
    })

# Kullanıcı özel alan ekleme
@login_required
@root_admin_required
def add_user_field(request):
    if request.method == 'POST':
        field_name = request.POST.get('name', '').strip()
        if field_name:
            # Slug oluştur
            turkish_map = {'ı': 'i', 'ğ': 'g', 'ü': 'u', 'ş': 's', 'ö': 'o', 'ç': 'c', 'İ': 'I', 'Ğ': 'G', 'Ü': 'U', 'Ş': 'S', 'Ö': 'O', 'Ç': 'C'}
            name_clean = field_name
            for tr, en in turkish_map.items():
                name_clean = name_clean.replace(tr, en)
            slug = slugify(name_clean)
            
            try:
                UserFieldDefinition.objects.create(name=field_name, slug=slug)
                messages.success(request, f"'{field_name}' alanı tüm kullanıcılara eklendi.")
            except:
                messages.error(request, "Bu alan adı zaten var veya geçersiz.")
        else:
            messages.error(request, "Alan adı boş olamaz.")
    
    return redirect(request.META.get('HTTP_REFERER', 'user_list'))

@login_required
@root_admin_required
def delete_user(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    if is_root_admin(user):
        messages.error(request, "Root Admin kullanıcısı silinemez.")
        return redirect('user_list')
    if request.method == 'POST':
        user.delete()
        messages.warning(request, "Silindi.")
        return redirect('user_list')
    return render(request, 'apps/users/delete_confirm.html', {'user': user})

@login_required
@root_admin_required
def toggle_user_status(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    if is_root_admin(user):
        messages.error(request, "Root Admin pasife alınamaz.")
        return redirect('user_list')
    user.is_active = not user.is_active
    user.save()
    return redirect('user_list')

# --- EXCEL İŞLEMLERİ (GÜNCELLENDİ) ---
@login_required
@root_admin_required
def export_users(request):
    users = CustomUser.objects.all()
    data = []
    for u in users:
        data.append({
            'ID (DOKUNMAYIN)': u.id,
            'Kullanıcı Kodu': u.user_code,
            'Ad': u.first_name,
            'Soyad': u.last_name,
            'E-posta': u.email,
            'Telefon': u.phone,
            'Rol': u.role.name if u.role else '', # Rolün adını al
            'Aktif Durumu': u.is_active,
            'Şifre': '',
        })

    content = xlsx_from_rows(data, sheet_name="Kullanıcılar")
    response = HttpResponse(content, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=kullanici_listesi.xlsx'
    return response

@login_required
@root_admin_required
def import_users(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        try:
            rows = xlsx_to_rows(request.FILES['excel_file'])
            if not rows:
                messages.error(request, "Excel boş veya okunamadı.")
                return redirect('user_list')
            root_admin = get_root_admin_user()

            def _is_blank(v) -> bool:
                return v is None or str(v).strip() == "" or str(v).strip().lower() == "nan"

            for row in rows:
                user_id = row.get('ID (DOKUNMAYIN)')
                user_code = row.get('Kullanıcı Kodu')
                
                # Rolü bul veya oluştur
                role_name = row.get('Rol')
                role_obj = None
                if role_name:
                    role_obj, _ = UserRole.objects.get_or_create(name=role_name)

                # Kullanıcı verilerini hazırla
                defaults = {
                    'first_name': row.get('Ad'),
                    'last_name': row.get('Soyad'),
                    'email': row.get('E-posta'),
                    'phone': row.get('Telefon'),
                    'role': role_obj,
                    'is_active': (row.get('Aktif Durumu', True) if not _is_blank(row.get('Aktif Durumu', None)) else True)
                }

                # Güncelleme veya Oluşturma
                if not _is_blank(user_id):
                    try:
                        user = CustomUser.objects.get(pk=int(float(str(user_id).strip())))
                        # Root Admin değiştirilemez
                        if root_admin and user.id == root_admin.id:
                            continue
                        for key, value in defaults.items():
                            setattr(user, key, value)
                        # Şifre varsa güncelle
                        pwd = row.get('Şifre')
                        if not _is_blank(pwd):
                            user.set_password(str(pwd))
                        user.save()
                    except: pass
                else:
                    # Yeni Kayıt
                    if root_admin and str(user_code).strip() == str(root_admin.user_code).strip():
                        continue
                    defaults['username'] = user_code
                    defaults['user_code'] = user_code
                    pwd = row.get('Şifre')
                    if _is_blank(pwd):
                        pwd = "123"
                    user = CustomUser.objects.create(**defaults)
                    user.set_password(str(pwd))
                    user.save()
                    
            messages.success(request, "Excel başarıyla işlendi.")
        except Exception as e:
            messages.error(request, f"Hata: {e}")
            
    return redirect('user_list')


# --- HİYERARŞİ ---
@login_required
@root_admin_required
def hierarchy(request):
    # En azından Admin root düğümü olsun + root admin sabitlensin (SystemSetting)
    ensure_root_admin_configured(request.user)
    admin_node = get_admin_node(create_if_missing=True)

    qs = AuthorityNode.objects.select_related('assigned_user').all().order_by('sort_order', 'id')
    all_nodes = list(qs.values(
        'id', 'authority', 'parent_id', 'sort_order', 'label',
        'assigned_user_id', 'assigned_user__first_name', 'assigned_user__last_name', 'assigned_user__user_code'
    ))

    # Sadece Admin'den aşağı bağlı olanları göster
    children = {}
    for n in all_nodes:
        p = n["parent_id"]
        if p is not None:
            children.setdefault(p, []).append(n["id"])

    visible = set()
    visible.add(admin_node.id)
    stack = [admin_node.id]
    while stack:
        cur = stack.pop()
        for ch in children.get(cur, []):
            if ch not in visible:
                visible.add(ch)
                stack.append(ch)

    nodes = [n for n in all_nodes if n["id"] in visible]
    users = list(CustomUser.objects.all().order_by('first_name', 'last_name').values('id', 'first_name', 'last_name', 'user_code', 'authority'))
    context = {
        'nodes_json': json.dumps(nodes, ensure_ascii=False),
        'users_json': json.dumps(users, ensure_ascii=False),
        'authority_choices': CustomUser.AUTHORITY_CHOICES,
    }
    return render(request, 'apps/users/hierarchy.html', context)

@login_required
@require_POST
@root_admin_required
def hierarchy_create_node(request):
    """Seçilen düğümün altına yeni bir düğüm oluştur (yetki düğümü veya kullanıcı düğümü)."""
    try:
        data = json.loads(request.body.decode('utf-8'))
        parent_id = data.get('parent_id')
        authority = data.get('authority')
        label = (data.get('label') or '').strip()
        assigned_user_id = data.get('assigned_user_id')

        if not authority:
            return JsonResponse({'success': False, 'message': 'authority gerekli'}, status=400)

        valid_authorities = {c[0] for c in CustomUser.AUTHORITY_CHOICES}
        if authority not in valid_authorities:
            return JsonResponse({'success': False, 'message': 'Geçersiz authority'}, status=400)

        # Admin hariç birden fazla düğüm serbest; Admin'i tek tutalım
        if authority == 'Admin' and AuthorityNode.objects.filter(authority='Admin').exists():
            return JsonResponse({'success': False, 'message': 'Admin düğümü zaten var.'}, status=400)

        parent = None
        if parent_id is not None:
            parent = get_object_or_404(AuthorityNode, id=parent_id)
        else:
            # Root olarak sadece Admin olabilir
            if authority != 'Admin':
                return JsonResponse({'success': False, 'message': 'Root düğüm sadece Admin olabilir.'}, status=400)

        # Sıra: kardeşlerde max + 1
        max_sort = AuthorityNode.objects.filter(parent=parent).order_by('-sort_order').values_list('sort_order', flat=True).first()
        sort_order = (max_sort + 1) if max_sort is not None else 0

        node = AuthorityNode.objects.create(
            authority=authority,
            parent=parent,
            sort_order=sort_order,
            label=label,
        )

        if assigned_user_id:
            user = get_object_or_404(CustomUser, id=assigned_user_id)
            root_admin = get_root_admin_user()
            if root_admin and user.id == root_admin.id:
                return JsonResponse({'success': False, 'message': 'Root Admin başka bir düğüme taşınamaz.'}, status=400)
            # Kullanıcı başka düğümdeyse taşı
            AuthorityNode.objects.filter(assigned_user_id=user.id).exclude(id=node.id).update(assigned_user=None)
            node.assigned_user = user
            node.save(update_fields=['assigned_user'])
            # Kullanıcı yetkisini node yetkisine senkronla
            if user.authority != node.authority:
                user.authority = node.authority
                user.save(update_fields=['authority'])

        payload = {
            'id': node.id,
            'authority': node.authority,
            'parent_id': node.parent_id,
            'sort_order': node.sort_order,
            'label': node.label,
            'assigned_user_id': node.assigned_user_id,
            'assigned_user__first_name': node.assigned_user.first_name if node.assigned_user_id else '',
            'assigned_user__last_name': node.assigned_user.last_name if node.assigned_user_id else '',
            'assigned_user__user_code': node.assigned_user.user_code if node.assigned_user_id else '',
        }
        return JsonResponse({'success': True, 'node': payload})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
@require_POST
@root_admin_required
def hierarchy_set_parent(request):
    """Bir düğümü başka bir düğümün altına bağla."""
    try:
        data = json.loads(request.body.decode('utf-8'))
        child_id = data.get('child_id')
        parent_id = data.get('parent_id')  # None olabilir (root yapmak için)
        if not child_id:
            return JsonResponse({'success': False, 'message': 'child_id gerekli'}, status=400)

        child_node = get_object_or_404(AuthorityNode, id=child_id)
        if child_node.authority == 'Admin' and parent_id:
            return JsonResponse({'success': False, 'message': 'Admin taşınamaz.'}, status=400)

        new_parent = None
        if parent_id:
            parent_node = get_object_or_404(AuthorityNode, id=parent_id)
            # Döngü koruması
            cur = parent_node
            while cur:
                if cur.id == child_node.id:
                    return JsonResponse({'success': False, 'message': 'Döngü oluşturulamaz.'}, status=400)
                cur = cur.parent
            new_parent = parent_node
        else:
            # Root olarak sadece Admin olabilir
            if child_node.authority != 'Admin':
                return JsonResponse({'success': False, 'message': 'Sadece Admin root olabilir.'}, status=400)
            new_parent = None

        # Aynı parent'a taşıma yoksa son sıraya ekle
        if child_node.parent_id != (new_parent.id if new_parent else None):
            max_sort = AuthorityNode.objects.filter(parent=new_parent).exclude(id=child_node.id).order_by('-sort_order').values_list('sort_order', flat=True).first()
            child_node.sort_order = (max_sort + 1) if max_sort is not None else 0
            child_node.parent = new_parent
            child_node.save(update_fields=['parent', 'sort_order'])
        else:
            # yine de payload dönelim
            pass

        node = AuthorityNode.objects.select_related('assigned_user').get(id=child_node.id)
        payload = {
            'id': node.id,
            'authority': node.authority,
            'parent_id': node.parent_id,
            'sort_order': node.sort_order,
            'label': node.label,
            'assigned_user_id': node.assigned_user_id,
            'assigned_user__first_name': node.assigned_user.first_name if node.assigned_user_id else '',
            'assigned_user__last_name': node.assigned_user.last_name if node.assigned_user_id else '',
            'assigned_user__user_code': node.assigned_user.user_code if node.assigned_user_id else '',
        }
        return JsonResponse({'success': True, 'node': payload})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
@require_POST
@root_admin_required
def hierarchy_unassign_user(request):
    """Düğümden kullanıcıyı kaldır."""
    try:
        data = json.loads(request.body.decode('utf-8'))
        node_id = data.get('node_id')
        if not node_id:
            return JsonResponse({'success': False, 'message': 'node_id gerekli'}, status=400)
        node = get_object_or_404(AuthorityNode, id=node_id)
        if node.authority == 'Admin':
            return JsonResponse({'success': False, 'message': 'Admin düğümünden kullanıcı kaldırılamaz.'}, status=400)
        node.assigned_user = None
        node.save(update_fields=['assigned_user'])
        payload = {
            'id': node.id,
            'authority': node.authority,
            'parent_id': node.parent_id,
            'sort_order': node.sort_order,
            'label': node.label,
            'assigned_user_id': None,
            'assigned_user__first_name': '',
            'assigned_user__last_name': '',
            'assigned_user__user_code': '',
        }
        return JsonResponse({'success': True, 'node': payload})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
@require_POST
@root_admin_required
def hierarchy_delete_node(request):
    """Düğümü sil. Çocuk düğümleri bir üst parent'a taşınır (root silinmez)."""
    try:
        data = json.loads(request.body.decode('utf-8'))
        node_id = data.get('node_id')
        if not node_id:
            return JsonResponse({'success': False, 'message': 'node_id gerekli'}, status=400)
        node = get_object_or_404(AuthorityNode, id=node_id)
        if node.authority == 'Admin':
            return JsonResponse({'success': False, 'message': 'Admin düğümü silinemez.'}, status=400)

        parent = node.parent
        if parent is None:
            parent = AuthorityNode.objects.filter(authority='Admin').order_by('id').first()

        # hedef parent altına son sıradan başlayarak çocukları taşı
        max_sort = AuthorityNode.objects.filter(parent=parent).exclude(id=node.id).order_by('-sort_order').values_list('sort_order', flat=True).first()
        next_sort = (max_sort + 1) if max_sort is not None else 0

        children = list(AuthorityNode.objects.filter(parent=node).order_by('sort_order', 'id'))
        reparented = []
        for ch in children:
            ch.parent = parent
            ch.sort_order = next_sort
            next_sort += 1
            reparented.append({'id': ch.id, 'parent_id': ch.parent_id, 'sort_order': ch.sort_order})
        if children:
            AuthorityNode.objects.bulk_update(children, ['parent', 'sort_order'])

        deleted_id = node.id
        node.delete()
        return JsonResponse({'success': True, 'deleted_id': deleted_id, 'reparented': reparented})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@login_required
@require_POST
@root_admin_required
def hierarchy_assign_user(request):
    """Seçilen düğüme kullanıcı ata (ağaçta Ad Soyad (Yetki) görünür)."""
    try:
        data = json.loads(request.body.decode('utf-8'))
        user_id = data.get('user_id')
        node_id = data.get('node_id')
        if not user_id or not node_id:
            return JsonResponse({'success': False, 'message': 'user_id ve node_id gerekli'}, status=400)
        user = get_object_or_404(CustomUser, id=user_id)
        node = get_object_or_404(AuthorityNode, id=node_id)

        if node.authority == 'Admin':
            return JsonResponse({'success': False, 'message': 'Admin düğümüne kullanıcı atanamaz/değiştirilemez.'}, status=400)

        root_admin = get_root_admin_user()
        if root_admin and user.id == root_admin.id:
            return JsonResponse({'success': False, 'message': 'Root Admin başka bir düğüme taşınamaz.'}, status=400)

        # Kullanıcı başka düğümdeyse taşı
        AuthorityNode.objects.filter(assigned_user_id=user.id).exclude(id=node.id).update(assigned_user=None)
        node.assigned_user = user
        node.save(update_fields=['assigned_user'])

        # Kullanıcı yetkisini node yetkisine senkronla
        if user.authority != node.authority:
            user.authority = node.authority
            user.save(update_fields=['authority'])

        payload = {
            'id': node.id,
            'authority': node.authority,
            'parent_id': node.parent_id,
            'sort_order': node.sort_order,
            'label': node.label,
            'assigned_user_id': node.assigned_user_id,
            'assigned_user__first_name': user.first_name,
            'assigned_user__last_name': user.last_name,
            'assigned_user__user_code': user.user_code,
        }
        return JsonResponse({'success': True, 'node': payload})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
@root_admin_required
def hierarchy_users_for_authority(request):
    authority = request.GET.get('authority')
    if not authority:
        return JsonResponse({'success': False, 'message': 'authority gerekli'}, status=400)
    qs = CustomUser.objects.filter(authority=authority).order_by('first_name', 'last_name')
    return JsonResponse({
        'success': True,
        'users': [{'id': u.id, 'name': f"{u.first_name} {u.last_name}".strip() or u.user_code, 'user_code': u.user_code} for u in qs]
    })

@login_required
@root_admin_required
def hierarchy_get_menu_permissions(request):
    """Kullanıcının menü izinlerini getir"""
    user_id = request.GET.get('user_id')
    if not user_id:
        return JsonResponse({'success': False, 'message': 'user_id gerekli'}, status=400)
    
    try:
        user = CustomUser.objects.get(pk=user_id)
        permissions = {}
        for perm in UserMenuPermission.objects.filter(user=user):
            permissions[perm.menu_key] = {
                'can_view': perm.can_view,
                'can_edit': perm.can_edit
            }
        
        # Anketleri de ekle
        surveys = Survey.objects.all().order_by('title')
        surveys_data = [{'id': s.id, 'title': s.title} for s in surveys]
        
        return JsonResponse({
            'success': True, 
            'permissions': permissions,
            'surveys': surveys_data
        })
    except CustomUser.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Kullanıcı bulunamadı'}, status=404)

@login_required
@require_POST
@root_admin_required
def hierarchy_save_menu_permissions(request):
    """Kullanıcının menü izinlerini kaydet"""
    try:
        data = json.loads(request.body.decode('utf-8'))
        user_id = data.get('user_id')
        permissions = data.get('permissions', {})
        
        if not user_id:
            return JsonResponse({'success': False, 'message': 'user_id gerekli'}, status=400)
        
        user = CustomUser.objects.get(pk=user_id)
        
        # Mevcut izinleri sil
        UserMenuPermission.objects.filter(user=user).delete()
        
        # Yeni izinleri kaydet
        for menu_key, perm_data in permissions.items():
            UserMenuPermission.objects.create(
                user=user,
                menu_key=menu_key,
                menu_label=perm_data.get('menu_label', menu_key),
                can_view=perm_data.get('can_view', False),
                can_edit=perm_data.get('can_edit', False)
            )
        
        return JsonResponse({'success': True, 'message': 'İzinler kaydedildi'})
    except CustomUser.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Kullanıcı bulunamadı'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)