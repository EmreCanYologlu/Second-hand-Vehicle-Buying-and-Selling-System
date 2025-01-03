from flask import Blueprint, render_template, session, redirect, url_for, flash
import mysql.connector

admin_routes = Blueprint('admin_routes', __name__)

def get_db_connection():
    return mysql.connector.connect(
        host="db",
        user="user",
        password="password",
        database="mydatabase"
    )

@admin_routes.route('/admin/dashboard', methods=['GET'])
def admin_dashboard():
    # Ensure the user is an admin
    if 'user_id' not in session or session.get('is_admin') != True:
        flash('Access denied. Admins only.', 'danger')
        return redirect(url_for('auth_routes.login'))

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Fetch daily ads statistics
        daily_ads_query = """
            SELECT 
                DATE(created_at) AS date, 
                COUNT(*) AS total_ads
            FROM 
                VehicleAd
            GROUP BY 
                DATE(created_at)
            ORDER BY 
                DATE(created_at) DESC;
        """
        cursor.execute(daily_ads_query)
        daily_ads_stats = cursor.fetchall()

        # Fetch overall stats
        total_ads_query = "SELECT COUNT(*) AS total_ads FROM VehicleAd;"
        cursor.execute(total_ads_query)
        total_ads = cursor.fetchone()['total_ads']

        active_ads_query = "SELECT COUNT(*) AS active_ads FROM VehicleAd WHERE status = 'available';"
        cursor.execute(active_ads_query)
        active_ads = cursor.fetchone()['active_ads']

        total_users_query = "SELECT COUNT(*) AS total_users FROM User;"
        cursor.execute(total_users_query)
        total_users = cursor.fetchone()['total_users']

        # Pass data to the template
        return render_template(
            'admin_dashboard.html',
            daily_ads_stats=daily_ads_stats,
            total_ads=total_ads,
            active_ads=active_ads,
            total_users=total_users
        )

    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
        return redirect(url_for('auth_routes.dashboard'))

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals():
            db.close()



@admin_routes.route('/create-admin', methods=['GET'])
def create_admin():
    try:
        db = get_db_connection()
        cursor = db.cursor()

        # Insert into User table
        cursor.execute("""
            INSERT INTO User (username, email, password, account_status) 
            VALUES ('admin_user', 'admin@example.com', '123', 'active');
        """)

        # Insert into Admin table
        cursor.execute("""
            INSERT INTO Admin (user_id, permission_level) 
            VALUES (
                (SELECT user_id FROM User WHERE username = 'admin_user'),
                5
            );
        """)

        db.commit()
        return "Admin user created successfully!"

    except mysql.connector.Error as err:
        return f"Error: {err}"

    finally:
        cursor.close()
        db.close()
