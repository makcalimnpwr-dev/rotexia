#!/usr/bin/env bash
set -e

echo "== Rotexia: pre-start checks =="

echo "Running migrations..."
python manage.py migrate --noinput

echo "Ensuring superuser (optional)..."
python manage.py ensure_superuser || true

echo "Starting gunicorn..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT}




