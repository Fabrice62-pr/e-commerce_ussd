# Document des améliorations (avant Phase 7)

> Cinq améliorations apportées au prototype après la Phase 6, sur l'axe
> **expérience utilisateur et inclusion** :
> 1. Multi-langue (5 langues) · 2. Enregistrement du nom du client ·
> 3. Pagination · 4. Écran de confirmation · 5. Alerte stock bas (admin).

---

## 1. Multi-langue (français + 4 langues d'Afrique de l'Ouest)

### Langues supportées
| Code | Langue |
|---|---|
| `fr` | Français (langue de référence) |
| `ha` | Haoussa |
| `dyu` | Dioula |
| `ff` | Peul |
| `wo` | Wolof |

### Comment c'est fait
- **Messages de l'interface** : dictionnaire dans `ussd/translations.py`.
  La fonction `t(clé, langue, **variables)` renvoie le message traduit, avec
  **repli automatique sur le français** si la traduction est vide (aucun plantage).
- **Noms de catégories et de produits** : champs traduits en base
  (`name_ha`, `name_dyu`, `name_ff`, `name_wo`) sur `Category` et `Product`,
  remplis depuis l'admin. La méthode `get_name(langue)` applique le même repli.
- **Choix de la langue** : écran affiché **au tout premier appel** d'un nouveau
  numéro. Mémorisé dans `CustomerUSSD.language` → les sessions suivantes
  s'affichent directement dans la langue du client.
- Une option **« Changer de langue »** est disponible dans le menu d'accueil.

> ⚠️ **Note de qualité** : les traductions doivent être **relues par des locuteurs
> natifs**. L'architecture supporte les 5 langues ; la justesse linguistique relève
> d'une validation humaine.

### Ajouter une langue plus tard
1. Ajouter le code dans `LANGUAGES` (`ussd/translations.py`) et remplir les messages.
2. Ajouter le code dans `CustomerUSSD.Language` (`orders/models.py`).
3. Ajouter un champ `name_<code>` sur `Category` et `Product` + migration.

## 2. Enregistrement du nom du client

Au **premier contact**, après le choix de la langue, le client saisit son nom
(stocké dans `CustomerUSSD.name`). Le menu l'accueille ensuite par son prénom
(« Bonjour Awa, bienvenue sur MTS Shop »).

- Validation : 2 à 50 caractères, pas uniquement des chiffres.
- Le client est désormais **créé dès la première interaction USSD** (et non plus
  seulement à la première commande) : nécessaire pour mémoriser langue et nom.

## 3. Pagination des listes

Les listes longues sont découpées en pages de **4 éléments** (`PAGE_SIZE`) :

```
CON Vivres (page 1/2)
1. Farine 5kg - 4500 F
2. Haricot 1kg - 1500 F
3. Huile 1L - 3500 F
4. Mil 5kg - 3000 F
99. Suivant
0. Retour
```

- **`99`** = page suivante · **`98`** = page précédente · **`0`** = retour.
- Appliquée aux **catégories**, aux **produits** et à **mes commandes**.
- La page courante est mémorisée dans `USSDSession.context`.
- Motivation : un écran USSD est limité (~160 caractères) — sans pagination, une
  catégorie de 15 produits déborderait.

## 4. Écran de confirmation avant validation

Le client ne crée plus une commande d'un seul clic : un **récapitulatif** lui est
présenté pour éviter les erreurs.

```
CON Confirmer la commande ?
2x Huile 1L = 7000 F
Total: 7000 F
1. Oui, valider
2. Non, annuler
```
Nouvel état `CONFIRM` dans la machine à états ; « Non » ramène au panier.

## 5. Alerte stock bas (côté administrateur)

- Nouveau champ **`Product.low_stock_threshold`** (seuil **par produit**, défaut 5)
  et propriété `is_low_stock` (`stock ≤ seuil`).
- **Dans l'admin (Produits)** :
  - une **pastille** de couleur : 🔴 `RUPTURE` (stock 0) · 🟠 `STOCK BAS` · 🟢 `OK` ;
  - un **filtre « Niveau de stock »** (rupture / stock bas / suffisant) ;
  - le seuil est éditable directement depuis la liste.
- **Dans les rapports** : une carte **« Produits en stock bas »** + un **tableau
  d'alerte** listant les produits concernés (stock restant, seuil, état).

---

## Fichiers créés / modifiés

| Fichier | Modification |
|---|---|
| `ussd/translations.py` | 🆕 Dictionnaire des messages (5 langues) + fonction `t()` |
| `ussd/engine.py` | 🔄 Refonte : états `LANGUAGE` et `NAME`, pagination, état `CONFIRM`, tous les textes traduits |
| `catalog/models.py` | Mixin `TranslatedNameMixin` (noms traduits) + `low_stock_threshold` + `is_low_stock` |
| `orders/models.py` | `CustomerUSSD.language` (5 langues) |
| `catalog/admin.py` | Pastille d'alerte, filtre « Niveau de stock », champs de traduction |
| `orders/admin.py` | Colonne et filtre « Langue » du client |
| `orders/reports.py` | Comptage + liste des produits en stock bas |
| `templates/orders/rapports.html` | Carte + tableau d'alerte stock bas |
| `catalog/management/commands/seed_demo.py` | 3 produits supplémentaires (pour illustrer la pagination) |

Migrations : `catalog/0002_*` (traductions + seuil), `orders/0002_customerussd_language`.

## Vérifications effectuées

Parcours complet simulé pour un **nouveau numéro**, en **haoussa** :

| Étape | Résultat |
|---|---|
| Choix de la langue | `Langue / Language: 1. Francais 2. Haoussa …` ✅ |
| Saisie du nom | `Shigar da sunanka:` → *Na gode, Awa Diallo!* ✅ |
| Menu d'accueil traduit | `1. Sayi · 2. Umarnaina · 3. Kayan da na zaba …` ✅ |
| Pagination (7 produits) | `Vivres (shafi 1/2)` → `99` suivant → `98` précédent ✅ |
| Écran de confirmation | `Tabbatar da odar?` → `1. Eh, tabbatar / 2. A'a, soke` ✅ |
| Commande créée | Commande #14, code `TRY95S` ✅ |
| Langue mémorisée | `CustomerUSSD.language = "ha"` ✅ |

Alerte stock bas :

| Test | Résultat |
|---|---|
| Sucre 1kg : stock 3 / seuil 5 | `is_low_stock = True` → **STOCK BAS** ✅ |
| Thé : stock 0 | **RUPTURE**, et **non proposé** au client USSD ✅ |
| Rapports | carte + tableau d'alerte affichés (HTTP 200) ✅ |
| Admin produits | pastilles + filtre « Niveau de stock » présents ✅ |

## Prochaine étape — Phase 7

Documentation technique, guide utilisateur (admin + client USSD), guide
d'installation, et vérification finale avant la démonstration à MTS.
