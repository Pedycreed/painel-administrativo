from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from catalog.views import (
    ObraViewSet, CapituloViewSet, PaginaViewSet,
    upload_imagem, upload_pagina, upload_capitulo_zip,
    ScanObraViewSet, AgregadorObraViewSet,
    PublicObraViewSet, FavoritoViewSet, HistoricoViewSet,
    ListaLeituraViewSet, generos_favoritos,
    ingest_chapter,
    chapter_job_sync, chapter_job_claim, chapter_job_publish,
    chapter_job_fail, chapter_job_reclaim_stale, chapter_job_status,
)
from accounts.views import (
    RegistroView,
    LoginView,
    LogoutView,
    MeView,
    MudarSenhaView,
    UsuariosViewSet,
)

# Router genérico — acessa todas as obras
router = DefaultRouter()
router.register(r'obras', ObraViewSet, basename='obra')
router.register(r'capitulos', CapituloViewSet, basename='capitulo')
router.register(r'paginas', PaginaViewSet, basename='pagina')
router.register(r'auth/usuarios', UsuariosViewSet, basename='usuario-gestao')

# Router público (BiToons)
public_router = DefaultRouter()
public_router.register(r'obras', PublicObraViewSet, basename='public-obra')

# Router autenticado (favoritos + histórico)
user_router = DefaultRouter()
user_router.register(r'favoritos', FavoritoViewSet, basename='favorito')
user_router.register(r'historico', HistoricoViewSet, basename='historico')
user_router.register(r'lista-leitura', ListaLeituraViewSet, basename='lista-leitura')

urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth endpoints customizados
    path('api/auth/register/', RegistroView.as_view(), name='register'),
    path('api/auth/login/', LoginView.as_view(), name='login'),
    path('api/auth/logout/', LogoutView.as_view(), name='logout'),
    path('api/auth/me/', MeView.as_view(), name='me'),
    path('api/auth/password/', MudarSenhaView.as_view(), name='change-password'),
    # /api/auth/usuarios/ é registrado via router (UsuariosViewSet)

    # JWT endpoints (fallback/alternativa)
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # API genérica
    path('api/', include(router.urls)),
    path('api/upload/imagem/', upload_imagem, name='upload-imagem'),
    path('api/upload/pagina/', upload_pagina, name='upload-pagina'),
    path('api/upload/capitulo-zip/', upload_capitulo_zip, name='upload-capitulo-zip'),

    # API pública (BiToons)
    path('api/public/', include(public_router.urls)),

    # API autenticada (favoritos + histórico + lista)
    path('api/', include(user_router.urls)),
    path('api/generos-favoritos/', generos_favoritos, name='generos-favoritos'),
    path('api/ingest-chapter/', ingest_chapter, name='ingest-chapter'),

    # ChapterJob API (estado persistente de processamento)
    path('api/chapter-jobs/sync/', chapter_job_sync, name='chapter-job-sync'),
    path('api/chapter-jobs/claim/', chapter_job_claim, name='chapter-job-claim'),
    path('api/chapter-jobs/publish/', chapter_job_publish, name='chapter-job-publish'),
    path('api/chapter-jobs/fail/', chapter_job_fail, name='chapter-job-fail'),
    path('api/chapter-jobs/reclaim-stale/', chapter_job_reclaim_stale, name='chapter-job-reclaim'),
    path('api/chapter-jobs/status/', chapter_job_status, name='chapter-job-status'),

    # Rotas separadas por fonte (Scan)
    path('api/scan/', include([
        path('obras/', ScanObraViewSet.as_view({'get': 'list', 'post': 'create'}), {'fonte': 'scan'}),
        path('obras/<slug:slug>/', ScanObraViewSet.as_view({
            'get': 'retrieve',
            'put': 'update',
            'patch': 'partial_update',
            'delete': 'destroy'
        }), {'fonte': 'scan'}),
    ])),

    # Rotas separadas por fonte (Agregador)
    path('api/agregador/', include([
        path('obras/', AgregadorObraViewSet.as_view({'get': 'list', 'post': 'create'}), {'fonte': 'agregador'}),
        path('obras/<slug:slug>/', AgregadorObraViewSet.as_view({
            'get': 'retrieve',
            'put': 'update',
            'patch': 'partial_update',
            'delete': 'destroy'
        }), {'fonte': 'agregador'}),
    ])),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)