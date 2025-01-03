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


def allowed_file(filename, allowed_extensions=None):
    if allowed_extensions is None:
        allowed_extensions = ALLOWED_EXTENSIONS  # Default to global ALLOWED_EXTENSIONS
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


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
                Photo ON Vehicle.vehicle_id = Photo.vehicle_id AND Photo.is_primary = 1
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
        # Fetch listings for the logged-in user, including primary photo data
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
                Photo ON Vehicle.vehicle_id = Photo.vehicle_id AND Photo.is_primary = TRUE
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

        # Validate uploaded photos
        photos = request.files.getlist('photos')
        if not photos:
            flash('Please upload at least one photo.', 'danger')
            return redirect(url_for('listing_routes.create_car'))

        allowed_photos = []
        for photo in photos:
            if photo and allowed_file(photo.filename):
                allowed_photos.append(photo)

        if not allowed_photos:
            flash('Invalid photo format. Please upload JPG, JPEG, or PNG files.', 'danger')
            return redirect(url_for('listing_routes.create_car'))

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

            # Save photos and set `is_primary` attribute
            for i, photo in enumerate(allowed_photos):
                filename = secure_filename(photo.filename)
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                photo.save(file_path)

                # Generate the URL for the saved photo
                photo_url = f'/static/uploads/{filename}'

                # Set is_primary to True for the first photo, False for others
                is_primary = True if i == 0 else False

                # Save the photo data into the Photo table
                photo_query = """
                    INSERT INTO Photo (content, vehicle_id, is_primary)
                    VALUES (%s, %s, %s);
                """
                photo_data = (photo_url, vehicle_id, is_primary)
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


@listing_routes.route('/create-ad/create_van', methods=['GET', 'POST'])
def create_van():
    if request.method == 'GET':
        # Render the form
        return render_template('list_van_ad.html')

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

        seating_config = request.form['seating_config']
        sliding_doors = 'sliding_doors' in request.form
        cargo_volume = request.form['cargo_volume']
        removable_seats = 'removable_seats' in request.form
        roof_height = request.form['roof_height']
        van_type = request.form['van_type']

        # Validate uploaded photos
        photos = request.files.getlist('photos')
        if not photos:
            flash('Please upload at least one photo.', 'danger')
            return redirect(url_for('listing_routes.create_van'))

        allowed_photos = []
        for photo in photos:
            if photo and allowed_file(photo.filename):
                allowed_photos.append(photo)

        if not allowed_photos:
            flash('Invalid photo format. Please upload JPG, JPEG, or PNG files.', 'danger')
            return redirect(url_for('listing_routes.create_van'))

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

            # Insert data into Van table
            van_query = """
                INSERT INTO Van (vehicle_id, seating_config, sliding_doors, cargo_volume, removable_seats, roof_height, van_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """
            van_data = (vehicle_id, seating_config, sliding_doors, cargo_volume, removable_seats, roof_height, van_type)
            cursor.execute(van_query, van_data)

            # Insert data into VehicleAd table
            ad_query = """
                INSERT INTO VehicleAd (title, description, price, status, vehicle_id, seller_id)
                VALUES (%s, %s, %s, 'available', %s, %s);
            """
            ad_data = (title, description, price, vehicle_id, session['user_id'])
            cursor.execute(ad_query, ad_data)
            ad_id = cursor.lastrowid

            # Save photos and set `is_primary` attribute
            for i, photo in enumerate(allowed_photos):
                filename = secure_filename(photo.filename)
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                photo.save(file_path)

                # Generate the URL for the saved photo
                photo_url = f'/static/uploads/{filename}'

                # Set is_primary to True for the first photo, False for others
                is_primary = True if i == 0 else False

                # Save the photo data into the Photo table
                photo_query = """
                    INSERT INTO Photo (content, vehicle_id, is_primary)
                    VALUES (%s, %s, %s);
                """
                photo_data = (photo_url, vehicle_id, is_primary)
                cursor.execute(photo_query, photo_data)

            # Commit the transaction
            db.commit()

            flash('Van ad created successfully!', 'success')
            return redirect(url_for('listing_routes.view_listings'))

        except mysql.connector.Error as err:
            db.rollback()
            flash(f'Error: {err}', 'danger')
            return redirect(url_for('listing_routes.create_van'))

        finally:
            cursor.close()
            db.close()
  

