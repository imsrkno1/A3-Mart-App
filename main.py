import sqlite3
import os

# --- REMOVED unused import 'current_app' for simplicity here, add back if needed later ---
# --- Make sure 'Flask', 'request', 'g', 'render_template_string', 'redirect', 'url_for' are imported ---
from flask import Flask, request, g, render_template_string, redirect, url_for, current_app # Re-added current_app as it's used in init_db in the corrected version

# Define the path for your database file
DATABASE = 'inventory.db'

# --- THIS IS THE CORRECT LOCATION FOR APP CREATION ---
# --- Flask Application Setup ---
app = Flask(__name__)
# You might want to add a secret key for security later,
# e.g., app.config['SECRET_KEY'] = 'your_secret_key_here'
# --- End Flask Application Setup ---


# Database connection helper functions (Defined BEFORE they are used or registered)
def get_db():
    """Connects to the specific database."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE, check_same_thread=False)
        db.row_factory = sqlite3.Row
    return db

def close_db_connection(error=None): # Renamed slightly to avoid collision with the function name used below
    """Closes the database again at the end of the request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# init_db function definition (uses current_app.open_resource)
def init_db():
    """Initializes the database schema."""
    # Use current_app here as this function is called from the CLI context
    db = get_db()
    with current_app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


# --- NOW REGISTER FUNCTIONS/COMMANDS WITH THE 'app' INSTANCE ---
# --- These lines MUST come AFTER 'app = Flask(__name__)' ---

@app.teardown_appcontext # This uses 'app'
def teardown_db(error): # This function name is often used for the teardown
    """Closes the database again at the end of the request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# You were using close_db for both teardown and the function name - let's use teardown_db for the context tear down.
# And keep close_db_connection if you need to call it manually elsewhere (though typically teardown_appcontext is enough).
# Let's simplify and use teardown_db directly.

# Let's correct the teardown to use the logic you had but under a distinct name for clarity
@app.teardown_appcontext
def close_db_at_end_of_request(error=None):
    """Closes the database again at the end of the request context."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.cli.command('init-db') # This uses 'app'
def init_db_command():
    """Creates the database tables."""
    init_db() # This calls the init_db function defined above
    print('Initialized the database.')


# --- Your routes (@app.route) go here ---
# --- These lines MUST come AFTER 'app = Flask(__name__)' ---

@app.route('/') # This uses 'app'
def index():
    return '<h1>Welcome to A3-Mart Merchant Software!</h1><p>Database is set up.</p>' # Basic message for now

# --- You can add more routes and logic below this line ---

@app.route('/inventory') # This uses 'app'
def view_inventory():
    db = get_db()
    products = db.execute('SELECT * FROM products').fetchall()
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


# --- This block is for running directly, NOT used by 'python -m flask' commands ---
if __name__ == '__main__':
    # Code in this block is ignored by 'python -m flask init-db' or 'python -m flask run' commands
    pass
