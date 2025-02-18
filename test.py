import io
from unittest import TestCase
import base64

from app import create_app
from flask import session

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
        Rolling back database, dropping all tables
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

    def test_addingtocart(self):

        """
        Testing session state when we add to cart
        """

        with app.test_client() as client:
            with client.session_transaction() as change_session:
                change_session['userid'] = 1                    # We'll set the user id to 1 to simulate a logged in user
            client.post('/product/1/addtocart')

            self.assertEqual(session['cart'], [1])

    def test_next_page(self):                                   # Testing to see if next page route changes session state appropriately

        """
        Testing the next page feature
        """

        with app.test_client() as client:
            client.get('/?page=next')

            self.assertEqual(session['page'], 1)

    def test_previous_page(self):

        """
        Testing the previous page feature
        """

        with app.test_client() as client:                       # Testing to see if previous page route changes session state appropriately
            with client.session_transaction() as change_session:
                change_session['page'] = 1
            client.get('/?page=previous')

            self.assertEqual(session['page'], 0)

    def test_signingup(self):                                   # Testing to see if signing up a user works and we have a database entry
        
        """
        Testing signing up a regular user account
        """

        with app.test_client() as client:
            client.post('/signup', data = {'username': 'janedoe', 'password': 'password', 'firstname': 'Jane', 'lastname': 'Doe'})
            
            user = User.query.filter_by(username = 'janedoe').first()
            
            self.assertEqual(user.id, 2)

    def test_loggingin(self):                                   # Testing to see if logging in a user works and we have a session entry of their user id (of 1)

        """
        Testing logging in a regular user account
        """

        with app.test_client() as client:
            client.post('/login', data = {'username': 'johndoe', 'password': 'password'})

            self.assertEqual(session['userid'], 1)

    def test_loggingout(self):                                  # Testing to see if logging out a user works and we have no session entry of their user id

        """
        Testing logging out a regular user account
        """

        with app.test_client() as client:
            with client.session_transaction() as change_session:
                change_session['userid'] = 1
            client.get('/logout')

            self.assertNotIn('userid', session)

    def test_uploadingproduct_fail(self):                       # Testing to see if we get the right redirect location when a product upload fails
        
        """
        Testing uploading a product and failing. We then see if we get a form error
        """

        with app.test_client() as client:
            with client.session_transaction() as change_session:
                change_session['userid'] = 1
            resp = client.post('/upload/1', data = {'productname': 'New uploaded Product', 'productdescription': 
                                                    'Product for testing purposes', 'price': 25, 'file': 'test.jpg'})
            data = resp.get_data(as_text = True)

            self.assertEqual(resp.location, '/userdetail')

    def test_uploadingproduct_fail(self):                       # Testing to see if we get the right error when a product upload fails
        
        """
        Testing uploading a product and failing. We then see if we get a form error
        """

        with app.test_client() as client:
            with client.session_transaction() as change_session:
                change_session['userid'] = 1
            resp = client.post('/upload/1', data = {'productname': 'New uploaded Product', 'productdescription': 
                                                    'Product for testing purposes', 'price': '25', 'file': 'test.jpg'}, follow_redirects = True)
            data = resp.get_data(as_text = True)

            self.assertIn('Product Upload failed', data)

    def test_uploadingproduct_success(self):                    # Testing to see if we can get a product uploaded

        """
        Testing uploading a product and succeeding
        """

        with app.test_client() as client:
            with client.session_transaction() as change_session:
                change_session['userid'] = 1

            SMALLEST_JPEG_B64 = """\
            /9j/2wBDAAMCAgICAgMCAgIDAwMDBAYEBAQEBAgGBgUGCQgKCgkICQkKDA8MCgsOCwkJDRENDg8Q
            EBEQCgwSExIQEw8QEBD/yQALCAABAAEBAREA/8wABgAQEAX/2gAIAQEAAD8A0s8g/9k=
            """

            data = {'name': 'New uploaded Product', 'description': 
                                                    'Product for testing purposes', 'price': '25'}
            data['image'] = (io.BytesIO(base64.b64decode(SMALLEST_JPEG_B64)), 'test.jpeg')
            resp = client.post('/upload/1', data = data, follow_redirects = True, content_type='multipart/form-data')
            html = resp.get_data(as_text = True)
            
            product = Product.query.filter_by(productname = 'New uploaded Product').first()

            self.assertEqual(product.productname, 'New uploaded Product')
            self.assertIn('Product Listed Successfully', html)

    def test_APIgetallusers(self):
        
        """
        Testing the API route to get all users
        """

        with app.test_client() as client:
            resp = client.get('/v1/users')              # Should return a JSON

            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.json["Users"][0]["username"], 'johndoe')


    def test_APIgetallproducts(self):
        
        """
        Testing the API route to get all products
        """

        with app.test_client() as client:
            resp = client.get('/v1/products')              # Should return a JSON

            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.json["Products"][0]["productname"], 'Product Name')
