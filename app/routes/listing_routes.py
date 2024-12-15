import base64
from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from werkzeug.utils import secure_filename
import mysql.connector
import os

listing_routes = Blueprint('listing_routes', __name__)

UPLOAD_FOLDER = 'app/static/uploads/'  # Directory to save uploaded files
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Establish database connection
def get_db_connection():
    return mysql.connector.connect(
        host="db",
        user="user",
        password="password",
        database="mydatabase"
    )

@listing_routes.route('/listings')
def view_listings():
    # Ensure the user is logged in
    if 'user_id' not in session:
        flash('You need to log in first!', 'danger')
        return redirect(url_for('auth_routes.login'))

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Fetch listings from all users
        query = """
            SELECT 
                VehicleAd.ad_id, 
                VehicleAd.title, 
                VehicleAd.description, 
                VehicleAd.price, 
                Vehicle.brand, 
                Vehicle.model, 
                Vehicle.year, 
                Photo.content AS photo_url
            FROM 
                VehicleAd
            JOIN 
                Vehicle ON VehicleAd.vehicle_id = Vehicle.vehicle_id
            LEFT JOIN 
                Photo ON Vehicle.vehicle_id = Photo.vehicle_id
            WHERE 
                VehicleAd.status = 'available'
        """
        cursor.execute(query)
        listings = cursor.fetchall()
        print(listings)
    
        return render_template('listings.html', results=listings)

    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
        return redirect(url_for('auth_routes.login'))
    finally:
        cursor.close()
        db.close()
        
@listing_routes.route('/mylistings')
def view_mylistings():
    # Ensure the user is logged in
    if 'user_id' not in session:
        flash('You need to log in first!', 'danger')
        return redirect(url_for('auth_routes.login'))

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        user_id = session['user_id']
        # Fetch listings for the logged-in user, including photo data
        query = """
            SELECT 
                VehicleAd.ad_id, 
                VehicleAd.title, 
                VehicleAd.description, 
                VehicleAd.price,
                Vehicle.brand, 
                Vehicle.model, 
                Vehicle.year,
                Photo.content AS photo_url
            FROM 
                VehicleAd
            JOIN 
                Vehicle ON VehicleAd.vehicle_id = Vehicle.vehicle_id
            LEFT JOIN 
                Photo ON Vehicle.vehicle_id = Photo.vehicle_id
            WHERE 
                VehicleAd.seller_id = %s
        """
        cursor.execute(query, (user_id,))
        listings = cursor.fetchall()

        return render_template('my_ads.html', listings=listings)
    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
        return redirect(url_for('auth_routes.login'))
    finally:
        cursor.close()
        db.close()
        
        
@listing_routes.route('/create-ad', methods=['GET'])
def select_vehicle_type():
    # Render the page to select vehicle type
    return render_template('select_vehicle_type.html')        


