"""
Script one-shot: reseta o `time` de todos os superusers pra None.

Quando o `EditarUsuarioDialog` tinha o bug de mandar `time='scan'` no payload
mesmo pra superuser, o time ficou setado no banco. Esse script corrige.

Rodar: python fix_superuser_time.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model  # noqa: E402

Usuario = get_user_model()

supers = Usuario.objects.filter(is_superuser=True)
if not supers.exists():
    print('Nenhum superuser encontrado.')
    raise SystemExit

for u in supers:
    if u.time:
        print(f'  - {u.username}: tinha time={u.time!r}, agora None')
        u.time = None
        u.save(update_fields=['time'])
    else:
        print(f'  - {u.username}: já tinha time=None, ok')

print('Pronto.')
