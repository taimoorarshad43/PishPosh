from flask import Blueprint, session, render_template, redirect, flash
from models import Product, db

productroutes = Blueprint("productroutes", __name__)

########################################################### Product Routes #####################################################################

@productroutes.route('/product/<int:productid>')
def getproduct(productid):

    product = Product.query.get_or_404(productid)

    # to bookmark what product we last visited, so we can redirect back to it
    session['lastviewedproduct'] = productid

    return render_template('productdetail.html', product=product)

@productroutes.route('/product/<int:productid>/delete')
def deleteproduct(productid):

    Product.query.filter_by(productid=productid).delete()
    db.session.commit()

    userid = session['userid']

    flash('Product Deleted', 'btn-danger')
    return redirect(f'/user/{userid}')

################################################################################################################################################