import os

from flask import Flask
from flask_debugtoolbar import DebugToolbarExtension
from dotenv import load_dotenv

from models import connect_db

# Blueprint dependencies
from blueprints.apiroutes import apiroutes
from blueprints.checkout import productcheckout
from blueprints.cart import cartroutes
from blueprints.product import productroutes
from blueprints.userroutes import userroutes
from blueprints.uploadroutes import uploadroutes
from blueprints.indexroutes import indexroutes

load_dotenv()                               # Load environmental variables

# app = Flask(__name__)
# app.json.sort_keys = False                  # Prevents Flask from sorting keys in API JSON responses.
# # app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///pishposh"                    # Can be used for testing
# app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///unittest_debugging_test"       # Debugging test, TODO: Delete
# # app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("SUPABASE_DATABASE_URI")
# app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# app.config["SQLALCHEMY_ECHO"] = True
# app.config["SECRET_KEY"] = "seekrat"
# app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

# Creating an application factory
def create_app(db_uri):
    app = Flask(__name__)

    with app.app_context(): # Need this for Flask 3
        connect_db(app, db_uri)

    return app

# db_uri = os.environ.get("SUPABASE_DATABASE_URI")
# db_uri = "postgresql:///pishposh"
db_uri = "postgresql:///unittest_debugging_test"

app = create_app(db_uri)

app.json.sort_keys = False                  # Prevents Flask from sorting keys in API JSON responses.
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "seekrat"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

app.register_blueprint(apiroutes, url_prefix = "/v1")
app.register_blueprint(productcheckout)
app.register_blueprint(cartroutes)
app.register_blueprint(productroutes)
app.register_blueprint(userroutes)
app.register_blueprint(uploadroutes)
app.register_blueprint(indexroutes)

toolbar = DebugToolbarExtension(app)