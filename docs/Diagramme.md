# Diagrammes du projet e-commerce USSD

> Ce document présente la modélisation **complète** du système (parties déjà
> développées **et** parties à venir), sous plusieurs formes complémentaires :
> 1. le **diagramme de cas d'utilisation** (UML — vue fonctionnelle globale) ;
> 2. le **diagramme de classes** complet (UML — vue structurelle) ;
> 3. le **diagramme de séquence** du parcours d'achat (UML — vue dynamique) ;
> 4. le **diagramme Entité-Association** (MCD, méthode MERISE) ;
> 5. le **passage au schéma relationnel** (MLD : les tables PostgreSQL).
>
> Les éléments **non encore développés** sont annotés par phase : `Phase 4`
> (Africa's Talking), `Phase 5` (paiement), `Phase 6` (rapports).
>
> Les diagrammes Mermaid s'affichent graphiquement sur GitHub ; des versions ASCII
> sont fournies en complément.

---

## 1. Diagramme de cas d'utilisation (UML)

Vue d'ensemble des **acteurs** et de **toutes les fonctionnalités** du système.

```mermaid
flowchart LR
    client([👤 Client USSD])
    admin([👤 Administrateur])
    agent([👤 Agent / Commerçant])
    at([📡 Africa's Talking]):::ext

    subgraph S[Système e-commerce USSD]
        u1(Consulter le catalogue)
        u2(Passer une commande)
        u3(Obtenir un code de paiement)
        u4(Suivre ses commandes)
        u5(Gérer produits et catégories - CRUD)
        u6(Consulter les commandes)
        u7(Valider un paiement - Phase 5)
        u8(Consulter les rapports - Phase 6)
    end

    client --- u1
    client --- u2
    client --- u3
    client --- u4
    admin --- u5
    admin --- u6
    admin --- u7
    admin --- u8
    agent --- u7
    at -. relaie .- u1
    at -. relaie .- u2

    classDef ext fill:#eee,stroke:#999,stroke-dasharray:5 5;
```

### Cas d'utilisation par acteur

| Acteur | Cas d'utilisation | État |
|---|---|---|
| **Client USSD** | Consulter le catalogue (catégories, produits) | ✅ fait |
| | Passer une commande (panier multi-produits) | ✅ fait |
| | Obtenir un code de paiement | ✅ fait |
| | Suivre ses commandes | ✅ fait |
| **Administrateur** | Gérer produits et catégories (CRUD) | ✅ fait |
| | Consulter les commandes | ✅ fait |
| | Valider un paiement (saisie du code, décrément du stock) | 🔜 Phase 5 |
| | Consulter les rapports (CA, ventes, statuts) | 🔜 Phase 6 |
| **Agent / Commerçant** | Valider un paiement au comptoir | 🔜 Phase 5 |
| **Africa's Talking** | Relayer les requêtes USSD (passerelle externe) | 🔜 Phase 4 |

---

## 2. Diagramme de classes complet (UML)

Vue structurelle de **tout le système** : acteurs, passerelle, webhook, moteur USSD,
entités du domaine et services à venir.

```mermaid
classDiagram
    direction LR

    %% ===== Acteurs / utilisateurs =====
    class User {
        <<Django auth>>
        +String username
        +String password
        +bool is_staff
        +bool is_superuser
    }
    class Administrateur {
        <<acteur>>
        +gerer_produits()
        +valider_paiement(code)
        +consulter_rapports()
    }

    %% ===== Passerelle & couche USSD =====
    class AfricaTalkingGateway {
        <<externe - Phase 4>>
        +String sessionId
        +String phoneNumber
        +String text
        +String serviceCode
    }
    class USSDCallbackView {
        <<boundary / webhook>>
        +post(request) HttpResponse
    }
    class USSDEngine {
        <<control>>
        +process_ussd(session_id, phone, text)
        +show_home()
        +show_categories()
        +show_products()
        +show_quantity()
        +show_cart()
        +show_my_orders()
        +validate_order()
    }

    %% ===== Entités du domaine =====
    class Category {
        +BigAutoField id
        +CharField name
        +BooleanField is_active
    }
    class Product {
        +BigAutoField id
        +CharField name
        +PositiveIntegerField price
        +PositiveIntegerField stock
        +TextField description
        +BooleanField is_active
        +DateTimeField created_at
        +is_available() bool
    }
    class CustomerUSSD {
        +BigAutoField id
        +CharField phone_number
        +CharField name
        +DateTimeField created_at
    }
    class Order {
        +BigAutoField id
        +CharField status
        +PositiveIntegerField total_amount
        +CharField validation_code
        +BooleanField is_paid
        +DateTimeField created_at
        +DateTimeField updated_at
        +save()
        +update_total()
        +valider_paiement() bool
    }
    class OrderItem {
        +BigAutoField id
        +PositiveIntegerField quantity
        +PositiveIntegerField unit_price
        +PositiveIntegerField line_total
        +save()
    }
    class USSDSession {
        +BigAutoField id
        +CharField session_id
        +CharField phone_number
        +JSONField cart
        +CharField state
        +JSONField context
        +DateTimeField created_at
        +DateTimeField updated_at
    }

    %% ===== Services à venir =====
    class PaiementService {
        <<control - Phase 5>>
        +valider(code_validation) bool
        +decrementer_stock(order)
    }
    class RapportService {
        <<control - Phase 6>>
        +chiffre_affaires()
        +commandes_par_statut()
        +produits_les_plus_vendus()
    }

    %% ===== Relations d'usage (dépendances) =====
    Administrateur --|> User
    Administrateur ..> Product : CRUD
    Administrateur ..> PaiementService : utilise
    Administrateur ..> RapportService : consulte

    AfricaTalkingGateway ..> USSDCallbackView : POST
    USSDCallbackView ..> USSDEngine : process_ussd()
    USSDEngine ..> USSDSession : lit / écrit
    USSDEngine ..> Category : parcourt
    USSDEngine ..> Product : parcourt
    USSDEngine ..> CustomerUSSD : crée
    USSDEngine ..> Order : crée

    PaiementService ..> Order : valide
    PaiementService ..> Product : décrémente stock
    RapportService ..> Order : agrège

    %% ===== Associations structurelles (le modèle de données) =====
    Category "1" --> "0..*" Product : contient
    CustomerUSSD "1" --> "0..*" Order : passe
    Order "1" *-- "1..*" OrderItem : comprend
    Product "1" --> "0..*" OrderItem : référencé par
```

### Légende des relations

| Notation | Signification |
|---|---|
| `--|>` | Héritage (Administrateur **est un** User Django) |
| `..>` | Dépendance / utilisation (une classe en appelle une autre) |
| `-->` | Association (lien structurel entre entités) |
| `*--` | **Composition** : `OrderItem` n'existe pas sans son `Order` (cascade) |
| `<<...>>` | Stéréotype (rôle de la classe) ; `Phase N` = à développer |

> **Couches** (architecture) :
> - *Acteurs* : `User`, `Administrateur` (et le Client, représenté par `CustomerUSSD`).
> - *Frontière (boundary)* : `AfricaTalkingGateway` (externe), `USSDCallbackView` (webhook).
> - *Contrôle (control)* : `USSDEngine`, `PaiementService`, `RapportService`.
> - *Entités du domaine* : `Category`, `Product`, `CustomerUSSD`, `Order`, `OrderItem`, `USSDSession`.

---

## 3. Diagramme de séquence (UML) — parcours d'achat complet

Vue dynamique : du composé USSD jusqu'au paiement validé, **incluant Africa's
Talking (Phase 4) et la validation du paiement (Phase 5)**.

```mermaid
sequenceDiagram
    actor Client as 👤 Client (téléphone)
    participant AT as 📡 Africa's Talking
    participant View as 🌐 Webhook /ussd/callback/
    participant Engine as ⚙️ USSDEngine
    participant DB as 🗄️ PostgreSQL
    actor Agent as 👤 Agent / Admin

    Client->>AT: compose *384*XXXXX#
    AT->>View: POST (sessionId, phoneNumber, text="")
    View->>Engine: process_ussd(...)
    Engine->>DB: lit catégories / produits
    Engine-->>View: CON menu d'accueil
    View-->>AT: CON menu
    AT-->>Client: affiche le menu

    Note over Client,AT: navigation : catégorie → produit → quantité

    Client->>AT: valide le panier (choix "1")
    AT->>View: POST (text="...*1")
    View->>Engine: process_ussd(...)
    Engine->>DB: crée Order + OrderItem, génère le code
    Engine-->>View: END + code de paiement
    View-->>AT: END (ex. 9V7RKT)
    AT-->>Client: affiche le code de paiement

    Note over Client,Agent: paiement hors-ligne (espèces)

    Client->>Agent: présente le code 9V7RKT + espèces
    Agent->>DB: valide le paiement (PaiementService, Phase 5)
    DB-->>DB: Order.is_paid=True, statut=PAYEE, stock décrémenté
    DB-->>Agent: confirmation
```

---

## 4. Diagramme Entité-Association (MCD — MERISE)

Modèle Conceptuel de Données. Les **associations** (APPARTENIR, PASSER, CONTENIR)
sont dessinées explicitement (ovales), avec les cardinalités notées **(min, max)**
selon la convention MERISE.

### 4.1 Le MCD (notation MERISE)

```
   +-----------------+                            +------------------+
   |   CATEGORIE     |                            |   CLIENT_USSD    |
   |-----------------|                            |------------------|
   | id_categorie    |                            | id_client        |
   | nom             |                            | telephone        |
   | actif           |                            | nom              |
   +--------+--------+                            | date_creation    |
            |                                      +--------+---------+
         (0,n)                                          (0,n)
            |                                              |
       <  APPARTENIR  >                              <  PASSER  >
            |                                              |
         (1,1)                                          (1,1)
            |                                              |
   +--------+--------+                            +--------+---------+
   |    PRODUIT      |                            |    COMMANDE      |
   |-----------------|       +-------------+      |------------------|
   | id_produit      |       |  CONTENIR   |      | id_commande      |
   | nom             |(0,n)  |-------------|(1,n) | statut           |
   | prix            +-------< quantite    >------+ montant_total    |
   | stock           |       | prix_unitaire|     | code_validation  |
   | description     |       | total_ligne |      | payee            |
   | actif           |       +-------------+      | date_creation    |
   | date_creation   |                            | date_maj         |
   +-----------------+                            +------------------+


   +-------------------+
   |   SESSION_USSD    |   Entité technique INDÉPENDANTE (panier + état de
   |-------------------|   navigation d'une session USSD). Aucune association :
   | id_session        |   reliée seulement de façon logique au client par le
   | session_id        |   numéro de téléphone, sans clé étrangère (le panier
   | telephone         |   est volatile, antérieur à la création de la commande).
   | panier (JSON)     |
   | etat              |
   | contexte (JSON)   |
   | date_creation     |
   | date_maj          |
   +-------------------+
```

Lecture des cardinalités :
- **APPARTENIR** : un PRODUIT appartient à **(1,1)** une CATEGORIE ; une CATEGORIE
  regroupe **(0,n)** produits.
- **PASSER** : une COMMANDE est passée par **(1,1)** un CLIENT ; un CLIENT passe
  **(0,n)** commandes.
- **CONTENIR** : une COMMANDE contient **(1,n)** produits ; un PRODUIT figure dans
  **(0,n)** commandes. Cette association **porte des données propres** (`quantite`,
  `prix_unitaire`, `total_ligne`) → c'est une association **n,m** porteuse.

### 4.2 Le même MCD en notation ER (Mermaid, affiché sur GitHub)

```mermaid
erDiagram
    CATEGORIE  ||--o{ PRODUIT        : "APPARTENIR"
    CLIENT_USSD ||--o{ COMMANDE      : "PASSER"
    COMMANDE   ||--|{ LIGNE_COMMANDE : "CONTENIR"
    PRODUIT    ||--o{ LIGNE_COMMANDE : "CONCERNER"

    CATEGORIE {
        int id_categorie PK
        string nom
        bool actif
    }
    PRODUIT {
        int id_produit PK
        string nom
        int prix
        int stock
        string description
        bool actif
        datetime date_creation
        int id_categorie FK
    }
    CLIENT_USSD {
        int id_client PK
        string telephone
        string nom
        datetime date_creation
    }
    COMMANDE {
        int id_commande PK
        string statut
        int montant_total
        string code_validation
        bool payee
        datetime date_creation
        datetime date_maj
        int id_client FK
    }
    LIGNE_COMMANDE {
        int id_ligne PK
        int quantite
        int prix_unitaire
        int total_ligne
        int id_commande FK
        int id_produit FK
    }
    SESSION_USSD {
        int id_session PK
        string session_id
        string telephone
        json panier
        string etat
        json contexte
        datetime date_creation
        datetime date_maj
    }
```

### Détail des associations et cardinalités (MERISE)

| Association | Entité 1 | Cardinalité | Entité 2 | Cardinalité |
|---|---|---|---|---|
| **APPARTENIR** | PRODUIT | (1,1) | CATEGORIE | (0,n) |
| **PASSER** | COMMANDE | (1,1) | CLIENT_USSD | (0,n) |
| **CONTENIR** | COMMANDE | (1,n) | PRODUIT | (0,n) |

> **Point important (MERISE)** : l'association **CONTENIR** entre `COMMANDE` et
> `PRODUIT` est de type **plusieurs-à-plusieurs (n,m)** et porte des **données
> propres** (*quantité*, *prix unitaire* figé, *total de ligne*). Au passage au
> relationnel, elle devient la table `LIGNE_COMMANDE` (section 5).

> **`SESSION_USSD`** : entité **technique et indépendante** (panier + état de
> navigation). Reliée *logiquement* au client par le numéro de téléphone, sans clé
> étrangère (le panier est volatile, antérieur à la commande).

---

## 5. Passage au schéma relationnel (MLD)

Règles de passage du MCD (section 4) vers le modèle relationnel :

| Élément du MCD | Règle appliquée | Résultat relationnel |
|---|---|---|
| Chaque **entité** | → une **table** | CATEGORIE, PRODUIT, CLIENT_USSD, COMMANDE, SESSION_USSD |
| **APPARTENIR** (1,1)–(0,n) | la clé de CATEGORIE migre dans PRODUIT | `id_categorie` => CATEGORIE dans PRODUIT |
| **PASSER** (1,1)–(0,n) | la clé de CLIENT_USSD migre dans COMMANDE | `id_client` => CLIENT_USSD dans COMMANDE |
| **CONTENIR** (1,n)–(0,n) **porteuse** | une association **n,m** devient une **table de jonction** qui hérite des clés des deux entités + ses attributs propres | nouvelle table `LIGNE_COMMANDE` (`quantite`, `prix_unitaire`, `total_ligne`, `id_commande`, `id_produit`) |

Légende : `#` = clé primaire, `=>` = clé étrangère.

```
CATEGORIE (#id_categorie, nom, actif)

PRODUIT   (#id_produit, nom, prix, stock, description, actif, date_creation,
           id_categorie => CATEGORIE)

CLIENT_USSD (#id_client, telephone, nom, date_creation)

COMMANDE  (#id_commande, statut, montant_total, code_validation, payee,
           date_creation, date_maj,
           id_client => CLIENT_USSD)

LIGNE_COMMANDE (#id_ligne, quantite, prix_unitaire, total_ligne,
                id_commande => COMMANDE,
                id_produit  => PRODUIT)

SESSION_USSD (#id_session, session_id, telephone, panier, etat, contexte,
              date_creation, date_maj)
```

### Contraintes d'intégrité

| Table | Contrainte |
|---|---|
| `CATEGORIE` | `nom` UNIQUE |
| `PRODUIT` | `prix ≥ 0`, `stock ≥ 0` ; catégorie non supprimable si utilisée (PROTECT) |
| `CLIENT_USSD` | `telephone` UNIQUE |
| `COMMANDE` | `code_validation` UNIQUE ; `statut` ∈ {EN_ATTENTE, PAYEE, PREPAREE, LIVREE, ANNULEE} ; client non supprimable si utilisé (PROTECT) |
| `LIGNE_COMMANDE` | `total_ligne = quantite × prix_unitaire` ; cascade avec la commande ; produit non supprimable si utilisé (PROTECT) |
| `SESSION_USSD` | `session_id` UNIQUE |

### Correspondance noms MERISE ↔ Django ↔ PostgreSQL

| MERISE | Modèle Django | Table PostgreSQL |
|---|---|---|
| `CATEGORIE` | `Category` | `catalog_category` |
| `PRODUIT` | `Product` | `catalog_product` |
| `CLIENT_USSD` | `CustomerUSSD` | `orders_customerussd` |
| `COMMANDE` | `Order` | `orders_order` |
| `LIGNE_COMMANDE` | `OrderItem` | `orders_orderitem` |
| `SESSION_USSD` | `USSDSession` | `ussd_ussdsession` |

> **Clé de `LIGNE_COMMANDE`** : en MERISE « pur », la clé serait la combinaison
> (`id_commande`, `id_produit`). L'implémentation Django conserve une **clé technique**
> auto-incrémentée (`id_ligne`) — plus simple et autorisant plusieurs lignes pour un
> même produit. Les deux approches sont fonctionnellement équivalentes.
