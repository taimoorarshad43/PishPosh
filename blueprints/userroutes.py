from flask import Blueprint, session, render_template, redirect, flash
from models import User, db
from forms import SignUpForm, LoginForm, ProductUploadForm
from sqlalchemy.exc import IntegrityError

userroutes = Blueprint("userroutes", __name__)

############################################################### User Routes ###############################################################

@userroutes.route('/user/<int:userid>')
def profile(userid):

    user = User.query.get_or_404(userid)

    userproducts = []

    for product in user.products: # Get all user products to list on page
        userproducts.append(product)

    return render_template('profile.html', user = user, products = userproducts)

@userroutes.route('/userdetail')
def userdetail():

    userid = session.get('userid', None)

    form = ProductUploadForm()

    if userid:

        user = User.query.get_or_404(session.get('userid', -1))     # Should only be able to get here if you are logged in
        userproducts = []

        for product in user.products: # Get all user products to list on page
            userproducts.append(product)

        return render_template('userdetail.html', user = user, products = userproducts, form = form)
    
    else:

        flash('Please login to view your profile', 'btn-info')
        return redirect('/')

@userroutes.route('/signup', methods = ['GET', 'POST'])
def signup():

    signinform = SignUpForm()

    if signinform.validate_on_submit(): # Handles our POST requests
        username = signinform.username.data
        password = signinform.password.data
        firstname = signinform.firstname.data
        lastname = signinform.lastname.data

        ####################### Validation of user input #################################
        if len(username) < 4:
            signinform.username.errors.append("Username must be at least 4 characters long")
            return render_template('signup.html', form = signinform)
        if len(password) <= 6:
            signinform.password.errors.append("Password must be at least 6 characters long")
            return render_template('signup.html', form = signinform)
        if len(firstname) == 0:
            signinform.firstname.errors.append("You need to add your first name")
            return render_template('signup.html', form = signinform)
        ##################################################################################

        user = User.hashpassword(username, password, firstname, lastname)

        db.session.add(user)
        try:                            # Handles the possibility that the username is already taken
            db.session.commit()
        except IntegrityError:
            signinform.username.errors.append("Username already taken")
            return render_template('signup.html', form = signinform) # Return to GET route of signin

        session['userid'] = user.id
        session['username'] = user.username
        session['userfirstname'] = user.firstname
        session['userlastname']= user.lastname

        flash("Sign Up Successful!", 'btn-success')

        return redirect('/')

    else:                              # Handles our GET requests
        return render_template('signup.html', form = signinform)
    
@userroutes.route('/login', methods = ['GET', 'POST'])
def login():

    loginform = LoginForm()

    if loginform.validate_on_submit(): # Handles our POST requests

        username = loginform.username.data
        password = loginform.password.data
        user = User.authenticate(username, password)

        if user:                       # With valid user redirect to index and add userid (and other attributes) to session object
            session['userid'] = user.id
            session['username'] = user.username
            session['userfirstname'] = user.firstname
            session['userlastname']= user.lastname

            return redirect('/')
        else:
            loginform.username.errors.append('Incorrect Username/Password combination')
            return render_template('login.html', form=loginform)
    else:                              # Handles our GET requests
        return render_template('login.html', form = loginform)
    
@userroutes.route('/logout')
def logout():

    # When you log out, remove userid from session and clear cart from session

    session.pop('userid', None)
    session.pop('username', None)
    session.pop('userfirstname', None)
    session.pop('userlastname', None)
    session.pop('cart', None)

    # Trying to remove everything from session after logout

    session.clear()

    flash("You are no longer logged in", 'btn-success')

    return redirect('/')
    
# TODO: Delete User route - need to test this
    
@userroutes.route('/user/<int:userid>/delete')
def deleteuser(userid):

    User.query.get(userid).delete()
    db.session.commit()

    # Should delete all products associated with user as well

    # Should remove userid from session as well.

    session.pop['username', None]

    return redirect('/')

################################################################################################################################################