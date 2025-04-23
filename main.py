import sqlite3
import os

# --- Imports for Flask, session, security, rendering, redirect ---
from flask import (
    Flask, request, g, render_template, render_template_string, # render_template_string might still be useful for testing
    redirect, url_for, current_app, session # current_app for CLI, session for login
)
from werkzeug.security import generate_password_hash, check_password_hash # For password handling

# Define the path for your database file
DATABASE = 'inventory.db'

# --- Flask Application Setup (This must be BEFORE any @app decorators or app. method calls) ---
app = Flask(__name__)
# !!! IMPORTANT: CHANGE THIS SECRET KEY IN A REAL APPLICATION !!!
# Use a long, random string like os.urandom(24)
app.config['SECRET_KEY'] = 'a_very_secret_and_random_key_change_this_on_deployment'
# --- End Flask Application Setup ---


# --- Database Helper Functions ---

def get_db():
    """Connects to the specific database."""
    # Use current_app.root_path to make the database path relative to the app
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(
            os.path.join(current_app.root_path, DATABASE),
            check_same_thread=False # Needed for Flask dev server, use different approach in production
        )
        db.row_factory = sqlite3.Row # Return rows as dictionaries
    return db

@app.teardown_appcontext
def close_db_at_end_of_request(error=None):
    """Closes the database again at the end of the request context."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    """Initializes the database schema from schema.sql."""
    db = get_db() # Get a connection using the helper
    # Use current_app to access files relative to the application root
    with current_app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

@app.cli.command('init-db') # Registers 'init-db' command with 'flask' CLI
def init_db_command():
    """Creates the database tables."""
    init_db() # Call the init_db function
    print('Initialized the database.')

# --- Authentication Helper / Decorator ---

# This function checks if a user is logged in by looking for 'user_id' in the session
def login_required(view):
    """View decorator that redirects to the login page if not logged in."""
    from functools import wraps # Import wraps inside the decorator is common practice

    @wraps(view) # Use @wraps to preserve original view function's name/docs
    def wrapped_view(**kwargs):
        # If user_id is not in the session, redirect to the login route
        if session.get('user_id') is None:
            return redirect(url_for('login'))
        # Otherwise, the user is logged in, execute the original view function
        return view(**kwargs)

    return wrapped_view

# --- Routes ---

# Login route
@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None

        # Query the database for the user by username
        user = db.execute(
            'SELECT * FROM users WHERE username = ?', (username,)
        ).fetchone()

        if user is None:
            error = 'Incorrect username.'
        # Check the provided password against the hashed password in the database
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        # If no errors, login the user
        if error is None:
            session.clear() # Clear any previous session
            session['user_id'] = user['id'] # Store user ID in the session
            # Optional: store username in session for display
            session['username'] = user['username']
            # Redirect to the index page (which is now the dashboard)
            return redirect(url_for('index'))

        # If there was an error, re-render the login template with the error message
        return render_template('login.html', error=error)

    # If it's a GET request, just render the empty login form
    return render_template('login.html', error=None)

# Logout route
@app.route('/logout')
def logout():
    session.clear() # Clear the session to log the user out
    return redirect(url_for('index')) # Redirect to index (which will now prompt login)


# Dashboard (Index) route - Requires login
@app.route('/')
@login_required # Apply the decorator to protect this route
def index():
    db = get_db()
    # --- Fetch Dashboard Data Here ---
    # These queries assume your database structure (schema.sql) is updated
    # Use 'or 0' or similar to handle cases where queries return None (e.g., no sales yet)

    # Today's Sales
    today_sales_data = db.execute(
        'SELECT SUM(final_amount) FROM invoices WHERE DATE(sale_date) = CURRENT_DATE'
    ).fetchone()[0] or 0

    # Low Stock Count (Assuming a low_stock_threshold in products table)
    # You might need to fetch threshold from config or hardcode for now
    low_stock_threshold = 10 # Example threshold
    low_stock_count_data = db.execute(
        'SELECT COUNT(*) FROM products WHERE stock < ?', (low_stock_threshold,)
    ).fetchone()[0] or 0

    # Expiring Soon Count (Assuming expiry_date in products table)
    # Adjust '+30 days' as needed for your definition of "soon"
    expiring_soon_count_data = db.execute(
        'SELECT COUNT(*) FROM products WHERE expiry_date IS NOT NULL AND expiry_date <= DATE("now", "+30 days")'
    ).fetchone()[0] or 0

    # Total Customers
    total_customers_data = db.execute('SELECT COUNT(*) FROM customers').fetchone()[0] or 0

    # Top Selling Products (Adjust LIMIT as needed)
    top_selling_products_data = db.execute(
        '''
        SELECT p.name, SUM(ii.quantity) AS total_sold
        FROM invoice_items ii
        JOIN products p ON ii.product_id = p.id
        GROUP BY p.id, p.name
        ORDER BY total_sold DESC
        LIMIT 5
        '''
    ).fetchall() # fetchall for multiple rows

    # --- Suggest More Dashboard Data ---
    # Total Stock Value (at selling price)
    total_stock_value_selling = db.execute(
        'SELECT SUM(stock * selling_price) FROM products'
    ).fetchone()[0] or 0

    # Total Stock Value (at cost price - requires cost_price in products and handling initial stock cost)
    # This is more complex if inventory cost fluctuates, but simple sum works if cost_price is fixed per product
    total_stock_value_cost = db.execute(
        'SELECT SUM(stock * cost_price) FROM products WHERE cost_price IS NOT NULL'
    ).fetchone()[0] or 0


    # Pass the fetched data to the dashboard template
    return render_template(
        'dashboard.html',
        today_sales=today_sales_data,
        low_stock_count=low_stock_count_data,
        expiring_soon_count=expiring_soon_count_data,
        total_customers=total_customers_data,
        top_selling_products=top_selling_products_data,
        total_stock_value_selling=total_stock_value_selling,
        total_stock_value_cost=total_stock_value_cost,
        # Add more variables for other data you fetch
    )

# Inventory List route - Requires login
@app.route('/inventory')
@login_required # Apply the decorator to protect this route
def view_inventory():
    db = get_db()
    products = db.execute('SELECT * FROM products').fetchall() # Get all products from the table
    # We'll use a simple HTML string for now, later we'll use templates
    # TODO: Create a proper inventory.html template
    html_template = """
    <h1>Inventory List</h1>
    <p>Logged in as: {{ session.get('username', 'Merchant') }}</p>
    <ul>
        {% for product in products %}
            <li>{{ product['name'] }} (SKU: {{ product['sku'] }}) - Stock: {{ product['stock'] }} - Price: {{ product['selling_price'] }}</li>
        {% else %}
            <li>No products found.</li>
        {% endfor %}
    </ul>
    <p><a href="{{ url_for('index') }}">Dashboard</a> | <a href="{{ url_for('logout') }}">Logout</a></p>
    """
    return render_template_string(html_template, products=products, session=session) # Pass session to template_string if needed


# --- This block is for running directly (e.g., `python main.py`), NOT used by `python -m flask` commands ---
# Keep this at the very bottom
if __name__ == '__main__':
    # This code is ignored by `python -m flask run` or `python -m flask init-db`
    # It's mainly for simpler scripts or if you were using a different runner
    pass
