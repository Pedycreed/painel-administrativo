from rest_framework import viewsets, status, filters
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
import re

# Extensões aceitas para capa
ALLOWED_IMAGE_EXTS = {'jpg', 'jpeg', 'png', 'webp'}
# Slug seguro: apenas letras minúsculas, dígitos e hífens
SAFE_SLUG_RE = re.compile(r'^[a-z0-9][a-z0-9-]*$')

from .models import Obra, Capitulo, Pagina
from .serializers import ObraSerializer, CapituloSerializer, PaginaSerializer
from accounts.permissions import MatchUserTime


def _user_time(request):
    """
    Retorna o time efetivo do usuário pra filtrar querysets.

    - Não autenticado: None (queryset não filtra, mas o IsAuthenticatedOrReadOnly
      do settings ainda regula leituras)
    - Superuser: None (acesso transversal a scan + agregador)
    - Demais: retorna user.time (pode ser None se for um usuário mal cadastrado)
    """
    user = getattr(request, 'user', None)
    if user is None or not user.is_authenticated:
        return None
    if user.is_superuser:
        return None
    return user.time


class ObraViewSet(viewsets.ModelViewSet):
    serializer_class = ObraSerializer
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter]
    search_fields = ['^titulo', '^autor', '^slug']
    permission_classes = [MatchUserTime]

    def get_queryset(self):
        qs = Obra.objects.all().prefetch_related('capitulos__paginas')
        user_time = _user_time(self.request)
        if user_time:
            qs = qs.filter(fonte=user_time)
        return qs

    def perform_create(self, serializer):
        user_time = _user_time(self.request)
        if user_time:
            # Força fonte = time do usuário, ignora payload manipulado
            serializer.save(fonte=user_time)
        else:
            serializer.save()


class ScanObraViewSet(ObraViewSet):
    """ViewSet específico para obras da Scan."""

    def get_queryset(self):
        user_time = _user_time(self.request)
        if user_time and user_time != 'scan':
            raise PermissionDenied('Você não pertence ao time Scan.')
        return Obra.objects.filter(fonte='scan').prefetch_related('capitulos__paginas')

    def perform_create(self, serializer):
        user_time = _user_time(self.request)
        if user_time and user_time != 'scan':
            raise PermissionDenied('Você não pertence ao time Scan.')
        serializer.save(fonte='scan')


class AgregadorObraViewSet(ObraViewSet):
    """ViewSet específico para obras do Agregador."""

    def get_queryset(self):
        user_time = _user_time(self.request)
        if user_time and user_time != 'agregador':
            raise PermissionDenied('Você não pertence ao time Agregador.')
        return Obra.objects.filter(fonte='agregador').prefetch_related('capitulos__paginas')

    def perform_create(self, serializer):
        user_time = _user_time(self.request)
        if user_time and user_time != 'agregador':
            raise PermissionDenied('Você não pertence ao time Agregador.')
        serializer.save(fonte='agregador')


class CapituloViewSet(viewsets.ModelViewSet):
    serializer_class = CapituloSerializer
    permission_classes = [MatchUserTime]

    def get_queryset(self):
        qs = Capitulo.objects.all().select_related('obra').prefetch_related('paginas')
        user_time = _user_time(self.request)
        if user_time:
            qs = qs.filter(obra__fonte=user_time)
        return qs

    def perform_create(self, serializer):
        user_time = _user_time(self.request)
        obra = serializer.validated_data.get('obra')
        if user_time and obra and obra.fonte != user_time:
            raise PermissionDenied('Capítulo deve pertencer a uma obra do seu time.')
        serializer.save()


class PaginaViewSet(viewsets.ModelViewSet):
    serializer_class = PaginaSerializer
    permission_classes = [MatchUserTime]

    def get_queryset(self):
        qs = Pagina.objects.all().select_related('capitulo__obra')
        user_time = _user_time(self.request)
        if user_time:
            qs = qs.filter(capitulo__obra__fonte=user_time)
        return qs

    def perform_create(self, serializer):
        user_time = _user_time(self.request)
        capitulo = serializer.validated_data.get('capitulo')
        if user_time and capitulo and capitulo.obra.fonte != user_time:
            raise PermissionDenied('Página deve pertencer a uma obra do seu time.')
        serializer.save()

_CONTENT_TYPE_TO_EXT = {
    'image/jpeg': 'jpg',
    'image/jpg': 'jpg',
    'image/png': 'png',
    'image/webp': 'webp',
}