@listing_routes.route('/create-ad/create_bike', methods=['GET', 'POST'])
def create_bike():
    if request.method == 'GET':
        # Render the form
        return render_template('list_bike_ad.html')

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

        bike_type = request.form['bike_type']
        frame_material = request.form['frame_material']
        saddle_height = request.form['saddle_height']
        handlebar_type = request.form['handlebar_type']

        # Validate uploaded photos
        photos = request.files.getlist('photos')
        if not photos:
            flash('Please upload at least one photo.', 'danger')
            return redirect(url_for('listing_routes.create_bike'))

        allowed_photos = []
        for photo in photos:
            if photo and allowed_file(photo.filename):
                allowed_photos.append(photo)

        if not allowed_photos:
            flash('Invalid photo format. Please upload JPG, JPEG, or PNG files.', 'danger')
            return redirect(url_for('listing_routes.create_bike'))

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

            # Insert data into Bike table
            bike_query = """
                INSERT INTO Bike (vehicle_id, bike_type, frame_material, saddle_height, handlebar_type)
                VALUES (%s, %s, %s, %s, %s);
            """
            bike_data = (vehicle_id, bike_type, frame_material, saddle_height, handlebar_type)
            cursor.execute(bike_query, bike_data)

            # Insert data into VehicleAd table
            ad_query = """
                INSERT INTO VehicleAd (title, description, price, status, vehicle_id, seller_id)
                VALUES (%s, %s, %s, 'available', %s, %s);
            """
            ad_data = (title, description, price, vehicle_id, session['user_id'])
            cursor.execute(ad_query, ad_data)
            ad_id = cursor.lastrowid

            # Save photos and set `is_primary` attribute
            for i, photo in enumerate(allowed_photos):
                filename = secure_filename(photo.filename)
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                photo.save(file_path)

                # Generate the URL for the saved photo
                photo_url = f'/static/uploads/{filename}'

                # Set is_primary to True for the first photo, False for others
                is_primary = True if i == 0 else False

                # Save the photo data into the Photo table
                photo_query = """
                    INSERT INTO Photo (content, vehicle_id, is_primary)
                    VALUES (%s, %s, %s);
                """
                photo_data = (photo_url, vehicle_id, is_primary)
                cursor.execute(photo_query, photo_data)

            # Commit the transaction
            db.commit()

            flash('Bike ad created successfully!', 'success')
            return redirect(url_for('listing_routes.view_listings'))

        except mysql.connector.Error as err:
            db.rollback()
            flash(f'Error: {err}', 'danger')
            return redirect(url_for('listing_routes.create_bike'))

        finally:
            cursor.close()
            db.close()
   


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
        
