python manage.py makemigrations --no-input
python manage.py migrate --no-input
python manage.py collectstatic --no-input
cp -r /app/api/docs /app/static/
gunicorn --bind 0.0.0.0:8000 foodgram_backend.wsgi