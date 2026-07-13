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
│            USSDSession                    │   (état de NAVIGATION d'une session)
│───────────────────────────────────────────│
│ session_id   ◆U   (fourni par Africa's T.)│
│ phone_number                              │
│ state (écran courant)                     │
│ context (JSON : numéros affichés → ids)   │
│ created_at / updated_at                   │
└──────────────────────────────────────────┘

⚠️ Le PANIER n'est PAS dans USSDSession : il est porté par CustomerUSSD
   (champs `cart` et `cart_updated_at`), car la passerelle attribue un
   NOUVEAU session_id à chaque appel. Rattaché au client, le panier
   survit aux coupures réseau.

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
| `name` | CharField | saisi au premier contact USSD |
| `language` | CharField (choices) | `fr` / `ha` / `dyu` / `ff` / `wo` |
| `cart` | JSONField | **panier en cours** : `[{"product_id": 1, "qty": 2}, ...]` |
| `cart_updated_at` | DateTimeField | sert à expirer les paniers abandonnés (24h) |
| `created_at` | DateTimeField | `auto_now_add` |

> Le panier est **porté par le client** (et non par la session) : il survit ainsi aux
> coupures réseau et aux expirations de session USSD.

### `Order` — commande
| Champ | Type | Notes |
|---|---|---|
| `customer` | ForeignKey(CustomerUSSD) | `on_delete=PROTECT` |
| `status` | CharField (choices) | voir statuts ci-dessous |
| `total_amount` | PositiveIntegerField | recalculé depuis les lignes |
| `validation_code` | CharField **unique** | ex. `A7K2M9`, généré à la création (RG4) |
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

### `USSDSession` — état de NAVIGATION d'une session
| Champ | Type | Notes |
|---|---|---|
| `session_id` | CharField **unique** | fourni par Africa's Talking (nouveau à chaque appel) |
| `phone_number` | CharField | |
| `state` | CharField | écran courant (machine à états) |
| `context` | JSONField | correspondance « numéro affiché → id en base », page courante |
| `created_at` / `updated_at` | DateTimeField | nettoyage périodique des vieilles sessions |

> ⚠️ **Pas de panier ici.** La passerelle attribue un **nouveau `session_id` à chaque
> appel** : un panier stocké dans la session serait perdu à la moindre coupure réseau.
> Il est donc porté par `CustomerUSSD`.

---

## Décisions de conception figées (Phase 0)

1. **Panier multi-produits**, porté par le **client** (`CustomerUSSD.cart`) → survit aux coupures réseau. ✅
2. **Décrément du stock à la validation du paiement** (quand l'agent saisit le code dans l'admin), pas à la création de la commande. Contrôle de disponibilité à l'ajout au panier et à la confirmation. ⚠️ Survente possible sur le dernier article — acceptable pour le prototype.
3. **`validation_code`** : code **alphanumérique de 6 caractères** (ex. `A7K2M9`), sans préfixe, toujours avec au moins une lettre et un chiffre, sans caractères ambigus (0/O, 1/I). Unique, à usage unique.
4. **Pas de PIN client** : identification par `phone_number` seul. ✅

---

## Pourquoi ce découpage ?

- **`CustomerUSSD` séparé de l'`User` Django** : le client USSD n'a pas de compte web ; on le modélise par son numéro. Les `User` Django restent réservés aux admins/agents.
- **`OrderItem.unit_price` figé** : si le prix du produit change demain, les anciennes commandes gardent le bon montant (historisation correcte).
- **`CustomerUSSD.cart` en JSON (et non dans `USSDSession`)** : la passerelle génère un **nouveau `session_id` à chaque appel**. Un panier stocké dans la session serait donc perdu dès que le client raccroche ou que le réseau coupe. En le rattachant au **client** (identifié par son numéro), il est **retrouvé intact** au rappel suivant. Un champ `cart_updated_at` permet d'**expirer** les paniers abandonnés (24 h par défaut, réglable via `USSD_CART_TTL_HOURS`), et les produits devenus indisponibles sont **purgés automatiquement**. Le format JSON évite une table de lignes tant que la commande n'est pas validée.
