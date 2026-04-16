from django.contrib import admin
from .models import Obra, Capitulo, Pagina

class CapituloInline(admin.TabularInline):
    model = Capitulo
    extra = 0
    fields = ['numero', 'titulo', 'ordem', 'data_publicacao']

class PaginaInline(admin.TabularInline):
    model = Pagina
    extra = 0
    fields = ['ordem', 'imagem_url', 'thumbnail_url', 'width', 'height']

@admin.register(Obra)
class ObraAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'autor', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['titulo', 'autor']
    prepopulated_fields = {'slug': ('titulo',)}
    inlines = [CapituloInline]

@admin.register(Capitulo)
class CapituloAdmin(admin.ModelAdmin):
    list_display = ['obra', 'numero', 'titulo', 'ordem', 'data_publicacao']
    list_filter = ['obra']
    search_fields = ['titulo', 'obra__titulo']
    inlines = [PaginaInline]

@admin.register(Pagina)
class PaginaAdmin(admin.ModelAdmin):
    list_display = ['capitulo', 'ordem', 'imagem_url']