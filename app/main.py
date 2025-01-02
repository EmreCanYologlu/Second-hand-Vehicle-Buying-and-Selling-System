from flask import Flask, render_template
from routes.auth_routes import auth_routes
from routes.listing_routes import listing_routes
from routes.messaging_routes import messaging_routes
from routes.notification_routes import notification_routes
from routes.bidding_routes import bidding_routes
import os

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key')

# Database configuration
db_config = {
    'host': 'db',
    'user': 'user',
    'password': 'password',
    'database': 'mydatabase'
}

app.register_blueprint(auth_routes, url_prefix='/auth')
app.register_blueprint(listing_routes, url_prefix='/listings')
app.register_blueprint(messaging_routes, url_prefix='/message')
app.register_blueprint(notification_routes, url_prefix='/notification')
app.register_blueprint(bidding_routes, url_prefix='/bidding')
@app.route('/')
def home():
    return render_template('home.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
