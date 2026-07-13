"""
Moteur de menu USSD.

Principe (machine à états) :
- La passerelle (Africa's Talking) appelle notre serveur à CHAQUE touche pressée,
  en renvoyant tout l'historique saisi (ex. text = "1*2*3").
- On ne regarde que la DERNIÈRE saisie, et on s'appuie sur l'état mémorisé dans
  `USSDSession.state` pour savoir quel écran afficher.
- Chaque réponse commence par :
    "CON ..."  -> on continue (on attend une saisie)
    "END ..."  -> on termine (fin de session)

Parcours du premier contact (nouveau numéro) :
    Choix de la langue  ->  Saisie du nom  ->  Accueil

Tous les textes proviennent de `translations.py` (multi-langue avec repli sur
le français). Les listes longues sont paginées.
"""
import math

from django.db import transaction

from catalog.models import Category, Product
from orders.models import CustomerUSSD, Order, OrderItem

from .models import USSDSession
from .translations import LANGUAGES, t

# --- Identifiants des écrans (états) ---
LANGUAGE = "LANGUAGE"
NAME = "NAME"
HOME = "HOME"
CATEGORIES = "CATEGORIES"
PRODUCTS = "PRODUCTS"
QUANTITY = "QUANTITY"
CART = "CART"
CONFIRM = "CONFIRM"
MY_ORDERS = "MY_ORDERS"

# --- Pagination ---
PAGE_SIZE = 4          # éléments affichés par écran
NEXT_KEY = "99"        # touche « page suivante »
PREV_KEY = "98"        # touche « page précédente »
BACK_KEY = "0"         # touche « retour »


# =========================================================================
# Utilitaires
# =========================================================================
def con(text):
    """Réponse « continuer » (la session reste ouverte)."""
    return "CON " + text


def end(text):
    """Réponse « terminer » (la session se ferme)."""
    return "END " + text


def _to_index(choice, length):
    """Convertit une saisie '1'..'N' en index de liste 0..N-1, ou None si invalide."""
    if choice.isdigit():
        n = int(choice)
        if 1 <= n <= length:
            return n - 1
    return None


def _paginate(items, page):
    """Découpe une liste en pages. Retourne (éléments de la page, page, nb_pages)."""
    total_pages = max(1, math.ceil(len(items) / PAGE_SIZE))
    page = min(max(page, 1), total_pages)
    start = (page - 1) * PAGE_SIZE
    return items[start:start + PAGE_SIZE], page, total_pages


def _nav_lines(lang, page, total_pages):
    """Lignes de navigation (Suivant / Precedent / Retour) selon la page courante."""
    lines = []
    if page < total_pages:
        lines.append(f"{NEXT_KEY}. {t('next', lang)}")
    if page > 1:
        lines.append(f"{PREV_KEY}. {t('prev', lang)}")
    lines.append(f"{BACK_KEY}. {t('back', lang)}")
    return lines


# =========================================================================
# Point d'entrée
# =========================================================================
def process_ussd(session_id, phone_number, text):
    """Traite une requête USSD et renvoie la réponse texte (CON/END)."""
    session, _ = USSDSession.objects.get_or_create(
        session_id=session_id,
        defaults={"phone_number": phone_number},
    )
    # Le client est identifié (ou créé) dès la première interaction : on a besoin
    # de mémoriser sa langue et son nom.
    customer, _ = CustomerUSSD.objects.get_or_create(
        phone_number=session.phone_number
    )

    text = (text or "").strip()
    if text == "":
        # Début de session : premier contact (pas de nom) -> choix de la langue.
        if not customer.name:
            return show_language(session, customer, first_time=True)
        return show_home(session, customer)

    user_input = text.split("*")[-1].strip()

    handlers = {
        LANGUAGE: handle_language,
        NAME: handle_name,
        HOME: handle_home,
        CATEGORIES: handle_categories,
        PRODUCTS: handle_products,
        QUANTITY: handle_quantity,
        CART: handle_cart,
        CONFIRM: handle_confirm,
        MY_ORDERS: handle_my_orders,
    }
    handler = handlers.get(session.state or HOME, handle_home)
    return handler(session, customer, user_input)


