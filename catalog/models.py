from django.db import models

class Obra(models.Model):
    STATUS_CHOICES = [
        ('ongoing', 'Em andamento'),
        ('completed', 'Completo'),
    ]
    FONTE_CHOICES = [
        ('scan', 'Scan'),
        ('agregador', 'Agregador'),
    ]
    titulo = models.CharField(max_length=255, db_index=True)
    autor = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ongoing')
    fonte = models.CharField(max_length=20, choices=FONTE_CHOICES, default='scan')
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