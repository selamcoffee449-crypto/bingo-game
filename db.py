import sqlite3

# ==================================================
# CONNECTION
# ==================================================
conn = sqlite3.connect("bingo.db", check_same_thread=False)
cur = conn.cursor()

# ==================================================
# TABLES
# ==================================================

# Users table
cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 0
)
""")

conn.commit()


# ==================================================
# HELPER FUNCTIONS (optional but powerful)
# ==================================================

def add_user(user_id: int):
    cur.execute(
        "INSERT OR IGNORE INTO users(user_id, balance) VALUES(?, 0)",
        (user_id,)
    )
    conn.commit()


def get_balance(user_id: int) -> int:
    cur.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    return row[0] if row else 0


def add_balance(user_id: int, amount: int):
    cur.execute(
        "UPDATE users SET balance = balance + ? WHERE user_id=?",
        (amount, user_id)
    )
    conn.commit()


def get_user_count() -> int:
    cur.execute("SELECT COUNT(*) FROM users")
    return cur.fetchone()[0]
