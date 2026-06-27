# Arbre des menus USSD — parcours client

> Convention de réponse de notre serveur :
> - `CON ...` → afficher le menu et **attendre** une saisie (session continue)
> - `END ...` → afficher le message final et **fermer** la session
>
> Rappel : à chaque touche, Africa's Talking nous renvoie **tout** ce que le client a
> tapé depuis le début, séparé par `*` (ex. `text = "1*2*3"`). On en déduit l'écran courant.

---

## Vue d'ensemble (schéma)

```
                       *384*XXXXX#
                            │
                  ┌─────────▼─────────┐
                  │   ÉCRAN ACCUEIL   │  (text = "")
                  │ 1. Acheter        │
                  │ 2. Mes commandes  │
                  │ 3. Mon panier     │
                  │ 0. Quitter        │
                  └───┬─────┬─────┬───┘
            "1"       │     │"2"  │"3"
        ┌─────────────┘     │     └──────────────┐
        ▼                   ▼                     ▼
 ┌───────────────┐  ┌──────────────┐     ┌────────────────┐
 │  CATÉGORIES   │  │ MES COMMANDES│     │   MON PANIER   │
 │ 1. Vivres     │  │ #102 PAYEE   │     │ 1x Riz = 12000 │
 │ 2. Hygiène    │  │ #098 LIVREE  │     │ Total: 12000   │
 │ 0. Retour     │  │ 0. Retour    │     │ 1. Valider     │
 └──────┬────────┘  └──────────────┘     │ 2. Vider       │
   "1"  │ (END)                          │ 0. Retour      │
        ▼                                └───────┬────────┘
 ┌───────────────┐                          "1" │
 │   PRODUITS    │                              ▼
 │ 1. Riz 12000  │                     ┌─────────────────┐
 │ 2. Huile 3500 │                     │  CONFIRMATION   │
 │ 0. Retour     │                     │ Commande créée  │
 └──────┬────────┘                     │ Code: MTS-7F3A  │
   "1"  │                              │ Payez en agence │
        ▼                              │     (END)       │
 ┌───────────────┐                     └─────────────────┘
 │  QUANTITÉ ?   │
 │ (saisir un    │
 │  nombre)      │
 └──────┬────────┘
   "2"  │
        ▼
   Ajouté au panier
   → retour ACCUEIL
```

---

## Détail des écrans

### Écran 0 — Accueil  (`text = ""`)
```
CON Bienvenue sur MTS Shop
1. Acheter
2. Mes commandes
3. Mon panier
0. Quitter
```
- `1` → Catégories
- `2` → Mes commandes
- `3` → Mon panier
- `0` → `END Merci, à bientôt !`

### Écran 1 — Catégories  (`text = "1"`)
```
CON Categories:
1. Vivres
2. Hygiene
3. ...
0. Retour
```
- `1..N` → Produits de la catégorie choisie
- `0` → retour Accueil

### Écran 2 — Produits  (`text = "1*1"`)
```
CON Vivres:
1. Riz 25kg - 12000 F
2. Huile 1L - 3500 F
0. Retour
```
- `1..N` → écran Quantité pour le produit choisi
- `0` → retour Catégories

### Écran 3 — Quantité  (`text = "1*1*1"`)
```
CON Riz 25kg - 12000 F
Stock: 40
Entrez la quantite:
```
- saisie d'un **nombre** → ajout au panier, message court puis retour Accueil
- saisie invalide / quantité > stock → message d'erreur, on redemande

### Écran 4 — Mon panier  (`text = "3"`)
```
CON Votre panier:
1x Riz 25kg = 12000 F
2x Huile = 7000 F
Total: 19000 F
1. Valider la commande
2. Vider le panier
0. Retour
```
- `1` → création commande + génération du code → écran Confirmation (END)
- `2` → vide le panier → retour Accueil
- `0` → retour Accueil
- panier vide → message « Panier vide » + retour Accueil

### Écran 5 — Confirmation / Code de validation
```
END Commande #102 enregistree.
Montant: 19000 F
Code de paiement: MTS-7F3A
Presentez ce code en agence pour payer.
```

### Écran 6 — Mes commandes  (`text = "2"`)
```
CON Vos commandes:
#102 - 19000 F - EN ATTENTE
#098 - 8500 F - LIVREE
0. Retour
```
- `0` → retour Accueil
- aucune commande → `CON Aucune commande.\n0. Retour`

---

## Gestion des erreurs (transversale)

| Cas | Comportement |
|---|---|
| Saisie non prévue (ex. `9` sur un menu à 3 options) | Réafficher le menu avec « Choix invalide » |
| Quantité non numérique ou ≤ 0 | « Quantite invalide » + redemander |
| Quantité > stock | « Stock insuffisant (max N) » + redemander |
| Produit/ catégorie devenu indisponible | Message + retour menu parent |
| Session expirée (timeout passerelle) | Nouvelle session repart de l'accueil ; panier conservé en base |

---

## Notes de conception

- **Menus courts** : 160 caractères max recommandés par écran USSD ; on reste concis.
- **Pagination** : si une catégorie a beaucoup de produits, prévoir `#. Suivant` (à ajouter en Phase 3 si besoin).
- **Numéro de téléphone** = identité du client : pas de login/PIN dans le prototype (à confirmer — voir specs Q4).
- Le **panier** est persistant côté serveur (`USSDSession`) pour survivre aux timeouts de session.
