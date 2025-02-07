import json
import os
import io
from time import sleep

from flask import Flask, render_template, redirect, session, flash, request, jsonify, url_for
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv
from PIL import Image

from stripe_payment import create_payment_intent
from models import db, connect_db, User, Product
from forms import SignUpForm, LoginForm
from mistraldescription import getproductdescription, encodeimage, decodeimage

# Blueprint dependencies
from blueprints.apiroutes import apiroutes
from blueprints.checkout import productcheckout
from blueprints.cart import cartroutes
from blueprints.product import productroutes

load_dotenv()                               # Load environmental variables

app = Flask(__name__)
app.json.sort_keys = False                  # Prevents Flask from sorting keys in API JSON responses.
# app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///pishposh"                    # Can be used for testing
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("SUPABASE_DATABASE_URI")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "seekrat"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

app.register_blueprint(apiroutes, url_prefix = "/v1")
app.register_blueprint(productcheckout)
app.register_blueprint(cartroutes)
app.register_blueprint(productroutes)


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

    if session.get("userid", None) is None:
        flash('Please login to upload products', 'btn-info')
        return redirect('/')

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
        image.save(stream, format = 'JPEG')         # Save the image as stream of bytes
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

    if session.get("userid", None) is None:
        flash('Please login to upload products', 'btn-info')
        return redirect('/')

    user = User.query.get_or_404(userid)
    return render_template('aiupload.html', user=user)

@app.route('/upload/aiprocess', methods = ['POST'])
def aiprocess():

    image = request.files['file']
    title_prompt = "Give me a short title for this picture that is 2-5 words long. This title should describe the picture as a product"
    description_prompt = "Give me a product description for this picture that is about 6-12 words long."

    img_data = encodeimage(image)               # Need both an encoded and decoded image for the HTML and API calls respectively
    img_data_decoded = decodeimage(img_data)

    title = getproductdescription(img_data_decoded, title_prompt)     # Get both the title and description from Mistral AI
    sleep(2) # To avoid Mistral API's rate limit
    description = getproductdescription(img_data_decoded, description_prompt)

    output = {"title" : title,
              "description" : description}

    return jsonify(output)


@app.route('/upload/<int:userid>/aiconfirm')
def aiconfirm(userid):

    if session.get("userid", None) is None:
        flash('Please login to upload products', 'btn-info')
        return redirect('/')

    user = User.query.get_or_404(userid)

    img_data_decoded = session.get("aiimage", 1)
    description = session.get("aidesc", 1)
    title = session.get("aititle", 1)

    return render_template('aiconfirm.html', image=img_data_decoded, user=user, title=title, description=description)

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

    # Trying to remove everything from session after logout

    session.clear()

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



# ########################################################### Product Routes #####################################################################

# @app.route('/product/<int:productid>')
# def getproduct(productid):

#     product = Product.query.get_or_404(productid)

#     # to bookmark what product we last visited, so we can redirect back to it
#     session['lastviewedproduct'] = productid

#     return render_template('productdetail.html', product=product)

# @app.route('/product/<int:productid>/delete')
# def deleteproduct(productid):

#     Product.query.filter_by(productid=productid).delete()
#     db.session.commit()

#     userid = session['userid']

#     flash('Product Deleted', 'btn-danger')
#     return redirect(f'/user/{userid}')

# ################################################################################################################################################