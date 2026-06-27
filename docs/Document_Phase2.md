# Document de la Phase 2 — Modèles de données & interface d'administration

> Objectif de la phase : créer les modèles de données métier, générer leurs
> migrations, configurer l'interface d'administration web (CRUD produits,
> visualisation des commandes), et injecter des données de démonstration.

---

## 1. Résultat obtenu

- Les **6 modèles** du projet existent en base PostgreSQL.
- L'**interface d'administration** permet de gérer produits, catégories, clients,
  commandes et sessions USSD.
- Un jeu de **données de démonstration** (3 catégories, 10 produits) est en place.
- La **logique métier** (génération du code de validation, calcul des totaux) est
  vérifiée par un test.

## 2. Modèles créés

### Application `catalog`
| Modèle | Champs principaux | Rôle |
|---|---|---|
| `Category` | `name` (unique), `is_active` | Catégorie de produits |
| `Product` | `category` (FK), `name`, `price` (XOF entier), `stock`, `description`, `is_active`, `created_at` | Produit vendu |

`Product.is_available` : propriété qui indique si le produit est proposable au client
USSD (actif **et** stock > 0).

### Application `orders`
| Modèle | Champs principaux | Rôle |
|---|---|---|
| `CustomerUSSD` | `phone_number` (unique), `name`, `created_at` | Client identifié par son numéro |
| `Order` | `customer` (FK), `status`, `total_amount`, `validation_code` (unique), `is_paid`, `created_at`, `updated_at` | Commande |
| `OrderItem` | `order` (FK), `product` (FK), `quantity`, `unit_price`, `line_total` | Ligne de commande |

Statuts de commande (`Order.Status`) :
`EN_ATTENTE` → `PAYEE` → `PREPAREE` → `LIVREE`, ou `ANNULEE`.

### Application `ussd`
| Modèle | Champs principaux | Rôle |
|---|---|---|
| `USSDSession` | `session_id` (unique), `phone_number`, `cart` (JSON), `state`, horodatages | Panier / état d'une session USSD en cours |

## 3. Logique métier implémentée

- **Génération du code de validation** (`generate_validation_code`) : format `MTS-XXXX`,
  4 caractères, sans caractères ambigus (pas de 0/O ni 1/I pour faciliter la dictée).
  Unicité garantie (nouvelle tentative en cas de collision). Généré automatiquement à
  la création de la commande (`Order.save`).
- **Prix unitaire figé** : `OrderItem.unit_price` est copié au moment de l'achat. Si le
  prix du produit change ensuite, les anciennes commandes gardent le bon montant.
- **Calcul automatique des totaux** :
  - `OrderItem.line_total` = `quantity × unit_price` (calculé à l'enregistrement).
  - `Order.update_total()` = somme des lignes.

## 4. Configuration de l'interface d'administration

- **Produits** : liste avec catégorie, prix, stock, disponibilité ; édition rapide du
  prix / stock / activation directement depuis la liste ; recherche et filtres.
- **Catégories** : affichage du nombre de produits par catégorie.
- **Commandes** : les lignes de commande s'affichent et s'éditent directement dans la
  page de la commande (inline) ; le code de validation et les totaux sont en lecture
  seule ; recherche par code de validation ou par client. Le montant total est
  recalculé automatiquement après modification des lignes.
- **Clients USSD** : affichage du nombre de commandes par client.
- **Sessions USSD** : vue technique pour déboguer les paniers (utile en Phase 3).

## 5. Données de démonstration

Commande de peuplement réutilisable : `catalog/management/commands/seed_demo.py`
(idempotente — relançable sans créer de doublons).

| Catégorie | Produits |
|---|---|
| Vivres | Riz 25kg (12000 F), Huile 1L (3500 F), Sucre 1kg (1000 F), Farine 5kg (4500 F) |
| Hygiène | Savon (500 F), Dentifrice (1200 F), Lessive 1kg (1500 F) |
| Boissons | Eau 1.5L (400 F), Jus 1L (1800 F), Thé (800 F) |

## 6. Commandes exécutées et vérifications

```bash
# Génération des migrations à partir des modèles
docker compose exec web python manage.py makemigrations   # → 3 migrations créées

# Application des migrations à PostgreSQL
docker compose exec web python manage.py migrate           # → catalog, orders, ussd OK

# Peuplement des données de démonstration
docker compose exec web python manage.py seed_demo         # → 3 catégories, 10 produits

# Test de la logique métier (shell Django) : création d'une commande de test
#   → code de validation généré : MTS-XXXX
#   → total ligne = quantité × prix unitaire
#   → total commande = 19000 F (conforme à l'attendu)
```

## 7. Comment tester soi-même

1. Démarrer le projet : `docker compose up`
2. Ouvrir http://localhost:8000/admin/ (admin / admin123)
3. Section **Catalogue → Produits** : 10 produits visibles, modifiables.
4. Section **Commandes** : la commande de test #1 avec ses 2 lignes et son total.

## 8. Prochaine étape — Phase 3

Implémenter le **moteur USSD** : un webhook qui reçoit les requêtes de la passerelle,
reconstruit l'état du menu, gère la navigation (catégories → produits → quantité →
panier → validation) et renvoie les réponses `CON` / `END`. Testable en local avant
de brancher Africa's Talking (Phase 4).
