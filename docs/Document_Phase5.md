# Document de la Phase 5 — Paiement (validation & décrément du stock)

> Objectif de la phase : permettre à un agent / administrateur de **valider le
> paiement** d'une commande à partir de son code de paiement. La validation fait
> passer la commande au statut `PAYEE`, met `is_paid = True` et **décrémente le
> stock** des produits (décision de conception : le stock baisse au paiement, pas à
> la création de la commande).

---

## 1. Résultat obtenu

- Une méthode métier `Order.valider_paiement()` centralise toute la logique.
- Une **action dans l'admin** permet de valider une ou plusieurs commandes.
- Une **commande en ligne** `valider_paiement <code>` reproduit le geste de l'agent
  au comptoir (et sert aux tests).
- Les cas d'erreur (déjà payée, stock insuffisant) sont gérés proprement, sans
  effet de bord (opération atomique).

## 2. Logique métier — `Order.valider_paiement()`

Fichier : `orders/models.py`.

Étapes (dans une **transaction atomique**) :
1. **Verrouille** la commande (`select_for_update`) pour éviter une double
   validation concurrente.
2. Si la commande est **déjà payée** → lève `DejaPayeeError`.
3. **Vérifie le stock** de chaque ligne ; si insuffisant → lève
   `StockInsuffisantError` (rien n'est modifié).
4. **Décrémente le stock** de chaque produit (décrément atomique via `F("stock") - quantité`).
5. Passe la commande à `status = PAYEE`, `is_paid = True`.

Exceptions dédiées :
- `PaiementError` (base)
- `DejaPayeeError`
- `StockInsuffisantError`

> **Atomicité** : en cas d'erreur (ex. stock insuffisant sur une ligne), aucune
> modification n'est appliquée — ni le stock, ni le statut. La commande reste
> `EN_ATTENTE`.

## 3. Action d'administration

Fichier : `orders/admin.py`.

Action **« Valider le paiement (→ PAYEE, décrémente le stock) »** disponible dans la
liste des commandes.

**Workflow agent :**
1. Rechercher la commande par son **code de paiement** (champ de recherche de l'admin).
2. Cocher la commande.
3. Choisir l'action « Valider le paiement » et l'exécuter.

Les résultats (succès, déjà payée, stock insuffisant) sont affichés en messages.

## 4. Commande en ligne (workflow agent / tests)

```bash
docker compose exec web python manage.py valider_paiement A8A7FZ
```
Réponse en cas de succès :
```
Paiement validé pour la commande #10 (montant 10500 F). Statut : Payée. Stock décrémenté.
```
En cas de code inconnu : `CommandError: Aucune commande trouvée pour le code « ... ».`

## 5. Vérifications effectuées

| Cas testé | Résultat |
|---|---|
| **Paiement nominal** (2 Riz) | statut `PAYEE`, `is_paid=True`, stock 40 → 38 ✅ |
| **Double validation** | refusée (`DejaPayeeError`) ✅ |
| **Stock insuffisant** (100 demandés / 38 dispo) | refusé, **stock inchangé**, commande non payée ✅ |
| **Validation via CLI** (code `A8A7FZ`) | validée, stock Huile 60 → 57 ✅ |
| **Code inexistant** | erreur claire ✅ |

## 6. Remarque technique

Les montants (`line_total`, `total_amount`) sont des `PositiveIntegerField`, soit un
entier PostgreSQL (max ~2,1 milliards). Largement suffisant pour des commandes
réalistes en XOF. Une quantité absurde (ex. 999 999 unités) peut théoriquement
dépasser cette borne — cas ignoré pour un prototype, mais à garder en tête pour une
mise à l'échelle (passer en `BigIntegerField` si nécessaire).

## 7. Prochaine étape — Phase 6

Mettre en place les **rapports** pour l'administrateur : chiffre d'affaires,
nombre de commandes, répartition par statut, produits les plus vendus — sous forme
d'une page de tableau de bord simple.
