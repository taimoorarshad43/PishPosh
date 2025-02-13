import os

from flask import Flask, render_template, session, request
from flask_debugtoolbar import DebugToolbarExtension
from dotenv import load_dotenv

from models import connect_db, Product

# Blueprint dependencies
from blueprints.apiroutes import apiroutes
from blueprints.checkout import productcheckout
from blueprints.cart import cartroutes
from blueprints.product import productroutes
from blueprints.userroutes import userroutes
from blueprints.uploadroutes import uploadroutes

load_dotenv()                               # Load environmental variables

app = Flask(__name__)
app.json.sort_keys = False                  # Prevents Flask from sorting keys in API JSON responses.
# app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///pishposh"                    # Can be used for testing
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///unittest_debugging_test"       # Debugging test, TODO: Delete
# app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("SUPABASE_DATABASE_URI")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "seekrat"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

# Register blueprints
app.register_blueprint(apiroutes, url_prefix = "/v1")
app.register_blueprint(productcheckout)
app.register_blueprint(cartroutes)
app.register_blueprint(productroutes)
app.register_blueprint(userroutes)
app.register_blueprint(uploadroutes)


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

@app.errorhandler(404)
def page_not_found(e):
    print(e)
    return render_template('404.html'), 404