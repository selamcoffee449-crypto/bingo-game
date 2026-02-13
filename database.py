import sqlite3

conn = sqlite3.connect("bingo.db", check_same_thread=False)
cur = conn.cursor()


def setup():
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        name TEXT,
        balance INTEGER DEFAULT 0
    )
    """)
    conn.commit()


def get_balance(user_id):
    cur.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    return row[0] if row else 0


def add_user(user_id, name):
    cur.execute(
        "INSERT OR IGNORE INTO users(user_id,name,balance) VALUES(?,?,0)",
        (user_id, name),
    )
    conn.commit()


def add_balance(user_id, amount):
    cur.execute(
        "UPDATE users SET balance = balance + ? WHERE user_id=?",
        (amount, user_id),
    )
    conn.commit()
