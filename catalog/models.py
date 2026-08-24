from django.db import models
from django.conf import settings
from django.utils import timezone


class Obra(models.Model):
    STATUS_CHOICES = [
        ('ongoing', 'Em andamento'),
        ('completed', 'Completo'),
    ]
    FONTE_CHOICES = [
        ('scan', 'Scan'),
        ('agregador', 'Agregador'),
    ]
    IDIOMA_CHOICES = [
        ('pt', 'Português'),
        ('en', 'English'),
    ]
    TIPO_CHOICES = [
        ('manga', 'Mangá'),
        ('manhwa', 'Manhwa'),
        ('manhua', 'Manhua'),
        ('novel', 'Novel'),
        ('light_novel', 'Light Novel'),
        ('webtoon', 'Webtoon'),
        ('unknown', 'Desconhecido'),
    ]
    titulo = models.CharField(max_length=255, db_index=True)
    autor = models.CharField(max_length=255, blank=True, default='')
    slug = models.SlugField(unique=True, db_index=True, max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ongoing')
    fonte = models.CharField(max_length=20, choices=FONTE_CHOICES, default='scan')
    idioma = models.CharField(max_length=2, choices=IDIOMA_CHOICES, default='pt', db_index=True)
    tipo_obra = models.CharField(max_length=20, choices=TIPO_CHOICES, default='manga')
    capa_url = models.TextField(blank=True, default='')
    sinopse = models.TextField(blank=True, default='')
    tags = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo

class Capitulo(models.Model):
    obra = models.ForeignKey(Obra, on_delete=models.CASCADE, related_name='capitulos')
    numero = models.DecimalField(max_digits=6, decimal_places=1)
    titulo = models.CharField(max_length=255, blank=True)
    conteudo = models.TextField(blank=True, default='')
    data_publicacao = models.DateTimeField(null=True, blank=True)
    ordem = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['obra', 'ordem'])]
        ordering = ['ordem']

    def __str__(self):
        return f'{self.obra.titulo} - Cap. {self.numero}'

class Pagina(models.Model):
    capitulo = models.ForeignKey(Capitulo, on_delete=models.CASCADE, related_name='paginas')
    imagem_url = models.CharField(max_length=500)
    thumbnail_url = models.CharField(max_length=500, blank=True)
    ordem = models.IntegerField(default=0)
    width = models.IntegerField(default=0)
    height = models.IntegerField(default=0)

    class Meta:
        indexes = [models.Index(fields=['capitulo'])]
        ordering = ['ordem']

    def __str__(self):
        return f'Página {self.ordem} - {self.capitulo}'


class Favorito(models.Model):
    FONTE_CHOICES = [
        ('scan', 'Scan'),
        ('agregador', 'Agregador'),
    ]
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favoritos'
    )
    obra = models.ForeignKey(Obra, on_delete=models.CASCADE, related_name='favoritos')
    fonte = models.CharField(max_length=20, choices=FONTE_CHOICES, default='scan', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'obra', 'fonte')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.usuario} ★ {self.obra} [{self.fonte}]'


class HistoricoLeitura(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='historico'
    )
    capitulo = models.ForeignKey(Capitulo, on_delete=models.CASCADE, related_name='historico')
    lido_em = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=['usuario', '-lido_em'])]
        ordering = ['-lido_em']

    def __str__(self):
        return f'{self.usuario} → {self.capitulo}'


class ListaLeitura(models.Model):
    FONTE_CHOICES = [
        ('scan', 'Scan'),
        ('agregador', 'Agregador'),
    ]
    TIPO_CHOICES = [
        ('reading', 'Lendo'),
        ('plan', 'Planejado'),
        ('completed', 'Concluído'),
        ('paused', 'Pausado'),
    ]
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='lista_leitura'
    )
    obra = models.ForeignKey(Obra, on_delete=models.CASCADE, related_name='listas')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='reading')
    fonte = models.CharField(max_length=20, choices=FONTE_CHOICES, default='scan', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'obra', 'fonte')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.usuario} [{self.tipo}] {self.obra} [{self.fonte}]'


class ChapterJob(models.Model):
    """
    Estado persistente de processamento de capítulos.
    O scheduler e o worker usam esta tabela em vez de cache Redis.

    Estados:
      pending    — aguardando processamento
      processing — worker está processando (com lease)
      published  — capítulo publicado com sucesso
      failed     — falha após tentativa(s)
    """
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('processing', 'Processando'),
        ('published', 'Publicado'),
        ('failed', 'Falhou'),
    ]

    slug = models.CharField(max_length=255, db_index=True)
    chapter_num = models.CharField(max_length=20)
    source_id = models.CharField(max_length=50, blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    attempts = models.IntegerField(default=0)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    lease_until = models.DateTimeField(null=True, blank=True)
    lease_worker_id = models.CharField(max_length=100, blank=True, default='')
    error_message = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('slug', 'chapter_num')
        indexes = [
            models.Index(fields=['slug', 'status']),
            models.Index(fields=['status', 'lease_until']),
        ]
        ordering = ['created_at']

    def __str__(self):
        return f'{self.slug} cap {self.chapter_num} [{self.status}]'

    @property
    def is_lease_expired(self):
        if self.lease_until is None:
            return False
        return timezone.now() > self.lease_until

    def claim(self, worker_id: str, lease_minutes: int = 10):
        """Marca como processing com lease."""
        self.status = 'processing'
        self.attempts += 1
        self.last_attempt_at = timezone.now()
        self.lease_until = timezone.now() + timezone.timedelta(minutes=lease_minutes)
        self.lease_worker_id = worker_id
        self.error_message = ''
        self.save()

    def publish(self):
        """Marca como published."""
        self.status = 'published'
        self.lease_until = None
        self.lease_worker_id = ''
        self.error_message = ''
        self.save()

    def fail(self, error: str = ''):
        """Marca como failed."""
        self.status = 'failed'
        self.lease_until = None
        self.lease_worker_id = ''
        self.error_message = error[:1000]
        self.save()

    def release(self):
        """Libera de volta pra pending (lease expirou ou worker morreu)."""
        self.status = 'pending'
        self.lease_until = None
        self.lease_worker_id = ''
        self.save()