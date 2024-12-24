from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from werkzeug.utils import secure_filename
import mysql.connector
import os

messaging_routes = Blueprint('messaging_routes', __name__)

def get_db_connection():
    return mysql.connector.connect(
        host="db",
        user="user",
        password="password",
        database="mydatabase"
    )
    
@messaging_routes.route('/send', methods=['POST'])
def send_message():
    # Ensure user is logged in
    if 'user_id' not in session:
        flash('You must be logged in to send a message.', 'danger')
        return redirect(url_for('auth_routes.login'))

    # Log the incoming data
    print("Form data received:", request.form)

    # Extract data from the form
    try:
        sender_id = int(session['user_id'])  # Logged-in user
        receiver_id = int(request.form['receiver_id'])  # Receiver from the form
        ad_id = int(request.form['ad_id'])  # Ad ID for redirection
        message_content = request.form.get('message_content', '').strip()  # Message content
    except (ValueError, KeyError) as e:
        print("Error extracting form data:", e)  # Log the error
        flash('Invalid form data.', 'danger')
        return redirect(url_for('listing_routes.view_ad_details', ad_id=request.form.get('ad_id', '')))

    # Validate sender and receiver are not the same
    if sender_id == receiver_id:
        flash('You cannot send a message to yourself.', 'danger')
        return redirect(url_for('listing_routes.view_ad_details', ad_id=ad_id))

    # Validate message content
    if not message_content:
        flash('Message content cannot be empty.', 'danger')
        return redirect(url_for('listing_routes.view_ad_details', ad_id=ad_id))

    try:
        db = get_db_connection()
        cursor = db.cursor()

        # Insert the message into the database
        message_query = """
            INSERT INTO Message (content, sender_id, receiver_id, status)
            VALUES (%s, %s, %s, 'sent');
        """
        cursor.execute(message_query, (message_content, sender_id, receiver_id))

        db.commit()
        flash('Message sent successfully!', 'success')
        return redirect(url_for('listing_routes.view_ad_details', ad_id=ad_id))

    except mysql.connector.Error as err:
        db.rollback()
        flash(f'Database error: {err}', 'danger')
        return redirect(url_for('listing_routes.view_ad_details', ad_id=ad_id))

    finally:
        cursor.close()
        db.close()

@messaging_routes.route('/conversations', methods=['GET'])
def view_conversations():
    if 'user_id' not in session:
        flash('You must be logged in to view your messages.', 'danger')
        return redirect(url_for('auth_routes.login'))

    user_id = session['user_id']

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Fetch conversations for the logged-in user
        conversation_query = """
            SELECT 
                participant_id,
                participant_name,
                last_message_time,
                (SELECT content 
                 FROM Message 
                 WHERE (sender_id = %s AND receiver_id = participant_id) 
                    OR (sender_id = participant_id AND receiver_id = %s)
                 ORDER BY created_at DESC 
                 LIMIT 1) AS last_message_content
            FROM (
                SELECT 
                    CASE
                        WHEN sender_id = %s THEN receiver_id
                        ELSE sender_id
                    END AS participant_id,
                    User.username AS participant_name,
                    MAX(Message.created_at) AS last_message_time
                FROM 
                    Message
                JOIN 
                    User ON User.user_id = CASE 
                        WHEN Message.sender_id = %s THEN Message.receiver_id
                        ELSE Message.sender_id
                    END
                WHERE 
                    Message.sender_id = %s OR Message.receiver_id = %s
                GROUP BY 
                    participant_id, participant_name
            ) AS conversations
            ORDER BY last_message_time DESC;
        """
        cursor.execute(conversation_query, (user_id, user_id, user_id, user_id, user_id, user_id))
        conversations = cursor.fetchall()

        return render_template('conversations.html', conversations=conversations)

    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
        return redirect(url_for('auth_routes.dashboard'))

    finally:
        cursor.close()
        db.close()




@messaging_routes.route('/conversation/<int:participant_id>', methods=['GET', 'POST'])
def view_conversation(participant_id):
    if 'user_id' not in session:
        flash('You must be logged in to view messages.', 'danger')
        return redirect(url_for('auth_routes.login'))

    user_id = session['user_id']

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        if request.method == 'POST':
            # Handle sending a new message
            message_content = request.form.get('message_content', '').strip()

            if not message_content:
                flash('Message content cannot be empty.', 'danger')
                return redirect(url_for('messaging_routes.view_conversation', participant_id=participant_id))

            try:
                # Insert the new message into the database
                message_query = """
                    INSERT INTO Message (content, sender_id, receiver_id, status)
                    VALUES (%s, %s, %s, 'sent');
                """
                cursor.execute(message_query, (message_content, user_id, participant_id))
                db.commit()
                flash('Message sent successfully!', 'success')
            except mysql.connector.Error as err:
                db.rollback()
                flash(f'Error sending message: {err}', 'danger')

            return redirect(url_for('messaging_routes.view_conversation', participant_id=participant_id))

        # Fetch messages with the participant
        message_query = """
            SELECT 
                content, 
                sender_id, 
                receiver_id, 
                created_at
            FROM 
                Message
            WHERE 
                (sender_id = %s AND receiver_id = %s) OR
                (sender_id = %s AND receiver_id = %s)
            ORDER BY 
                created_at ASC;
        """
        cursor.execute(message_query, (user_id, participant_id, participant_id, user_id))
        messages = cursor.fetchall()

        # Fetch participant name
        participant_query = "SELECT username FROM User WHERE user_id = %s;"
        cursor.execute(participant_query, (participant_id,))
        participant = cursor.fetchone()

        if not participant:
            flash('The participant does not exist.', 'danger')
            return redirect(url_for('messaging_routes.view_conversations'))

        return render_template(
            'conversation.html',
            messages=messages,
            participant=participant,
            participant_id=participant_id
        )

    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
        return redirect(url_for('messaging_routes.view_conversations'))

    finally:
        cursor.close()
        db.close()


