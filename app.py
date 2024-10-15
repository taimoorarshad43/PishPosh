from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, User
from forms import AddUserForm
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///pishposh"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "seekrat"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False


with app.app_context(): # Need this for Flask 3
    connect_db(app)

toolbar = DebugToolbarExtension(app)


@app.route('/')
def home_page():
    return render_template('index.html')

@app.route('/signup', methods = ['GET', 'POST'])
def signup_page():

    userform = AddUserForm()

    if userform.validate_on_submit(): # Handle our POST requests
        username = userform.username.data
        password = userform.password.data
        firstname = userform.firstname.data
        lastname = userform.lastname.data

        user = User(username = username, password = password, firstname = firstname, lastname = lastname)

        db.session.add(user)
        db.session.commit()

    else:
        return render_template('signup.html', form = userform)