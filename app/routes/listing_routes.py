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

def get_db_connection():
    return mysql.connector.connect(
        host="db",
        user="user",
        password="password",
        database="mydatabase"
    )

@listing_routes.route('/listings')
def view_listings():
    if 'user_id' not in session:
        flash('You need to log in first!', 'danger')
        return redirect(url_for('auth_routes.login'))

    db = None
    cursor = None
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        query = """
            SELECT 
                VehicleAd.ad_id, 
                VehicleAd.title, 
                VehicleAd.description, 
                VehicleAd.price, 
                Vehicle.brand, 
                Vehicle.model, 
                Vehicle.year, 
                Vehicle.vehicle_condition,
                Photo.content AS photo_url,
                CASE 
                    WHEN Car.vehicle_id IS NOT NULL THEN 'car'
                    WHEN Motorcycle.vehicle_id IS NOT NULL THEN 'motorcycle'
                    WHEN Van.vehicle_id IS NOT NULL THEN 'van'
                END as vehicle_type
            FROM 
                VehicleAd
            JOIN 
                Vehicle ON VehicleAd.vehicle_id = Vehicle.vehicle_id
            LEFT JOIN 
                Photo ON Vehicle.vehicle_id = Photo.vehicle_id
            LEFT JOIN
                Car ON Vehicle.vehicle_id = Car.vehicle_id
            LEFT JOIN
                Motorcycle ON Vehicle.vehicle_id = Motorcycle.vehicle_id
            LEFT JOIN
                Van ON Vehicle.vehicle_id = Van.vehicle_id
            WHERE 
                VehicleAd.status = 'available'
            ORDER BY
                VehicleAd.created_at DESC
        """
        cursor.execute(query)
        listings = cursor.fetchall()
        return render_template('listings.html', results=listings)

    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
        return redirect(url_for('auth_routes.login'))
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

@listing_routes.route('/mylistings')
def view_mylistings():
    if 'user_id' not in session:
        flash('You need to log in first!', 'danger')
        return redirect(url_for('auth_routes.login'))

    db = None
    cursor = None
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        user_id = session['user_id']

        query = """
            SELECT 
                VehicleAd.ad_id, 
                VehicleAd.title, 
                VehicleAd.description, 
                VehicleAd.price,
                Vehicle.brand, 
                Vehicle.model, 
                Vehicle.year,
                Vehicle.vehicle_condition,
                Photo.content AS photo_url,
                CASE 
                    WHEN Car.vehicle_id IS NOT NULL THEN 'car'
                    WHEN Motorcycle.vehicle_id IS NOT NULL THEN 'motorcycle'
                    WHEN Van.vehicle_id IS NOT NULL THEN 'van'
                END as vehicle_type
            FROM 
                VehicleAd
            JOIN 
                Vehicle ON VehicleAd.vehicle_id = Vehicle.vehicle_id
            LEFT JOIN 
                Photo ON Vehicle.vehicle_id = Photo.vehicle_id
            LEFT JOIN
                Car ON Vehicle.vehicle_id = Car.vehicle_id
            LEFT JOIN
                Motorcycle ON Vehicle.vehicle_id = Motorcycle.vehicle_id
            LEFT JOIN
                Van ON Vehicle.vehicle_id = Van.vehicle_id
            WHERE 
                VehicleAd.seller_id = %s
            ORDER BY
                VehicleAd.created_at DESC
        """
        cursor.execute(query, (user_id,))
        listings = cursor.fetchall()
        return render_template('my_ads.html', listings=listings)

    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
        return redirect(url_for('auth_routes.login'))
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

@listing_routes.route('/create-ad', methods=['GET'])
def select_vehicle_type():
    return render_template('select_vehicle_type.html')

