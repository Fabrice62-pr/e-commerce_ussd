# Document de la Phase 4 — Intégration Africa's Talking

> Objectif de la phase : connecter le moteur USSD (développé en Phase 3) à la
> passerelle **Africa's Talking** (environnement Sandbox), et tester le menu depuis
> le simulateur USSD d'Africa's Talking, comme le ferait un vrai téléphone.

---

## 1. Résultat obtenu

Le parcours complet fonctionne **de bout en bout** :

```
Simulateur Africa's Talking  →  Internet  →  tunnel ngrok  →  Django (Docker)  →  réponse
```

Le menu « Bienvenue sur MTS Shop » s'affiche dans le simulateur USSD d'Africa's
Talking, et un achat complet crée une commande réelle en base avec son code de
paiement.

## 2. Le problème à résoudre : exposer un serveur local à Internet

Notre serveur Django tourne en local (`localhost:8000`), donc invisible depuis
Internet. Or Africa's Talking, service en ligne, doit pouvoir **appeler notre
webhook** à chaque interaction. Solution : un **tunnel** qui crée une adresse
publique temporaire redirigeant le trafic vers `localhost:8000`.

```
Africa's Talking  ──►  https://XXXX.ngrok-free.dev  ──►  localhost:8000 (Django)
   (Internet)              (tunnel ngrok public)            (machine locale)
```

## 3. Mise en place du tunnel (ngrok)

### Installation
```powershell
winget install --id ngrok.ngrok
```

> ⚠️ La version fournie par winget (3.3.1) était trop ancienne (le compte exige
> ≥ 3.20.0, erreur `ERR_NGROK_121`). Mise à jour nécessaire :
> ```powershell
> ngrok update
> ```
> Version obtenue : **3.39.8**.

### Authentification (une seule fois)
Créer un compte gratuit sur https://dashboard.ngrok.com, récupérer l'**authtoken**
puis :
```powershell
ngrok config add-authtoken <VOTRE_TOKEN>
```

### Lancer le tunnel
```powershell
ngrok http 8000
```
ngrok affiche alors une adresse publique, par exemple :
`https://amaretto-umbrella-endurance.ngrok-free.dev`

## 4. Ajustement côté Django

Django n'accepte que les hôtes listés dans `ALLOWED_HOSTS`. On a ajouté les domaines
ngrok dans le fichier `.env` :
```
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,.ngrok-free.app,.ngrok-free.dev,.ngrok.io
```
> Le préfixe `.` autorise tous les sous-domaines (ex. `xxxx.ngrok-free.dev`).
> Après modification du `.env`, redémarrer : `docker compose up -d`.

Le webhook `/ussd/callback/` est déjà `@csrf_exempt` (Phase 3), donc aucune
protection CSRF ne bloque les appels externes d'Africa's Talking.

## 5. Configuration du canal USSD dans Africa's Talking (Sandbox)

1. Se connecter sur https://account.africastalking.com/ et passer en **Sandbox**.
2. Menu **USSD → Create Channel** (« Créer un canal USSD »).
3. Renseigner :
   - **Code de service partagé** : `*384#`
   - **Chaîne** (suffixe) : un nombre au choix, ex. `12345`
     → le code complet devient **`*384*12345#`**
   - **URL de rappel (Callback URL)** :
     `https://<votre-tunnel>.ngrok-free.dev/ussd/callback/`
4. Cliquer sur **Créer un canal**.

## 6. Test dans le simulateur

1. Menu **Launch Simulator** dans Africa's Talking.
2. Choisir le numéro de téléphone de test, lancer le simulateur.
3. Composer le code (ex. `*384*12345#`) → le menu « Bienvenue sur MTS Shop » apparaît.
4. Naviguer : Acheter → catégorie → produit → quantité → panier → valider.
5. Un code de paiement (6 caractères) s'affiche ; la commande apparaît dans l'admin.

### Vérification effectuée en amont (via le tunnel, avant le simulateur)
```bash
curl -X POST https://<tunnel>.ngrok-free.dev/ussd/callback/ \
     -d "sessionId=tunneltest1" -d "phoneNumber=+22790000090" -d "text="
# → CON Bienvenue sur MTS Shop ...
```
Réponse conforme : le webhook est bien joignable depuis Internet. ✅

## 7. Points d'attention

- **URL ngrok temporaire** : sur le plan gratuit, l'adresse change à chaque
  redémarrage de ngrok. Il faut alors mettre à jour la Callback URL dans Africa's
  Talking. (Une adresse fixe est possible avec un domaine ngrok réservé ou un plan
  payant.)
- **Garder le tunnel actif** pendant toute la durée des tests.
- **Sécurité de l'authtoken** : c'est un secret personnel ; ne jamais le versionner
  (il reste dans `ngrok.yml`, hors du dépôt).

## 8. Prochaine étape — Phase 5

Implémenter le **paiement** : une action d'administration (ou vue agent) qui valide
une commande à partir de son code de paiement, passe le statut à `PAYEE`, marque
`is_paid = True` et **décrémente le stock** des produits commandés.