# =========================================================================
# ÉCRAN : CHOIX DE LA LANGUE
# =========================================================================
def show_language(session, customer, first_time=False, prefix=""):
    session.state = LANGUAGE
    session.context = {"first_time": first_time}
    session.save()

    # Les noms de langues sont écrits dans leur propre langue : pas besoin de
    # traduction pour cet écran (le client n'a pas encore choisi).
    lines = ["Langue / Language:"]
    for i, (_code, label) in enumerate(LANGUAGES, start=1):
        lines.append(f"{i}. {label}")
    if not first_time:
        lines.append(f"{BACK_KEY}. {t('back', customer.language)}")
    return con(prefix + "\n".join(lines))


def handle_language(session, customer, choice):
    first_time = (session.context or {}).get("first_time", False)

    if not first_time and choice == BACK_KEY:
        return show_home(session, customer)

    index = _to_index(choice, len(LANGUAGES))
    if index is None:
        return show_language(
            session, customer, first_time=first_time,
            prefix=t("invalid_choice", customer.language) + "\n\n",
        )

    customer.language = LANGUAGES[index][0]
    customer.save(update_fields=["language"])

    # Premier contact : on enchaîne sur la saisie du nom.
    if not customer.name:
        return show_name(session, customer)
    return show_home(
        session, customer,
        prefix=t("language_changed", customer.language) + "\n\n",
    )


# =========================================================================
# ÉCRAN : SAISIE DU NOM (premier contact)
# =========================================================================
def show_name(session, customer, prefix=""):
    session.state = NAME
    session.save()
    return con(prefix + t("ask_name", customer.language))


def handle_name(session, customer, value):
    name = value.strip()
    # Un nom valide : 2 à 50 caractères, et pas uniquement des chiffres.
    if len(name) < 2 or len(name) > 50 or name.isdigit():
        return show_name(
            session, customer,
            prefix=t("invalid_name", customer.language) + "\n\n",
        )

    customer.name = name
    customer.save(update_fields=["name"])
    return show_home(
        session, customer,
        prefix=t("name_saved", customer.language, name=name) + "\n\n",
    )


# =========================================================================
# ÉCRAN : ACCUEIL
# =========================================================================
def show_home(session, customer, prefix=""):
    session.state = HOME
    session.save()
    lang = customer.language

    lines = [
        t("home_greeting", lang, name=customer.name),
        f"1. {t('menu_buy', lang)}",
        f"2. {t('menu_orders', lang)}",
        f"3. {t('menu_cart', lang)}",
        f"4. {t('menu_language', lang)}",
        f"0. {t('menu_quit', lang)}",
    ]
    return con(prefix + "\n".join(lines))


def handle_home(session, customer, choice):
    if choice == "1":
        return show_categories(session, customer, page=1)
    if choice == "2":
        return show_my_orders(session, customer, page=1)
    if choice == "3":
        return show_cart(session, customer)
    if choice == "4":
        return show_language(session, customer, first_time=False)
    if choice == "0":
        return end(t("goodbye", customer.language))
    return show_home(
        session, customer,
        prefix=t("invalid_choice", customer.language) + "\n\n",
    )


# =========================================================================
# ÉCRAN : CATÉGORIES (paginé)
# =========================================================================
def show_categories(session, customer, page=1, prefix=""):
    lang = customer.language
    categories = list(Category.objects.filter(is_active=True))
    if not categories:
        return show_home(session, customer, prefix=t("no_category", lang) + "\n\n")

    items, page, total_pages = _paginate(categories, page)

    lines = [f"{t('categories_title', lang)} ({t('page', lang, page=page, total=total_pages)})"]
    ids = []
    for i, category in enumerate(items, start=1):
        lines.append(f"{i}. {category.get_name(lang)}")
        ids.append(category.id)
    lines += _nav_lines(lang, page, total_pages)

    session.state = CATEGORIES
    session.context = {"category_ids": ids, "page": page}
    session.save()
    return con(prefix + "\n".join(lines))


def handle_categories(session, customer, choice):
    context = session.context or {}
    page = context.get("page", 1)

    if choice == BACK_KEY:
        return show_home(session, customer)
    if choice == NEXT_KEY:
        return show_categories(session, customer, page=page + 1)
    if choice == PREV_KEY:
        return show_categories(session, customer, page=page - 1)

    ids = context.get("category_ids", [])
    index = _to_index(choice, len(ids))
    if index is None:
        return show_categories(
            session, customer, page=page,
            prefix=t("invalid_choice", customer.language) + "\n\n",
        )
    return show_products(session, customer, ids[index], page=1)


