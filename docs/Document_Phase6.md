# Document de la Phase 6 — Rapports (tableau de bord administrateur)

> Objectif de la phase : fournir à l'administrateur MTS une page de **tableau de
> bord** synthétisant l'activité : chiffre d'affaires, nombre de commandes,
> répartition par statut, et produits les plus vendus.

---

## 1. Résultat obtenu

- Une page **/rapports/** (réservée au personnel connecté) affiche les indicateurs
  clés et deux visualisations simples.
- Un lien **« 📊 Rapports »** est intégré dans l'en-tête de l'interface d'administration.
- Les données sont calculées **en temps réel** à partir de la base.

## 2. Indicateurs affichés

| Indicateur | Calcul |
|---|---|
| **Chiffre d'affaires (encaissé)** | somme des montants des commandes **payées** |
| **Commandes (total)** | nombre total de commandes |
| **Commandes payées** / **En attente** | ventilation payées vs non payées |
| **Panier moyen (payé)** | CA ÷ nombre de commandes payées |
| **Clients** | nombre de clients distincts ayant commandé |
| **Commandes par statut** | répartition (barres) par statut |
| **Produits les plus vendus** | top 10 par quantité vendue (commandes payées) + CA généré |

## 3. Fichiers créés / modifiés

| Fichier | Rôle |
|---|---|
| `orders/reports.py` | Calcul des statistiques (« RapportService » des diagrammes) |
| `orders/views.py` | Vue `rapports` protégée par `@staff_member_required` |
| `orders/urls.py` | Route `/rapports/` |
| `config/urls.py` | Inclusion des URLs de `orders` |
| `templates/orders/rapports.html` | Le tableau de bord (HTML + CSS) |
| `templates/admin/base_site.html` | Titre « MTS Shop » + lien « 📊 Rapports » dans l'admin |
| `config/settings.py` | Ajout de `django.contrib.humanize` (formatage des nombres) |

## 4. Comment ça fonctionne

- **Calcul** : `get_rapport_data()` utilise l'ORM de Django (agrégations `Sum`,
  `Count`, regroupement `values().annotate()`) pour produire tous les indicateurs
  en quelques requêtes.
- **Sécurité** : la vue est décorée par `@staff_member_required` → un visiteur non
  connecté est **redirigé vers la page de connexion** de l'admin.
- **Affichage** : le template présente des **cartes d'indicateurs**, un **graphique
  à barres CSS** (sans JavaScript) pour les statuts, et un **tableau** pour le top
  produits. Les montants sont formatés à la française (séparateur de milliers) via
  le filtre `intcomma` de `humanize`.
- **Intégration** : la surcharge de `admin/base_site.html` ajoute le lien vers le
  tableau de bord directement dans l'en-tête de l'administration.

## 5. Vérifications effectuées

| Test | Résultat |
|---|---|
| Calcul des indicateurs | CA 59 700 F, 12 commandes (4 payées, 8 en attente), panier moyen 14 925 F, 9 clients ✅ |
| Top produits | Jus 1L (14), Huile 1L (3), Riz 25kg (2) ✅ |
| Rendu de la page (admin connecté) | HTTP 200, contient tous les blocs ✅ |
| Accès non authentifié | HTTP 302 → redirection vers `/admin/login` ✅ |
| Admin non cassé | HTTP 200, titre « MTS Shop » et lien « Rapports » présents ✅ |

## 6. Comment y accéder

1. Démarrer le projet (`docker compose up`).
2. Se connecter à l'admin : http://localhost:8000/admin/ (admin / admin123).
3. Cliquer sur **« 📊 Rapports »** dans l'en-tête, ou aller directement sur
   http://localhost:8000/rapports/.

## 7. Prochaine étape — Phase 7

Dernière phase : **documentation & déploiement** — documentation technique
(architecture, modèles, API interne), guide utilisateur (admin + client USSD),
guide d'installation (commandes Docker), et vérification finale avant la démo à MTS.
