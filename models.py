from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

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
    
    firstname = db.Column(db.String(50), nullable = False)
    lastname = db.Column(db.String(50))