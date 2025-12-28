from __future__ import annotations

from typing import Optional

from django.contrib.auth import get_user_model

from apps.core.models import SystemSetting
from .models import AuthorityNode

User = get_user_model()

ROOT_ADMIN_SETTING_KEY = "root_admin_user_id"


def get_admin_node(create_if_missing: bool = True) -> Optional[AuthorityNode]:
    node = AuthorityNode.objects.filter(authority="Admin").order_by("id").first()
    if node or not create_if_missing:
        # Admin düğümüne kullanıcı atanamaz: varsa otomatik sök.
        if node and node.assigned_user_id:
            node.assigned_user = None
            node.save(update_fields=["assigned_user"])
        return node
    node = AuthorityNode.objects.create(authority="Admin", parent=None, sort_order=0)
    return node


def get_root_admin_user() -> Optional[User]:
    setting = SystemSetting.objects.filter(key=ROOT_ADMIN_SETTING_KEY).first()
    if not setting:
        return None
    try:
        user_id = int(str(setting.value).strip())
    except Exception:
        return None
    return User.objects.filter(id=user_id).first()


def ensure_root_admin_configured(user: User) -> None:
    """
    Root Admin'i SystemSetting üstünden sabitler.
    İlk set eden kazanır (immutable).
    """
    if not getattr(user, "is_authenticated", False):
        return

    # Admin düğümü varsa bile boş kalmalı
    get_admin_node(create_if_missing=True)

    existing = SystemSetting.objects.filter(key=ROOT_ADMIN_SETTING_KEY).first()
    if existing:
        return

    # Root admin'i sadece Admin authority veya superuser set edebilir (ilk girişte).
    if getattr(user, "is_superuser", False) or getattr(user, "authority", None) == "Admin":
        SystemSetting.objects.create(
            key=ROOT_ADMIN_SETTING_KEY,
            label="Root Admin Kullanıcı ID (DEĞİŞTİRMEYİN)",
            value=str(user.id),
            category="user",
            input_type="number",
            description="Sistemin tanrısı olan Admin kullanıcının ID'si. Otomatik set edilir, değiştirilemez.",
        )


def is_root_admin(user: User) -> bool:
    if not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False):
        return True
    root = get_root_admin_user()
    return bool(root and root.id == user.id)


def get_assigned_user_ids_under_admin_node() -> set[int]:
    """
    Returns assigned_user_ids in the subtree of the Admin AuthorityNode (Admin node itself included).
    Admin node is always treated as root and has no assigned user.
    """
    admin_node = get_admin_node(create_if_missing=True)
    if not admin_node:
        return set()

    nodes = list(AuthorityNode.objects.all().values("id", "parent_id", "assigned_user_id"))
    children: dict[int, list[int]] = {}
    assigned_by_id: dict[int, int | None] = {}
    for n in nodes:
        nid = n["id"]
        assigned_by_id[nid] = n["assigned_user_id"]
        pid = n["parent_id"]
        if pid is not None:
            children.setdefault(pid, []).append(nid)

    visible_node_ids: set[int] = set()
    stack: list[int] = [admin_node.id]
    while stack:
        cur = stack.pop()
        if cur in visible_node_ids:
            continue
        visible_node_ids.add(cur)
        stack.extend(children.get(cur, []))

    user_ids: set[int] = set()
    for nid in visible_node_ids:
        uid = assigned_by_id.get(nid)
        if uid:
            user_ids.add(uid)
    return user_ids


