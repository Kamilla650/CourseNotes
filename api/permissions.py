from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Доступ только администраторам. Иначе — 403 Forbidden."""

    message = 'Недостаточно прав: требуется роль администратора.'

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'role', None) == 'admin'
        )