@listing_routes.route('/create-ad/create_car', methods=['GET', 'POST'])
def create_car():
    if request.method == 'GET':
        # Render the form
        return render_template('list_car_ad.html')

    if request.method == 'POST':
        # Validate session
        if 'user_id' not in session:
            flash('You must be logged in to create an ad.', 'danger')
            return redirect(url_for('auth_routes.login'))

        # Extract data from form
        title = request.form['title']
        description = request.form.get('description', '')
        price = request.form['price']
        brand = request.form['brand']
        series = request.form.get('series', None)
        model = request.form['model']
        year = request.form['year']
        fuel_type = request.form['fuel_type']
        km = request.form['km']
        hp = request.form.get('hp', None)
        cc = request.form.get('cc', None)
        drivetrain = request.form['drivetrain']
        color = request.form['color']
        guarantee = request.form.get('guarantee', None)
        plate = request.form.get('plate', None)
        condition = request.form['condition']

        body_style = request.form['body_style']
        door_count = request.form['door_count']
        airbags_count = request.form.get('airbags_count', None)
        infotainment_screen = 'infotainment_screen' in request.form
        ac = 'ac' in request.form
        lane_assist = 'lane_assist' in request.form
        abs = 'abs' in request.form

        # Validate uploaded photo
        photo = request.files.get('photos')
        if not photo or not allowed_file(photo.filename):
            flash('Invalid photo format. Please upload a JPG, JPEG, or PNG file.', 'danger')
            return redirect(url_for('listing_routes.create_car'))

        # Save the photo locally
        filename = secure_filename(photo.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        photo.save(file_path)

        # Generate the URL for the saved photo
        photo_url = f'/static/uploads/{filename}'

        # Extract optional photo metadata
        photo_width = request.form.get('width', None)
        photo_height = request.form.get('height', None)

        try:
            db = get_db_connection()
            cursor = db.cursor()

            # Insert data into Vehicle table
            vehicle_query = """
                INSERT INTO Vehicle (brand, series, model, year, fuel_type, km, hp, cc, drivetrain, color, guarantee, car_condition, plate)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """
            vehicle_data = (brand, series, model, year, fuel_type, km, hp, cc, drivetrain, color, guarantee, condition, plate)
            cursor.execute(vehicle_query, vehicle_data)
            vehicle_id = cursor.lastrowid

            # Insert data into Car table
            car_query = """
                INSERT INTO Car (vehicle_id, body_style, door_count, infotainment_screen, ac, airbags_count, lane_assist, abs)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            """
            car_data = (vehicle_id, body_style, door_count, infotainment_screen, ac, airbags_count, lane_assist, abs)
            cursor.execute(car_query, car_data)

            # Insert data into VehicleAd table
            ad_query = """
                INSERT INTO VehicleAd (title, description, price, status, vehicle_id, seller_id)
                VALUES (%s, %s, %s, 'available', %s, %s);
            """
            ad_data = (title, description, price, vehicle_id, session['user_id'])
            cursor.execute(ad_query, ad_data)
            ad_id = cursor.lastrowid

            # Save the photo URL and optional metadata into the Photo table
            photo_query = """
                INSERT INTO Photo (content, vehicle_id, width, height)
                VALUES (%s, %s, %s, %s);
            """
            photo_data = (photo_url, vehicle_id, photo_width, photo_height)
            cursor.execute(photo_query, photo_data)

            # Commit the transaction
            db.commit()

            flash('Ad created successfully!', 'success')
            return redirect(url_for('listing_routes.view_listings'))

        except mysql.connector.Error as err:
            db.rollback()
            flash(f'Error: {err}', 'danger')
            return redirect(url_for('listing_routes.create_car'))
        finally:
            cursor.close()
            db.close() 


@listing_routes.route('/create-ad/create_van', methods=['GET'])
def create_van():
    # Render the page to select vehicle type
    return render_template('select_vehicle_type.html')   

@listing_routes.route('/create-ad/create_bike', methods=['GET'])
def create_motorcycle():
    # Render the page to select vehicle type
    return render_template('select_vehicle_type.html')   


@listing_routes.route('/confirm-delete/<int:ad_id>', methods=['GET'])
def confirm_delete(ad_id):
    # Ensure the user is logged in
    if 'user_id' not in session:
        flash('You need to log in first!', 'danger')
        return redirect(url_for('auth_routes.login'))

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Fetch the ad details to display on the confirmation page
        query = """
            SELECT ad_id, title
            FROM VehicleAd
            WHERE ad_id = %s AND seller_id = %s
        """
        cursor.execute(query, (ad_id, session['user_id']))
        ad = cursor.fetchone()

        if not ad:
            flash("Ad not found or you are not authorized to delete it.", "danger")
            return redirect(url_for('listing_routes.view_mylistings'))

        return render_template('confirm_delete.html', ad=ad)

    except mysql.connector.Error as err:
        flash(f"Error: {err}", "danger")
        return redirect(url_for('listing_routes.view_mylistings'))
    finally:
        cursor.close()
        db.close()
        
@listing_routes.route('/delete-ad/<int:ad_id>', methods=['POST'])
def delete_ad(ad_id):
    # Ensure the user is logged in
    if 'user_id' not in session:
        flash('You need to log in first!', 'danger')
        return redirect(url_for('auth_routes.login'))

    try:
        db = get_db_connection()
        cursor = db.cursor()

        # Check if the logged-in user is the owner of the ad
        check_query = """
            SELECT seller_id FROM VehicleAd WHERE ad_id = %s
        """
        cursor.execute(check_query, (ad_id,))
        result = cursor.fetchone()

        if not result or result[0] != session['user_id']:
            flash("You are not authorized to delete this ad!", "danger")
            return redirect(url_for('listing_routes.view_mylistings'))

        # Delete the ad
        delete_query = "DELETE FROM VehicleAd WHERE ad_id = %s"
        cursor.execute(delete_query, (ad_id,))
        db.commit()

        flash("Ad deleted successfully!", "success")
        return redirect(url_for('listing_routes.view_mylistings'))

    except mysql.connector.Error as err:
        db.rollback()
        flash(f"Error deleting ad: {err}", "danger")
        return redirect(url_for('listing_routes.view_mylistings'))
    finally:
        cursor.close()
        db.close()
