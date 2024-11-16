from models import User, Product, db
from app import app
from random import randint
from mistraldescription import getproductdescription, getimages
from time import sleep
import requests
import base64



firstnamesfile = 'firstnames.txt'
lastnamesfile = 'lastnames.txt'

# user1 = User(id = 1, username = 'jsmith', firstname = 'John', lastname = 'Smith', passwordhash = 'asdf')
# user2 = User(id = 2, username = 'jstaten', firstname = 'Jason', lastname = 'Staten', passwordhash = 'asdb')

# product1 = Product(productname = 'Ralph Lauren Duffle Bag',
#                     productdescription = 'A beautiful Ralph Lauren Duffle Bag in great condition', user_id = 1, price=Product.generateprice())

# product2 = Product(productname = 'Reach Edition Xbox360', productdescription = 'A mint condition Reach Edition Xbox360 with controllers and batteries'
#                    ,user_id = 2, price=Product.generateprice())


# with app.app_context(): # Need this for Flask 3

#     db.drop_all() # starting with a fresh slate
#     db.create_all()
#     db.session.add(user1)
#     db.session.add(user2)
#     db.session.add(product1)
#     db.session.add(product2)

#     db.session.commit()

def gen_names(filename): 

    """Function to take in a file with names and returns a list of names"""

    names = []
    with open(filename, 'r') as file:
        for line in file:
            name = line.strip() #get rid of whitespace

            if name:
                names.append(name)

    return names

# Generating names
firstnameslist = gen_names('./names/firstnames.txt')
lastnameslist = gen_names('./names/lastnames.txt')


def generateusers(n):

    """Generate list of User objects to be added to the postgresql db."""

    users = []

    for x in range(n):

        first = firstnameslist[randint(0,len(firstnameslist)-1)]
        last = lastnameslist[randint(0,len(lastnameslist)-1)]
        password = 'password'
        userhandle = first.lower() + last.lower()

        user = User.hashpassword(firstname = first, lastname = last, password = password, username = userhandle)

        users.append(user)

    return users

def generateproducts(n):

    """Generate list of Product objects to be added to postgresql db. Uses Mistral AI to generate product titles and descriptions."""

    conditions = ['good', 'great', 'ok', 'decent']
    products = []

    for x in range(n):

        image = getimages() # get a base64 binary image to store in to PSQL

        productname = getproductdescription(image.decode('utf-8')) # need to decode it for 
        productdescription = productname + " which is in " + conditions[randint(0,len(conditions)-1)] + " condition"
        price = Product.generateprice()
                                                                                                   # offsetting user_id by two because we have two existing.
        product = Product(productname = productname, productdescription = productdescription, price = price, image = image, user_id = x+1)

        sleep(5) # to avoid rate limits with minstral's API
        products.append(product)

    return products


# Generating the users and products and committing to database.
with app.app_context():
    # db.session.rollback() # in case there's a failure somewhere
    # db.drop_all()
    db.create_all()
    
    users = generateusers(20)
    db.session.add_all(users)
    db.session.commit()

    products = generateproducts(20)
    db.session.add_all(products)
    db.session.commit()