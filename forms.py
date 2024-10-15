from flask_wtf import FlaskForm
from wtforms import StringField, FloatField

class AddUserForm(FlaskForm):

    username = StringField("Login Name (required)")
    password = StringField("Password (required)")
    firstname = StringField("First Name (required)")
    lastname = StringField("Last Name")

