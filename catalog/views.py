from rest_framework import viewsets, status, filters
from rest_framework.decorators import api_view, parser_classes, action, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from .models import Obra, Capitulo, Pagina, Favorito, HistoricoLeitura, ListaLeitura, ChapterJob
from .serializers import (
    ObraPublicListSerializer, ObraPublicDetailSerializer,
    CapituloPublicoSerializer, CapituloLeitorSerializer, CapituloSerializer, CapituloWriteSerializer,
    PaginaPublicaSerializer, FavoritoSerializer,
    HistoricoSerializer, ListaLeituraSerializer,
    ObraSerializer, PaginaSerializer,
)


# ── ViewSets de gestão (admin / painel) ─────────────────────────────────────

class ObraViewSet(viewsets.ModelViewSet):
    """
    CRUD completo de obras (uso interno/admin).
    GET/POST  /api/obras/
    GET/PUT/PATCH/DELETE  /api/obras/{slug}/
    """
    serializer_class = ObraSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter]
    search_fields = ['^titulo', '^autor']

    def get_queryset(self):
        qs = Obra.objects.all().order_by('-created_at')
        fonte = (
            self.kwargs.get('fonte')
            or self.request.query_params.get('fonte')
        )
        if fonte in ('scan', 'agregador'):
            qs = qs.filter(fonte=fonte)
        return qs


class ScanObraViewSet(ObraViewSet):
    """Obras filtradas por fonte='scan' (/api/scan/obras/)."""

    def get_queryset(self):
        return Obra.objects.filter(fonte='scan').order_by('-created_at')


class AgregadorObraViewSet(ObraViewSet):
    """Obras filtradas por fonte='agregador' (/api/agregador/obras/)."""

    def get_queryset(self):
        qs = Obra.objects.filter(fonte='agregador')
        idioma = self.request.query_params.get('idioma')
        if idioma in ('pt', 'en'):
            qs = qs.filter(idioma=idioma)
        return qs.order_by('-created_at')


class CapituloViewSet(viewsets.ModelViewSet):
    """CRUD de capítulos (/api/capitulos/)."""

    queryset = Capitulo.objects.select_related('obra').order_by('numero')
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return CapituloWriteSerializer
        return CapituloSerializer


class PaginaViewSet(viewsets.ModelViewSet):
    """CRUD de páginas (/api/paginas/)."""

    queryset = Pagina.objects.select_related('capitulo').order_by('ordem')
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return PaginaSerializer
        return PaginaPublicaSerializer


# ── Uploads individuais ──────────────────────────────────────────────────────

