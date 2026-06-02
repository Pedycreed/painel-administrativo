from django.contrib import admin
from .models import Obra, Capitulo, Pagina, Favorito, HistoricoLeitura

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
    list_display = ['titulo', 'autor', 'status', 'idioma', 'created_at']
    list_filter = ['status', 'idioma', 'fonte']
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


@admin.register(Favorito)
class FavoritoAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'obra', 'created_at']
    list_filter = ['created_at']
    search_fields = ['usuario__username', 'obra__titulo']


@admin.register(HistoricoLeitura)
class HistoricoLeituraAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'capitulo', 'lido_em']
    list_filter = ['lido_em']
    search_fields = ['usuario__username', 'capitulo__obra__titulo']