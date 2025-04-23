import sqlite3
import os

from flask import Flask, request, g, render_template_string, redirect, url_for

# Define the path for your database file
DATABASE = 'inventory.db'

def get_db():
    """Connects to the specific database."""
    db = getattr(g, '_database', None)
    if db is None:
        # Use check_same_thread=False for SQLite with Flask development server,
        # though be cautious in production with concurrent access.
        db = g._database = sqlite3.connect(DATABASE, check_same_thread=False)
        # Configure sqlite3 to return rows as dictionaries (more convenient)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    """Initializes the database schema."""
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

@app.cli.command('init-db')
def init_db_command():
    """Creates the database tables."""
    init_db()
    print('Initialized the database.')

# --- Flask Application Setup ---
app = Flask(__name__)
# You might want to add a secret key for security later,
# e.g., app.config['SECRET_KEY'] = 'your_secret_key_here'

# --- Define your first route (homepage) ---
@app.route('/')
def index():
    return '<h1>Welcome to A3-Mart Merchant Software!</h1><p>Database is set up.</p>' # Basic message for now

# --- You can add more routes and logic below this line ---

# Example: A simple page to view products (will be empty initially)
@app.route('/inventory')
def view_inventory():
    db = get_db()
    products = db.execute('SELECT * FROM products').fetchall() # Get all products from the table
    # We'll use a simple HTML string for now, later we'll use templates
    html_template = """
    <h1>Inventory List</h1>
    <ul>
        {% for product in products %}
            <li>{{ product['name'] }} (SKU: {{ product['sku'] }}) - Stock: {{ product['stock'] }}</li>
        {% else %}
            <li>No products found.</li>
        {% endfor %}
    </ul>
    <p><a href="/">Go Home</a></p>
    """
    return render_template_string(html_template, products=products)


if __name__ == '__main__':
    # Replit runs the app automatically, you usually don't need this block
    # in the default Replit setup, but it's standard Flask practice.
    # Replit's entrypoint handles running 'app'.
    pass
