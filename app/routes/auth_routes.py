from flask import Blueprint, request, render_template, redirect, url_for, flash, session
import mysql.connector

auth_routes = Blueprint('auth_routes', __name__)

# Establish database connection (replace credentials as necessary)
def get_db_connection():
    return mysql.connector.connect(
        host="db",  # The service name from docker-compose
        user="user",
        password="password",
        database="mydatabase"
    )

@auth_routes.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return render_template('register.html')

        try:
            db = get_db_connection()
            cursor = db.cursor()
            query = """
                INSERT INTO User (username, email, password)
                VALUES (%s, %s, %s);
            """
            cursor.execute(query, (username, email, password))
            db.commit()
            flash('Registration successful!', 'success')
            return redirect(url_for('auth_routes.login'))
        except mysql.connector.Error as err:
            flash(f'Error: {err}', 'danger')
            return render_template('register.html')
        finally:
            cursor.close()
            db.close()

    return render_template('register.html')

@auth_routes.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')  # Safely get email
        password = request.form.get('password')  # Safely get password

        # Validate input
        if not email or not password:
            flash('Email and password are required!', 'danger')
            return render_template('login.html')

        try:
            db = get_db_connection()
            cursor = db.cursor(dictionary=True)

            # Debug inputs
            print(f"Email: {email}, Password: {password}")

            # Query the database
            query = "SELECT * FROM User WHERE email = %s AND password = %s;"
            cursor.execute(query, (email, password))
            user = cursor.fetchone()

            if user:

                # Check if the user is an admin
                admin_check_query = "SELECT 1 FROM Admin WHERE user_id = %s"
                cursor.execute(admin_check_query, (user['user_id'],))
                is_admin = cursor.fetchone() is not None

                # Set session variables
                session['user_id'] = user['user_id']
                session['username'] = user['username']
                session['is_admin'] = is_admin  # True if the user is an admin
                flash('Login successful!', 'success')
                return redirect(url_for('listing_routes.view_listings'))
            else:
                flash('Invalid email or password!', 'danger')
        except mysql.connector.Error as err:
            flash(f'Error: {err}', 'danger')
        finally:
            cursor.close()
            db.close()

    return render_template('login.html')

@auth_routes.route('/edit-profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        flash('You need to log in first!', 'danger')
        return redirect(url_for('auth_routes.login'))

    if request.method == 'POST':
        new_email = request.form['email']
        new_password = request.form['password']

        try:
            db = get_db_connection()
            cursor = db.cursor()
            query = """
                UPDATE User SET email = %s, password = %s WHERE user_id = %s;
            """
            cursor.execute(query, (new_email, new_password, session['user_id']))
            db.commit()
            flash('Profile updated successfully!', 'success')
        except mysql.connector.Error as err:
            flash(f'Error: {err}', 'danger')
        finally:
            cursor.close()
            db.close()

    return render_template('edit_profile.html')

@auth_routes.route('/dashboard')
def dashboard():
    # Ensure the user is logged in
    if 'user_id' not in session:
        flash('You need to log in first!', 'danger')
        return redirect(url_for('auth_routes.login'))

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Fetch user-specific data
        query = "SELECT username, email FROM User WHERE user_id = %s"
        cursor.execute(query, (session['user_id'],))
        user_data = cursor.fetchone()

        if not user_data:
            flash('User not found!', 'danger')
            return redirect(url_for('auth_routes.login'))

        # Pass user data to the template
        return render_template('dashboard.html', user=user_data)
    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
        return redirect(url_for('auth_routes.login'))
    finally:
        cursor.close()
        db.close()



@auth_routes.route('/logout')
def logout():
    session.clear()  # Clear the user session
    flash('You have been logged out!', 'success')
    return redirect(url_for('auth_routes.login'))
