from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    """Admin para o modelo de usuário customizado."""

    list_display = ['username', 'email', 'papel', 'time', 'is_active', 'is_staff', 'date_joined']
    list_filter = ['papel', 'time', 'is_active', 'is_staff']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-date_joined']

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Permissões do Painel', {
            'fields': ('papel', 'time', 'avatar_url'),
            'description': (
                'Admins do painel precisam ter um <b>time</b>. '
                'Apenas superusers ficam sem time.'
            ),
        }),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Permissões do Painel', {
            'fields': ('papel', 'time', 'avatar_url')
        }),
    )
