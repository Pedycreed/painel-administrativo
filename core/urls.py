from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from catalog.views import ObraViewSet, CapituloViewSet, PaginaViewSet, upload_imagem

# Router genérico — acessa todas as obras
router = DefaultRouter()
router.register(r'obras', ObraViewSet, basename='obra')
router.register(r'capitulos', CapituloViewSet, basename='capitulo')
router.register(r'paginas', PaginaViewSet, basename='pagina')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/upload/imagem/', upload_imagem, name='upload-imagem'),

    # Rotas separadas por fonte
    path('api/scan/', include([
        path('obras/', ObraViewSet.as_view({'get': 'list', 'post': 'create'}), {'fonte': 'scan'}),
    ])),
    path('api/agregador/', include([
        path('obras/', ObraViewSet.as_view({'get': 'list', 'post': 'create'}), {'fonte': 'agregador'}),
    ])),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
