from models import User, Product, db, connect_db
from app import app


user1 = User(id = 1, username = 'jsmith', firstname = 'John', lastname = 'Smith', passwordhash = 'asdf')
user2 = User(id = 2, username = 'jstaten', firstname = 'Jason', lastname = 'Staten', passwordhash = 'asdb')

product1 = Product(productname = 'Ralph Lauren Duffle Bag',
                    productdescription = 'A beautiful Ralph Lauren Duffle Bag in great condition', user_id = 1, price=30)

product2 = Product(productname = 'Reach Edition Xbox360', productdescription = 'A mint condition Reach Edition Xbox360 with controllers and batteries'
                   ,user_id = 2, price=30)


with app.app_context(): # Need this for Flask 3

    db.create_all()
    db.session.add(user1)
    db.session.add(user2)
    db.session.add(product1)
    db.session.add(product2)

    db.session.commit()