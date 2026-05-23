import sqlite3
import random
from datetime import datetime, timedelta

conn = sqlite3.connect('e_commerce.db')
cursor = conn.cursor()

# ── helpers ──────────────────────────────────────────────────────────────────
def rand_date(start_days_ago=365, end_days_ago=0):
    base = datetime.today() - timedelta(days=random.randint(end_days_ago, start_days_ago))
    return base.strftime("%Y-%m-%d")

# ── 1. products (100 rows) ────────────────────────────────────────────────────
brands     = ["Nike", "Adidas", "Puma", "Levi's", "Zara", "H&M", "Reebok", "Under Armour", "Gap", "Uniqlo"]
categories = ["Footwear", "Topwear", "Bottomwear", "Accessories", "Sportswear"]
sub_cats   = {"Footwear": ["Sneakers","Boots","Sandals"],
               "Topwear": ["T-Shirt","Shirt","Jacket"],
               "Bottomwear": ["Jeans","Shorts","Trousers"],
               "Accessories": ["Belt","Cap","Watch"],
               "Sportswear": ["Track Pants","Sports Bra","Compression Shorts"]}
sizes   = ["XS","S","M","L","XL","XXL"]
colors  = ["Black","White","Red","Blue","Green","Grey","Navy","Beige"]
genders = ["Men","Women","Unisex","Kids"]

products = []
for i in range(1, 101):
    cat  = random.choice(categories)
    sub  = random.choice(sub_cats[cat])
    brand = random.choice(brands)
    price = round(random.uniform(10, 300), 2)
    products.append((
        i, f"{brand} {sub} {i}", brand, cat, sub,
        random.choice(sizes), random.choice(colors),
        random.choice(genders), price,
        random.randint(0, 200),
        round(random.uniform(0, 0.5), 2)
    ))

cursor.executemany("""
    INSERT OR IGNORE INTO products
    (product_id, name, brand, category, sub_category, size, color, gender, price, stock, discount)
    VALUES (?,?,?,?,?,?,?,?,?,?,?)
""", products)

# ── 2. customers (100 rows) ───────────────────────────────────────────────────
first_names = ["James","Mary","John","Patricia","Robert","Jennifer","Michael","Linda","William","Barbara",
               "David","Susan","Richard","Jessica","Joseph","Sarah","Thomas","Karen","Charles","Lisa"]
last_names  = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Wilson","Moore",
               "Taylor","Anderson","Thomas","Jackson","White","Harris","Martin","Thompson","Young","Lewis"]
cities  = ["New York","Los Angeles","Chicago","Houston","Phoenix","Philadelphia","San Antonio","San Diego","Dallas","San Jose"]
states  = ["NY","CA","IL","TX","AZ","PA","TX","CA","TX","CA"]
countries = ["USA"]

customers = []
for i in range(1, 101):
    fn = random.choice(first_names)
    ln = random.choice(last_names)
    customers.append((
        i, fn, ln, f"{fn.lower()}.{ln.lower()}{i}@email.com",
        f"555-{random.randint(1000,9999)}",
        f"{random.randint(1,999)} {random.choice(['Main','Oak','Pine','Maple'])} St",
        random.choice(cities), random.choice(states),
        f"{random.randint(10000,99999)}", "USA"
    ))

cursor.executemany("""
    INSERT OR IGNORE INTO customers
    (customer_id, first_name, last_name, email, phone, address, city, state, zip_code, country)
    VALUES (?,?,?,?,?,?,?,?,?,?)
""", customers)

# ── 3. orders (100 rows) ──────────────────────────────────────────────────────
statuses = ["Pending","Processing","Shipped","Delivered","Cancelled","Returned"]

orders = []
for i in range(1, 101):
    order_date    = rand_date(365, 10)
    delivery_date = (datetime.strptime(order_date, "%Y-%m-%d") + timedelta(days=random.randint(3,14))).strftime("%Y-%m-%d")
    status = random.choice(statuses)
    orders.append((
        i, random.randint(1, 100), order_date,
        round(random.uniform(20, 500), 2),
        status,
        delivery_date if status in ["Shipped","Delivered"] else None
    ))

cursor.executemany("""
    INSERT OR IGNORE INTO orders
    (order_id, customer_id, order_date, total_amount, status, delivery_date)
    VALUES (?,?,?,?,?,?)
""", orders)

# ── 4. order_items (~150 rows, 1-3 items per order) ───────────────────────────
order_items = []
item_id = 1
for order in orders:
    order_id = order[0]
    for _ in range(random.randint(1, 3)):
        pid        = random.randint(1, 100)
        product    = next(p for p in products if p[0] == pid)
        unit_price = round(product[8] * (1 - product[10]), 2)
        qty        = random.randint(1, 4)
        order_items.append((item_id, order_id, pid, qty, unit_price, round(qty * unit_price, 2)))
        item_id += 1

cursor.executemany("""
    INSERT OR IGNORE INTO order_items
    (order_item_id, order_id, product_id, quantity, unit_price, total_price)
    VALUES (?,?,?,?,?,?)
""", order_items)

# ── 5. payments (100 rows, one per order) ────────────────────────────────────
methods = ["Credit Card","Debit Card","PayPal","UPI","Net Banking","Gift Card"]

payments = []
for i, order in enumerate(orders, start=1):
    order_id   = order[0]
    order_date = order[2]
    pay_date   = (datetime.strptime(order_date, "%Y-%m-%d") + timedelta(days=random.randint(0,2))).strftime("%Y-%m-%d")
    payments.append((i, order_id, pay_date, order[3], random.choice(methods)))

cursor.executemany("""
    INSERT OR IGNORE INTO payments
    (payment_id, order_id, payment_date, amount, payment_method)
    VALUES (?,?,?,?,?)
""", payments)

conn.commit()
conn.close()

print("✅ Inserted 100 products, 100 customers, 100 orders,", len(order_items), "order_items, 100 payments")
