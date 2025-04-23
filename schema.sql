DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS users; -- Planning ahead for merchant login

CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    category TEXT,
    cost_price REAL,
    selling_price REAL NOT NULL,
    stock INTEGER NOT NULL DEFAULT 0,
    -- You can add more fields later (e.g., supplier_id, description, image_url)
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Basic users table for merchant login (planning for ReplAuth or custom auth)
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL -- This would store hashed passwords
    -- You can add more fields later (e.g., email, role)
);
