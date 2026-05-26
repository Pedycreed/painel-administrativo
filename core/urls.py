from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from catalog.views import ObraViewSet, CapituloViewSet, PaginaViewSet, upload_imagem, upload_pagina, ScanObraViewSet, AgregadorObraViewSet
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