# Fiche de spécifications — Plateforme e-commerce USSD

> Projet : prototype e-commerce accessible par USSD pour populations non-bancarisées
> Client : MTS Group Africa — Document de cadrage (Phase 0)
> Version : 0.1 (brouillon à valider)

---

## 1. Contexte et objectif

Une large part de la population d'Afrique de l'Ouest (Niger, Guinée, etc.) n'est **pas bancarisée** mais dispose d'un téléphone mobile utilisable via **USSD** (sans Internet). L'objectif est de fournir un **prototype** de plateforme e-commerce permettant à ces utilisateurs de **consulter des produits, passer commande et suivre leur commande** par simple menu téléphonique, avec un **paiement hors-ligne** validé par code.

Le prototype doit être **démontrable à distance** et **reproductible** (Docker) afin de servir de vitrine commerciale à MTS auprès d'opérateurs télécoms, ONG et commerçants.

## 2. Acteurs (utilisateurs)

| Acteur | Canal | Rôle |
|---|---|---|
| **Client USSD** | Téléphone (menu USSD) | Consulte le catalogue, commande, suit ses commandes |
| **Administrateur MTS** | Navigateur web (Django Admin) | Gère produits, catégories, commandes ; consulte les rapports |
| **Agent / commerçant** | Navigateur web | Valide les paiements (saisit / vérifie le code de validation), met à jour le statut |

## 3. Périmètre fonctionnel

### 3.1 Côté Client (USSD) — *must have*
- **F1** Consulter les catégories de produits.
- **F2** Consulter les produits d'une catégorie (nom, prix, stock).
- **F3** Ajouter un produit au panier (avec quantité).
- **F4** Voir / confirmer le panier et valider la commande.
- **F5** Recevoir un **code de validation** pour le paiement hors-ligne.
- **F6** Suivre le statut de ses commandes existantes.
- **F7** S'enregistrer implicitement à la 1re utilisation (via le numéro de téléphone).

### 3.2 Côté Admin (web) — *must have*
- **F8** CRUD produits et catégories (nom, prix, stock, description, actif/inactif).
- **F9** Visualiser les commandes et leur détail (lignes, client, montant, statut).
- **F10** Faire évoluer le statut d'une commande (en attente → payée → préparée → livrée / annulée).
- **F11** Valider un paiement à partir du code de validation.
- **F12** Rapports simples : chiffre d'affaires, nombre de commandes, commandes par statut, produits les plus vendus.

### 3.3 Hors périmètre du prototype (*nice to have / plus tard*)
- Paiement mobile money réel (Orange Money, etc.) — on simule par code.
- Notifications SMS automatiques — possibles via Africa's Talking, optionnelles.
- Multi-langue (français/langues locales) — prévu dans la conception, non prioritaire.
- Multi-vendeurs / marketplace — le prototype est mono-boutique.

## 4. Exigences non-fonctionnelles

- **Simplicité d'usage** : menus courts, numérotés, peu de texte (faible littératie numérique).
- **Sessions USSD sans état** : la logique reconstruit le contexte à chaque requête + état persistant en base.
- **Robustesse** : gérer les saisies invalides sans planter la session.
- **Reproductibilité** : déploiement complet via `docker-compose` (web + PostgreSQL).
- **Traçabilité** : code source versionné sur GitHub.
- **Sécurité minimale** : code de validation unique, non rejouable ; accès admin protégé.

## 5. Parcours type (scénario nominal)

1. Le client compose `*384*XXXXX#`.
2. Il navigue : `Acheter` → choisit une catégorie → choisit un produit → saisit la quantité.
3. Il confirme le panier → la commande est créée au statut **EN_ATTENTE**.
4. Le système génère et affiche un **code de validation** (ex. `MTS-7F3A`).
5. Le client paie en espèces auprès d'un agent ; l'agent saisit le code dans l'admin → commande **PAYEE**.
6. Le client peut composer de nouveau le code USSD et choisir `Mes commandes` pour suivre le statut.

## 6. Règles de gestion (à valider)

- **RG1** Un client est identifié par son **numéro de téléphone** (unique).
- **RG2** Une commande appartient à un client et contient 1..N lignes (`OrderItem`).
- **RG3** Le **stock** est décrémenté **à la validation du paiement** (saisie du code par l'agent), pas à la création de la commande. On vérifie quand même la disponibilité à l'ajout au panier et à la confirmation. *Implication : survente possible si deux clients commandent le dernier article — acceptable pour un prototype ; à signaler en démo.*
- **RG4** Le **code de validation** est unique par commande, généré à la création, à usage unique.
- **RG5** Le **prix** est figé sur la ligne de commande au moment de l'achat (historisation).
- **RG6** Une session USSD expire après inactivité (la passerelle gère le timeout ; on nettoie l'état).
- **RG7** Montants en **francs CFA (XOF)**, entiers (pas de décimales).

## 7. Livrables (rappel mission)

- [ ] Prototype fonctionnel (admin web + menu USSD + code de validation).
- [ ] Code source complet sur GitHub.
- [ ] Documentation technique (architecture, modèles, API interne).
- [ ] Guide utilisateur (admin + client USSD).
- [ ] Fichier d'installation (`docker-compose.yml` + commandes).

## 8. Décisions figées (Phase 0)

1. Devise et format de prix : **XOF entier** (pas de décimales). ✅
2. Décrément du stock : **à la validation du paiement**. ✅ (voir RG3)
3. Panier : **multi-produits** (vrai panier via `USSDSession`). ✅
4. Identification client : **numéro de téléphone seul**, pas de PIN pour le prototype. ✅