# =========================================================================
# ÉCRAN : PRODUITS d'une catégorie (paginé)
# =========================================================================
def show_products(session, customer, category_id, page=1, prefix=""):
    lang = customer.language
    category = Category.objects.filter(id=category_id, is_active=True).first()
    if not category:
        return show_categories(
            session, customer, page=1, prefix=t("no_category", lang) + "\n\n"
        )

    products = list(category.products.filter(is_active=True, stock__gt=0))
    if not products:
        return show_categories(
            session, customer, page=1, prefix=t("no_product", lang) + "\n\n"
        )

    items, page, total_pages = _paginate(products, page)

    lines = [f"{category.get_name(lang)} ({t('page', lang, page=page, total=total_pages)})"]
    ids = []
    for i, product in enumerate(items, start=1):
        lines.append(f"{i}. {product.get_name(lang)} - {product.price} F")
        ids.append(product.id)
    lines += _nav_lines(lang, page, total_pages)

    session.state = PRODUCTS
    session.context = {"category_id": category_id, "product_ids": ids, "page": page}
    session.save()
    return con(prefix + "\n".join(lines))


def handle_products(session, customer, choice):
    context = session.context or {}
    category_id = context.get("category_id")
    page = context.get("page", 1)

    if choice == BACK_KEY:
        return show_categories(session, customer, page=1)
    if choice == NEXT_KEY:
        return show_products(session, customer, category_id, page=page + 1)
    if choice == PREV_KEY:
        return show_products(session, customer, category_id, page=page - 1)

    ids = context.get("product_ids", [])
    index = _to_index(choice, len(ids))
    if index is None:
        return show_products(
            session, customer, category_id, page=page,
            prefix=t("invalid_choice", customer.language) + "\n\n",
        )
    return show_quantity(session, customer, ids[index])


# =========================================================================
# ÉCRAN : QUANTITÉ
# =========================================================================
def show_quantity(session, customer, product_id, prefix=""):
    lang = customer.language
    product = Product.objects.filter(id=product_id).first()
    if not product or not product.is_available:
        return show_categories(
            session, customer, page=1, prefix=t("no_product", lang) + "\n\n"
        )

    context = session.context or {}
    context["product_id"] = product_id
    session.state = QUANTITY
    session.context = context
    session.save()

    menu = (
        f"{product.get_name(lang)} - {product.price} F\n"
        f"{t('stock', lang, stock=product.stock)}\n"
        f"{t('enter_quantity', lang)}"
    )
    return con(prefix + menu)


def handle_quantity(session, customer, value):
    lang = customer.language
    context = session.context or {}
    product_id = context.get("product_id")
    product = Product.objects.filter(id=product_id).first()
    if not product:
        return show_categories(
            session, customer, page=1, prefix=t("no_product", lang) + "\n\n"
        )

    if not value.isdigit() or int(value) <= 0:
        return show_quantity(
            session, customer, product_id,
            prefix=t("invalid_quantity", lang) + "\n\n",
        )

    quantity = int(value)
    if quantity > product.stock:
        return show_quantity(
            session, customer, product_id,
            prefix=t("insufficient_stock", lang, max=product.stock) + "\n\n",
        )

    _add_to_cart(session, product_id, quantity)
    return show_home(
        session, customer,
        prefix=t("added_to_cart", lang, qty=quantity, name=product.get_name(lang)) + "\n\n",
    )


def _add_to_cart(session, product_id, quantity):
    """Ajoute un produit au panier (fusionne si le produit y est déjà)."""
    cart = session.cart or []
    for item in cart:
        if item["product_id"] == product_id:
            item["qty"] += quantity
            break
    else:
        cart.append({"product_id": product_id, "qty": quantity})
    session.cart = cart
    session.save()


# =========================================================================
# ÉCRAN : PANIER
# =========================================================================
def _cart_lines(session, lang):
    """Retourne (lignes du panier, total)."""
    lines = []
    total = 0
    for item in session.cart or []:
        product = Product.objects.filter(id=item["product_id"]).first()
        if not product:
            continue
        line_total = product.price * item["qty"]
        total += line_total
        lines.append(f"{item['qty']}x {product.get_name(lang)} = {line_total} F")
    return lines, total


