from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, PasswordField

class SignUpForm(FlaskForm):

    username = StringField("Username (required)")
    password = PasswordField("Password (required)")
    firstname = StringField("First Name (required)")
    lastname = StringField("Last Name")

class LoginForm(FlaskForm):

    username = StringField("Username (required)")
    password = PasswordField("Password (required)")