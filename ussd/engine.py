"""
Moteur de menu USSD.

Principe (machine à états) :
- La passerelle (Africa's Talking) appelle notre serveur à CHAQUE touche pressée,
  en renvoyant tout l'historique saisi (ex. text = "1*2*3").
- On ne regarde que la DERNIÈRE saisie (le dernier segment), et on s'appuie sur
  l'état mémorisé dans `USSDSession.state` pour savoir quel écran afficher.
- Chaque réponse commence par :
    "CON ..."  -> on continue (on attend une saisie)
    "END ..."  -> on termine (fin de session)

Note : les menus sont volontairement en texte simple (sans accents) pour une
compatibilité maximale avec les téléphones basiques.
"""
from django.db import transaction

from catalog.models import Category, Product
from orders.models import CustomerUSSD, Order, OrderItem

from .models import USSDSession

# --- Identifiants des écrans (états) ---
HOME = "HOME"
CATEGORIES = "CATEGORIES"
PRODUCTS = "PRODUCTS"
QUANTITY = "QUANTITY"
CART = "CART"
MY_ORDERS = "MY_ORDERS"


# --- Petits utilitaires ---
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


# --- Point d'entrée ---
def process_ussd(session_id, phone_number, text):
    """Traite une requête USSD et renvoie la réponse texte (CON/END)."""
    session, _ = USSDSession.objects.get_or_create(
        session_id=session_id,
        defaults={"phone_number": phone_number},
    )

    text = (text or "").strip()
    if text == "":
        # Tout début de session : on affiche l'accueil.
        return show_home(session)

    # On ne traite que la dernière saisie de l'utilisateur.
    user_input = text.split("*")[-1].strip()

    handlers = {
        HOME: handle_home,
        CATEGORIES: handle_categories,
        PRODUCTS: handle_products,
        QUANTITY: handle_quantity,
        CART: handle_cart,
        MY_ORDERS: handle_my_orders,
    }
    handler = handlers.get(session.state or HOME, handle_home)
    return handler(session, user_input)


# =========================================================================
# ÉCRAN : ACCUEIL
# =========================================================================
def show_home(session, prefix=""):
    session.state = HOME
    session.save()
    menu = (
        "Bienvenue sur MTS Shop\n"
        "1. Acheter\n"
        "2. Mes commandes\n"
        "3. Mon panier\n"
        "0. Quitter"
    )
    return con(prefix + menu)


def handle_home(session, choice):
    if choice == "1":
        return show_categories(session)
    if choice == "2":
        return show_my_orders(session)
    if choice == "3":
        return show_cart(session)
    if choice == "0":
        return end("Merci, a bientot !")
    return show_home(session, prefix="Choix invalide.\n\n")


# =========================================================================
# ÉCRAN : CATÉGORIES
# =========================================================================
def show_categories(session, prefix=""):
    categories = list(Category.objects.filter(is_active=True))
    if not categories:
        return show_home(session, prefix="Aucune categorie disponible.\n\n")

    lines = ["Categories:"]
    ids = []
    for i, category in enumerate(categories, start=1):
        lines.append(f"{i}. {category.name}")
        ids.append(category.id)
    lines.append("0. Retour")

    session.state = CATEGORIES
    session.context = {"category_ids": ids}
    session.save()
    return con(prefix + "\n".join(lines))


def handle_categories(session, choice):
    if choice == "0":
        return show_home(session)
    ids = session.context.get("category_ids", [])
    index = _to_index(choice, len(ids))
    if index is None:
        return show_categories(session, prefix="Choix invalide.\n\n")
    return show_products(session, ids[index])


# =========================================================================
# ÉCRAN : PRODUITS (d'une catégorie)
# =========================================================================
def show_products(session, category_id, prefix=""):
    category = Category.objects.filter(id=category_id, is_active=True).first()
    if not category:
        return show_categories(session, prefix="Categorie indisponible.\n\n")

    products = list(category.products.filter(is_active=True, stock__gt=0))
    if not products:
        return show_categories(session, prefix="Aucun produit disponible.\n\n")

    lines = [f"{category.name}:"]
    ids = []
    for i, product in enumerate(products, start=1):
        lines.append(f"{i}. {product.name} - {product.price} F")
        ids.append(product.id)
    lines.append("0. Retour")

    session.state = PRODUCTS
    session.context = {"category_id": category_id, "product_ids": ids}
    session.save()
    return con(prefix + "\n".join(lines))


