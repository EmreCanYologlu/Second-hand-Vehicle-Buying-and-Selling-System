from flask import Blueprint, abort, render_template, request, redirect, url_for, flash
import mysql.connector # type: ignore
import os


# Blueprint setup
ad_routes = Blueprint('ad_routes', __name__)

# Database configuration
db_config = {
    'host': os.getenv('MYSQL_HOST', 'db'),
    'user': os.getenv('MYSQL_USER', 'user'),
    'password': os.getenv('MYSQL_PASSWORD', 'password'),
    'database': os.getenv('MYSQL_DB', 'mydatabase')
}

@ad_routes.route("/<int:ad_id>")
def ad_details(ad_id):
    """Render Ad Details page."""
    try:
        # Establish database connection
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # Fetch Ad details with Vehicle, Seller, and Photos
        query_ad = """
            SELECT v.brand, v.model, v.year, v.color, v.vehicle_condition,
                   a.title, a.description, a.price, u.username AS seller
            FROM VehicleAd a
            JOIN Vehicle v ON a.vehicle_id = v.vehicle_id
            JOIN User u ON a.seller_id = u.user_id
            WHERE a.ad_id = %s
        """
        cursor.execute(query_ad, (ad_id,))
        ad = cursor.fetchone()

        if not ad:
            abort(404, description="Ad not found")

        # Fetch all photos for the vehicle
        query_photos = """
            SELECT p.content AS image
            FROM Photo p
            JOIN Vehicle v ON p.vehicle_id = v.vehicle_id
            WHERE v.vehicle_id = (SELECT vehicle_id FROM VehicleAd WHERE ad_id = %s)
        """
        cursor.execute(query_photos, (ad_id,))
        photos = cursor.fetchall()

        return render_template("ad_details.html", ad=ad, photos=photos)

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        abort(500, description="Internal Server Error")
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()

# Helper function to handle file uploads
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def save_uploaded_photos(files):
    """Save uploaded photos and return their file paths."""
    photo_paths = []
    for photo in files:
        if photo and photo.filename:
            filename = photo.filename
            save_path = os.path.join(UPLOAD_FOLDER, filename)
            photo.save(save_path)
            photo_paths.append(f"/{save_path}")
    return photo_paths

# Create Car Ad Route
@ad_routes.route("/create_car", methods=["GET", "POST"])
def create_car():
    """Handle car ad creation."""
    if request.method == "POST":
        # Collect form data
        title = request.form.get("title")
        description = request.form.get("description")
        price = request.form.get("price")
        brand = request.form.get("brand")
        model = request.form.get("model")
        year = request.form.get("year")
        fuel_type = request.form.get("fuel_type")
        mileage = request.form.get("mileage")
        body_style = request.form.get("body_style")
        door_count = request.form.get("door_count")
        color = request.form.get("color")

        # Handle file uploads
        photos = request.files.getlist("photos")  # Get list of uploaded files
        photo_paths = save_uploaded_photos(photos)

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        try:
            # Insert vehicle data
            cursor.execute("""
                INSERT INTO Vehicle (brand, model, year, fuel_type, mileage, body_style, door_count, color)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (brand, model, year, fuel_type, mileage, body_style, door_count, color))
            vehicle_id = cursor.lastrowid

            # Insert ad data
            cursor.execute("""
                INSERT INTO VehicleAd (title, description, price, vehicle_id)
                VALUES (%s, %s, %s, %s)
            """, (title, description, price, vehicle_id))

            # Insert photo paths into the Photo table
            for path in photo_paths:
                cursor.execute("""
                    INSERT INTO Photo (vehicle_id, content)
                    VALUES (%s, %s)
                """, (vehicle_id, path))

            conn.commit()
            flash("Car ad created successfully!", "success")
            return redirect(url_for("ad_routes.create_car"))
        except Exception as e:
            flash(f"An error occurred: {e}", "danger")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    return render_template("list_car_ad.html")

# Create Motorcycle Ad Route
@ad_routes.route("/create_motorcycle", methods=["GET", "POST"])
def create_motorcycle():
    """Handle motorcycle ad creation."""
    if request.method == "POST":
        # Collect form data
        title = request.form.get("title")
        description = request.form.get("description")
        price = request.form.get("price")
        brand = request.form.get("brand")
        model = request.form.get("model")
        year = request.form.get("year")
        bike_type = request.form.get("type")
        engine_size = request.form.get("engine_size")
        mileage = request.form.get("km")
        color = request.form.get("color")
        condition = request.form.get("condition")

        # Handle file uploads
        photos = request.files.getlist("photos")  # Get list of uploaded files
        photo_paths = save_uploaded_photos(photos)

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        try:
            # Insert motorcycle data
            cursor.execute("""
                INSERT INTO Vehicle (brand, model, year, type, engine_size, mileage, color, vehicle_condition)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (brand, model, year, bike_type, engine_size, mileage, color, condition))
            vehicle_id = cursor.lastrowid

            # Insert ad data
            cursor.execute("""
                INSERT INTO VehicleAd (title, description, price, vehicle_id)
                VALUES (%s, %s, %s, %s)
            """, (title, description, price, vehicle_id))

            # Insert photo paths into the Photo table
            for path in photo_paths:
                cursor.execute("""
                    INSERT INTO Photo (vehicle_id, content)
                    VALUES (%s, %s)
                """, (vehicle_id, path))

            conn.commit()
            flash("Motorcycle ad created successfully!", "success")
            return redirect(url_for("ad_routes.create_motorcycle"))
        except Exception as e:
            flash(f"An error occurred: {e}", "danger")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    return render_template("list_motorcycle_ad.html")

# Create Van Ad Route
@ad_routes.route("/create_van", methods=["GET", "POST"])
def create_van():
    """Handle van ad creation."""
    if request.method == "POST":
        # Collect form data
        title = request.form.get("title")
        description = request.form.get("description")
        price = request.form.get("price")
        brand = request.form.get("brand")
        model = request.form.get("model")
        year = request.form.get("year")
        cargo_capacity = request.form.get("cargo_capacity")
        fuel_type = request.form.get("fuel_type")
        mileage = request.form.get("km")
        color = request.form.get("color")
        condition = request.form.get("condition")

        # Handle file uploads
        photos = request.files.getlist("photos")  # Get list of uploaded files
        photo_paths = save_uploaded_photos(photos)

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        try:
            # Insert van data
            cursor.execute("""
                INSERT INTO Vehicle (brand, model, year, cargo_capacity, fuel_type, mileage, color, vehicle_condition)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (brand, model, year, cargo_capacity, fuel_type, mileage, color, condition))
            vehicle_id = cursor.lastrowid

            # Insert ad data
            cursor.execute("""
                INSERT INTO VehicleAd (title, description, price, vehicle_id)
                VALUES (%s, %s, %s, %s)
            """, (title, description, price, vehicle_id))

            # Insert photo paths into the Photo table
            for path in photo_paths:
                cursor.execute("""
                    INSERT INTO Photo (vehicle_id, content)
                    VALUES (%s, %s)
                """, (vehicle_id, path))

            conn.commit()
            flash("Van ad created successfully!", "success")
            return redirect(url_for("ad_routes.create_van"))
        except Exception as e:
            flash(f"An error occurred: {e}", "danger")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    return render_template("list_van_ad.html")