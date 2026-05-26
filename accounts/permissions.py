from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """Permite acesso apenas a administradores."""
    message = 'Acesso restrito a administradores.'

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.papel == 'admin'


class IsOwnerOrAdmin(permissions.BasePermission):
    """Permite acesso ao próprio usuário ou administradores."""
    message = 'Acesso não autorizado.'

    def has_object_permission(self, request, view, obj):
        if request.user.papel == 'admin':
            return True
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return obj == request.user


def _resolve_fonte(obj):
    """Extrai a `fonte` de Obra, Capitulo ou Pagina."""
    if hasattr(obj, 'fonte'):
        return obj.fonte
    if hasattr(obj, 'obra'):
        return obj.obra.fonte
    if hasattr(obj, 'capitulo'):
        return obj.capitulo.obra.fonte
    return None


class CanManageUsers(permissions.BasePermission):
    """
    Quem pode entrar na área de gestão de usuários do painel.

    Regras de objeto:
      - Superuser: tudo
      - Admin do painel: só usuários do próprio time, e nunca superusers
    """
    message = 'Você não tem permissão para gerenciar usuários.'

    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and (u.is_superuser or u.papel == 'admin'))

    def has_object_permission(self, request, view, obj):
        u = request.user
        if not u or not u.is_authenticated:
            return False
        if u.is_superuser:
            return True
        if u.papel != 'admin':
            return False
        if obj.is_superuser:
            return False
        return obj.time == u.time


class MatchUserTime(permissions.BasePermission):
    """
    Garante que cada usuário só mexe em obras do próprio time.

    Regras:
      - Usuário não autenticado: bloqueado.
      - Superuser: passa em tudo.
      - Em writes (POST/PUT/PATCH): se houver `fonte` no payload, ela deve
        bater com o time do usuário. Se ausente, o ViewSet força via
        perform_create/perform_update.
      - Em object-level: a `fonte` da obra (ou da obra dona do capítulo /
        página) deve bater com o time do usuário.
    """
    message = 'Você não tem permissão sobre essa fonte.'

    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        if user.has_full_access:
            return True
        if request.method in ('POST', 'PUT', 'PATCH'):
            fonte_payload = request.data.get('fonte')
            if fonte_payload and fonte_payload != user.time:
                return False
        return True

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user.is_authenticated:
            return False
        if user.has_full_access:
            return True
        fonte = _resolve_fonte(obj)
        return fonte == user.time