def show_cart(session, customer, prefix=""):
    lang = customer.language
    if not (session.cart or []):
        return show_home(session, customer, prefix=t("cart_empty", lang) + "\n\n")

    item_lines, total = _cart_lines(session, lang)
    lines = [t("cart_title", lang)] + item_lines
    lines.append(t("cart_total", lang, total=total))
    lines.append(f"1. {t('cart_validate', lang)}")
    lines.append(f"2. {t('cart_clear', lang)}")
    lines.append(f"0. {t('back', lang)}")

    session.state = CART
    session.save()
    return con(prefix + "\n".join(lines))


def handle_cart(session, customer, choice):
    lang = customer.language
    if choice == "1":
        return show_confirm(session, customer)      # écran de confirmation
    if choice == "2":
        session.cart = []
        session.save()
        return show_home(session, customer, prefix=t("cart_cleared", lang) + "\n\n")
    if choice == "0":
        return show_home(session, customer)
    return show_cart(session, customer, prefix=t("invalid_choice", lang) + "\n\n")


# =========================================================================
# ÉCRAN : CONFIRMATION (avant création de la commande)
# =========================================================================
def show_confirm(session, customer, prefix=""):
    lang = customer.language
    if not (session.cart or []):
        return show_home(session, customer, prefix=t("cart_empty", lang) + "\n\n")

    item_lines, total = _cart_lines(session, lang)
    lines = [t("confirm_title", lang)] + item_lines
    lines.append(t("cart_total", lang, total=total))
    lines.append(f"1. {t('confirm_yes', lang)}")
    lines.append(f"2. {t('confirm_no', lang)}")

    session.state = CONFIRM
    session.save()
    return con(prefix + "\n".join(lines))


def handle_confirm(session, customer, choice):
    if choice == "1":
        return _validate_order(session, customer)
    if choice == "2":
        return show_cart(session, customer)
    return show_confirm(
        session, customer,
        prefix=t("invalid_choice", customer.language) + "\n\n",
    )


@transaction.atomic
def _validate_order(session, customer):
    """Transforme le panier en commande et génère le code de paiement."""
    lang = customer.language
    cart = session.cart or []
    if not cart:
        return show_home(session, customer, prefix=t("cart_empty", lang) + "\n\n")

    order = Order.objects.create(customer=customer)
    for item in cart:
        product = Product.objects.filter(id=item["product_id"]).first()
        if not product:
            continue
        # Le prix unitaire est figé au moment de l'achat (prix courant du produit).
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=item["qty"],
            unit_price=product.price,
        )
    order.update_total()

    # Réinitialisation de la session (panier vidé).
    session.cart = []
    session.context = {}
    session.state = HOME
    session.save()

    message = "\n".join([
        t("order_created", lang, id=order.pk),
        t("order_amount", lang, total=order.total_amount),
        t("order_code", lang, code=order.validation_code),
        t("order_instructions", lang),
    ])
    return end(message)


# =========================================================================
# ÉCRAN : MES COMMANDES (paginé)
# =========================================================================
def show_my_orders(session, customer, page=1, prefix=""):
    lang = customer.language
    orders = list(customer.orders.all()[:20])

    session.state = MY_ORDERS
    if not orders:
        session.context = {"page": 1}
        session.save()
        return con(prefix + t("no_orders", lang) + f"\n{BACK_KEY}. {t('back', lang)}")

    items, page, total_pages = _paginate(orders, page)

    lines = [f"{t('my_orders_title', lang)} ({t('page', lang, page=page, total=total_pages)})"]
    for order in items:
        statut = t(f"status_{order.status}", lang)
        lines.append(f"#{order.pk} - {order.total_amount} F - {statut}")
    lines += _nav_lines(lang, page, total_pages)

    session.context = {"page": page}
    session.save()
    return con(prefix + "\n".join(lines))


def handle_my_orders(session, customer, choice):
    page = (session.context or {}).get("page", 1)

    if choice == BACK_KEY:
        return show_home(session, customer)
    if choice == NEXT_KEY:
        return show_my_orders(session, customer, page=page + 1)
    if choice == PREV_KEY:
        return show_my_orders(session, customer, page=page - 1)
    return show_my_orders(
        session, customer, page=page,
        prefix=t("invalid_choice", customer.language) + "\n\n",
    )
