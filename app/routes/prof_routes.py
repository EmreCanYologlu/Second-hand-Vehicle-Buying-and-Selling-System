from flask import Blueprint, request, render_template, redirect, url_for, flash, session
import mysql.connector

# Create a blueprint for profile-related routes
prof_routes = Blueprint('prof_routes', __name__)

# Establish database connection
def get_db_connection():
    return mysql.connector.connect(
        host="db",
        user="user",
        password="password",
        database="mydatabase"
    )

@prof_routes.route('/edit-profile', methods=['GET', 'POST'])
def edit_profile():
    # Ensure the user is logged in
    if 'user_id' not in session:
        flash('You need to log in first!', 'danger')
        return redirect(url_for('auth_routes.login'))

    if request.method == 'POST':
        # Get form data
        new_email = request.form['email']
        new_password = request.form['password']

        try:
            # Update the user's profile in the database
            db = get_db_connection()
            cursor = db.cursor()
            query = """
                UPDATE User
                SET email = %s, password = %s
                WHERE user_id = %s;
            """
            cursor.execute(query, (new_email, new_password, session['user_id']))
            db.commit()

            flash('Profile updated successfully!', 'success')
            return redirect(url_for('prof_routes.edit_profile'))
        except mysql.connector.Error as err:
            flash(f'Error: {err}', 'danger')
        finally:
            cursor.close()
            db.close()

    # Fetch the current user data for pre-filling the form
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        query = "SELECT email FROM User WHERE user_id = %s"
        cursor.execute(query, (session['user_id'],))
        user_data = cursor.fetchone()

        if not user_data:
            flash('User not found!', 'danger')
            return redirect(url_for('auth_routes.login'))
    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
        user_data = {}
    finally:
        cursor.close()
        db.close()

    return render_template('edit_profile.html', user=user_data)

@prof_routes.route('/delete-account', methods=['GET', 'POST'])
def delete_account():
    # Ensure the user is logged in
    if 'user_id' not in session:
        flash('You need to log in first!', 'danger')
        return redirect(url_for('auth_routes.login'))

    if request.method == 'POST':
        try:
            # Delete the user account
            db = get_db_connection()
            cursor = db.cursor()
            query = "DELETE FROM User WHERE user_id = %s"
            cursor.execute(query, (session['user_id'],))
            db.commit()

            # Clear session and redirect
            session.clear()
            flash('Your account has been deleted.', 'success')
            return redirect(url_for('auth_routes.register'))
        except mysql.connector.Error as err:
            flash(f'Error: {err}', 'danger')
        finally:
            cursor.close()
            db.close()

    return render_template('delete_account.html')
