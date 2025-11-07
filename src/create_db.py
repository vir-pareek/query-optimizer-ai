import sqlite3, random, string, os
from datetime import datetime, timedelta
import numpy as np

DB_PATH = os.path.join("data", "synth.db")
os.makedirs("data", exist_ok=True)

random.seed(42)
np.random.seed(42)

def rand_str(n=8):
    return ''.join(random.choices(string.ascii_lowercase, k=n))

def main():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Create tables
    cur.executescript("""
    PRAGMA journal_mode = WAL;
    CREATE TABLE users(
        user_id INTEGER PRIMARY KEY,
        name TEXT,
        country TEXT,
        signup_date TEXT
    );
    CREATE TABLE products(
        product_id INTEGER PRIMARY KEY,
        name TEXT,
        category TEXT,
        price REAL
    );
    CREATE TABLE orders(
        order_id INTEGER PRIMARY KEY,
        user_id INTEGER,
        product_id INTEGER,
        quantity INTEGER,
        order_date TEXT,
        status TEXT,
        FOREIGN KEY(user_id) REFERENCES users(user_id),
        FOREIGN KEY(product_id) REFERENCES products(product_id)
    );
    CREATE TABLE reviews(
        review_id INTEGER PRIMARY KEY,
        user_id INTEGER,
        product_id INTEGER,
        rating INTEGER,
        review_date TEXT,
        FOREIGN KEY(user_id) REFERENCES users(user_id),
        FOREIGN KEY(product_id) REFERENCES products(product_id)
    );
    """)

    # Seed users
    countries = ["IN","US","GB","DE","FR","SG","AU","CA","BR","JP"]
    start = datetime(2021,1,1)
    users = []
    for uid in range(1, 20001):  # 20k users
        d = start + timedelta(days=random.randint(0,1500))
        users.append((uid, rand_str(10), random.choice(countries), d.strftime("%Y-%m-%d")))
    cur.executemany("INSERT INTO users VALUES (?,?,?,?)", users)

    # Seed products
    cats = ["electronics","books","fashion","home","grocery","toys"]
    products = []
    for pid in range(1, 5001):  # 5k products
        products.append((pid, rand_str(12), random.choice(cats), round(random.uniform(3, 1500),2)))
    cur.executemany("INSERT INTO products VALUES (?,?,?,?)", products)

    # Seed orders
    statuses = ["placed","shipped","delivered","cancelled","returned"]
    orders = []
    for oid in range(1, 100001):  # 100k orders
        uid = random.randint(1, len(users))
        pid = random.randint(1, len(products))
        qty = int(np.clip(int(np.random.exponential(2))+1,1,10))
        d = start + timedelta(days=random.randint(0,1500))
        st = random.choices(statuses, weights=[40,25,25,5,5])[0]
        orders.append((oid, uid, pid, qty, d.strftime("%Y-%m-%d"), st))
    cur.executemany("INSERT INTO orders VALUES (?,?,?,?,?,?)", orders)

    # Seed reviews
    reviews = []
    for rid in range(1, 80001):  # 80k reviews
        uid = random.randint(1, len(users))
        pid = random.randint(1, len(products))
        rating = random.randint(1,5)
        d = start + timedelta(days=random.randint(0,1500))
        reviews.append((rid, uid, pid, rating, d.strftime("%Y-%m-%d")))
    cur.executemany("INSERT INTO reviews VALUES (?,?,?,?,?)", reviews)

    # Helpful indexes (we'll toggle/use variants later)
    cur.executescript("""
    CREATE INDEX idx_orders_user ON orders(user_id);
    CREATE INDEX idx_orders_product ON orders(product_id);
    CREATE INDEX idx_orders_date ON orders(order_date);
    CREATE INDEX idx_users_country ON users(country);
    CREATE INDEX idx_products_category ON products(category);
    CREATE INDEX idx_reviews_user ON reviews(user_id);
    CREATE INDEX idx_reviews_product ON reviews(product_id);
    """)
    conn.commit()
    conn.close()
    print("Database created at", DB_PATH)

if __name__ == "__main__":
    main()