@listing_routes.route('/edit-ad/<ad_id>', methods=['GET', 'POST'])
def edit_ad(ad_id):
    if request.method == 'GET':
        try:
            db = get_db_connection()
            cursor = db.cursor(dictionary=True)

            # Fetch vehicle and ad details
            vehicle_query = """
                SELECT 
                    VehicleAd.ad_id, VehicleAd.title, VehicleAd.description, VehicleAd.price,
                    Vehicle.brand, Vehicle.series, Vehicle.model, Vehicle.year, Vehicle.fuel_type,
                    Vehicle.km, Vehicle.HP, Vehicle.cc, Vehicle.drivetrain, Vehicle.color, Vehicle.guarantee,
                    Vehicle.car_condition, Vehicle.plate,
                    Vehicle.vehicle_id
                FROM 
                    VehicleAd
                JOIN 
                    Vehicle ON VehicleAd.vehicle_id = Vehicle.vehicle_id
                WHERE 
                    VehicleAd.ad_id = %s;
            """
            cursor.execute(vehicle_query, (ad_id,))
            ad_data = cursor.fetchone()

            # Identify the subclass
            subclass_query = """
                SELECT
                    CASE
                        WHEN EXISTS (SELECT 1 FROM Car WHERE vehicle_id = %s) THEN 'Car'
                        WHEN EXISTS (SELECT 1 FROM Van WHERE vehicle_id = %s) THEN 'Van'
                        WHEN EXISTS (SELECT 1 FROM Bike WHERE vehicle_id = %s) THEN 'Bike'
                        ELSE NULL
                    END AS subclass
            """
            cursor.execute(subclass_query, (ad_data['vehicle_id'], ad_data['vehicle_id'], ad_data['vehicle_id']))
            subclass = cursor.fetchone()['subclass']

            # Fetch subclass-specific attributes
            if subclass == 'Car':
                subclass_query = """
                    SELECT body_style, door_count, infotainment_screen, ac, emission_standard,
                        airbags_count, lane_assist, abs
                    FROM Car WHERE vehicle_id = %s;
                """
            elif subclass == 'Van':
                subclass_query = """
                    SELECT seating_config, sliding_doors, cargo_volume, removable_seats,
                        roof_height, van_type
                    FROM Van WHERE vehicle_id = %s;
                """
            elif subclass == 'Bike':
                subclass_query = """
                    SELECT bike_type, frame_material, saddle_height, handlebar_type
                    FROM Bike WHERE vehicle_id = %s;
                """
            else:
                subclass_query = None

            if subclass_query:
                cursor.execute(subclass_query, (ad_data['vehicle_id'],))
                subclass_attributes = cursor.fetchone()
            else:
                subclass_attributes = {}

            # Fetch photos for the vehicle
            photo_query = """
                SELECT p_id, content, is_primary
                FROM Photo
                WHERE vehicle_id = %s;
            """
            cursor.execute(photo_query, (ad_data['vehicle_id'],))
            photos = cursor.fetchall()

            # Fetch expert report for the vehicle
            report_query = """
                SELECT w_id, content
                FROM ExpertReport
                WHERE vehicle_id = %s;
            """
            cursor.execute(report_query, (ad_data['vehicle_id'],))
            report = cursor.fetchone()

            return render_template('edit_ad.html', ad=ad_data, photos=photos, report=report, subclass=subclass, subclass_attributes=subclass_attributes)

        except mysql.connector.Error as err:
            flash(f"Error fetching ad details: {err}", "danger")
            return redirect(url_for('listing_routes.view_mylistings'))

        finally:
            cursor.close()
            db.close()

    if request.method == 'POST':
        try:
            db = get_db_connection()
            cursor = db.cursor()

            # Extract and validate vehicle and ad data
            title = request.form['title']
            description = request.form['description']
            price = request.form['price']
            brand = request.form['brand']
            series = request.form['series']
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

            # Update Vehicle table
            vehicle_query = """
                UPDATE Vehicle
                SET brand = %s, series = %s, model = %s, year = %s, fuel_type = %s, km = %s,
                    HP = %s, cc = %s, drivetrain = %s, color = %s, guarantee = %s,
                    car_condition = %s, plate = %s
                WHERE vehicle_id = %s;
            """
            vehicle_data = (brand, series, model, year, fuel_type, km, hp, cc, drivetrain, color,
                            guarantee, condition, plate, request.form['vehicle_id'])
            cursor.execute(vehicle_query, vehicle_data)

            # Update subclass-specific table
            subclass = request.form['subclass']
            if subclass == 'Car':
                body_style = request.form['body_style']
                door_count = request.form['door_count']
                infotainment_screen = 'infotainment_screen' in request.form
                ac = 'ac' in request.form
                emission_standard = request.form.get('emission_standard', None)
                airbags_count = request.form.get('airbags_count', None)
                lane_assist = 'lane_assist' in request.form
                abs = 'abs' in request.form
                subclass_query = """
                    UPDATE Car
                    SET body_style = %s, door_count = %s, infotainment_screen = %s, ac = %s,
                        emission_standard = %s, airbags_count = %s, lane_assist = %s, abs = %s
                    WHERE vehicle_id = %s;
                """
                subclass_data = (body_style, door_count, infotainment_screen, ac, emission_standard,
                                airbags_count, lane_assist, abs, request.form['vehicle_id'])
            elif subclass == 'Van':
                seating_config = request.form['seating_config']
                sliding_doors = 'sliding_doors' in request.form
                cargo_volume = request.form['cargo_volume']
                removable_seats = 'removable_seats' in request.form
                roof_height = request.form['roof_height']
                van_type = request.form['van_type']
                subclass_query = """
                    UPDATE Van
                    SET seating_config = %s, sliding_doors = %s, cargo_volume = %s, removable_seats = %s,
                        roof_height = %s, van_type = %s
                    WHERE vehicle_id = %s;
                """
                subclass_data = (seating_config, sliding_doors, cargo_volume, removable_seats, roof_height, van_type, request.form['vehicle_id'])
            elif subclass == 'Motorcycle':
                bike_type = request.form['bike_type']
                frame_material = request.form['frame_material']
                saddle_height = request.form['saddle_height']
                handlebar_type = request.form['handlebar_type']
                subclass_query = """
                    UPDATE Motorcycle
                    SET bike_type = %s, frame_material = %s, saddle_height = %s, handlebar_type = %s
                    WHERE vehicle_id = %s;
                """
                subclass_data = (bike_type, frame_material, saddle_height, handlebar_type, request.form['vehicle_id'])

            if subclass_query:
                cursor.execute(subclass_query, subclass_data)

            # Update VehicleAd table
            ad_query = """
                UPDATE VehicleAd
                SET title = %s, description = %s, price = %s
                WHERE ad_id = %s;
            """
            ad_data = (title, description, price, ad_id)
            cursor.execute(ad_query, ad_data)

            # Handle photo removals
            if 'remove_photos' in request.form:
                photo_ids_to_remove = request.form.getlist('remove_photos')
                new_primary_photo_id = request.form.get('primary_photo')
                vehicle_id = request.form['vehicle_id']

                # Check for conflicts: Removing a photo that is set as primary
                if new_primary_photo_id and new_primary_photo_id in photo_ids_to_remove:
                    flash("Error: You cannot delete a photo that is set as the new primary photo. Please correct your selection.", "danger")
                    return redirect(url_for('listing_routes.edit_ad', ad_id=vehicle_id))

                # Prevent deleting the current primary photo
                check_primary_query = """
                    SELECT p_id FROM Photo
                    WHERE p_id IN (%s) AND is_primary = TRUE;
                """ % ','.join(['%s'] * len(photo_ids_to_remove))
                cursor.execute(check_primary_query, tuple(photo_ids_to_remove))
                primary_photos_to_remove = cursor.fetchall()

                if primary_photos_to_remove:
                    flash("Error: You cannot delete the current primary photo. Please set a different photo as primary first.", "danger")
                    return redirect(url_for('listing_routes.edit_ad', ad_id=vehicle_id))

                # Proceed to delete non-primary photos
                remove_query = "DELETE FROM Photo WHERE p_id = %s;"
                for photo_id in photo_ids_to_remove:
                    cursor.execute(remove_query, (photo_id,))

            # Handle setting a new primary photo
            if 'primary_photo' in request.form:
                new_primary_photo_id = request.form['primary_photo']
                vehicle_id = request.form['vehicle_id']

                # Reset all photos for this vehicle to non-primary
                reset_primary_query = """
                    UPDATE Photo
                    SET is_primary = FALSE
                    WHERE vehicle_id = %s;
                """
                cursor.execute(reset_primary_query, (vehicle_id,))

                # Set the selected photo as primary
                set_primary_query = """
                    UPDATE Photo
                    SET is_primary = TRUE
                    WHERE p_id = %s;
                """
                cursor.execute(set_primary_query, (new_primary_photo_id,))

            # Handle new photo uploads
            new_photos = request.files.getlist('photos')
            for photo in new_photos:
                if photo and allowed_file(photo.filename):
                    filename = secure_filename(photo.filename)
                    filepath = os.path.join(UPLOAD_FOLDER, filename)
                    photo.save(filepath)

                    # Insert the photo into the database
                    photo_query = """
                        INSERT INTO Photo (content, vehicle_id, is_primary)
                        VALUES (%s, %s, %s);
                    """
                    is_primary = False  # New photos cannot be primary immediately
                    cursor.execute(photo_query, (f'/static/uploads/{filename}', request.form['vehicle_id'], is_primary))

            # Handle expert report removal
            if 'remove_report' in request.form:
                report_id = request.form.get('remove_report')
                if report_id:
                    delete_report_query = "DELETE FROM ExpertReport WHERE w_id = %s;"
                    cursor.execute(delete_report_query, (report_id,))
            # Handle uploading a new expert report
            if 'expert_report' in request.files:
                report_file = request.files['expert_report']
                if report_file and allowed_file(report_file.filename, allowed_extensions={'pdf'}):
                    report_filename = secure_filename(report_file.filename)
                    report_filepath = os.path.join(UPLOAD_FOLDER, report_filename)
                    report_file.save(report_filepath)

                    # Insert or update the expert report in the database
                    insert_or_update_report_query = """
                        INSERT INTO ExpertReport (content, vehicle_id)
                        VALUES (%s, %s)
                        ON DUPLICATE KEY UPDATE content = VALUES(content);
                    """
                    cursor.execute(insert_or_update_report_query, 
                                (f'/static/uploads/{report_filename}', request.form['vehicle_id']))
            db.commit()
            flash("Ad updated successfully!", "success")
            return redirect(url_for('listing_routes.view_mylistings'))

        except mysql.connector.Error as err:
            db.rollback()
            flash(f"Error updating ad: {err}", "danger")
            return redirect(url_for('listing_routes.edit_ad', ad_id=ad_id))

        finally:
            cursor.close()
            db.close()

