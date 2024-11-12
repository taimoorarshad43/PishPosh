from flask import Flask, render_template, redirect, session, flash, request
from flask_debugtoolbar import DebugToolbarExtension
from models import db, connect_db, User, Product
from forms import SignUpForm, LoginForm
from sqlalchemy.exc import IntegrityError
from stripe_payment import create_payment_intent
import json


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

    products = Product.query.limit(20).all() # Get a bunch of products to display on the homepage. TODO: Randomize which ones to get.

    return render_template('index.html', products = products)

@app.route('/upload', methods = ['POST', 'GET'])
def pictureupload():

    if request.method == 'POST':

        # Get the productid and image data. TODO: Refactor to have product name or username to lookup product id

        file = request.files['file']
        productid = request.form['productid']
        
        product = Product.query.get(productid)

        # Save the file as base64 encoding to its image filed in DB.
        product.encode_image(file)

        db.session.add(product)
        db.session.commit()

        return redirect('/')
        

    return render_template('upload.html')

############################################################### User Routes #######################################################

# TODO: User Detail

@app.route('/user/<int:userid>')
def userdetail(userid):

    user = User.query.get_or_404(userid)

    return render_template('userdetail.html', user = user)

# TODO: Need to handle users already existing

@app.route('/signup', methods = ['GET', 'POST'])
def signup():

    signinform = SignUpForm()

    if signinform.validate_on_submit(): # Handles our POST requests
        username = signinform.username.data
        password = signinform.password.data
        firstname = signinform.firstname.data
        lastname = signinform.lastname.data

        user = User.hashpassword(username, password, firstname, lastname)

        db.session.add(user)
        try:                        # Possible username exists
            db.session.commit()
        except IntegrityError:
            signinform.username.errors.append("Username already taken")
            return render_template('signup.html', form = signinform) # Return to GET route of signin

        session['userid'] = user.id

        flash("Sign Up Successful!", 'btn-success')

        return redirect('/')

    else:                              # Handles our GET requests
        return render_template('signup.html', form = signinform)
    
@app.route('/login', methods = ['GET', 'POST'])
def login():

    loginform = LoginForm()

    if loginform.validate_on_submit(): # Handles our POST requests

        username = loginform.username.data
        password = loginform.password.data

        user = User.authenticate(username, password)

        if user:                       # With valid user redirect to index and add userid to session object
            session['userid'] = user.id
            return redirect('/')
    else:                              # Handles our GET requests
        return render_template('login.html', form = loginform)
    
@app.route('/logout')
def logout():

    # When you log out, remove userid from session and clear cart from session

    session.pop('userid', None)
    session.pop('cart')

    flash("You are no longer logged in", 'btn-success')

    return redirect('/')
    
# TODO: Delete User route - need to test this
    
@app.route('/user/<int:userid>/delete')
def deleteuser(userid):

    User.query.get(userid).delete()

    db.session.commit()

    # Should delete all products associated with user as well

    # Should remove userid from session as well.

    session.pop['username', None]

    return redirect('/')

################################################################################################################################################



############################################################## Product Routes #####################################################################

@app.route('/product/<int:productid>')
def getproduct(productid):

    product = Product.query.get_or_404(productid)

    return render_template('productdetail.html', product=product)

# TODO: Product delete route - need to test this

@app.route('/product/<int:productid>/delete')
def deleteproduct(productid):

    Product.query.get(productid).delete()

    db.session.commit()

    return redirect('/')

################################################################################################################################################



############################################################## Cart Routes #####################################################################

@app.route('/product/<int:productid>/addtocart', methods = ['POST'])
def addtocart(productid):

    userid = session.get('userid', None)

    if userid:                   # If user is logged in, then they can add to cart
        try:                                # Because we will have nothing in the cart initially, we'll just initialize it in the except block
            products = session['cart']
            products.append(productid)
            session['cart'] = products
        except:
            session['cart'] = [productid]

        flash('Added to Cart!', 'btn-success')

        return redirect(f'/product/{productid}')
    else:                                   # If not logged in, they get a message and redirect
        flash('You need to be logged in!', 'btn-danger')
        return redirect(f'/product/{productid}')


@app.route('/product/<int:productid>/removefromcart', methods = ['POST'])
def removefromcart(productid):

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
        session['cart_subtotal'] = subtotal

    return render_template('cart.html', products = products, subtotal = subtotal)

################################################################################################################################################



############################################################## Checkout Routes #####################################################################


@app.route('/checkout')
def checkout():

    # payment_data = request.get_json()

    # For debugging purposes - piping fake data until we can get it from /cart
    payment_data = {"amount" : 100}

    amount = int(payment_data['amount'])
    intent = create_payment_intent(amount)
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

@app.route('/confirmation')
def confirmation():
    return render_template('confirmation.html')

################################################################################################################################################



if __name__ == '__main__':
    app.run(ssl_context=("cert.pem", "key.pem"))
    # app.run(debug = True, ssl_context='adhoc', host='localhost', port=5000)