import os
import io
from time import sleep

from flask import Flask, render_template, redirect, session, flash, request, jsonify
from flask_debugtoolbar import DebugToolbarExtension
from dotenv import load_dotenv
from PIL import Image

from models import db, connect_db, User, Product
from mistraldescription import getproductdescription, encodeimage, decodeimage

# Blueprint dependencies
from blueprints.apiroutes import apiroutes
from blueprints.checkout import productcheckout
from blueprints.cart import cartroutes
from blueprints.product import productroutes
from blueprints.userroutes import userroutes

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
app.register_blueprint(userroutes)


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
