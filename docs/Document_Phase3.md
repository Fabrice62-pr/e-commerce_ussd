# Document de la Phase 3 — Moteur USSD

> Objectif de la phase : implémenter le moteur de menu USSD (navigation
> consultation → commande → code de paiement), exposé par un webhook, et
> testable en local avant l'intégration d'Africa's Talking (Phase 4).

---

## 1. Résultat obtenu

- Un **moteur de menu USSD** complet gère tout le parcours client :
  `Accueil → Catégories → Produits → Quantité → Panier → Validation → Code de paiement`.
- Un **webhook** (`/ussd/callback/`) reçoit les requêtes au format Africa's Talking
  et répond en `CON` / `END`.
- Un **simulateur en ligne de commande** permet de tester tout le parcours sans
  connexion externe.
- Le parcours d'achat complet a été vérifié : il crée une vraie commande en base
  avec son code de paiement.

## 2. Comment fonctionne l'USSD (rappel)

L'USSD est **sans état** : à chaque touche pressée, la passerelle rappelle notre
serveur en renvoyant **tout l'historique saisi** (ex. `text = "1*3*3*2"`). Notre
moteur :
1. lit uniquement la **dernière saisie** (`text.split("*")[-1]`) ;
2. s'appuie sur l'**état mémorisé** (`USSDSession.state`) pour savoir quel écran
   afficher ;
3. répond avec un préfixe :
   - `CON ...` → la session continue (on attend une saisie) ;
   - `END ...` → la session se termine.

C'est une **machine à états**.

## 3. Fichiers créés / modifiés

| Fichier | Rôle |
|---|---|
| `ussd/engine.py` | **Le moteur** : tous les écrans et la logique de navigation |
| `ussd/views.py` | Le **webhook** `ussd_callback` (reçoit le POST de la passerelle) |
| `ussd/urls.py` | Route `/ussd/callback/` |
| `config/urls.py` | Inclusion des URLs de l'app `ussd` |
| `ussd/models.py` | Ajout du champ `context` (mémorise la correspondance numéro affiché ↔ objet) |
| `ussd/migrations/0002_ussdsession_context.py` | Migration du champ `context` |
| `ussd/management/commands/ussd_sim.py` | **Simulateur** de téléphone en ligne de commande |

## 4. Les écrans (machine à états)

| État | Écran | Choix possibles |
|---|---|---|
| `HOME` | Accueil | 1 Acheter, 2 Mes commandes, 3 Mon panier, 0 Quitter |
| `CATEGORIES` | Liste des catégories | 1..N catégorie, 0 Retour |
| `PRODUCTS` | Produits d'une catégorie | 1..N produit, 0 Retour |
| `QUANTITY` | Saisie de la quantité | un nombre |
| `CART` | Panier récapitulatif | 1 Valider, 2 Vider, 0 Retour |
| `MY_ORDERS` | Mes commandes | 0 Retour |

### Points clés de la logique
- **Correspondance numéro ↔ objet** : quand on affiche une liste dynamique
  (catégories, produits), on mémorise les identifiants dans `session.context`
  (ex. `{"product_ids": [5, 8, 12]}`). Le choix `2` sélectionne alors l'objet
  d'identifiant `8`, indépendamment de l'ordre d'affichage.
- **Panier persistant** : stocké dans `USSDSession.cart` (JSON), il survit aux
  expirations de session. L'ajout d'un produit déjà présent **fusionne** les quantités.
- **Contrôles de saisie** : choix hors menu → « Choix invalide » ; quantité non
  numérique ou ≤ 0 → « Quantite invalide » ; quantité > stock → « Stock insuffisant
  (max N) ». La session ne plante jamais.
- **Validation de commande** (`_validate_order`, transaction atomique) : crée le
  `CustomerUSSD` (si nouveau), l'`Order` et ses `OrderItem` (prix figé), recalcule le
  total, vide le panier, et renvoie le **code de paiement** (`END`).
- **Texte sans accents** dans les menus → compatibilité maximale avec les téléphones
  basiques.

## 5. Le webhook

`POST /ussd/callback/` (form-encoded), paramètres attendus :
`sessionId`, `phoneNumber`, `text`. Réponse en texte brut (`CON`/`END`).
La vue est `@csrf_exempt` car la passerelle externe ne fournit pas de jeton CSRF.

## 6. Le simulateur de téléphone

```bash
docker compose exec web python manage.py ussd_sim
docker compose exec web python manage.py ussd_sim --phone +22790000099
```

Il imite Africa's Talking : à chaque saisie, il accumule l'historique séparé par
`*` et l'envoie au moteur, puis affiche la réponse comme un écran de téléphone.

> ⚠️ À lancer dans un terminal **interactif** (il attend vos saisies au clavier).

## 7. Vérifications effectuées

### a) Parcours d'achat complet (scripté)
Accueil → Acheter → Vivres → Riz 25kg → quantité 2 → Panier → Valider :
- Commande créée en base (#2), code `MTS-XXXX` généré ;
- Total = 24000 F (2 × 12000), ligne correcte ;
- Réponse finale `END` avec le code de paiement. ✅

### b) Webhook HTTP (comme Africa's Talking)
```bash
curl -X POST http://localhost:8000/ussd/callback/ \
     -d "sessionId=httptest1" -d "phoneNumber=+22790000061" -d "text="
# → CON Bienvenue sur MTS Shop ...

curl -X POST http://localhost:8000/ussd/callback/ \
     -d "sessionId=httptest1" -d "phoneNumber=+22790000061" -d "text=1"
# → CON Categories: ...
```
Réponses conformes. ✅

## 8. Prochaine étape — Phase 4

Intégrer la **passerelle Africa's Talking (sandbox)** : configurer le compte,
exposer notre webhook à Internet (ex. tunnel) et tester le menu depuis le
simulateur USSD d'Africa's Talking. (Accompagnement prévu pour la prise en main
du compte.)