@listing_routes.route('/create-ad/create_car', methods=['GET', 'POST'])
def create_car():
    if request.method == 'GET':
        return render_template('list_car_ad.html')

    if 'user_id' not in session:
        flash('You must be logged in to create an ad.', 'danger')
        return redirect(url_for('auth_routes.login'))

    db = None
    cursor = None
    try:
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

        photo = request.files.get('photos')
        if not photo or not allowed_file(photo.filename):
            flash('Invalid photo format. Please upload a JPG, JPEG, or PNG file.', 'danger')
            return redirect(url_for('listing_routes.create_car'))

        filename = secure_filename(photo.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        photo.save(file_path)
        photo_url = f'/static/uploads/{filename}'

        db = get_db_connection()
        cursor = db.cursor()

        vehicle_query = """
            INSERT INTO Vehicle (brand, series, model, year, fuel_type, km, hp, cc, 
                               drivetrain, color, guarantee, vehicle_condition, plate)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        vehicle_data = (brand, series, model, year, fuel_type, km, hp, cc, 
                       drivetrain, color, guarantee, condition, plate)
        cursor.execute(vehicle_query, vehicle_data)
        vehicle_id = cursor.lastrowid

        car_query = """
            INSERT INTO Car (vehicle_id, body_style, door_count, infotainment_screen, 
                           ac, airbags_count, lane_assist, abs)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """
        car_data = (vehicle_id, body_style, door_count, infotainment_screen, 
                   ac, airbags_count, lane_assist, abs)
        cursor.execute(car_query, car_data)

        ad_query = """
            INSERT INTO VehicleAd (title, description, price, status, vehicle_id, seller_id)
            VALUES (%s, %s, %s, 'available', %s, %s);
        """
        ad_data = (title, description, price, vehicle_id, session['user_id'])
        cursor.execute(ad_query, ad_data)

        photo_query = """
            INSERT INTO Photo (content, vehicle_id)
            VALUES (%s, %s);
        """
        photo_data = (photo_url, vehicle_id)
        cursor.execute(photo_query, photo_data)

        db.commit()
        flash('Car ad created successfully!', 'success')
        return redirect(url_for('listing_routes.view_listings'))

    except mysql.connector.Error as err:
        if db:
            db.rollback()
        flash(f'Error: {err}', 'danger')
        return redirect(url_for('listing_routes.create_car'))
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

@listing_routes.route('/create-ad/create_van', methods=['GET', 'POST'])
def create_van():
    if request.method == 'GET':
        return render_template('list_van_ad.html')

    if 'user_id' not in session:
        flash('You must be logged in to create an ad.', 'danger')
        return redirect(url_for('auth_routes.login'))

    db = None
    cursor = None
    try:
        title = request.form['title']
        description = request.form.get('description', '')
        price = request.form['price']
        brand = request.form['brand']
        model = request.form['model']
        year = request.form['year']
        cargo_capacity = request.form['cargo_capacity']
        cargo_length = request.form.get('cargo_length', None)
        cargo_width = request.form.get('cargo_width', None)
        cargo_height = request.form.get('cargo_height', None)
        max_payload = request.form.get('max_payload', None)
        fuel_type = request.form['fuel_type']
        km = request.form['km']
        color = request.form['color']
        condition = request.form['condition']

        photo = request.files.get('photos')
        if not photo or not allowed_file(photo.filename):
            flash('Invalid photo format. Please upload a JPG, JPEG, or PNG file.', 'danger')
            return redirect(url_for('listing_routes.create_van'))

        filename = secure_filename(photo.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        photo.save(file_path)
        photo_url = f'/static/uploads/{filename}'

        db = get_db_connection()
        cursor = db.cursor()

        vehicle_query = """
            INSERT INTO Vehicle (brand, model, year, fuel_type, km, color, vehicle_condition)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """
        vehicle_data = (brand, model, year, fuel_type, km, color, condition)
        cursor.execute(vehicle_query, vehicle_data)
        vehicle_id = cursor.lastrowid

        van_query = """
            INSERT INTO Van (vehicle_id, cargo_capacity, cargo_length, cargo_width, 
                           cargo_height, max_payload)
            VALUES (%s, %s, %s, %s, %s, %s);
        """
        van_data = (vehicle_id, cargo_capacity, cargo_length, cargo_width, 
                   cargo_height, max_payload)
        cursor.execute(van_query, van_data)

        ad_query = """
            INSERT INTO VehicleAd (title, description, price, status, vehicle_id, seller_id)
            VALUES (%s, %s, %s, 'available', %s, %s);
        """
        ad_data = (title, description, price, vehicle_id, session['user_id'])
        cursor.execute(ad_query, ad_data)

        photo_query = """
            INSERT INTO Photo (content, vehicle_id)
            VALUES (%s, %s);
        """
        photo_data = (photo_url, vehicle_id)
        cursor.execute(photo_query, photo_data)

        db.commit()
        flash('Van ad created successfully!', 'success')
        return redirect(url_for('listing_routes.view_listings'))

    except mysql.connector.Error as err:
        if db:
            db.rollback()
        flash(f'Error: {err}', 'danger')
        return redirect(url_for('listing_routes.create_van'))
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

@listing_routes.route('/create-ad/create_bike', methods=['GET', 'POST'])
def create_motorcycle():
    if request.method == 'GET':
        return render_template('list_motorcycle_ad.html')

    if 'user_id' not in session:
        flash('You must be logged in to create an ad.', 'danger')
        return redirect(url_for('auth_routes.login'))

    db = None
    cursor = None
    try:
        title = request.form['title']
        description = request.form.get('description', '')
        price = request.form['price']
        brand = request.form['brand']
        model = request.form['model']
        year = request.form['year']
        bike_type = request.form['type']
        engine_size = request.form['engine_size']
        km = request.form['km']
        color = request.form['color']
        condition = request.form['condition']

        photo = request.files.get('photos')
        if not photo or not allowed_file(photo.filename):
            flash('Invalid photo format. Please upload a JPG, JPEG, or PNG file.', 'danger')
            return redirect(url_for('listing_routes.create_motorcycle'))

        filename = secure_filename(photo.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        photo.save(file_path)
        photo_url = f'/static/uploads/{filename}'

        db = get_db_connection()
        cursor = db.cursor()

        vehicle_query = """
            INSERT INTO Vehicle (brand, model, year, km, color, vehicle_condition, engine_size)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """
        vehicle_data = (brand, model, year, km, color, condition, engine_size)
        cursor.execute(vehicle_query, vehicle_data)
        vehicle_id = cursor.lastrowid

        motorcycle_query = """
            INSERT INTO Motorcycle (vehicle_id, type)
            VALUES (%s, %s);
        """
        motorcycle_data = (vehicle_id, bike_type)
        cursor.execute(motorcycle_query, motorcycle_data)

        ad_query = """
            INSERT INTO VehicleAd (title, description, price, status, vehicle_id, seller_id)
            VALUES (%s, %s, %s, 'available', %s, %s);
        """
        ad_data = (title, description, price, vehicle_id, session['user_id'])
        cursor.execute(ad_query, ad_data)

        photo_query = """
            INSERT INTO Photo (content, vehicle_id)
            VALUES (%s, %s);
        """
        photo_data = (photo_url, vehicle_id)
        cursor.execute(photo_query, photo_data)

        db.commit()
        flash('Motorcycle ad created successfully!', 'success')
        return redirect(url_for('listing_routes.view_listings'))

    except mysql.connector.Error as err:
        if db:
            db.rollback()
        flash(f'Error: {err}', 'danger')
        return redirect(url_for('listing_routes.create_motorcycle'))
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

@listing_routes.route('/confirm-delete/<int:ad_id>', methods=['GET'])
def confirm_delete(ad_id):
    if 'user_id' not in session:
        flash('You need to log in first!', 'danger')
        return redirect(url_for('auth_routes.login'))

    db = None
    cursor = None
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

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
        if cursor:
            cursor.close()
        if db:
            db.close()

@listing_routes.route('/delete-ad/<int:ad_id>', methods=['POST'])
def delete_ad(ad_id):
    if 'user_id' not in session:
        flash('You need to log in first!', 'danger')
        return redirect(url_for('auth_routes.login'))

    db = None
    cursor = None
    try:
        db = get_db_connection()
        cursor = db.cursor()

        check_query = """
            SELECT seller_id FROM VehicleAd WHERE ad_id = %s
        """
        cursor.execute(check_query, (ad_id,))
        result = cursor.fetchone()

        if not result or result[0] != session['user_id']:
            flash("You are not authorized to delete this ad!", "danger")
            return redirect(url_for('listing_routes.view_mylistings'))

        delete_query = "DELETE FROM VehicleAd WHERE ad_id = %s"
        cursor.execute(delete_query, (ad_id,))
        db.commit()

        flash("Ad deleted successfully!", "success")
        return redirect(url_for('listing_routes.view_mylistings'))

    except mysql.connector.Error as err:
        if db:
            db.rollback()
        flash(f"Error deleting ad: {err}", "danger")
        return redirect(url_for('listing_routes.view_mylistings'))
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()