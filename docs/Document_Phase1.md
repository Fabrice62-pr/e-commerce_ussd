# Document de la Phase 1 — Socle technique

> Objectif de la phase : mettre en place les fondations du projet (Django + Docker +
> PostgreSQL + Git), de sorte qu'un serveur Django démarre dans Docker, connecté à
> PostgreSQL, **sans encore aucune logique métier**.

---

## 1. Résultat obtenu

À la fin de cette phase, le squelette du projet tourne :
- Le serveur Django démarre dans un conteneur Docker.
- Il est connecté à une base PostgreSQL (elle aussi dans un conteneur).
- L'interface d'administration de Django répond sur http://localhost:8000/admin/.
- Tout se lance avec **une seule commande** : `docker compose up`.

## 2. Choix techniques figés

| Élément | Choix | Raison |
|---|---|---|
| Framework | **Django 5.2 (LTS)** | Version à support long terme, stable et maintenue |
| Python (conteneur) | **3.13-slim** | Compatibilité maximale avec Django, image légère |
| Base de données | **PostgreSQL 16** | Demandée par le cahier des charges, robuste |
| Connecteur DB | **psycopg 3** (`psycopg[binary]`) | Connecteur moderne Django ↔ PostgreSQL |
| API | **Django REST Framework** | Servira au webhook USSD (Phase 3), installé dès maintenant |
| Serveur de prod | **gunicorn** | Serveur WSGI pour la production |
| Conteneurisation | **Docker + docker-compose** | Reproductibilité (exigence clé du projet) |

> Note : la version de Python installée sur la machine (3.14) n'a pas d'importance,
> car Django s'exécute dans le conteneur avec Python 3.13 que nous avons choisi.

## 3. Fichiers créés

### Configuration du projet (racine)
| Fichier | Rôle |
|---|---|
| `requirements.txt` | Liste des dépendances Python |
| `Dockerfile` | Recette de l'image Docker (Python + dépendances + code) |
| `docker-compose.yml` | Orchestration des 2 services : `web` (Django) et `db` (PostgreSQL) |
| `.env.example` | Modèle de variables d'environnement (à versionner) |
| `.env` | Variables réelles de développement (NON versionné) |
| `.gitignore` | Fichiers exclus du versionnement Git |
| `.dockerignore` | Fichiers exclus de l'image Docker |
| `README.md` | Présentation et guide de démarrage rapide |
| `manage.py` | Utilitaire en ligne de commande de Django |

### Package `config/` (réglages Django)
| Fichier | Rôle |
|---|---|
| `settings.py` | Configuration : apps, base de données (via variables d'env.), langue (fr), fuseau (Africa/Niamey) |
| `urls.py` | Routage des URLs (pour l'instant : `/admin/`) |
| `wsgi.py` / `asgi.py` | Points d'entrée du serveur |

### Applications (vides, prêtes pour la Phase 2)
| Application | Rôle futur |
|---|---|
| `catalog/` | Produits et catégories |
| `orders/` | Clients USSD, commandes, lignes de commande |
| `ussd/` | Passerelle et moteur de menu USSD |

## 4. Points techniques importants

- **Sécurité des secrets** : la clé secrète et les identifiants de base de données
  sont lus depuis des variables d'environnement (`.env`), jamais codés en dur ni
  versionnés. Le fichier `.env.example` documente les variables attendues.
- **Healthcheck PostgreSQL** : le service `web` attend que la base soit réellement
  prête (`condition: service_healthy`) avant de démarrer, ce qui évite les erreurs
  de connexion au lancement.
- **Volume monté** : le code local est monté dans le conteneur (`.:/app`), donc toute
  modification de code est prise en compte immédiatement (rechargement automatique).
- **Persistance des données** : un volume Docker (`postgres_data`) conserve les données
  de la base même si le conteneur est recréé.

## 5. Commandes exécutées et vérifications

```bash
# Validation de la configuration
docker compose config --quiet                      # → OK

# Construction et démarrage des conteneurs
docker compose up -d --build                       # → images construites, conteneurs démarrés

# État des conteneurs
docker compose ps                                  # → db (healthy), web (Up)

# Vérification de la configuration Django
docker compose exec web python manage.py check     # → "System check identified no issues"

# Création des tables système de Django
docker compose exec web python manage.py migrate   # → toutes les migrations appliquées

# Test de l'interface d'administration
curl http://localhost:8000/admin/                  # → HTTP 302 vers /admin/login/ (attendu)

# Création du compte administrateur
docker compose exec web python manage.py createsuperuser --no-input   # → "Superuser created"
```

### Identifiants administrateur (développement uniquement)
- **Utilisateur** : `admin`
- **Mot de passe** : `admin123`
- ⚠️ À changer avant toute mise en production.

## 6. Difficulté rencontrée

- **Le moteur Docker n'était pas démarré** au premier essai (`failed to connect to the
  docker API ... daemon is running`). La commande `docker --version` fonctionne même
  moteur éteint, mais construire/lancer des conteneurs exige que **Docker Desktop soit
  ouvert et actif**. Après son démarrage, la construction a réussi.

## 7. Comment relancer le projet

```bash
docker compose up            # démarre web + db
docker compose down          # arrête les conteneurs
docker compose down -v       # arrête ET supprime les données de la base
docker compose logs -f web   # consulte les logs du serveur Django
```

## 8. Prochaine étape — Phase 2

Créer les modèles de données (`Category`, `Product`, `CustomerUSSD`, `Order`,
`OrderItem`, `USSDSession`), générer leurs migrations, et configurer l'interface
d'administration web (CRUD produits, visualisation des commandes).
