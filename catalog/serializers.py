from rest_framework import serializers
from .models import Obra, Capitulo, Pagina

class PaginaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pagina
        fields = ['id', 'imagem_url', 'thumbnail_url', 'ordem', 'width', 'height']

class CapituloSerializer(serializers.ModelSerializer):
    paginas = PaginaSerializer(many=True, read_only=True)
    obra_slug = serializers.SlugRelatedField(
        source='obra', slug_field='slug', read_only=True
    )
    obra_fonte = serializers.CharField(source='obra.fonte', read_only=True)

    class Meta:
        model = Capitulo
        fields = ['id', 'obra', 'obra_slug', 'obra_fonte', 'numero', 'titulo', 'data_publicacao', 'ordem', 'paginas']

class ObraSerializer(serializers.ModelSerializer):
    capitulos = CapituloSerializer(many=True, read_only=True)

    class Meta:
        model = Obra
        fields = ['id', 'titulo', 'autor', 'slug', 'status', 'fonte', 'capa_url', 'sinopse', 'tags', 'created_at', 'capitulos']
