"""
Script one-shot pra trocar o admin antigo por um novo superuser.

O que faz:
  1. Pede interativamente username, email e senha do novo superuser.
  2. Cria o usuário com is_superuser=True, is_staff=True, papel='admin', time=None.
  3. Deleta o usuário 'admin' antigo (caso exista e não seja o que está sendo criado).

Rodar a partir da raiz do projeto:
    python setup_superuser.py

Depois que rodar com sucesso pode apagar este arquivo.
"""
import os
import sys
import getpass
from pathlib import Path

# --- Setup Django ---
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django  # noqa: E402

django.setup()

from django.contrib.auth import get_user_model  # noqa: E402
from django.contrib.auth.password_validation import validate_password  # noqa: E402
from django.core.exceptions import ValidationError  # noqa: E402

Usuario = get_user_model()


def prompt_non_empty(label: str) -> str:
    while True:
        value = input(f"{label}: ").strip()
        if value:
            return value
        print("  (não pode ser vazio)")


def prompt_password() -> str:
    while True:
        pwd = getpass.getpass("Senha: ")
        if not pwd:
            print("  (senha vazia, tenta de novo)")
            continue
        pwd2 = getpass.getpass("Confirmar senha: ")
        if pwd != pwd2:
            print("  (senhas não conferem)")
            continue
        try:
            validate_password(pwd)
        except ValidationError as exc:
            print("  Senha fraca:")
            for msg in exc.messages:
                print(f"    - {msg}")
            continue
        return pwd


def main():
    print("=" * 60)
    print("Setup do novo Superuser")
    print("=" * 60)
    print()

    username = prompt_non_empty("Username")
    email = prompt_non_empty("Email")
    password = prompt_password()

    # Se já existe usuário com esse username, aborta — não queremos sobrescrever
    if Usuario.objects.filter(username=username).exists():
        existing = Usuario.objects.get(username=username)
        if existing.is_superuser:
            print(f"\n⚠ Já existe um superuser com username {username!r}.")
            resp = input("Promover/atualizar ele (s/N)? ").strip().lower()
            if resp != "s":
                print("Abortando.")
                return
            existing.email = email
            existing.set_password(password)
            existing.is_superuser = True
            existing.is_staff = True
            existing.papel = "admin"
            existing.time = None
            existing.save()
            print(f"✓ Superuser {username!r} atualizado.")
            user = existing
        else:
            print(f"\n✗ Username {username!r} já existe e NÃO é superuser. Escolha outro.")
            return
    else:
        user = Usuario.objects.create(
            username=username,
            email=email,
            is_superuser=True,
            is_staff=True,
            papel="admin",
            time=None,
        )
        user.set_password(password)
        user.save()
        print(f"\n✓ Superuser {username!r} criado.")

    # Limpa o admin antigo (se for diferente do novo superuser)
    antigo = Usuario.objects.filter(username="admin").first()
    if antigo and antigo.pk != user.pk:
        print()
        print(f"Encontrado usuário antigo 'admin' (id={antigo.pk}, papel={antigo.papel}).")
        resp = input("Deletar ele agora (s/N)? ").strip().lower()
        if resp == "s":
            antigo.delete()
            print("✓ Usuário 'admin' antigo deletado.")
        else:
            print("Mantido. (você pode deletar depois pelo painel)")

    print()
    print("=" * 60)
    print("Pronto! Faça login no painel com o novo superuser:")
    print(f"  Username: {username}")
    print("  Senha: (a que você escolheu)")
    print("=" * 60)


if __name__ == "__main__":
    main()
