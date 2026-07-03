from rest_framework import viewsets, status, filters
from rest_framework.decorators import api_view, parser_classes, action, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from .models import Obra, Capitulo, Pagina, Favorito, HistoricoLeitura, ListaLeitura
from .serializers import (
    ObraPublicListSerializer, ObraPublicDetailSerializer,
    CapituloPublicoSerializer, CapituloLeitorSerializer,
    PaginaPublicaSerializer, FavoritoSerializer,
    HistoricoSerializer, ListaLeituraSerializer,
    ObraSerializer, PaginaSerializer,
)


class PublicObraViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API pública para sites BiToons/WindScan.
    - GET /api/public/obras/?idioma=pt&fonte=agregador  → lista obras
    - GET /api/public/obras/?order=popular              → por favoritos
    - GET /api/public/obras/{slug}/                     → detalhe completo
    - GET /api/public/obras/{slug}/capitulo/{numero}/   → capítulo com páginas
    """
    permission_classes = [AllowAny]
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter]
    search_fields = ['^titulo', '^autor']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ObraPublicDetailSerializer
        return ObraPublicListSerializer

    def get_queryset(self):
        qs = Obra.objects.all()

        idioma = self.request.query_params.get('idioma')
        if idioma in ('pt', 'en'):
            qs = qs.filter(idioma=idioma)

        fonte = self.request.query_params.get('fonte')
        if fonte in ('scan', 'agregador'):
            qs = qs.filter(fonte=fonte)

        order = self.request.query_params.get('order', 'recent')
        if order == 'popular':
            from django.db.models import Count
            qs = qs.annotate(fav_count=Count('favoritos')).order_by('-fav_count')
        elif order == 'title':
            qs = qs.order_by('titulo')
        else:
            qs = qs.order_by('-created_at')

        return qs.prefetch_related('capitulos')

    @action(detail=True, url_path=r'capitulo/(?P<numero>[\d.]+)')
    def capitulo(self, request, slug=None, numero=None):
        """Retorna capítulo com páginas para o leitor."""
        try:
            obra = Obra.objects.get(slug=slug)
        except Obra.DoesNotExist:
            return Response({'error': 'Obra não encontrada.'}, status=404)

        capitulo = Capitulo.objects.filter(
            obra=obra, numero=numero
        ).prefetch_related('paginas').first()

        if not capitulo:
            return Response({'error': 'Capítulo não encontrado.'}, status=404)

        serializer = CapituloLeitorSerializer(capitulo)
        return Response(serializer.data)


class FavoritoViewSet(viewsets.ModelViewSet):
    """
    CRUD de favoritos do usuário autenticado.
    - GET /api/favoritos/           → listar
    - POST /api/favoritos/          → adicionar {obra_id}
    - DELETE /api/favoritos/{id}/   → remover
    """
    serializer_class = FavoritoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Favorito.objects.filter(
            usuario=self.request.user
        ).select_related('obra')

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx

    @action(detail=False, url_path=r'obra/(?P<obra_id>\d+)')
    def por_obra(self, request, obra_id=None):
        """DELETE /api/favoritos/obra/{obra_id}/ — remove favorito pela obra."""
        fav = Favorito.objects.filter(usuario=request.user, obra_id=obra_id).first()
        if not fav:
            return Response({'error': 'Favorito não encontrado.'}, status=404)
        fav.delete()
        return Response(status=204)


class HistoricoViewSet(viewsets.ModelViewSet):
    """
    Histórico de leitura do usuário.
    - GET /api/historico/    → listar (ordenado por mais recente)
    - POST /api/historico/   → registrar {capitulo_id} (upsert)
    """
    serializer_class = HistoricoSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        return HistoricoLeitura.objects.filter(
            usuario=self.request.user
        ).select_related('capitulo', 'capitulo__obra')

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx


class ListaLeituraViewSet(viewsets.ModelViewSet):
    """
    Lista de leitura do usuário (Lendo/Planejado/Concluído).
    - GET /api/lista-leitura/                → listar tudo
    - GET /api/lista-leitura/?tipo=reading   → filtrar por tipo
    - POST /api/lista-leitura/               → adicionar {obra_id, tipo}
    - PATCH /api/lista-leitura/{id}/         → mudar tipo
    - DELETE /api/lista-leitura/{id}/        → remover
    """
    serializer_class = ListaLeituraSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = ListaLeitura.objects.filter(
            usuario=self.request.user
        ).select_related('obra')
        tipo = self.request.query_params.get('tipo')
        if tipo in ('reading', 'plan', 'completed'):
            qs = qs.filter(tipo=tipo)
        return qs

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx

    @action(detail=False, url_path=r'obra/(?P<obra_id>\d+)')
    def por_obra(self, request, obra_id=None):
        """DELETE /api/lista-leitura/obra/{obra_id}/ — remove pela obra."""
        item = ListaLeitura.objects.filter(usuario=request.user, obra_id=obra_id).first()
        if not item:
            return Response({'error': 'Item não encontrado.'}, status=404)
        item.delete()
        return Response(status=204)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def generos_favoritos(request):
    """
    GET /api/generos-favoritos/
    Retorna os gêneros mais frequentes nas obras favoritadas pelo usuário.
    """
    favoritos = Favorito.objects.filter(
        usuario=request.user
    ).select_related('obra').values_list('obra__tags', flat=True)

    from collections import Counter
    counter = Counter()
    for tags in favoritos:
        if tags:
            for tag in tags:
                counter[tag.lower()] += 1

    top = [{'genero': g, 'count': c} for g, c in counter.most_common(10)]
    return Response(top)


# ── Upload de ZIP com múltiplas páginas ──────────────────────────

@api_view(['POST'])
@parser_classes([MultiPartParser])
def upload_capitulo_zip(request):
    """
    Upload de capítulo completo via ZIP.
    Params: slug, capitulo_numero, zip
    """
    import zipfile
    import io
    from core.storage import upload_bytes, R2ConfigError

    slug = request.data.get('slug', '').strip()
    capitulo_numero = request.data.get('capitulo_numero', '').strip()
    arquivo_zip = request.FILES.get('zip')

    if not slug or not capitulo_numero or not arquivo_zip:
        return Response({'error': 'slug, capitulo_numero e zip são obrigatórios.'}, status=400)

    try:
        import re as _re

        def _natural_key(s: str):
            return [int(c) if c.isdigit() else c.lower() for c in _re.split(r'(\d+)', s)]

        # Validar ZIP
        zip_file = zipfile.ZipFile(io.BytesIO(arquivo_zip.read()))
        imagens = sorted(
            [f for f in zip_file.namelist() if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))],
            key=_natural_key,
        )

        if not imagens:
            return Response({'error': 'ZIP não contém imagens válidas.'}, status=400)

        # Upload de cada imagem
        urls = []
        for idx, img_name in enumerate(imagens):
            img_data = zip_file.read(img_name)
            ext = img_name.rsplit('.', 1)[-1].lower()
            if ext == 'jpeg':
                ext = 'jpg'

            key = f'mangas/{slug}/cap-{capitulo_numero}/p-{idx:03d}.{ext}'
            url = upload_bytes(key, img_data, content_type=f'image/{ext}')
            urls.append({'ordem': idx, 'url': url})

        return Response({'uploaded': len(urls), 'urls': urls}, status=200)

    except zipfile.BadZipFile:
        return Response({'error': 'Arquivo ZIP inválido.'}, status=400)
    except R2ConfigError as e:
        return Response({'error': str(e)}, status=500)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f'Erro no upload_capitulo_zip: {e}')
        return Response({'error': f'Falha no upload: {e}'}, status=500)
