from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    """
    Usuário customizado.

    Hierarquia:
      - superuser do Django: acesso transversal a todos os times e ao /admin/
      - admin do painel (papel='admin'): tem `time` obrigatório, gerencia
        usuários do próprio time e edita conteúdo do próprio time
    """
    PAPEIS = [
        ('admin', 'Administrador'),
    ]

    TIMES = [
        ('scan', 'Scan'),
        ('agregador', 'Agregador'),
    ]

    papel = models.CharField(
        max_length=10,
        choices=PAPEIS,
        default='admin',
        help_text='Nível de acesso do usuário'
    )
    time = models.CharField(
        max_length=20,
        choices=TIMES,
        blank=True,
        null=True,
        help_text='Time do usuário. Vazio apenas para superuser.'
    )
    avatar_url = models.CharField(
        max_length=500,
        blank=True,
        help_text='URL do avatar do usuário'
    )

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'

    def __str__(self):
        return f'{self.username} ({self.get_papel_display()})'

    @property
    def is_admin(self):
        return self.papel == 'admin'

    @property
    def can_edit(self):
        """Quem pode editar conteúdo (obras, capítulos, páginas)."""
        return self.is_superuser or self.papel == 'admin'

    @property
    def is_scan(self):
        return self.time == 'scan'

    @property
    def is_agregador(self):
        return self.time == 'agregador'

    @property
    def has_full_access(self):
        """Apenas superusers do Django têm acesso transversal a ambos os times."""
        return self.is_superuser

    @property
    def can_manage_users(self):
        """Superuser ou admin do painel podem gerenciar usuários."""
        return self.is_superuser or self.papel == 'admin'
