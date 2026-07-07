from rest_framework import serializers
from .models import Obra, Capitulo, Pagina, Favorito, HistoricoLeitura, ListaLeitura

class PaginaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pagina
        fields = ['id', 'capitulo', 'imagem_url', 'thumbnail_url', 'ordem', 'width', 'height']

class CapituloSerializer(serializers.ModelSerializer):
    paginas = PaginaSerializer(many=True, read_only=True)
    obra_slug = serializers.SlugRelatedField(
        source='obra', slug_field='slug', read_only=True
    )
    obra_titulo = serializers.CharField(source='obra.titulo', read_only=True)
    obra_fonte = serializers.CharField(source='obra.fonte', read_only=True)
    criado_em = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = Capitulo
        fields = [
            'id', 'obra', 'obra_slug', 'obra_titulo', 'obra_fonte',
            'numero', 'titulo', 'data_publicacao', 'ordem',
            'criado_em', 'paginas',
        ]


class CapituloCreateSerializer(serializers.ModelSerializer):
    """Serializer simplificado para criação de capítulos (sem campos read-only conflitantes)."""
    class Meta:
        model = Capitulo
        fields = ['id', 'obra', 'numero', 'titulo', 'data_publicacao', 'ordem', 'conteudo']

class ObraSerializer(serializers.ModelSerializer):
    capitulos = CapituloSerializer(many=True, read_only=True)

    class Meta:
        model = Obra
        fields = ['id', 'titulo', 'autor', 'slug', 'status', 'fonte', 'idioma', 'tipo_obra', 'capa_url', 'sinopse', 'tags', 'created_at', 'capitulos']


# ── Serializers públicos (site BiToons) ──────────────────────────

class CapituloPublicoSerializer(serializers.ModelSerializer):
    """Serializer leve para capítulos no detalhe público."""
    class Meta:
        model = Capitulo
        fields = ['id', 'numero', 'titulo', 'data_publicacao', 'ordem', 'conteudo']


class ObraPublicListSerializer(serializers.ModelSerializer):
    """Serializer leve para listagem pública (home, busca)."""
    total_capitulos = serializers.SerializerMethodField()
    ultimo_capitulo_numero = serializers.SerializerMethodField()
    ultimo_capitulo_data = serializers.SerializerMethodField()

    class Meta:
        model = Obra
        fields = [
            'id', 'titulo', 'autor', 'slug', 'status',
            'capa_url', 'tags', 'idioma', 'tipo_obra',
            'total_capitulos', 'ultimo_capitulo_numero', 'ultimo_capitulo_data',
        ]

    def get_total_capitulos(self, obj):
        return obj.capitulos.count()

    def get_ultimo_capitulo_numero(self, obj):
        ultimo = obj.capitulos.order_by('-ordem').first()
        return str(ultimo.numero) if ultimo else None

    def get_ultimo_capitulo_data(self, obj):
        ultimo = obj.capitulos.order_by('-ordem').first()
        return ultimo.data_publicacao if ultimo else None


class ObraPublicDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para detalhe público da obra."""
    capitulos = CapituloPublicoSerializer(many=True, read_only=True)
    total_capitulos = serializers.SerializerMethodField()

    class Meta:
        model = Obra
        fields = [
            'id', 'titulo', 'autor', 'slug', 'status',
            'capa_url', 'sinopse', 'tags', 'idioma', 'tipo_obra',
            'created_at', 'total_capitulos', 'capitulos',
        ]

    def get_total_capitulos(self, obj):
        return obj.capitulos.count()


class PaginaPublicaSerializer(serializers.ModelSerializer):
    """Serializer para páginas no leitor público."""
    class Meta:
        model = Pagina
        fields = ['id', 'imagem_url', 'thumbnail_url', 'ordem', 'width', 'height']


class CapituloLeitorSerializer(serializers.ModelSerializer):
    """Serializer do capítulo com páginas para o leitor."""
    paginas = PaginaPublicaSerializer(many=True, read_only=True)

    class Meta:
        model = Capitulo
        fields = ['id', 'numero', 'titulo', 'data_publicacao', 'paginas', 'conteudo']


class FavoritoSerializer(serializers.ModelSerializer):
    obra = ObraPublicListSerializer(read_only=True)
    obra_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Favorito
        fields = ['id', 'obra', 'obra_id', 'created_at']

    def create(self, validated_data):
        validated_data['usuario'] = self.context['request'].user
        return super().create(validated_data)


class HistoricoSerializer(serializers.ModelSerializer):
    capitulo = CapituloPublicoSerializer(read_only=True)
    capitulo_id = serializers.IntegerField(write_only=True)
    obra = serializers.SerializerMethodField()

    class Meta:
        model = HistoricoLeitura
        fields = ['id', 'capitulo', 'capitulo_id', 'obra', 'lido_em']

    def get_obra(self, obj):
        return {
            'id': obj.capitulo.obra.id,
            'titulo': obj.capitulo.obra.titulo,
            'slug': obj.capitulo.obra.slug,
            'capa_url': obj.capitulo.obra.capa_url,
        }

    def create(self, validated_data):
        validated_data['usuario'] = self.context['request'].user
        # Upsert: se já existe, atualiza lido_em
        obj, created = HistoricoLeitura.objects.update_or_create(
            usuario=validated_data['usuario'],
            capitulo_id=validated_data['capitulo_id'],
            defaults={},
        )
        # Força update do lido_em (auto_now)
        obj.save(update_fields=['lido_em'])
        return obj


class ListaLeituraSerializer(serializers.ModelSerializer):
    obra = ObraPublicListSerializer(read_only=True)
    obra_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = ListaLeitura
        fields = ['id', 'obra', 'obra_id', 'tipo', 'created_at']

    def create(self, validated_data):
        validated_data['usuario'] = self.context['request'].user
        obj, created = ListaLeitura.objects.update_or_create(
            usuario=validated_data['usuario'],
            obra_id=validated_data['obra_id'],
            defaults={'tipo': validated_data.get('tipo', 'reading')},
        )
        return obj
