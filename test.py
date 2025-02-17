from unittest import TestCase

from app import create_app
from flask import session, jsonify

from models import User, Product, db

from blueprints.apiroutes import apiroutes
from blueprints.checkout import productcheckout
from blueprints.cart import cartroutes
from blueprints.product import productroutes
from blueprints.userroutes import userroutes
from blueprints.uploadroutes import uploadroutes
from blueprints.indexroutes import indexroutes

app = create_app('postgresql:///pishposh_testing_db')  # TODO: Use an inmemory database like SQLite

app.config['SQLALCHEMY_ECHO'] = False

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

# Disable some of Flasks error behavior and disabling debugtoolbar. Disabling CSRF token.
app.config['TESTING'] = True
app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']
app.config['WTF_CSRF_ENABLED'] = False


class FlaskTests(TestCase):

    """
    Testing the functionalities of the app.py file

        Things covered:

        Does app respond with appropriate pages?

        Does app response with certain features intact?

    """
    # TODO -- write tests for every view function / feature!

    def setUp(self):
        
        """
        Setting up fake users and products to test
        """
        with app.app_context():

            db.drop_all()
            db.create_all()

            User.query.delete()

            username = 'johndoe'
            password = 'password'
            firstname = 'John'
            lastname = 'Doe'

            user = User.hashpassword(username, password, firstname, lastname)

            db.session.add(user)
            db.session.commit()

            Product.query.delete()

            productname = 'Product Name'
            productdescription = 'A product description'
            productprice = 25
            userid = 1

            product = Product(productname = productname, productdescription = productdescription, price = productprice, user_id = userid)

            db.session.add(product)
            db.session.commit()

    def tearDown(self):

        """
        Rolling back database
        """
        with app.app_context():
            db.session.rollback()
            db.drop_all()


    def test_index(self):

        """
        Test visiting index page
        """

        with app.test_client() as client:
            resp = client.get('/')

            self.assertEqual(resp.status_code, 200)

    def test_example_products(self):
        
        """
        Test visiting a product page
        """

        with app.test_client() as client:
            resp = client.get('/product/1')

            self.assertEqual(resp.status_code, 200)

    def test_404_product(self):

        """
        Test visiting a product that doesn't exist
        """

        with app.test_client() as client:
            resp = client.get('/product/43')

            self.assertEqual(resp.status_code, 404)

    def test_example_user(self):
        
        """
        Test visiting a user page
        """

        with app.test_client() as client:
            resp = client.get('/user/1')

            self.assertEqual(resp.status_code, 200)

    def test_404_user(self):
        
        """
        Test visiting a user that doesn't exist
        """

        with app.test_client() as client:
            resp = client.get('/user/43')

            self.assertEqual(resp.status_code, 404)

    # def test_addingtocart(self):

    #     """
    #     Testing session state when we add to cart
    #     """
    #     with app.test_client() as client:
    #         resp = client.get('/product/1/addtocart')

    #         self.assertEqual(session['cart'], [1])            


        

    # def test_words(self):
    #     with app.test_client() as client:
    #         with client.session_transaction() as change_session:
    #             boggle_game = Boggle()
    #             board = boggle_game.make_board()
    #             change_session['board'] = board
                
    #         resp = client.get(f"/guess?guess='cat'")
    #         self.assertIn(resp.json[0], ['ok', 'not-word'])

