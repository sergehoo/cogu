#!/bin/sh
set -e

# Attendre que la DB soit prête
echo "⏳ Attente de la base de données..."
until pg_isready -h "$DATABASE_HOST" -U "$DATABASE_USER" -d "$DATABASE_NAME"; do
  sleep 2
done
echo "✅ Base de données disponible"

# Appliquer migrations
echo "📦 Application des migrations..."
python manage.py migrate --noinput

# Collecter les fichiers statiques
echo "🎨 Collecte des statiques..."
python manage.py collectstatic --noinput

# Démarrer l’application (par défaut Daphne ici)
exec "$@"