@api_view(['POST'])
@parser_classes([MultiPartParser])
def upload_imagem(request):
    """
    POST /api/upload/imagem/
    Params: slug, imagem (file)
    Faz upload da capa de uma obra para o R2.
    """
    from core.storage import upload_bytes, R2ConfigError

    slug = request.data.get('slug', '').strip()
    arquivo = request.FILES.get('imagem')

    if not slug or not arquivo:
        return Response(
            {'error': 'slug e imagem são obrigatórios.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        data = arquivo.read()
        ext = arquivo.name.rsplit('.', 1)[-1].lower()
        if ext == 'jpeg':
            ext = 'jpg'
        key = f'mangas/{slug}/capa.{ext}'
        url = upload_bytes(key, data, content_type=f'image/{ext}')
        return Response({'url': url}, status=status.HTTP_200_OK)
    except R2ConfigError as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f'Erro no upload_imagem: {e}')
        return Response(
            {'error': f'Falha no upload: {e}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['POST'])
@parser_classes([MultiPartParser])
def upload_pagina(request):
    """
    POST /api/upload/pagina/
    Params: slug, capitulo_numero, ordem, pagina (file)
    Faz upload de uma página individual para o R2.
    """
    from core.storage import upload_bytes, R2ConfigError

    slug = request.data.get('slug', '').strip()
    capitulo_numero = request.data.get('capitulo_numero', '').strip()
    ordem = request.data.get('ordem', '0').strip()
    arquivo = request.FILES.get('pagina')

    if not slug or not capitulo_numero or not arquivo:
        return Response(
            {'error': 'slug, capitulo_numero e pagina são obrigatórios.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        data = arquivo.read()
        ext = arquivo.name.rsplit('.', 1)[-1].lower()
        if ext == 'jpeg':
            ext = 'jpg'
        key = f'mangas/{slug}/cap-{capitulo_numero}/p-{int(ordem):03d}.{ext}'
        url = upload_bytes(key, data, content_type=f'image/{ext}')
        return Response(
            {'url': url, 'ordem': int(ordem)},
            status=status.HTTP_200_OK,
        )
    except R2ConfigError as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f'Erro no upload_pagina: {e}')
        return Response(
            {'error': f'Falha no upload: {e}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ── API pública (BiToons / WindScan) ────────────────────────────────────────

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
        from django.db.models import Count
        qs = Obra.objects.all()

        idioma = self.request.query_params.get('idioma')
        if idioma in ('pt', 'en'):
            qs = qs.filter(idioma=idioma)

        fonte = self.request.query_params.get('fonte')
        if fonte in ('scan', 'agregador'):
            qs = qs.filter(fonte=fonte)

        qs = qs.annotate(cap_count=Count('capitulos'))

        order = self.request.query_params.get('order', 'recent')
        if order == 'popular':
            qs = qs.annotate(fav_count=Count('favoritos')).order_by('-fav_count')
        elif order == 'title':
            qs = qs.order_by('titulo')
        elif order == 'recent':
            from django.db.models import Max
            qs = qs.annotate(
                ultimo_cap_data=Max('capitulos__data_publicacao')
            ).order_by('-ultimo_cap_data')
        else:
            qs = qs.order_by('-created_at')

        if self.action == 'retrieve':
            return qs.prefetch_related('capitulos')

        # NO prefetch for list — conflicts with cap_count annotation
        return qs

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
    - GET /api/favoritos/?fonte=agregador  → listar (filtrar por fonte)
    - POST /api/favoritos/                 → adicionar {obra_id, fonte}
    - DELETE /api/favoritos/{id}/          → remover
    """
    serializer_class = FavoritoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Favorito.objects.filter(
            usuario=self.request.user
        ).select_related('obra')
        fonte = self.request.query_params.get('fonte')
        if fonte in ('scan', 'agregador'):
            qs = qs.filter(fonte=fonte)
        return qs

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx

    @action(detail=False, methods=['delete'], url_path=r'obra/(?P<obra_id>\d+)')
    def por_obra(self, request, obra_id=None):
        """DELETE /api/favoritos/obra/{obra_id}/?fonte=agregador — remove favorito pela obra e fonte."""
        fonte = request.query_params.get('fonte', 'scan')
        fav = Favorito.objects.filter(usuario=request.user, obra_id=obra_id, fonte=fonte).first()
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
    - GET /api/lista-leitura/?fonte=agregador  → filtrar por fonte
    - GET /api/lista-leitura/?tipo=reading     → filtrar por tipo
    - POST /api/lista-leitura/                 → adicionar {obra_id, tipo, fonte}
    - PATCH /api/lista-leitura/{id}/           → mudar tipo
    - DELETE /api/lista-leitura/{id}/          → remover
    """
    serializer_class = ListaLeituraSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = ListaLeitura.objects.filter(
            usuario=self.request.user
        ).select_related('obra')
        tipo = self.request.query_params.get('tipo')
        if tipo in ('reading', 'plan', 'completed', 'paused'):
            qs = qs.filter(tipo=tipo)
        fonte = self.request.query_params.get('fonte')
        if fonte in ('scan', 'agregador'):
            qs = qs.filter(fonte=fonte)
        return qs

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx

    @action(detail=False, methods=['delete'], url_path=r'obra/(?P<obra_id>\d+)')
    def por_obra(self, request, obra_id=None):
        """DELETE /api/lista-leitura/obra/{obra_id}/?fonte=agregador — remove pela obra e fonte."""
        fonte = request.query_params.get('fonte', 'scan')
        item = ListaLeitura.objects.filter(usuario=request.user, obra_id=obra_id, fonte=fonte).first()
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


# ── Ingest Chapter (Agregador) ──────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ingest_chapter(request):
    """
    POST /api/ingest-chapter/
    Body: {"slug": "...", "numero": "1", "paginas": [{"ordem": 1, "imagem_url": "..."}]}
    
    Endpoint para o worker do agregador registrar capítulos baixados.
    Cria/atualiza a obra e o capítulo. Substitui páginas se capítulo já existe.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    if not request.user.is_staff:
        return Response({'error': 'Apenas administradores.'}, status=403)
    
    slug = request.data.get('slug')
    numero = request.data.get('numero')
    paginas = request.data.get('paginas', [])
    
    if not slug or not numero:
        return Response({'error': 'slug e numero são obrigatórios.'}, status=400)
    if not paginas and not request.data.get('conteudo'):
        return Response({'error': 'paginas ou conteudo é obrigatório.'}, status=400)
    
    from django.db import transaction
    
    try:
        with transaction.atomic():
            # Buscar obra existente por título + idioma (evita duplicatas no mesmo idioma,
            # mas permite a mesma obra em PT e EN como entradas separadas)
            titulo = request.data.get('titulo', slug.replace('-', ' ').title())
            idioma = request.data.get('idioma', 'pt')
            obra_existente = Obra.objects.filter(
                titulo__iexact=titulo,
                idioma=idioma,
            ).first()
            
            if obra_existente:
                # Atualizar obra existente (não criar duplicata)
                slug = obra_existente.slug  # usar o slug já existente
                obra = obra_existente
                obra.tipo_obra = request.data.get('tipo_obra', obra.tipo_obra)
                obra.sinopse = request.data.get('sinopse') or obra.sinopse
                obra.capa_url = request.data.get('capa_url') or obra.capa_url
                obra.autor = request.data.get('autor') or obra.autor
                obra.status = request.data.get('status', obra.status)
                obra.idioma = request.data.get('idioma', obra.idioma)
                obra.tags = request.data.get('generos', obra.tags)
                obra.save()
                created = False
            else:
                # Criar nova obra
                obra, created = Obra.objects.update_or_create(
                    slug=slug,
                    defaults={
                        'titulo': titulo,
                        'tipo_obra': request.data.get('tipo_obra', 'manga'),
                        'sinopse': request.data.get('sinopse') or '',
                        'capa_url': request.data.get('capa_url') or '',
                        'autor': request.data.get('autor') or slug.replace('-', ' ').title(),
                        'status': request.data.get('status', 'ongoing'),
                        'fonte': 'agregador',
                        'idioma': request.data.get('idioma', 'pt'),
                        'tags': request.data.get('generos', []),
                    },
                )
            
            # Criar ou atualizar capítulo
            from django.utils import timezone
            conteudo = request.data.get('conteudo', '')
            capitulo, cap_created = Capitulo.objects.update_or_create(
                obra=obra,
                numero=str(numero),
                defaults={
                    'titulo': request.data.get('titulo_capitulo', ''),
                    'ordem': int(float(numero)),
                    'data_publicacao': timezone.now(),
                    'conteudo': conteudo,
                },
            )
            
            # Deletar páginas antigas e criar novas (só pra mangá/manhwa)
            if paginas:
                Pagina.objects.filter(capitulo=capitulo).delete()
                paginas_objs = []
                for p in paginas:
                    paginas_objs.append(Pagina(
                        capitulo=capitulo,
                        ordem=p['ordem'],
                        imagem_url=p['imagem_url'],
                        thumbnail_url=p.get('thumbnail_url', ''),
                        width=0,
                        height=0,
                    ))
                Pagina.objects.bulk_create(paginas_objs)
            
            logger.info(f'Ingerido: {slug} cap {numero} ({len(paginas)} pág)')
            
            return Response({
                'status': 'ok',
                'obra_id': obra.id,
                'capitulo_id': capitulo.id,
                'paginas_criadas': len(paginas_objs),
                'obra_criada': created,
                'capitulo_criado': cap_created,
            })
    
    except Exception as e:
        import traceback
        logger.error(f'Erro no ingest_chapter: {e}')
        logger.error(traceback.format_exc())
        return Response({'error': str(e)}, status=500)


# ── ChapterJob API (estado persistente de processamento) ────────────────────

from .models import ChapterJob
from django.utils import timezone
from datetime import timedelta
import uuid


@api_view(['POST'])
@permission_classes([AllowAny])
def chapter_job_sync(request):
    """
    Sincroniza capítulos de uma fonte com o estado persistente.
    Usado pelo scheduler pra saber quais capítulos precisam ser processados.

    POST /api/chapter-jobs/sync/
    Body: {
        "slug": "solo-leveling",
        "chapters": [
            {"chapter_num": "1", "chapter_id": "123", "source_id": "abc"},
            {"chapter_num": "2", "chapter_id": "124", "source_id": "abc"},
            ...
        ]
    }

    Response: {
        "pending": [{"chapter_num": "1", "chapter_id": "123"}, ...],
        "published_count": 85,
        "failed_count": 2,
        "processing_count": 1,
        "reclaimed": 0
    }
    """
    slug = request.data.get('slug', '')
    chapters = request.data.get('chapters', [])

    if not slug or not chapters:
        return Response({'error': 'slug and chapters required'}, status=400)

    now = timezone.now()

    # 1. Reclaim stale processing jobs (lease expired, >10min)
    stale = ChapterJob.objects.filter(
        slug=slug,
        status='processing',
        lease_until__lt=now,
    )
    reclaimed = stale.count()
    stale.update(status='pending', lease_until=None, lease_worker_id='')

    # 2. Get all existing jobs for this slug
    existing = {
        j.chapter_num: j
        for j in ChapterJob.objects.filter(slug=slug)
    }

    # 3. Create missing jobs and collect pending ones
    to_create = []
    pending = []

    for ch in chapters:
        ch_num = str(ch['chapter_num'])
        source_id = ch.get('source_id', '')

        if ch_num in existing:
            job = existing[ch_num]
            if job.status == 'failed':
                # Failed chapters are always re-queued
                pending.append({
                    'chapter_num': ch_num,
                    'chapter_id': ch.get('chapter_id', ''),
                    'job_id': job.id,
                    'attempts': job.attempts,
                })
            elif job.status == 'pending':
                # Only re-queue pending if created >5min ago (cooldown)
                age = (now - job.created_at).total_seconds()
                if age > 300:  # 5 minutes
                    pending.append({
                        'chapter_num': ch_num,
                        'chapter_id': ch.get('chapter_id', ''),
                        'job_id': job.id,
                        'attempts': job.attempts,
                    })
            # processing and published are skipped
        else:
            # New chapter — create pending job
            to_create.append(ChapterJob(
                slug=slug,
                chapter_num=ch_num,
                source_id=source_id,
                status='pending',
            ))
            pending.append({
                'chapter_num': ch_num,
                'chapter_id': ch.get('chapter_id', ''),
                'job_id': None,
            })

    if to_create:
        ChapterJob.objects.bulk_create(to_create, ignore_conflicts=True)
        # Re-fetch to get IDs
        new_nums = {j.chapter_num for j in to_create}
        new_jobs = {
            j.chapter_num: j
            for j in ChapterJob.objects.filter(slug=slug, chapter_num__in=new_nums)
        }
        for p in pending:
            if p['job_id'] is None and p['chapter_num'] in new_jobs:
                p['job_id'] = new_jobs[p['chapter_num']].id

    # 4. Count stats
    stats = ChapterJob.objects.filter(slug=slug).values_list('status', flat=True)
    from collections import Counter
    counts = Counter(stats)

    return Response({
        'pending': pending,
        'published_count': counts.get('published', 0),
        'failed_count': counts.get('failed', 0),
        'processing_count': counts.get('processing', 0),
        'reclaimed': reclaimed,
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def chapter_job_claim(request):
    """
    Worker marca um capítulo como processing (claim com lease).

    POST /api/chapter-jobs/claim/
    Body: {"job_id": 123, "worker_id": "worker-abc"}
    ou:   {"slug": "solo-leveling", "chapter_num": "1", "worker_id": "worker-abc"}
    """
    job_id = request.data.get('job_id')
    slug = request.data.get('slug')
    chapter_num = request.data.get('chapter_num')
    worker_id = request.data.get('worker_id', 'worker')

    try:
        if job_id:
            job = ChapterJob.objects.get(id=job_id)
        elif slug and chapter_num:
            job, _ = ChapterJob.objects.get_or_create(
                slug=slug, chapter_num=str(chapter_num),
                defaults={'status': 'pending'},
            )
        else:
            return Response({'error': 'job_id or slug+chapter_num required'}, status=400)

        if job.status == 'published':
            return Response({'status': 'already_published', 'job_id': job.id})

        job.claim(worker_id)
        return Response({'status': 'claimed', 'job_id': job.id})
    except ChapterJob.DoesNotExist:
        return Response({'error': 'job not found'}, status=404)


@api_view(['POST'])
@permission_classes([AllowAny])
def chapter_job_publish(request):
    """
    Worker marca um capítulo como published.

    POST /api/chapter-jobs/publish/
    Body: {"job_id": 123}
    ou:   {"slug": "solo-leveling", "chapter_num": "1"}
    """
    job_id = request.data.get('job_id')
    slug = request.data.get('slug')
    chapter_num = request.data.get('chapter_num')

    try:
        if job_id:
            job = ChapterJob.objects.get(id=job_id)
        elif slug and chapter_num:
            job = ChapterJob.objects.get(slug=slug, chapter_num=str(chapter_num))
        else:
            return Response({'error': 'job_id or slug+chapter_num required'}, status=400)

        job.publish()
        return Response({'status': 'published', 'job_id': job.id})
    except ChapterJob.DoesNotExist:
        return Response({'error': 'job not found'}, status=404)


@api_view(['POST'])
@permission_classes([AllowAny])
def chapter_job_fail(request):
    """
    Worker marca um capítulo como failed.

    POST /api/chapter-jobs/fail/
    Body: {"job_id": 123, "error": "timeout"}
    ou:   {"slug": "solo-leveling", "chapter_num": "1", "error": "timeout"}
    """
    job_id = request.data.get('job_id')
    slug = request.data.get('slug')
    chapter_num = request.data.get('chapter_num')
    error = request.data.get('error', '')

    try:
        if job_id:
            job = ChapterJob.objects.get(id=job_id)
        elif slug and chapter_num:
            job = ChapterJob.objects.get(slug=slug, chapter_num=str(chapter_num))
        else:
            return Response({'error': 'job_id or slug+chapter_num required'}, status=400)

        job.fail(error)
        return Response({'status': 'failed', 'job_id': job.id, 'attempts': job.attempts})
    except ChapterJob.DoesNotExist:
        return Response({'error': 'job not found'}, status=404)


@api_view(['POST'])
@permission_classes([AllowAny])
def chapter_job_reclaim_stale(request):
    """
    Reclaim all stale processing jobs (lease expired).
    Pode ser chamado periodicamente pelo scheduler ou worker.

    POST /api/chapter-jobs/reclaim-stale/
    """
    now = timezone.now()
    stale = ChapterJob.objects.filter(
        status='processing',
        lease_until__lt=now,
    )
    count = stale.count()
    stale.update(status='pending', lease_until=None, lease_worker_id='')

    return Response({'reclaimed': count})


@api_view(['GET'])
@permission_classes([AllowAny])
def chapter_job_status(request):
    """
    Consulta status de capítulos de uma obra.

    GET /api/chapter-jobs/status/?slug=solo-leveling
    """
    slug = request.query_params.get('slug', '')
    if not slug:
        return Response({'error': 'slug required'}, status=400)

    jobs = ChapterJob.objects.filter(slug=slug)
    from collections import Counter
    counts = Counter(j.status for j in jobs)

    return Response({
        'slug': slug,
        'total': jobs.count(),
        'published': counts.get('published', 0),
        'pending': counts.get('pending', 0),
        'processing': counts.get('processing', 0),
        'failed': counts.get('failed', 0),
    })
