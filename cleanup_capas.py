"""
Script one-shot de limpeza das capas legadas (parte local).

O que faz:
  1. Zera `capa_url` das obras cuja URL aponta pra `media/capas/` local
     (localhost / 127.0.0.1 / qualquer URL contendo `/media/capas/`).
  2. Apaga os arquivos físicos correspondentes em `media/capas/`.

A pasta órfã `mangas/capas/` no Supabase deve ser limpa manualmente pelo
painel (Storage > mangas > capas > selecionar tudo > apagar). Tentamos via
SDK mas o Python 3.13 no Windows tem incompatibilidade SSL com o cert atual
do Supabase ("Basic Constraints of CA cert not marked critical").

Como rodar (a partir da raiz do projeto):
    python cleanup_capas.py

Pode ser executado mais de uma vez sem efeitos colaterais (idempotente).
Depois que rodar com sucesso, pode apagar este arquivo.
"""
import os
import sys
from pathlib import Path

# --- Setup Django ---
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django  # noqa: E402

django.setup()

from django.conf import settings  # noqa: E402
from catalog.models import Obra  # noqa: E402


def is_local_capa_url(url: str) -> bool:
    """True se a URL aponta pra uma capa hospedada localmente (Django MEDIA)."""
    if not url:
        return False
    needles = ("localhost", "127.0.0.1", "/media/capas/")
    return any(n in url for n in needles)


def filename_from_url(url: str) -> str | None:
    """Extrai o filename final da URL (a parte depois do último `/`)."""
    if "/" not in url:
        return None
    return url.rsplit("/", 1)[-1]


def cleanup_db_and_local_files() -> tuple[int, int]:
    """Limpa capa_url no banco e remove arquivos físicos locais correspondentes."""
    obras_afetadas = 0
    arquivos_removidos = 0

    media_capas_dir = Path(settings.MEDIA_ROOT) / "capas"

    for obra in Obra.objects.exclude(capa_url=""):
        if not is_local_capa_url(obra.capa_url):
            continue

        print(f"  [DB]  Limpando capa_url da obra slug={obra.slug!r}")
        print(f"        antiga: {obra.capa_url}")

        # Tenta remover o arquivo físico referenciado por essa URL
        fname = filename_from_url(obra.capa_url)
        if fname:
            fpath = media_capas_dir / fname
            if fpath.exists():
                try:
                    fpath.unlink()
                    arquivos_removidos += 1
                    print(f"        arquivo removido: {fpath}")
                except OSError as exc:
                    print(f"        FALHOU remover {fpath}: {exc}")
            else:
                print(f"        arquivo não encontrado em disco: {fpath}")

        obra.capa_url = ""
        obra.save(update_fields=["capa_url"])
        obras_afetadas += 1

    # Limpa quaisquer arquivos órfãos restantes em media/capas/ (não referenciados
    # por nenhuma obra do banco — já apagamos os referenciados acima).
    if media_capas_dir.exists():
        for arq in media_capas_dir.iterdir():
            if arq.is_file():
                try:
                    arq.unlink()
                    arquivos_removidos += 1
                    print(f"  [FS]  Removido órfão local: {arq.name}")
                except OSError as exc:
                    print(f"  [FS]  FALHOU remover {arq}: {exc}")

    return obras_afetadas, arquivos_removidos


def main():
    print("=" * 60)
    print("Limpeza de capas legadas (parte local)")
    print("=" * 60)

    print("\nBanco de dados + arquivos locais...")
    obras_afetadas, arquivos_removidos = cleanup_db_and_local_files()

    print("\n" + "=" * 60)
    print("Relatório final:")
    print(f"  - Obras com capa_url zerada: {obras_afetadas}")
    print(f"  - Arquivos locais removidos: {arquivos_removidos}")
    print("=" * 60)
    print()
    print("LEMBRE: apague manualmente a pasta `mangas/capas/` no painel")
    print("do Supabase (Storage > mangas > capas > selecionar tudo > apagar).")


if __name__ == "__main__":
    main()
