import json
import os
import io
from time import sleep

from flask import Flask, render_template, redirect, session, flash, request, jsonify
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv
from PIL import Image

from stripe_payment import create_payment_intent
from models import db, connect_db, User, Product
from forms import SignUpForm, LoginForm
from mistraldescription import getproductdescription, encodeimage, decodeimage

load_dotenv()                               # Load environmental variables

app = Flask(__name__)
app.json.sort_keys = False                  # Prevents Flask from sorting keys in API JSON responses.
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///pishposh"                    # Can be used for testing
# app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("SUPABASE_DATABASE_URI")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "seekrat"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False


with app.app_context(): # Need this for Flask 3
    connect_db(app)

toolbar = DebugToolbarExtension(app)


@app.route('/')
def home_page():

    offset = request.args.get('page', None)                      # We'll set the offset based on whether user selects 'next' or 'previous'
    pagination = session.get('page', 0)

    # Offset will either be "next" or "previous", we'll then increase pagination and use that in our SQLA query
    if not offset:                                           
        session['page'] = 0
        pagination = 0
    elif offset == 'next':
        pagination = session.get('page', 0)
        pagination += 1
        session['page'] = pagination
    else:
        pagination = session.get('page', 0)
        pagination -= 1
        session['page'] = pagination


    if pagination < 1:  # To prevent negative pages
        pagination = 0
        session['page'] = pagination

    pagination = pagination* 20

    products = Product.query.offset(pagination).limit(20).all() # Get a bunch of products to display on the homepage. TODO: Randomize order of products listed

    return render_template('index.html', products = products)

############################################################## Upload Routes #############################################################

@app.route('/upload/<int:userid>', methods = ['POST'])
def pictureupload(userid):

    try:
        file = request.files['file']
        productname = request.form['productname']
        productdescription = request.form['productdescription']
        productprice = request.form['productprice']
        
        # Generate new product and attach it to passed userid
        product = Product(productname = productname, productdescription = productdescription, price = productprice, user_id = userid)

        image = Image.open(file)
        newsize = (200,200) # Resizing the image to be compact
        image = image.resize(newsize)
        stream = io.BytesIO()
        image.save(stream, format = 'JPEG')
        file = stream.getvalue()

        # Save the file as base64 encoding to its image filed in DB.
        product.encode_image(file)

        db.session.add(product)
        db.session.commit()

    except Exception as e:                                          # If certain fields are missing, redirect to user detail with flashed message
        print(e)
        flash('Product Upload failed (check required fields)', 'btn-danger')
        return redirect(f'/user/{userid}')

    flash('Product Listed Successfully', 'btn-success')
    return redirect(f'/user/{userid}')                          # After success, redirect to their user page with their products.

@app.route('/upload/<int:userid>/ai')
def uploadai(userid):

    user = User.query.get_or_404(userid)
    return render_template('aiupload.html', user=user)

@app.route('/upload/<int:userid>/aiconfirm', methods = ['GET', 'POST'])
def aiconfirm(userid):

    # TODO: Add better GET routing

    user = User.query.get_or_404(userid)

    if request.method == 'POST': # For when a picture is uploaded from the previous route

        image = request.files['file']
        title_prompt = "Give me a short title for this picture that is 2-5 words long. This title should describe the picture as a product"
        description_prompt = "Give me a product description for this picture that is about 6-12 words long."

        img_data = encodeimage(image)
        img_data_decoded = decodeimage(img_data)

        title = getproductdescription(img_data_decoded, title_prompt)
        sleep(2) # To avoid Mistral API's rate limit
        description = getproductdescription(img_data_decoded, description_prompt)

        return render_template('aiconfirm.html', image=img_data_decoded, user=user, title=title, description=description)

    return render_template('aiconfirm.html', user=user)

##########################################################################################################################################

        

############################################################### User Routes ###############################################################

@app.route('/user/<int:userid>')
def profile(userid):

    user = User.query.get_or_404(userid)

    userproducts = []

    for product in user.products: # Get all user products to list on page
        userproducts.append(product)

    return render_template('profile.html', user = user, products = userproducts)

@app.route('/userdetail')
def userdetail():

    userid = session.get('userid', None)

    if userid:

        user = User.query.get_or_404(session.get('userid', -1))     # Should only be able to get here if you are logged in
        userproducts = []

        for product in user.products: # Get all user products to list on page
            userproducts.append(product)

        return render_template('userdetail.html', user = user, products = userproducts)
    
    else:

        flash('Please login to view your profile', 'btn-info')
        return redirect('/')