def _validar_ext(nome_arquivo: str, content_type: str = ''):
    """
    Retorna a extensão normalizada ou (None, mensagem de erro).

    Estratégia em duas camadas:
    1. Tenta extrair extensão do nome do arquivo
    2. Fallback: deduz do content_type (importante pra uploads mobile que
       às vezes mandam nome vazio ou genérico tipo "image.jpg")
    """
    ext = None
    if '.' in (nome_arquivo or ''):
        ext = nome_arquivo.rsplit('.', 1)[-1].lower()
        if ext == 'jpeg':
            ext = 'jpg'
        if ext in ALLOWED_IMAGE_EXTS:
            return ext, None
        # Extensão inválida — tenta o fallback antes de rejeitar

    # Fallback pelo content_type (mobile costuma faltar nome decente)
    ct = (content_type or '').lower().split(';')[0].strip()
    fallback = _CONTENT_TYPE_TO_EXT.get(ct)
    if fallback:
        return fallback, None

    if ext is None:
        return None, 'Arquivo sem extensão e sem content-type reconhecido.'
    return None, f'Extensão "{ext}" não permitida. Aceitas: {", ".join(sorted(ALLOWED_IMAGE_EXTS))}.'


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upload_imagem(request):
    """
    Upload de capa de obra — salva no Cloudflare R2 em `mangas/{slug}/capa.{ext}`.

    Slug é OBRIGATÓRIO: toda capa deve viver dentro da pasta da própria obra.
    Sobrescreve a capa existente (mesmo comportamento de upsert).
    """
    from core.storage import upload_bytes, R2ConfigError

    arquivo = request.FILES.get('imagem')
    if not arquivo:
        return Response(
            {'error': 'Nenhuma imagem enviada. Use o campo "imagem".'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    slug = (request.POST.get('slug') or '').strip().lower()
    if not slug:
        return Response(
            {'error': 'Slug da obra é obrigatório. Envie o campo "slug" no form-data.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if not SAFE_SLUG_RE.match(slug):
        return Response(
            {'error': 'Slug inválido. Use apenas letras minúsculas, dígitos e hífens.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    ext, erro = _validar_ext(arquivo.name or '', arquivo.content_type or '')
    if erro:
        return Response({'error': erro}, status=status.HTTP_400_BAD_REQUEST)

    # Limite de tamanho: 15MB (celular faz fotos grandes, mas precisamos limitar
    # pra não estourar memória do container nem timeout do Railway)
    MAX_UPLOAD_MB = 15
    if arquivo.size and arquivo.size > MAX_UPLOAD_MB * 1024 * 1024:
        return Response(
            {'error': f'Imagem muito grande ({arquivo.size // 1024 // 1024}MB). Limite: {MAX_UPLOAD_MB}MB. Reduza a qualidade ou redimensione antes de enviar.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        key = f'mangas/{slug}/capa.{ext}'
        content_type = arquivo.content_type or f'image/{ext}'
        public_url = upload_bytes(key, arquivo.read(), content_type=content_type)
        return Response({'url': public_url}, status=status.HTTP_200_OK)
    except R2ConfigError as e:
        import logging
        logging.getLogger(__name__).error('R2ConfigError no upload_imagem: %s', e)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        import logging
        import traceback
        logging.getLogger(__name__).error(
            'Erro no upload_imagem (slug=%s, arquivo=%s, size=%s): %s\n%s',
            slug, getattr(arquivo, 'name', '?'),
            getattr(arquivo, 'size', '?'), e, traceback.format_exc(),
        )
        return Response({'error': f'Falha no upload: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upload_pagina(request):
    """
    Upload de página de capítulo — salva no R2 em
    `mangas/{slug}/cap-{numero}/p-{ordem:02d}.{ext}`.

    Campos esperados (multipart/form-data):
      - imagem: arquivo
      - slug: slug da obra
      - capitulo_numero: número do capítulo (ex: '1', '12.5')
      - ordem: ordem da página dentro do capítulo (inteiro >= 0)
    """
    from core.storage import upload_bytes, R2ConfigError

    arquivo = request.FILES.get('imagem')
    if not arquivo:
        return Response(
            {'error': 'Nenhuma imagem enviada. Use o campo "imagem".'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    slug = (request.POST.get('slug') or '').strip().lower()
    if not slug or not SAFE_SLUG_RE.match(slug):
        return Response(
            {'error': 'Slug inválido ou ausente.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    capitulo_numero = (request.POST.get('capitulo_numero') or '').strip()
    # Aceita "1", "12", "12.5" — sanitiza pra evitar barras/path traversal
    if not re.match(r'^[0-9]+(\.[0-9]+)?$', capitulo_numero):
        return Response(
            {'error': 'capitulo_numero inválido. Use número (ex: 1, 12, 12.5).'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    ordem_raw = (request.POST.get('ordem') or '').strip()
    try:
        ordem = int(ordem_raw)
        if ordem < 0 or ordem > 9999:
            raise ValueError
    except ValueError:
        return Response(
            {'error': 'ordem inválida (precisa ser inteiro entre 0 e 9999).'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    ext, erro = _validar_ext(arquivo.name or '', arquivo.content_type or '')
    if erro:
        return Response({'error': erro}, status=status.HTTP_400_BAD_REQUEST)

    # Limite de tamanho: 15MB
    MAX_UPLOAD_MB = 15
    if arquivo.size and arquivo.size > MAX_UPLOAD_MB * 1024 * 1024:
        return Response(
            {'error': f'Imagem muito grande ({arquivo.size // 1024 // 1024}MB). Limite: {MAX_UPLOAD_MB}MB. Reduza a qualidade ou redimensione antes de enviar.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        key = f'mangas/{slug}/cap-{capitulo_numero}/p-{ordem:03d}.{ext}'
        content_type = arquivo.content_type or f'image/{ext}'
        public_url = upload_bytes(key, arquivo.read(), content_type=content_type)
        return Response({'url': public_url}, status=status.HTTP_200_OK)
    except R2ConfigError as e:
        import logging
        logging.getLogger(__name__).error('R2ConfigError no upload_pagina: %s', e)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        import logging
        import traceback
        logging.getLogger(__name__).error(
            'Erro no upload_pagina (slug=%s, cap=%s, ordem=%s, arquivo=%s, size=%s): %s\n%s',
            slug, capitulo_numero, ordem,
            getattr(arquivo, 'name', '?'),
            getattr(arquivo, 'size', '?'), e, traceback.format_exc(),
        )
        return Response({'error': f'Falha no upload: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
