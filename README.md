# Plateforme e-commerce USSD

Prototype de plateforme e-commerce accessible par **USSD** (sans Internet), destiné
aux populations non-bancarisées d'Afrique de l'Ouest. Projet réalisé pour
**MTS Group Africa**.

Un client peut, depuis un simple téléphone (menu `*384*XXXXX#`), consulter un
catalogue, passer commande et obtenir un **code de paiement hors-ligne**. Un
administrateur gère les produits, les commandes et les rapports via une interface web.

## Pile technique

| Composant | Technologie |
|---|---|
| Backend | Django 5.2 (LTS) + Django REST Framework |
| Base de données | PostgreSQL 16 |
| Passerelle USSD | Africa's Talking (sandbox) |
| Conteneurisation | Docker + docker-compose |

## Démarrage rapide

Prérequis : **Docker Desktop** et **Git** installés.

```bash
# 1. Copier le modèle de configuration
cp .env.example .env        # (Windows PowerShell : Copy-Item .env.example .env)

# 2. Construire et lancer les conteneurs (web + base de données)
docker compose up --build

# 3. Dans un autre terminal : appliquer les migrations de base
docker compose exec web python manage.py migrate

# 4. Créer un compte administrateur
docker compose exec web python manage.py createsuperuser
```

L'application est ensuite accessible sur :
- Interface d'administration : http://localhost:8000/admin/

## Structure du projet

```
config/    Réglages Django (settings, urls, wsgi/asgi)
catalog/   Produits & catégories
orders/    Clients USSD, commandes, lignes de commande
ussd/      Passerelle et moteur de menu USSD
docs/      Documentation (spécifications, modèles, guides par phase)
```

## Documentation

La documentation détaillée se trouve dans le dossier [`docs/`](docs/) :
spécifications fonctionnelles, arbre des menus USSD, schéma des modèles de
données, et un document récapitulatif par phase de développement.

## État d'avancement

- [x] Phase 0 — Cadrage (spécifications, menus, modèles)
- [x] Phase 1 — Socle technique (Django + Docker + PostgreSQL + Git)
- [x] Phase 2 — Modèles & interface d'administration
- [x] Phase 3 — Moteur USSD
- [ ] Phase 4 — Intégration Africa's Talking
- [ ] Phase 5 — Paiement (code de validation)
- [ ] Phase 6 — Rapports
- [ ] Phase 7 — Documentation & déploiement