def handle_products(session, choice):
    if choice == "0":
        return show_categories(session)
    ids = session.context.get("product_ids", [])
    index = _to_index(choice, len(ids))
    if index is None:
        category_id = session.context.get("category_id")
        return show_products(session, category_id, prefix="Choix invalide.\n\n")
    return show_quantity(session, ids[index])


# =========================================================================
# ÉCRAN : QUANTITÉ
# =========================================================================
def show_quantity(session, product_id, prefix=""):
    product = Product.objects.filter(id=product_id).first()
    if not product or not product.is_available:
        return show_categories(session, prefix="Produit indisponible.\n\n")

    context = session.context
    context["product_id"] = product_id
    session.state = QUANTITY
    session.context = context
    session.save()

    menu = (
        f"{product.name} - {product.price} F\n"
        f"Stock: {product.stock}\n"
        "Entrez la quantite:"
    )
    return con(prefix + menu)


def handle_quantity(session, value):
    product_id = session.context.get("product_id")
    product = Product.objects.filter(id=product_id).first()
    if not product:
        return show_categories(session, prefix="Produit indisponible.\n\n")

    if not value.isdigit() or int(value) <= 0:
        return show_quantity(session, product_id, prefix="Quantite invalide.\n\n")

    quantity = int(value)
    if quantity > product.stock:
        return show_quantity(
            session, product_id, prefix=f"Stock insuffisant (max {product.stock}).\n\n"
        )

    _add_to_cart(session, product_id, quantity)
    return show_home(
        session, prefix=f"{quantity} x {product.name} ajoute au panier.\n\n"
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
def show_cart(session, prefix=""):
    cart = session.cart or []
    if not cart:
        return show_home(session, prefix="Votre panier est vide.\n\n")

    lines = ["Votre panier:"]
    total = 0
    for item in cart:
        product = Product.objects.filter(id=item["product_id"]).first()
        if not product:
            continue
        line_total = product.price * item["qty"]
        total += line_total
        lines.append(f"{item['qty']}x {product.name} = {line_total} F")
    lines.append(f"Total: {total} F")
    lines.append("1. Valider la commande")
    lines.append("2. Vider le panier")
    lines.append("0. Retour")

    session.state = CART
    session.save()
    return con(prefix + "\n".join(lines))


def handle_cart(session, choice):
    if choice == "1":
        return _validate_order(session)
    if choice == "2":
        session.cart = []
        session.save()
        return show_home(session, prefix="Panier vide.\n\n")
    if choice == "0":
        return show_home(session)
    return show_cart(session, prefix="Choix invalide.\n\n")


@transaction.atomic
def _validate_order(session):
    """Transforme le panier en commande et génère le code de paiement."""
    cart = session.cart or []
    if not cart:
        return show_home(session, prefix="Votre panier est vide.\n\n")

    customer, _ = CustomerUSSD.objects.get_or_create(
        phone_number=session.phone_number
    )
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

    message = (
        f"Commande #{order.pk} enregistree.\n"
        f"Montant: {order.total_amount} F\n"
        f"Code de paiement: {order.validation_code}\n"
        "Presentez ce code en agence pour payer."
    )
    return end(message)


# =========================================================================
# ÉCRAN : MES COMMANDES
# =========================================================================
def show_my_orders(session, prefix=""):
    session.state = MY_ORDERS
    session.save()

    customer = CustomerUSSD.objects.filter(
        phone_number=session.phone_number
    ).first()
    orders = list(customer.orders.all()[:5]) if customer else []

    if not orders:
        return con(prefix + "Aucune commande.\n0. Retour")

    lines = ["Vos commandes:"]
    for order in orders:
        lines.append(f"#{order.pk} - {order.total_amount} F - {order.get_status_display()}")
    lines.append("0. Retour")
    return con(prefix + "\n".join(lines))


def handle_my_orders(session, choice):
    if choice == "0":
        return show_home(session)
    return show_my_orders(session, prefix="Choix invalide.\n\n")
