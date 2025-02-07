import json
from flask import Blueprint, session, render_template
from stripe_payment import create_payment_intent
from models import Product

productcheckout = Blueprint("checkout", __name__)

@productcheckout.route('/checkout')
def checkout():

    payment_data = {"amount" : session['cart_subtotal']}

    amount = int(payment_data['amount'])
    intent = create_payment_intent(amount)                          # Intent returns a response object
    intent_data = json.loads(intent.get_data().decode('utf-8'))

    # Retrieve all product ids that are in the cart session object.
    try:
        productids = session['cart']
    except:
        productids = []

    products = []
    subtotal = 0

    # Get all product objects and derive other features
    for productid in productids:
        product = Product.query.get(productid)

        products.append(product)
        subtotal += product.price

    return render_template('checkout.html', client_secret = intent_data['clientSecret'], products = products, subtotal = subtotal)

@productcheckout.route('/confirmation')
def confirmation():

    # Empty cart after a purchase is made.

    session.pop('cart', None)

    return render_template('confirmation.html')
