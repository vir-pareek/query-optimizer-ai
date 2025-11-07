import random

random.seed(7)

COUNTRIES = ["IN","US","GB","DE","FR","SG","AU","CA","BR","JP"]
CATEGORIES = ["electronics","books","fashion","home","grocery","toys"]
STATUSES = ["placed","shipped","delivered","cancelled","returned"]

def gen_country_filter():
    return random.choice(COUNTRIES)

def gen_category_filter():
    return random.choice(CATEGORIES)

def gen_status_filter():
    return random.choice(STATUSES)

def pair_in_exists():
    country = gen_country_filter()
    a = f"""
    SELECT u.user_id
    FROM users u
    WHERE u.country = '{country}'
      AND u.user_id IN (SELECT o.user_id FROM orders o WHERE o.status='delivered');
    """
    b = f"""
    SELECT u.user_id
    FROM users u
    WHERE u.country = '{country}'
      AND EXISTS (SELECT 1 FROM orders o WHERE o.user_id = u.user_id AND o.status='delivered');
    """
    return a, b, "in_vs_exists"

def pair_join_vs_subquery():
    cat = gen_category_filter()
    a = f"""
    SELECT o.order_id, p.price
    FROM orders o
    JOIN products p ON p.product_id = o.product_id
    WHERE p.category = '{cat}' AND o.quantity >= 2;
    """
    b = f"""
    SELECT o.order_id,
           (SELECT p.price FROM products p WHERE p.product_id = o.product_id) AS price
    FROM orders o
    WHERE (SELECT p.category FROM products p WHERE p.product_id = o.product_id) = '{cat}'
      AND o.quantity >= 2;
    """
    return a, b, "join_vs_subquery"

def pair_orderby_limit():
    status = gen_status_filter()
    a = f"""
    SELECT o.order_id, o.order_date
    FROM orders o
    WHERE o.status = '{status}'
    ORDER BY o.order_date DESC
    LIMIT 200;
    """
    b = f"""
    SELECT o.order_id, o.order_date
    FROM orders o
    WHERE o.status = '{status}'
    ORDER BY o.order_id DESC
    LIMIT 200;
    """
    return a, b, "orderby_variant"

def pair_count_variants():
    country = gen_country_filter()
    a = f"""
    SELECT COUNT(*) AS c
    FROM users u
    WHERE u.country = '{country}';
    """
    b = f"""
    SELECT COUNT(1) AS c
    FROM users u
    WHERE u.country = '{country}';
    """
    return a, b, "count_star_vs_one"

PAIRS = [pair_in_exists, pair_join_vs_subquery, pair_orderby_limit, pair_count_variants]

def generate(n_pairs=200):
    out = []
    for _ in range(n_pairs):
        f = random.choice(PAIRS)
        a,b,tag = f()
        out.append((a.strip(), b.strip(), tag))
    return out

if __name__ == "__main__":
    pairs = generate(400)
    with open("data/query_pairs.txt","w") as f:
        for a,b,tag in pairs:
            f.write("###PAIR###\n--A--\n"+a+"\n--B--\n"+b+"\n--TAG--\n"+tag+"\n")
    print("Wrote pairs to data/query_pairs.txt")