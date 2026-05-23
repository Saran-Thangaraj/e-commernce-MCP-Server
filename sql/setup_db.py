import sqlite3

## Connect to the SQLite database (or create it if it doesn't exist)

conn = sqlite3.connect('e_commerce.db') ## open the connection to the database
cursor = conn.cursor()  ## execute SQL commands using the cursor object

## Create tables for products, customers, orders, and order items
cursor.execute('''
CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    brand TEXT,
    category TEXT,
    sub_category TEXT,
    size TEXT,
    color TEXT,
    gender TEXT,
    price REAL NOT NULL,
    stock INTEGER NOT NULL,
    discount REAL)''')

## create customers table
cursor.execute('''
CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    address TEXT,
    city TEXT,
    state TEXT,
    zip_code TEXT,
    country TEXT
)''')

## create orders table
cursor.execute('''
CREATE TABLE IF NOT EXISTS orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    order_date TEXT NOT NULL,
    total_amount REAL NOT NULL,
    status TEXT NOT NULL,
    delivery_date TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
)''')   

## create order_items table
cursor.execute('''
CREATE TABLE IF NOT EXISTS order_items (
    order_item_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL,         
    total_price REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
)''')

# create payments table
cursor.execute('''
CREATE TABLE IF NOT EXISTS payments (
    payment_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL,
    payment_date TEXT NOT NULL,
    amount REAL NOT NULL,
    payment_method TEXT NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
)''')

## Commit the changes and close the connection
conn.commit()
conn.close()    
