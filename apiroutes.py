from flask import Blueprint, jsonify
from models import User, Product
from sqlalchemy import inspect


apiroutes = Blueprint("apiroutes", __name__)

@apiroutes.route('/users')
def getusers():

    # get all users
    sqlausers = User.query.all()

    params = ['id', 'username', 'firstname', 'lastname']

    users = [serialize(sqlauser, params) for sqlauser in sqlausers]

    return jsonify(Users=users)

@apiroutes.route('/v1/users/<userid>')
def getsingleuser(userid):

    user = User.query.get(userid)
    params = ['id', 'username', 'firstname', 'lastname']
    user = serialize(user, params)

    return jsonify(User=user)

@apiroutes.route('/v1/products')
def getproducts():

    sqlaproducts = Product.query.all()
    params = ['productid', 'productname', 'productdescription', 'price', 'user_id']
    products = [serialize(product, params) for product in sqlaproducts]

    return jsonify(Products=products)

@apiroutes.route('/v1/products/<productid>')
def getsingleproduct(productid):

    product = Product.query.get(productid)
    params = ['productid', 'productname', 'productdescription', 'price', 'user_id']
    product = serialize(product, params)

    return jsonify(Product=product)


def serialize(object, params): # Helper function for serializing different SQLA objects

    """
    Serializer helper function. All it needs is the object and its respective params to serialize.

    Takes the object to be serialized as well as the params to serialize it with
    """

    # TODO: Refactor to allow SQL relationships

    mapper = inspect(object)
    output = {}

    for column in mapper.attrs:
        if column.key in params:
            output[column.key] = getattr(object, column.key)

    return output


