from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from django.contrib.auth import get_user_model

from .models import AuthorityNode

User = get_user_model()


@dataclass(frozen=True)
class HierarchyScope:
    """Convenience object for permission/scoping checks."""

    usernames: set[str]

    def contains_username(self, username: str) -> bool:
        return username in self.usernames


def get_hierarchy_scope_for_user(user, include_self: bool = True) -> HierarchyScope:
    """
    Returns the set of usernames (merch_code) visible to `user` via AuthorityNode subtree.

    - If user is superuser or Admin authority => everything (empty set means "all").
    - If user is not attached to any AuthorityNode => only self (if include_self).
    """
    if getattr(user, "is_superuser", False) or getattr(user, "authority", None) == "Admin":
        return HierarchyScope(usernames=set())

    if not getattr(user, "is_authenticated", False):
        return HierarchyScope(usernames=set())

    root = AuthorityNode.objects.filter(assigned_user_id=user.id).values_list("id", flat=True).first()
    if not root:
        return HierarchyScope(usernames={user.username} if include_self else set())

    # Single query graph walk (tree size is small, keep it simple)
    nodes = list(
        AuthorityNode.objects.all().values("id", "parent_id", "assigned_user_id")
    )
    children: dict[int, list[int]] = {}
    assigned_by_id: dict[int, int | None] = {}
    for n in nodes:
        nid = n["id"]
        assigned_by_id[nid] = n["assigned_user_id"]
        pid = n["parent_id"]
        if pid is not None:
            children.setdefault(pid, []).append(nid)

    visible_node_ids: set[int] = set()
    stack: list[int] = [root]
    while stack:
        cur = stack.pop()
        if cur in visible_node_ids:
            continue
        visible_node_ids.add(cur)
        stack.extend(children.get(cur, []))

    usernames: set[str] = set()
    if include_self:
        usernames.add(user.username)

    user_ids: set[int] = set()
    for nid in visible_node_ids:
        # include_self=False ise root düğüm (kullanıcının kendi düğümü) dahil edilmesin
        if not include_self and nid == root:
            continue
        uid = assigned_by_id.get(nid)
        if uid:
            user_ids.add(uid)

    if user_ids:
        usernames.update(
            User.objects.filter(id__in=user_ids).values_list("username", flat=True)
        )

    return HierarchyScope(usernames=usernames)


def get_descendant_users(user) -> Iterable[User]:
    """
    Returns assigned users in the subtree *excluding* self, ordered by name.
    """
    scope = get_hierarchy_scope_for_user(user, include_self=False)
    if not scope.usernames:
        return User.objects.none()
    return User.objects.filter(username__in=scope.usernames).order_by("first_name", "last_name", "username")


