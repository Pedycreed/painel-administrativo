release: python manage.py migrate --noinput
web: gunicorn core.wsgi --log-file - --timeout 120 --workers 2
