from models import User, Product, db, connect_db
from app import app
import requests
from random import randint
import base64

# with app.app_context(): # Start with a fresh slate
    # db.drop_all()

user1 = User(id = 1, username = 'jsmith', firstname = 'John', lastname = 'Smith', passwordhash = 'asdf')
user2 = User(id = 2, username = 'jstaten', firstname = 'Jason', lastname = 'Staten', passwordhash = 'asdb')

product1 = Product(productname = 'Ralph Lauren Duffle Bag',
                    productdescription = 'A beautiful Ralph Lauren Duffle Bag in great condition', user_id = 1, price=Product.generateprice())

product2 = Product(productname = 'Reach Edition Xbox360', productdescription = 'A mint condition Reach Edition Xbox360 with controllers and batteries'
                   ,user_id = 2, price=Product.generateprice())

def getimages():
    img_url = 'https://picsum.photos/200'

    img_data = requests.get(img_url).content

    img_data_encoded = base64.b64encode(img_data).decode('utf-8')

    # print(img_data_encoded)
    return img_data_encoded


with app.app_context(): # Need this for Flask 3

    db.create_all()
    db.session.add(user1)
    db.session.add(user2)
    db.session.add(product1)
    db.session.add(product2)

    db.session.commit()

firstnamesfile = 'firstnames.txt'
lastnamesfile = 'lastnames.txt'

def gen_names(filename): 

    """Function to take in a file with names and returns a list of names"""

    names = []
    with open(filename, 'r') as file:
        for line in file:
            name = line.strip() #get rid of whitespace


        if name:
            names.append(names)

    return names


firstnames = gen_names('firstnames.txt')
lastnames = gen_names('lastnames.txt')


def generateusers(n=100):

    for x in range(n):

        firstname = firstnames[randint(0,len(firstnames))]
        lastname = lastnames[randint(0,len(lastnames))]
        passwordhash = 'abc'
        username = firstname + lastname


        user = User(firstname = firstname, lastname = lastname, passwordhash = passwordhash, username = username)

def generateusers(n=100):

    for x in range(n):

        productname = 'test'
