from flask import Blueprint, render_template, request, redirect, url_for, flash
import mysql.connector
import os

# Define the listing_routes Blueprint
listing_routes = Blueprint("listing_routes", __name__)

# Database configuration
db_config = {
    'host': 'db',
    'user': 'user',
    'password': 'password',
    'database': 'mydatabase'
}

# Directory to store uploaded photos
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure the folder exists

# Listings Route
@listing_routes.route("/")
def listings():
    """Fetch all ads with their details and optional photos."""
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT a.ad_id, a.title, a.description, a.price, v.brand, v.model, v.year, 
                   COALESCE(p.content, '/static/default_photo.jpg') AS photo_url
            FROM VehicleAd a
            JOIN Vehicle v ON a.vehicle_id = v.vehicle_id
            LEFT JOIN Photo p ON v.vehicle_id = p.vehicle_id
            WHERE a.status = 'available'
        """)
        ads = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    return render_template("listings.html", results=ads)


# Select Vehicle Type Route
@listing_routes.route("/select_vehicle_type")
def select_vehicle_type():
    """Render the page for selecting vehicle type."""
    return render_template("select_vehicle_type.html")


# Search Route
@listing_routes.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '').strip()  # Get the search query from the URL
    if query:
        # Placeholder: Replace with database search logic later
        results = [f"Result matching '{query}'"]
    else:
        results = []

    return render_template('search_results.html', query=query, results=results)


# Helper function to handle file uploads
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


