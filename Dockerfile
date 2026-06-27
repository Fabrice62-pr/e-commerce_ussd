# Image de base : Python 3.13 (version "slim" = légère)
FROM python:3.13-slim

# Réglages Python pour Docker :
#  - n'écrit pas les fichiers .pyc
#  - sortie console non bufferisée (logs en temps réel)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Dossier de travail dans le conteneur
WORKDIR /app

# On installe d'abord les dépendances (mise en cache Docker efficace)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Puis on copie le code du projet
COPY . .

# Le serveur écoute sur le port 8000
EXPOSE 8000

# Commande par défaut (production). En développement, docker-compose la remplace
# par "runserver" (voir docker-compose.yml).
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
