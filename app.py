from flask import Flask, render_template, redirect, session, flash, request
from flask_debugtoolbar import DebugToolbarExtension
from models import db, connect_db, User, Product
from forms import AddUserForm
from sqlalchemy.exc import IntegrityError


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///pishposh"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "seekrat"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False


with app.app_context(): # Need this for Flask 3
    connect_db(app)

toolbar = DebugToolbarExtension(app)


@app.route('/')
def home_page():

    products = Product.query.limit(20).all() # Get a bunch of products to display on the homepage

    return render_template('index.html', products = products)

@app.route('/upload', methods = ['POST', 'GET'])
def pictureupload():

    if request.method == 'POST':

        file = request.files['file']
        productid = request.form['productid']
        
        product = Product.query.get(productid)

        product.encode_image(file)

        db.session.add(product)
        db.session.commit()

        return redirect('/')
        

    return render_template('upload.html')

############################################################### User Login & Sign Up Routes #######################################################

@app.route('/signup', methods = ['GET', 'POST'])
def signup_page():

    userform = AddUserForm()

    if userform.validate_on_submit(): # Handle our POST requests
        username = userform.username.data
        password = userform.password.data
        firstname = userform.firstname.data
        lastname = userform.lastname.data

        user = User.hashpassword(username, password, firstname, lastname)

        db.session.add(user)
        db.session.commit()

    else:                               # Handle our GET requests
        return render_template('signup.html', form = userform)


###################################################################################################################################################

@app.route('/product/<int:productid>')
def getproduct(productid):

    product = Product.query.get_or_404(productid)

    # print(product)

    return render_template('productdetail.html', product=product)

############################################################## Cart Routes #####################################################################

@app.route('/product/<int:productid>/addtocart', methods = ['POST'])
def addtocart(productid):

    print("Endpoint triggered")

    try:                                    # Because we will have nothing in the cart initially, we'll just initialize it in the except block
        products = session['cart']
        products.append(productid)
        session['cart'] = products
    except:
        session['cart'] = [productid]

    flash('Added to Cart!', 'btn-success')

    return redirect(f'/product/{productid}')


@app.route('/product/<int:productid>/removefromcart', methods = ['POST'])
def removefromcart(productid):

    print("Removing from cart endpoint triggered")

    try:                                    # If theres nothing to remove from the cart, then we don't need to do anything
        products = session['cart']
        products.remove(productid)
        session['cart'] = products
        flash('Removed from Cart!', 'btn-warning')
    except:
        flash('Nothing in Cart', 'btn-info')

    return redirect(f'/product/{productid}')

@app.route('/cart')
def cart():

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

    return render_template('cart.html', products = products, subtotal = subtotal)

#######################################################################################################################################

@app.route('/checkout')
def checkout():

    # TODO: Add Stripe API integration

    return render_template('checkout.html')


