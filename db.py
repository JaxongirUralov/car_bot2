import sqlite3
from datetime import datetime

DB_NAME = "orders.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_code TEXT,
            user_id INTEGER,
            first_name TEXT,
            last_name TEXT,
            phone TEXT,
            model TEXT,
            option TEXT,
            color TEXT,
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()

def generate_order_code():
    conn = get_connection()
    cur = conn.cursor()

    now = datetime.now()
    timestamp_part = now.strftime("%y%m%d%H%M")  # yymmddhhmm

    # Count orders created in the same minute
    cur.execute("""
        SELECT COUNT(*) FROM orders
        WHERE order_code LIKE ?
    """, (f"KG-{timestamp_part}-%",))

    count = cur.fetchone()[0] + 1

    sequence = str(count).zfill(4)  # 0001 format

    conn.close()

    return f"KG-{timestamp_part}-{sequence}"


def save_order(order):
    conn = get_connection()
    cur = conn.cursor()

    order_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    order_code = generate_order_code()

    cur.execute("""
        INSERT INTO orders (
            order_code, user_id, first_name, last_name,
            phone, model, option, color, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        order_code,
        order["user_id"],
        order["first_name"],
        order["last_name"],
        order["phone"],
        order["model"],
        order["option"],
        order["color"],
        order_time
    ))

    conn.commit()
    conn.close()

    return order_code


def get_all_orders():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, order_code, user_id, first_name, last_name,
               phone, model, option, color, created_at
        FROM orders
        ORDER BY id ASC
    """)

    rows = cur.fetchall()
    conn.close()
    return rows
