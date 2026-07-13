# Arbre des menus USSD — parcours client

> Convention de réponse de notre serveur :
> - `CON ...` → afficher le menu et **attendre** une saisie (session continue)
> - `END ...` → afficher le message final et **fermer** la session
>
> Rappel : à chaque touche, Africa's Talking nous renvoie **tout** ce que le client a
> tapé depuis le début, séparé par `*` (ex. `text = "1*2*3"`). On en déduit l'écran courant.
>
> **Multi-langue** : tous les textes ci-dessous sont affichés dans la langue choisie
> par le client (français, haoussa, dioula, peul, wolof). Les exemples sont en français.

---

## Vue d'ensemble (schéma)

```
                       *384*XXXXX#
                            │
              ┌─────────────▼──────────────┐
              │  PREMIER CONTACT ?         │   (nouveau numéro = pas de nom)
              └──────┬──────────────┬──────┘
                 oui │              │ non (client connu)
                     ▼              │
          ┌────────────────────┐    │
          │  CHOIX DE LA LANGUE│    │
          │ 1. Francais        │    │
          │ 2. Haoussa         │    │
          │ 3. Dioula          │    │
          │ 4. Peul            │    │
          │ 5. Wolof           │    │
          └─────────┬──────────┘    │
                    ▼               │
          ┌────────────────────┐    │
          │  SAISIE DU NOM     │    │
          │ Entrez votre nom:  │    │
          └─────────┬──────────┘    │
                    └───────┬───────┘
                            ▼
                  ┌───────────────────────┐
                  │   ÉCRAN ACCUEIL       │
                  │ Bonjour Awa, ...      │
                  │ 1. Acheter            │
                  │ 2. Mes commandes      │
                  │ 3. Mon panier         │
                  │ 4. Changer de langue  │
                  │ 0. Quitter            │
                  └───┬─────┬─────┬───────┘
            "1"       │     │"2"  │"3"
        ┌─────────────┘     │     └──────────────┐
        ▼                   ▼                     ▼
 ┌───────────────┐  ┌──────────────┐     ┌────────────────┐
 │  CATÉGORIES   │  │ MES COMMANDES│     │   MON PANIER   │
 │  (paginé)     │  │   (paginé)   │     │ 1x Riz = 12000 │
 │ 1. Vivres     │  │ #102 PAYEE   │     │ Total: 12000   │
 │ 2. Hygiène    │  │ #098 LIVREE  │     │ 1. Valider     │
 │ 99. Suivant   │  │ 99. Suivant  │     │ 2. Vider       │
 │ 0. Retour     │  │ 0. Retour    │     │ 0. Retour      │
 └──────┬────────┘  └──────────────┘     └───────┬────────┘
   "1"  │                                    "1" │
        ▼                                        ▼
 ┌───────────────┐                     ┌────────────────────┐
 │   PRODUITS    │                     │   CONFIRMATION     │
 │   (paginé)    │                     │ Confirmer la       │
 │ 1. Riz 12000  │                     │ commande ?         │
 │ 2. Huile 3500 │                     │ Total: 12000 F     │
 │ 99. Suivant   │                     │ 1. Oui, valider    │
 │ 0. Retour     │                     │ 2. Non, annuler    │
 └──────┬────────┘                     └─────────┬──────────┘
   "1"  │                                    "1" │
        ▼                                        ▼
 ┌───────────────┐                     ┌────────────────────┐
 │  QUANTITÉ ?   │                     │   COMMANDE CRÉÉE   │
 │ (saisir un    │                     │ Code: A7K2M9       │
 │  nombre)      │                     │ Payez en agence    │
 └──────┬────────┘                     │      (END)         │
        ▼                              └────────────────────┘
   Ajouté au panier
   → retour ACCUEIL
```

---

## Détail des écrans

### Écran 0a — Choix de la langue (premier contact uniquement)
```
CON Langue / Language:
1. Francais
2. Haoussa
3. Dioula
4. Peul
5. Wolof
```
Les noms de langues sont écrits dans leur propre langue (le client n'a encore rien
choisi). La langue est mémorisée dans `CustomerUSSD.language`.

