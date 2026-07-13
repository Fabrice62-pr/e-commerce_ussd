"""Traductions des messages du menu USSD.

╔══════════════════════════════════════════════════════════════════════════════╗
║  FICHIER À COMPLÉTER PAR UN LOCUTEUR NATIF                                    ║
║                                                                              ║
║  Le français ("fr") est la langue de référence : il est complet.              ║
║  Les autres langues ("ha", "dyu", "ff", "wo") sont VIDES ("").                ║
║                                                                              ║
║  → Il suffit de remplir les chaînes vides pour activer une langue.            ║
║  → Une chaîne vide retombe AUTOMATIQUEMENT sur le français (aucun plantage).  ║
║                                                                              ║
║  Règles de rédaction (important pour l'USSD) :                                ║
║   - messages COURTS (un écran USSD ≈ 160 caractères) ;                        ║
║   - PAS d'accents ni de caractères spéciaux (compatibilité téléphones basiques);║
║   - garder les {variables} entre accolades telles quelles.                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

# Langues proposées au client (ordre d'affichage dans le menu de choix).
LANGUAGES = [
    ("fr", "Francais"),
    ("ha", "Haoussa"),
    ("dyu", "Dioula"),
    ("ff", "Peul"),
    ("wo", "Wolof"),
]

MESSAGES = {
    # ---------------------------------------------------------------- Accueil
    "home_greeting": {
        "fr": "Bonjour {name}, bienvenue sur MTS Shop",
        "ha": "Sannu {name}, barka da zuwa MTS Shop.", "dyu": "I ni sɔgɔma {name} Aw ni ce MTS ka magazɛn na ", "ff": "On njaaraama {name}, on njaaraama e MTS Shop.", "wo": "Nanga def {name}, dalal jàmm ci MTS Shop.",
    },
    "menu_buy": {
        "fr": "Acheter",
        "ha": "Sayi", "dyu": "San", "ff": "Soodugo", "wo": "Jën",
    },
    "menu_orders": {
        "fr": "Mes commandes",
        "ha": "Umarnaina", "dyu": "Nne ka cikanw", "ff": "Jamirooje am", "wo": "Samay komànd",
    },
    "menu_cart": {
        "fr": "Mon panier",
        "ha": "Kayan da na zaba", "dyu": "Nne ka wotoro", "ff": "Woto am", "wo": "Sama wagon",
    },
    "menu_language": {
        "fr": "Changer de langue",
        "ha": "Canza harshe", "dyu": "Kaan yɛlɛma", "ff": "Waylu ɗemngal", "wo": "Soppi làkk",
    },
    "menu_quit": {
        "fr": "Quitter",
        "ha": "Don tafiya", "dyu": "Ka taga", "ff": "Ngam yahde", "wo": "Ngir dem",
    },
    "goodbye": {
        "fr": "Merci, a bientot !",
        "ha": "Na gode, sai mun sake haduwa nan ba da jimawa ba.", "dyu": "I ni ce, an bena ɲɔgɔn ye joona.", "ff": "On njaaraama, nji'en ko ɓooyaani.", "wo": "Jërëjëf, nu gise ci lu yaggul dara.",
    },

    # ------------------------------------------------ Premier contact (nom)
    "ask_name": {
        "fr": "Entrez votre nom:",
        "ha": "Shigar da sunanka:", "dyu": "I tɔgɔ sɛbɛn:", "ff": "Winndu innde maa:", "wo": "Bindal sa tur:",
    },
    "invalid_name": {
        "fr": "Nom invalide.",
        "ha": "Sunan da bai dace ba", "dyu": "Tɔgɔ min bɛnnin tɛ", "ff": "Innde nde sellaani", "wo": "Tur bu baaxul",
    },
    "name_saved": {
        "fr": "Merci {name} !",
        "ha": "Na gode, {name}!", "dyu": "I ni ce, {name}!", "ff": "On njaaraama, {name}!", "wo": "Jërëjëf, {name}!",
    },

    # ------------------------------------------------------------- Langue
    "language_changed": {
        "fr": "Langue modifiee.",
        "ha": "An canza harshe", "dyu": "Kaan yɛlɛmana", "ff": "Ɗemngal wayliima", "wo": "Làkk wi soppiku na",
    },

    # -------------------------------------------------------- Navigation
    "back": {
        "fr": "Retour",
        "ha": "Baya", "dyu": "Kɔfɛ", "ff": "Bawo", "wo": "Ci gànnaaw",
    },
    "next": {
        "fr": "Suivant",
        "ha": "Biye da", "dyu": "Nata", "ff": "Tokki", "wo": "Topp",
    },
    "prev": {
        "fr": "Precedent",
        "ha": "na baya", "dyu": "Kɔfɛ", "ff": "Bawo", "wo": "Ci gànnaaw",
    },
    "page": {
        "fr": "page {page}/{total}",
        "ha": "shafi {page}/{total}", "dyu": "ɲɛɛ {page}/{total}", "ff": "hello {page}/{total}", "wo": "xët {page}/{total}",
    },
    "invalid_choice": {
        "fr": "Choix invalide.",
        "ha": "Zabi mara inganci.", "dyu": "Sugandili min tɛ tiɲɛn ye.", "ff": "Suɓngo ngo moƴƴaani.", "wo": "Tanneef bu baaxul.",
    },

    # -------------------------------------------------- Catalogue / produits
    "categories_title": {
        "fr": "Categories",
        "ha": "Rukuni", "dyu": "Suguya", "ff": "Geeɓe", "wo": "Tolluwaay",
    },
    "no_category": {
        "fr": "Aucune categorie disponible.",
        "ha": "Babu rukuni da zaa samar da.", "dyu": "Suguya min bɛnnin tɛ", "ff": "Geeɓe nde sellaani", "wo": "Tolluwaay bu yamoo",
    },
    "no_product": {
        "fr": "Aucun produit disponible.",
        "ha": "Babu kayayyakin da ake da su", "dyu": "Fɛɛn si tɛ sɔrɔ", "ff": "Alaa geɗe keɓaaɗe", "wo": "Amul produit",
    },
    "stock": {
        "fr": "Stock: {stock}",
        "ha": "Adadi: {stock}", "dyu": "Stoki: {stock}", "ff": "Restoraaji: {stock}", "wo": "Stock: {stock}",
    },
    "enter_quantity": {
        "fr": "Entrez la quantite:",
        "ha": "Shigar da adadin:", "dyu": "A hakɛ sɛbɛ:", "ff": "Winndu keewal ngal:", "wo": "Bindal limu:",
    },
    "invalid_quantity": {
        "fr": "Quantite invalide.",
        "ha": "Adadin da ba daidai ba.", "dyu": "Hakɛ min tɛ bɛn.", "ff": "Limre nde moƴƴaani.", "wo": "Bariwaay bu baaxul.",
    },
    "insufficient_stock": {
        "fr": "Stock insuffisant (max {max}).",
        "ha": "Yawan kayan bai isa ba (max {max}).", "dyu": "Fɛɛn minw be sɔrɔ, u man ca (max {max}).", "ff": "Restoraaji ɗi ŋakkaani (max {max}).", "wo": "Stock bi doyul (max {max}).",
    },
    "added_to_cart": {
        "fr": "{qty} x {name} ajoute au panier.",
        "ha": "An ƙara {qty} x {name} a cikin kwandon siyayya.", "dyu": "{qty} x {name} farala wotoro kan.", "ff": "{qty} x {name} ɓeydaama e jolngo.", "wo": "{qty} x {name} yokk nañu ko ci pañe bi.",
    },

    # ------------------------------------------------------------- Panier
    "cart_title": {
        "fr": "Votre panier:",
        "ha": "Kayan da ka zaba:", "dyu": "I ka wotoro:", "ff": "Woto maa:", "wo": "Sa pañe:",
    },
    "cart_empty": {
        "fr": "Votre panier est vide.",
        "ha": "Kayan da ka zaba ta kuma.", "dyu": "I ka wotoro ta kuma.", "ff": "Woto maa ta kuma.", "wo": "Sa pañe: ta kuma.",
    },
    "cart_total": {
        "fr": "Total: {total} F",
        "ha": "Jama: {total} F", "dyu": "Sɔrɔ: {total} F", "ff": "Togal: {total} F", "wo": "Jamm: {total} F",
    },
    "cart_validate": {
        "fr": "Valider la commande",
        "ha": "Tabbatar da oda", "dyu": "Aw ye komandi sɛgɛsɛgɛ", "ff": "Tabintin yamiroore", "wo": "Firndelal komànd bi",
    },
    "cart_clear": {
        "fr": "Vider le panier",
        "ha": "Rufe kwandon siyayya", "dyu": "Sɔrɔ wotoro", "ff": "Pakka woto", "wo": "Firndelal pañe bi",
    },
    # Affiché au retour du client si un panier non validé l'attend (coupure réseau,
    # session expirée...). À REMPLIR dans les 4 autres langues.
    "cart_restored": {
        "fr": "Panier en cours: {n} article(s).",
        "ha": "", "dyu": "", "ff": "", "wo": "",
    },
    "cart_cleared": {
        "fr": "Panier vide.",
        "ha": "Kayan da ka zaba ta kuma.", "dyu": "I ka wotoro ta kuma.", "ff": "Woto maa ta kuma.", "wo": "Sa pañe: ta kuma.",
    },

    # ------------------------------------------------------- Confirmation
    "confirm_title": {
        "fr": "Confirmer la commande ?",
        "ha": "Tabbatar da odar?", "dyu": "Yala i be komandi sɛmɛntiya wa?", "ff": "Tabitin yamiroore ndee?", "wo": "Firndeel komànd bi?",
    },
    "confirm_yes": {
        "fr": "Oui, valider",
        "ha": "Eh, tabbatar", "dyu": "Ɔnhɔn, a sɛmɛntiya", "ff": "Eey, tabitin", "wo": "Waaw, firndeel",
    },
    "confirm_no": {
        "fr": "Non, annuler",
        "ha": "A'a, soke", "dyu": "Ɔn ɔn, a bɔ yen", "ff": "Alaa, woppu", "wo": "Dédeet, fomm",
    },

    # ---------------------------------------------------------- Commande
    "order_created": {
        "fr": "Commande #{id} enregistree.",
        "ha": "Odar #{id} an rufe.", "dyu": "Komandi #{id} a sɔrɔ.", "ff": "Yamiroore #{id} a tabitin.", "wo": "Komànd #{id} a firndeel.",
    },
    "order_amount": {
        "fr": "Montant: {total} F",
        "ha": "Jama: {total} F", "dyu": "Sɔrɔ: {total} F", "ff": "Togal: {total} F", "wo": "Jamm: {total} F",
    },
    "order_code": {
        "fr": "Code de paiement: {code}",
        "ha": "Lambar biya: {code}", "dyu": "Sarali kode: {code}", "ff": "Kod yoɓde: {code}", "wo": "Kodu fay: {code}",
    },
    "order_instructions": {
        "fr": "Presentez ce code en agence pour payer.",
        "ha": "Duk da lambar biya cikin agence don kai.", "dyu": "Sɔrɔ wotoro ɲɛɛ cikin agence don kai.", "ff": "Pakka woto ndee cikin agence don kai.", "wo": "Firndelal kodu fay cikin agence don kai.",
    },
    "my_orders_title": {
        "fr": "Vos commandes",
        "ha": "Odar da kai", "dyu": "Komandi da kai", "ff": "Yamiroore da kai", "wo": "Komànd bi ci kai",
    },
    "no_orders": {
        "fr": "Aucune commande.",
        "ha": "Babu umarni.", "dyu": "Yamaruya tɛ yen.", "ff": "Alaa yamiroore.", "wo": "Amul komànd.",
    },

    # ------------------------------------------- Statuts (affichés au client)
    "status_EN_ATTENTE": {
        "fr": "En attente de paiement",
        "ha": "Ana cikin rubutu", "dyu": "A sɔrɔ ɲɛɛ", "ff": "A tabitin", "wo": "Ci kànti",
    },
    "status_PAYEE": {
        "fr": "Payee",
        "ha": "An biya", "dyu": "Sarala", "ff": "Yoɓɓi", "wo": "Fayda",
    },
    "status_PREPAREE": {
        "fr": "Preparee",
        "ha": "An rufe", "dyu": "Sɔrɔ", "ff": "Tabitin", "wo": "Firndeel",
    },
    "status_LIVREE": {
        "fr": "Livree",
        "ha": "Livery", "dyu": "Livery", "ff": "Livery", "wo": "Livery",
    },
    "status_ANNULEE": {
        "fr": "Annulee",
        "ha": "A'a, soke", "dyu": "Ɔn ɔn, a bɔ yen", "ff": "Alaa, woppu", "wo": "Dédeet, fomm",
    },
}


def t(key, lang="fr", **kwargs):
    """Renvoie le message `key` dans la langue `lang`.

    Repli automatique sur le français si la traduction est absente ou vide.
    Les variables éventuelles sont injectées via `.format()`.
    """
    entry = MESSAGES.get(key, {})
    text = entry.get(lang) or entry.get("fr") or key
    return text.format(**kwargs) if kwargs else text
