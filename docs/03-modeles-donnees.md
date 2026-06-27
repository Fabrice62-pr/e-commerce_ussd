# Schéma des modèles de données

> Cible : Django ORM + PostgreSQL. Montants en **francs CFA (XOF)**, entiers.
> Convention : `id` auto par défaut, `created_at` / `updated_at` sur les tables principales.

---

## Diagramme relationnel (vue logique)

```
┌──────────────────┐         ┌──────────────────┐
│   Category       │         │  CustomerUSSD    │
│──────────────────│         │──────────────────│
│ name             │         │ phone_number  ◆U │
│ is_active        │         │ name (optionnel) │
└────────┬─────────┘         │ created_at       │
         │ 1                 └────────┬─────────┘
         │                            │ 1
         │ N                          │
┌────────▼─────────┐                  │ N
│    Product       │         ┌────────▼─────────┐         ┌──────────────────┐
│──────────────────│         │     Order        │   1   N │   OrderItem      │
│ category  (FK)   │         │──────────────────│────────▶│──────────────────│
│ name             │         │ customer  (FK)   │         │ order   (FK)     │
│ price (XOF int)  │    N    │ status           │         │ product (FK)     │
│ stock            │◀────────│ total_amount     │         │ quantity         │
│ description      │  (via   │ validation_code◆U│         │ unit_price (figé)│
│ is_active        │  Item)  │ created_at       │         │ line_total       │
│ created_at       │         │ updated_at       │         └──────────────────┘
└──────────────────┘         └──────────────────┘

┌──────────────────────────────────────────┐
│            USSDSession                    │   (état de session / panier en cours)
│───────────────────────────────────────────│
│ session_id   ◆U   (fourni par Africa's T.)│
│ phone_number                              │
│ cart (JSON: [{product_id, qty}, ...])     │
│ last_screen / state (optionnel)           │
│ created_at / updated_at                   │
└──────────────────────────────────────────┘

◆U = unique
```

---

## Détail des modèles

### `Category` — catégorie de produits
| Champ | Type | Notes |
|---|---|---|
| `name` | CharField | ex. « Vivres », « Hygiène » |
| `is_active` | BooleanField | défaut `True` |

### `Product` — produit
| Champ | Type | Notes |
|---|---|---|
| `category` | ForeignKey(Category) | `on_delete=PROTECT` |
| `name` | CharField | ex. « Riz 25kg » |
| `price` | PositiveIntegerField | en XOF (entier) |
| `stock` | PositiveIntegerField | quantité disponible |
| `description` | TextField | optionnel |
| `is_active` | BooleanField | masque le produit côté USSD si `False` |
| `created_at` | DateTimeField | `auto_now_add` |

### `CustomerUSSD` — client identifié par son téléphone
| Champ | Type | Notes |
|---|---|---|
| `phone_number` | CharField **unique** | identité du client (RG1) |
| `name` | CharField | optionnel (rempli plus tard) |
| `created_at` | DateTimeField | `auto_now_add` |

### `Order` — commande
| Champ | Type | Notes |
|---|---|---|
| `customer` | ForeignKey(CustomerUSSD) | `on_delete=PROTECT` |
| `status` | CharField (choices) | voir statuts ci-dessous |
| `total_amount` | PositiveIntegerField | recalculé depuis les lignes |
| `validation_code` | CharField **unique** | ex. `MTS-7F3A`, généré à la création (RG4) |
| `is_paid` | BooleanField | passe à `True` à la validation du code |
| `created_at` / `updated_at` | DateTimeField | |

**Statuts (`status`)** :
`EN_ATTENTE` → `PAYEE` → `PREPAREE` → `LIVREE` ; ou `ANNULEE`.

### `OrderItem` — ligne de commande
| Champ | Type | Notes |
|---|---|---|
| `order` | ForeignKey(Order, related_name="items") | `on_delete=CASCADE` |
| `product` | ForeignKey(Product) | `on_delete=PROTECT` |
| `quantity` | PositiveIntegerField | |
| `unit_price` | PositiveIntegerField | **figé** au moment de l'achat (RG5) |
| `line_total` | PositiveIntegerField | `quantity * unit_price` |

### `USSDSession` — état de session / panier en cours
| Champ | Type | Notes |
|---|---|---|
| `session_id` | CharField **unique** | fourni par Africa's Talking |
| `phone_number` | CharField | |
| `cart` | JSONField | `[{"product_id": 1, "qty": 2}, ...]` |
| `state` | CharField | écran courant (optionnel, aide au debug) |
| `created_at` / `updated_at` | DateTimeField | nettoyage périodique des vieilles sessions |

---

## Décisions de conception figées (Phase 0)

1. **Panier multi-produits** (vrai panier via `USSDSession.cart`). ✅
2. **Décrément du stock à la validation du paiement** (quand l'agent saisit le code dans l'admin), pas à la création de la commande. Contrôle de disponibilité à l'ajout au panier et à la confirmation. ⚠️ Survente possible sur le dernier article — acceptable pour le prototype.
3. **`validation_code`** : format court et lisible `MTS-XXXX` (4 caractères alphanumériques), unique, à usage unique.
4. **Pas de PIN client** : identification par `phone_number` seul. ✅

---

## Pourquoi ce découpage ?

- **`CustomerUSSD` séparé de l'`User` Django** : le client USSD n'a pas de compte web ; on le modélise par son numéro. Les `User` Django restent réservés aux admins/agents.
- **`OrderItem.unit_price` figé** : si le prix du produit change demain, les anciennes commandes gardent le bon montant (historisation correcte).
- **`USSDSession.cart` en JSON** : le panier « en cours » est volatile ; pas besoin d'une table de lignes tant que la commande n'est pas validée. Simple et suffisant pour un prototype.
