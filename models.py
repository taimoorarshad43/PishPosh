from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from random import randint

db = SQLAlchemy()

bcrypt = Bcrypt()


def connect_db(app):
    """Connect to database."""

    db.app = app
    db.init_app(app)
    db.create_all()
    # db.drop_all() # For debugging if we want to start with a new table each time

class User(db.Model):

    """User model with username, first name, last name, and hashedpassword"""

    __tablename__ = "users"

    id = db.Column(db.Integer,
                   primary_key=True,
                   autoincrement=True)
    username = db.Column(db.String(50),
                         nullable = False,
                         unique = True)

    passwordhash = db.Column(db.String,
                             nullable = False,
                             unique = True)
    
    firstname = db.Column(db.String(50), nullable = False)
    lastname = db.Column(db.String(50))

    products = db.relationship("Product", cascade = 'all, delete-orphan')

    @classmethod
    def hashpassword(cls, username, password, firstname, lastname):

        hashpw = bcrypt.generate_password_hash(password)
        hashedpw_utf8 = hashpw.decode('utf8')

        return cls(username=username, password=hashedpw_utf8, firstname=firstname, lastname=lastname)


class Product(db.Model):

    """Product model with product ID, product name, product description, and user ID as a foreign key"""


    __tablename__ = 'products'

    productid = db.Column(db.Integer,
                          primary_key = True,
                          autoincrement=True)
    
    productname = db.Column(db.String(50),
                            nullable = False)
    
    productdescription = db.Column(db.String,
                                   nullable = True)
    price = db.Column(db.Integer,
                      nullable = False)
    
    user_id = db.Column(db.Integer,
                        db.ForeignKey('users.id', ondelete = 'cascade'))

    def generateprice(self):
        price = randint(0,100)

        self.price = price
