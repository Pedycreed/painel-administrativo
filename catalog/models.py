from django.db import models
from django.conf import settings


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
        ('manga', 'Mangá/Manhwa'),
        ('novel', 'Light Novel'),
    ]
    titulo = models.CharField(max_length=255, db_index=True)
    autor = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ongoing')
    fonte = models.CharField(max_length=20, choices=FONTE_CHOICES, default='scan')
    idioma = models.CharField(max_length=2, choices=IDIOMA_CHOICES, default='pt', db_index=True)
    tipo_obra = models.CharField(max_length=10, choices=TIPO_CHOICES, default='manga')
    capa_url = models.CharField(max_length=500, blank=True)
    sinopse = models.TextField(blank=True)
    tags = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo

class Capitulo(models.Model):
    obra = models.ForeignKey(Obra, on_delete=models.CASCADE, related_name='capitulos')
    numero = models.DecimalField(max_digits=6, decimal_places=1)
    titulo = models.CharField(max_length=255, blank=True)
    data_publicacao = models.DateField(null=True, blank=True)
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
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favoritos'
    )
    obra = models.ForeignKey(Obra, on_delete=models.CASCADE, related_name='favoritos')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'obra')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.usuario} ★ {self.obra}'


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