### Écran 0b — Saisie du nom (premier contact uniquement)
```
CON Entrez votre nom:
```
- 2 à 50 caractères, pas uniquement des chiffres.
- Stocké dans `CustomerUSSD.name` → sert à personnaliser l'accueil.

### Écran 1 — Accueil  (`text = ""` pour un client connu)
```
CON Bonjour Awa, bienvenue sur MTS Shop
1. Acheter
2. Mes commandes
3. Mon panier
4. Changer de langue
0. Quitter
```

### Écran 2 — Catégories (paginé)
```
CON Categories (page 1/1)
1. Vivres
2. Hygiene
3. Boissons
0. Retour
```

### Écran 3 — Produits d'une catégorie (paginé)
```
CON Vivres (page 1/2)
1. Farine 5kg - 4500 F
2. Haricot 1kg - 1500 F
3. Huile 1L - 3500 F
4. Mil 5kg - 3000 F
99. Suivant
0. Retour
```

### Écran 4 — Quantité
```
CON Riz 25kg - 12000 F
Stock: 40
Entrez la quantite:
```

### Écran 5 — Mon panier
```
CON Votre panier:
1x Riz 25kg = 12000 F
2x Huile = 7000 F
Total: 19000 F
1. Valider la commande
2. Vider le panier
0. Retour
```

### Écran 6 — Confirmation (avant création de la commande)
```
CON Confirmer la commande ?
1x Riz 25kg = 12000 F
2x Huile = 7000 F
Total: 19000 F
1. Oui, valider
2. Non, annuler
```
« Non » ramène au panier ; « Oui » crée la commande.

### Écran 7 — Commande créée / Code de paiement
```
END Commande #102 enregistree.
Montant: 19000 F
Code de paiement: A7K2M9
Presentez ce code en agence pour payer.
```

### Écran 8 — Mes commandes (paginé)
```
CON Vos commandes (page 1/1)
#102 - 19000 F - En attente de paiement
#098 - 8500 F - Livree
0. Retour
```

---

## Pagination (transversale)

| Touche | Action |
|---|---|
| `99` | Page suivante |
| `98` | Page précédente |
| `0` | Retour à l'écran parent |

Taille d'une page : **4 éléments** (`PAGE_SIZE`). Appliquée aux catégories, aux
produits et aux commandes. La page courante est mémorisée dans `USSDSession.context`.

---

## Gestion des erreurs (transversale)

| Cas | Comportement |
|---|---|
| Saisie non prévue (ex. `7` sur un menu à 4 options) | Réafficher le menu avec « Choix invalide » |
| Nom invalide (trop court, uniquement des chiffres) | « Nom invalide » + redemander |
| Quantité non numérique ou ≤ 0 | « Quantite invalide » + redemander |
| Quantité > stock | « Stock insuffisant (max N) » + redemander |
| Produit / catégorie devenu indisponible | Message + retour menu parent |
| Session expirée / **coupure réseau** | Nouvelle session repart de l'accueil, avec le message *« Panier en cours : N article(s) »* — le **panier est intact** (rattaché au client, pas à la session) |

---

## Notes de conception

- **Menus courts** : 160 caractères max par écran USSD → pagination indispensable.
- **Texte sans accents** dans les messages → compatibilité avec les téléphones basiques.
- **Numéro de téléphone = identité** du client : pas de login ni de PIN.
- Le **panier** est rattaché au **client** (`CustomerUSSD.cart`), et non à la session :
  la passerelle attribue un nouveau `sessionId` à chaque appel, donc un panier stocké
  dans la session serait perdu à la moindre coupure réseau. Un panier abandonné expire
  au bout de 24 h (`USSD_CART_TTL_HOURS`).
- La **langue et le nom** sont mémorisés (`CustomerUSSD`) : le client ne les ressaisit
  jamais.