@listing_routes.route('/view-ad/<int:ad_id>', methods=['GET'])
def view_ad_details(ad_id):
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Fetch ad details including vehicle_id
        ad_query = """
            SELECT 
                VehicleAd.ad_id, 
                VehicleAd.title, 
                VehicleAd.description, 
                VehicleAd.price, 
                VehicleAd.status,
                VehicleAd.seller_id, 
                Vehicle.vehicle_id, 
                Vehicle.brand, 
                Vehicle.series, 
                Vehicle.model, 
                Vehicle.year, 
                Vehicle.fuel_type, 
                Vehicle.km, 
                Vehicle.hp, 
                Vehicle.cc, 
                Vehicle.drivetrain, 
                Vehicle.color, 
                Vehicle.guarantee, 
                Vehicle.car_condition, 
                Vehicle.plate
            FROM 
                VehicleAd
            JOIN 
                Vehicle ON VehicleAd.vehicle_id = Vehicle.vehicle_id
            WHERE 
                VehicleAd.ad_id = %s;
        """
        cursor.execute(ad_query, (ad_id,))
        ad_details = cursor.fetchone()

        if not ad_details:
            flash('Ad not found.', 'danger')
            return redirect(url_for('listing_routes.view_listings'))

        # Fetch all photos for the vehicle, including marking the primary photo
        photo_query = """
            SELECT content, is_primary
            FROM Photo
            WHERE vehicle_id = %s;
        """
        cursor.execute(photo_query, (ad_details['vehicle_id'],))
        photos = cursor.fetchall()

        # Fetch subclass details (Car, Van, Bike)
        subclass_queries = {
            'Car': """
                SELECT body_style, door_count, infotainment_screen, ac, emission_standard, airbags_count, lane_assist, abs
                FROM Car WHERE vehicle_id = %s;
            """,
            'Van': """
                SELECT seating_config, sliding_doors, cargo_volume, removable_seats, roof_height, van_type
                FROM Van WHERE vehicle_id = %s;
            """,
            'Bike': """
                SELECT bike_type, frame_material, saddle_height, handlebar_type
                FROM Bike WHERE vehicle_id = %s;
            """
        }

        subclass_data = None
        subclass = None
        for sub, query in subclass_queries.items():
            cursor.execute(query, (ad_details['vehicle_id'],))
            result = cursor.fetchone()
            if result:
                subclass = sub
                subclass_data = result
                break

        return render_template(
            'view_ad_details.html', 
            ad=ad_details, 
            subclass=subclass, 
            subclass_attributes=subclass_data, 
            photos=photos
        )

    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
        return redirect(url_for('listing_routes.view_listings'))

    finally:
        cursor.close()
        db.close()

