from django.shortcuts import render
from django.conf import settings
from rest_framework import viewsets, status, filters
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
import os
import uuid

from .models import Obra, Capitulo, Pagina
from .serializers import ObraSerializer, CapituloSerializer, PaginaSerializer

class ObraViewSet(viewsets.ModelViewSet):
    queryset = Obra.objects.all().prefetch_related('capitulos__paginas')
    serializer_class = ObraSerializer
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter]
    search_fields = ['^titulo', '^autor', '^slug']

class ScanObraViewSet(ObraViewSet):
    """ViewSet específico para obras da Scan."""
    def get_queryset(self):
        return Obra.objects.filter(fonte='scan').prefetch_related('capitulos__paginas')

class AgregadorObraViewSet(ObraViewSet):
    """ViewSet específico para obras do Agregador."""
    def get_queryset(self):
        return Obra.objects.filter(fonte='agregador').prefetch_related('capitulos__paginas')

class CapituloViewSet(viewsets.ModelViewSet):
    queryset = Capitulo.objects.all().select_related('obra').prefetch_related('paginas')
    serializer_class = CapituloSerializer

class PaginaViewSet(viewsets.ModelViewSet):
    queryset = Pagina.objects.all()
    serializer_class = PaginaSerializer

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upload_imagem(request):
    """Upload de imagem para capa/capa temporária."""
    arquivo = request.FILES.get('imagem')
    if not arquivo:
        return Response({'error': 'Nenhuma imagem enviada'}, status=status.HTTP_400_BAD_REQUEST)

    # Garante que a pasta media/capas existe
    pasta = os.path.join(settings.MEDIA_ROOT, 'capas')
    os.makedirs(pasta, exist_ok=True)

    # Nome único para o arquivo
    ext = arquivo.name.split('.')[-1]
    nome_arquivo = f"{uuid.uuid4().hex}.{ext}"
    caminho = os.path.join(pasta, nome_arquivo)

    with open(caminho, 'wb+') as dest:
        for chunk in arquivo.chunks():
            dest.write(chunk)

    url = f"{settings.MEDIA_URL}capas/{nome_arquivo}"
    return Response({'url': url}, status=status.HTTP_200_OK)
