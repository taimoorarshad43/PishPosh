import io
from time import sleep

from flask import Blueprint, session, render_template, redirect, flash, request, jsonify
from PIL import Image

from forms import ProductUploadForm
from models import User, Product, db
from mistraldescription import getproductdescription, encodeimage, decodeimage


uploadroutes = Blueprint("uploadroutes", __name__)

############################################################## Upload Routes #################################################################

@uploadroutes.route('/upload/<int:userid>', methods = ['POST'])
def pictureupload(userid):

    productform = ProductUploadForm()

    if session.get("userid", None) is None:
        flash('Please login to upload products', 'btn-info')
        return redirect('/')

    if productform.validate_on_submit(): # Handles our POST request for the form submission
        try:
            productname = productform.name.data                    # Refactoring to have WTForms handle the file submission
            productdescription = productform.description.data
            productprice = productform.price.data
            file = productform.image.data

            file_ext = file.filename.split('.')[-1]                # Check if the file is an image and if its in the accepted formats
            print("File ext: ", file_ext)
            if file_ext not in ['jpg', 'jpeg', 'png']:
                session['ProductFileError'] = 'Invalid File Type'          # If invalid file type, we'll add an error to session and display it after a redirect
            else:
                if file_ext == 'jpg':
                    file_ext = 'jpeg'

            # Generate new product and attach it to passed userid
            product = Product(productname = productname, productdescription = productdescription, price = productprice, user_id = userid)

            image = Image.open(file)
            newsize = (200,200)                         # Resizing the image to be compact
            image = image.resize(newsize)
            stream = io.BytesIO()
            image.save(stream, format = file_ext.replace('.','').upper())         # Save the image as stream of bytes 
            file = stream.getvalue()

            # Save the file as base64 encoding to its image filed in DB.
            product.encode_image(file)

            db.session.add(product)
            db.session.commit()

        except Exception as e:                                          # If certain fields are missing, redirect to user detail with flashed message
            if not productname or productname.replace("-","").isdigit() == True:
                session['ProductNameError'] = 'Invalid Product Name'
            if not productdescription or productname.replace("-","").isdigit() == True:
                session['ProductDescriptionError'] = 'Invalid Product Description'
            if not productprice:
                session['ProductPriceError'] = 'Invalid Product Price'
            print(e)
            flash('Product Upload failed (check required fields)', 'btn-danger')
            return redirect(f'/userdetail')

    print("If condition failed")
    flash('Product Listed Successfully', 'btn-success')
    return redirect(f'/user/{userid}')                          # After success, redirect to their user page with their products.

@uploadroutes.route('/upload/<int:userid>/ai')
def uploadai(userid):

    if session.get("userid", None) is None:
        flash('Please login to upload products', 'btn-info')
        return redirect('/')

    user = User.query.get_or_404(userid)
    return render_template('aiupload.html', user=user)

@uploadroutes.route('/upload/aiprocess', methods = ['POST'])
def aiprocess():

    image = request.files['file']
    title_prompt = "Give me a short title for this picture that is 2-5 words long. This title should describe the picture as a product"
    description_prompt = "Give me a product description for this picture that is about 6-12 words long."

    img_data = encodeimage(image)               # Need both an encoded and decoded image for the HTML and API calls respectively
    img_data_decoded = decodeimage(img_data)

    title = getproductdescription(img_data_decoded, title_prompt)     # Get both the title and description from Mistral AI
    sleep(2) # To avoid Mistral API's rate limit
    description = getproductdescription(img_data_decoded, description_prompt)

    output = {"title" : title,
              "description" : description}

    return jsonify(output)


@uploadroutes.route('/upload/<int:userid>/aiconfirm')
def aiconfirm(userid):

    if session.get("userid", None) is None:
        flash('Please login to upload products', 'btn-info')
        return redirect('/')

    user = User.query.get_or_404(userid)

    img_data_decoded = session.get("aiimage", 1)
    description = session.get("aidesc", 1)
    title = session.get("aititle", 1)

    return render_template('aiconfirm.html', image=img_data_decoded, user=user, title=title, description=description)

##########################################################################################################################################









################################# Temporary Back Up #######################################################################

# @uploadroutes.route('/upload/<int:userid>', methods = ['POST'])
# def pictureupload(userid):

#     if session.get("userid", None) is None:
#         flash('Please login to upload products', 'btn-info')
#         return redirect('/')

#     try:
#         file = request.files['file']
#         productname = request.form['productname']
#         productdescription = request.form['productdescription']
#         productprice = request.form['productprice']
        
#         # Generate new product and attach it to passed userid
#         product = Product(productname = productname, productdescription = productdescription, price = productprice, user_id = userid)

#         image = Image.open(file)
#         newsize = (200,200) # Resizing the image to be compact
#         image = image.resize(newsize)
#         stream = io.BytesIO()
#         image.save(stream, format = 'JPEG')         # Save the image as stream of bytes
#         file = stream.getvalue()

#         # Save the file as base64 encoding to its image filed in DB.
#         product.encode_image(file)

#         db.session.add(product)
#         db.session.commit()

#     except Exception as e:                                          # If certain fields are missing, redirect to user detail with flashed message
#         print(e)
#         flash('Product Upload failed (check required fields)', 'btn-danger')
#         return redirect(f'/user/{userid}')

#     flash('Product Listed Successfully', 'btn-success')
#     return redirect(f'/user/{userid}')                          # After success, redirect to their user page with their products.