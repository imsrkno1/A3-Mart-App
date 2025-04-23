import sqlite3
import os

from flask import Flask, request, g, render_template_string, redirect, url_for, current_app # Added current_app, useful later

# Define the path for your database file
DATABASE = 'inventory.db'

# --- Flask Application Setup (MOVE THIS UP HERE) ---
app = Flask(__name__)
# You might want to add a secret key for security later,
# e.g., app.config['SECRET_KEY'] = 'your_secret_key_here'
# --- End Flask Application Setup ---


# Database connection helper functions (these don't directly use 'app' instance in their definition)
# get_db uses Flask's 'g', close_db is registered with app later
def get_db():
    """Connects to the specific database."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE, check_same_thread=False)
        db.row_factory = sqlite3.Row
    return db

# close_db function definition
def close_db(error):
    """Closes the database again at the end of the request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# init_db function definition (uses app.open_resource - needs 'app' defined BEFORE this definition)
def init_db():
    """Initializes the database schema."""
    # Using current_app instead of 'app' here is often better practice
    # because this function might be called from the CLI context
    # where the 'app' global might not be directly available,
    # but current_app points to the loaded app.
    db = get_db()
    with current_app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

# --- Register functions/commands with the 'app' instance (NOW 'app' is defined) ---
@app.teardown_appcontext # This line uses app, must be AFTER app = Flask(...)
def close_db_at_end_of_request(error): # Renamed slightly to avoid conflict with the function name above
    """Closes the database again at the end of the request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.cli.command('init-db') # This line uses app, must be AFTER app = Flask(...)
def init_db_command():
    """Creates the database tables."""
    init_db() # This calls the init_db function defined above
    print('Initialized the database.')

# --- Define your first route (homepage) ---
@app.route('/') # This line uses app, must be AFTER app = Flask(...)
def index():
    return '<h1>Welcome to A3-Mart Merchant Software!</h1><p>Database is set up.</p>' # Basic message for now

# --- You can add more routes and logic below this line ---

# Example: A simple page to view products (will be empty initially)
@app.route('/inventory') # This line uses app, must be AFTER app = Flask(...)
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
    # Code in this block is ignored by 'python -m flask' commands
    pass
