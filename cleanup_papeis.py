"""
Script one-shot: deleta usuários com papel='editor' ou 'viewer'.

Roda antes do makemigrations/migrate da remoção de choices.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model

Usuario = get_user_model()

qs = Usuario.objects.filter(papel__in=['editor', 'viewer'])
total = qs.count()

if total == 0:
    print('Nenhum editor/viewer encontrado. Nada a fazer.')
else:
    print(f'Encontrados {total} usuário(s) editor/viewer:')
    for u in qs:
        print(f'  - {u.username} (papel={u.papel}, time={u.time})')

    resp = input('\nConfirma a EXCLUSÃO de todos eles? [s/N]: ').strip().lower()
    if resp == 's':
        qs.delete()
        print(f'\n✔ {total} usuário(s) deletado(s).')
    else:
        print('\nCancelado.')