@app.route('/signup', methods = ['GET', 'POST'])
def signup():

    signinform = SignUpForm()

    if signinform.validate_on_submit(): # Handles our POST requests
        username = signinform.username.data
        password = signinform.password.data
        firstname = signinform.firstname.data
        lastname = signinform.lastname.data

        ####################### Validation of user input #################################
        if len(username) < 4:
            signinform.username.errors.append("Username must be at least 4 characters long")
            return render_template('signup.html', form = signinform)
        if len(password) <= 6:
            signinform.password.errors.append("Password must be at least 6 characters long")
            return render_template('signup.html', form = signinform)
        if len(firstname) == 0:
            signinform.firstname.errors.append("You need to add your first name")
            return render_template('signup.html', form = signinform)
        ##################################################################################

        user = User.hashpassword(username, password, firstname, lastname)

        db.session.add(user)
        try:                            # Handles the possibility that the username is already taken
            db.session.commit()
        except IntegrityError:
            signinform.username.errors.append("Username already taken")
            return render_template('signup.html', form = signinform) # Return to GET route of signin

        session['userid'] = user.id
        session['username'] = user.username
        session['userfirstname'] = user.firstname
        session['userlastname']= user.lastname

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

        if user:                       # With valid user redirect to index and add userid (and other attributes) to session object
            session['userid'] = user.id
            session['username'] = user.username
            session['userfirstname'] = user.firstname
            session['userlastname']= user.lastname

            return redirect('/')
        else:
            loginform.username.errors.append('Incorrect Username/Password combination')
            return render_template('login.html', form=loginform)
    else:                              # Handles our GET requests
        return render_template('login.html', form = loginform)
    
@app.route('/logout')
def logout():

    # When you log out, remove userid from session and clear cart from session

    session.pop('userid', None)
    session.pop('username', None)
    session.pop('userfirstname', None)
    session.pop('userlastname', None)
    session.pop('cart', None)

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



########################################################### Product Routes #####################################################################

@app.route('/product/<int:productid>')
def getproduct(productid):

    product = Product.query.get_or_404(productid)

    # to bookmark what product we last visited, so we can redirect back to it
    session['lastviewedproduct'] = productid

    return render_template('productdetail.html', product=product)

@app.route('/product/<int:productid>/delete')
def deleteproduct(productid):

    Product.query.filter_by(productid=productid).delete()
    db.session.commit()

    userid = session['userid']

    flash('Product Deleted', 'btn-danger')
    return redirect(f'/user/{userid}')

################################################################################################################################################



############################################################## Cart Routes #####################################################################

# TODO: Add quantities to cart

@app.route('/cart')
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


@app.route('/product/<int:productid>/addtocart', methods = ['POST'])
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


@app.route('/product/<int:productid>/removefromcart', methods = ['POST'])
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



############################################################## Checkout Routes ###################################################################

@app.route('/checkout')
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

@app.route('/confirmation')
def confirmation():

    # Empty cart after a purchase is made.

    session.pop('cart', None)

    return render_template('confirmation.html')

################################################################################################################################################



############################################################## API Routes ######################################################################
@app.route('/v1/users')
def getusers():

    # get all users
    sqlausers = User.query.all()

    params = ['id', 'username', 'firstname', 'lastname']

    users = [serialize(sqlauser, params) for sqlauser in sqlausers]

    return jsonify(Users=users)

@app.route('/v1/users/<userid>')
def getsingleuser(userid):

    user = User.query.get(userid)
    params = ['id', 'username', 'firstname', 'lastname']
    user = serialize(user, params)

    return jsonify(User=user)

@app.route('/v1/products')
def getproducts():

    sqlaproducts = Product.query.all()
    params = ['productid', 'productname', 'productdescription', 'price', 'user_id']
    products = [serialize(product, params) for product in sqlaproducts]

    return jsonify(Products=products)

@app.route('/v1/products/<productid>')
def getsingleproduct(productid):

    product = Product.query.get(productid)
    params = ['productid', 'productname', 'productdescription', 'price', 'user_id']
    product = serialize(product, params)

    return jsonify(Product=product)


def serialize(object, params): # Helper function for serializing different SQLA objects

    """
    Serializer helper function. All it needs is the object and its respective params to serialize.

    Takes the object to be serialized as well as the params to serialize it with
    """

    # TODO: Refactor to allow SQL relationships

    mapper = inspect(object)
    output = {}

    for column in mapper.attrs:
        if column.key in params:
            output[column.key] = getattr(object, column.key)

    return output

################################################################################################################################################

