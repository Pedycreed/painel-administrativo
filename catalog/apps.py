from django.apps import AppConfig


class CatalogConfig(AppConfig):
    name = 'catalog'

    def ready(self):
        # Registra signals de cleanup do R2 ao apagar Obra/Capitulo/Pagina.
        # Import dentro de ready() evita import circular com models.
        from . import signals  # noqa: F401
