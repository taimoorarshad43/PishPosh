from flask import Blueprint, session, render_template, redirect, flash
from models import Product

cartroutes = Blueprint("cartroutes", __name__)

############################################################## Cart Routes #####################################################################

# TODO: Add quantities to cart

@cartroutes.route('/cart')
def cart():

    userid = session.get('userid', None)

    if not userid:
        flash("Please log in to view your cart", "btn-info")
        productid = session['lastviewedproduct']
        return redirect(f'/product/{productid}')


    # Retrieve all product ids that are in the cart session object, if any.
    try:
        productids = session['cart']
    except:
        productids = []

    products = []
    subtotal = 0

    # Get all product objects and derive other features
    for productid in productids:
        product = Product.query.get(productid)

        if product is None:
            productids = session['cart']
            productids.remove(productid)
            session['cart'] = productids
            continue                        # Go on to the next product

        products.append(product)
        subtotal += product.price
        session['cart_subtotal'] = subtotal

    return render_template('cart.html', products = products, subtotal = subtotal)


@cartroutes.route('/product/<int:productid>/addtocart', methods = ['POST'])
def addtocart(productid):

    userid = session.get('userid', None)

    if userid:                              # If user is logged in, then they can add to cart
        try:                                # Because we will have nothing in the cart initially, we'll just initialize it in the except block
            products = session['cart']
            products.append(productid)
            session['cart'] = products
        except:
            session['cart'] = [productid]

        flash('Added to Cart!', 'btn-success')

        return redirect(f'/product/{productid}')
    else:                                   # If not logged in, they get a message and redirect
        flash('Please login to add items to your cart', 'btn-danger')
        return redirect(f'/product/{productid}')


@cartroutes.route('/product/<int:productid>/removefromcart', methods = ['POST'])
def removefromcart(productid):

    try:                                    # If theres nothing to remove from the cart, then we don't need to do anything
        products = session['cart']
        products.remove(productid)
        session['cart'] = products
        flash('Removed from Cart!', 'btn-warning')
    except:
        flash('Not in Cart', 'btn-info')

    return redirect(f'/product/{productid}')

################################################################################################################################################
