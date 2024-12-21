from flask import Flask, render_template
from routes.auth_routes import auth_routes
from routes.listing_routes import listing_routes
from routes.ad_routes import ad_routes  # Import the new Blueprint
from routes.prof_routes import prof_routes

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

# Register Blueprints
app.register_blueprint(auth_routes, url_prefix='/auth')
app.register_blueprint(listing_routes, url_prefix='/listings')
app.register_blueprint(ad_routes, url_prefix='/ad')  # New Blueprint
app.register_blueprint(prof_routes, url_prefix='/profile')

@app.route('/')
def home():
    return render_template('home.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