@listing_routes.route('/search', methods=['GET', 'POST'])
def search_ads():
    # Ensure the user is logged in
    if 'user_id' not in session:
        flash('You need to log in first!', 'danger')
        return redirect(url_for('auth_routes.login'))

    # Retrieve search and filter parameters
    query = request.args.get('query', '')  # Search query
    min_price = request.args.get('min_price', None)
    max_price = request.args.get('max_price', None)
    min_year = request.args.get('min_year', None)
    max_year = request.args.get('max_year', None)
    fuel_type = request.args.get('fuel_type', None)
    car_condition = request.args.get('car_condition', None)

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Base SQL query
        sql_query = """
            SELECT
                VehicleAd.ad_id,
                VehicleAd.title,
                VehicleAd.description,
                VehicleAd.price,
                Vehicle.brand,
                Vehicle.model,
                Vehicle.year,
                Vehicle.fuel_type,
                Vehicle.car_condition,
                Photo.content AS photo_url
            FROM
                VehicleAd
            JOIN
                Vehicle ON VehicleAd.vehicle_id = Vehicle.vehicle_id
            LEFT JOIN
                Photo ON Vehicle.vehicle_id = Photo.vehicle_id AND Photo.is_primary = 1
            WHERE
                VehicleAd.status = 'available'
        """

        # Add search conditions
        search_conditions = []
        if query:
            search_conditions.append("(VehicleAd.title LIKE %s OR Vehicle.brand LIKE %s OR Vehicle.model LIKE %s)")

        # Add filter conditions
        filter_conditions = []
        if min_price:
            filter_conditions.append("VehicleAd.price >= %s")
        if max_price:
            filter_conditions.append("VehicleAd.price <= %s")
        if min_year:
            filter_conditions.append("Vehicle.year >= %s")
        if max_year:
            filter_conditions.append("Vehicle.year <= %s")
        if fuel_type:
            filter_conditions.append("Vehicle.fuel_type = %s")
        if car_condition:
            filter_conditions.append("Vehicle.car_condition = %s")

        # Combine conditions
        conditions = search_conditions + filter_conditions
        if conditions:
            sql_query += " AND " + " AND ".join(conditions)

        # Prepare query parameters
        params = []
        if query:
            like_query = f"%{query}%"
            params.extend([like_query, like_query, like_query])
        if min_price:
            params.append(min_price)
        if max_price:
            params.append(max_price)
        if min_year:
            params.append(min_year)
        if max_year:
            params.append(max_year)
        if fuel_type:
            params.append(fuel_type)
        if car_condition:
            params.append(car_condition)

        # Execute query
        cursor.execute(sql_query, params)
        search_results = cursor.fetchall()

        return render_template('listings.html', results=search_results)

    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
        return redirect(url_for('auth_routes.dashboard'))

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals():
            db.close()




