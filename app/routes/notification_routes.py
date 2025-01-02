from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from werkzeug.utils import secure_filename
import mysql.connector
import os

notification_routes = Blueprint('notification_routes', __name__)

def get_db_connection():
    return mysql.connector.connect(
        host="db",
        user="user",
        password="password",
        database="mydatabase"
    )
    
@notification_routes.route('/send', methods=['POST'])
def send_message():
    if 'user_id' not in session:
        flash('You must be logged in to send a message.', 'danger')
        return redirect(url_for('auth_routes.login'))

    try:
        db = get_db_connection()
        cursor = db.cursor()

        sender_id = session['user_id']
        receiver_id = int(request.form['receiver_id'])
        message_content = request.form.get('message_content', '').strip()

        if not message_content:
            flash('Message content cannot be empty.', 'danger')
            return redirect(url_for('messaging_routes.view_conversation', participant_id=receiver_id))

        if sender_id == receiver_id:
            flash('You cannot send a message to yourself.', 'danger')
            return redirect(url_for('messaging_routes.view_conversation', participant_id=receiver_id))

        # Insert the new message into the database
        message_query = """
            INSERT INTO Message (content, sender_id, receiver_id, status)
            VALUES (%s, %s, %s, 'sent');
        """
        cursor.execute(message_query, (message_content, sender_id, receiver_id))
        message_id = cursor.lastrowid

        # Create a notification for the receiver
        notification_query = """
            INSERT INTO Notification (user_id, message)
            VALUES (%s, %s);
        """
        notification_message = f'New message from {session["username"]}'
        cursor.execute(notification_query, (receiver_id, notification_message))
        notification_id = cursor.lastrowid

        # Link the notification to the message
        message_notif_query = """
            INSERT INTO MessageNotif (notification_id, message_id)
            VALUES (%s, %s);
        """
        cursor.execute(message_notif_query, (notification_id, message_id))

        db.commit()
        flash('Message sent successfully!', 'success')
        return redirect(url_for('messaging_routes.view_conversation', participant_id=receiver_id))

    except mysql.connector.Error as err:
        db.rollback()
        flash(f'Error: {err}', 'danger')
        return redirect(url_for('messaging_routes.view_conversation', participant_id=receiver_id))

    finally:
        cursor.close()
        db.close()


@notification_routes.route('/notifications', methods=['GET'])
def view_notifications():
    if 'user_id' not in session:
        flash('You must be logged in to view notifications.', 'danger')
        return redirect(url_for('auth_routes.login'))

    user_id = session['user_id']

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Fetch notifications for the logged-in user
        notifications_query = """
            SELECT n.notification_id, n.message, n.created_at, m.content AS related_message
            FROM Notification n
            LEFT JOIN MessageNotif mn ON n.notification_id = mn.notification_id
            LEFT JOIN Message m ON mn.message_id = m.message_id
            WHERE n.user_id = %s
            ORDER BY n.created_at DESC;
        """
        cursor.execute(notifications_query, (user_id,))
        notifications = cursor.fetchall()

        return render_template('notifications.html', notifications=notifications)

    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
        return redirect(url_for('auth_routes.dashboard'))

    finally:
        cursor.close()
        db.close()
