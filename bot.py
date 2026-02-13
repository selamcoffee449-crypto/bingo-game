import os
import threading
import sqlite3
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# =========================
# CONFIG
# =========================
TOKEN = os.getenv("TOKEN")
ADMIN_PASSWORD = "1234"
DB_FILE = "bingo.db"
TICKET_PRICE = 10

# =========================
# DATABASE INIT
# =========================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        name TEXT,
        balance INTEGER DEFAULT 0
    )
    """)
    conn.commit()
    conn.close()

init_db()

# =========================
# WEB ADMIN (FLASK)
# =========================
def run_web():
    app = Flask(__name__)

    def get_db():
        return sqlite3.connect(DB_FILE, check_same_thread=False)

    @app.route("/")
    def home():
        return "Bingo system online."

    @app.route("/admin")
    def admin():
        pw = request.args.get("pw")
        if pw != ADMIN_PASSWORD:
            return "Wrong password."

        return """
        <h1>Bingo Admin</h1>
        <a href="/admin/users?pw=1234">Users</a>
        """

    @app.route("/admin/users")
    def users():
        pw = request.args.get("pw")
        if pw != ADMIN_PASSWORD:
            return "Wrong password."

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT user_id,name,balance FROM users")
        rows = cur.fetchall()
        conn.close()

        html = "<h1>Users</h1><table border=1>"
        html += "<tr><th>ID</th><th>Name</th><th>Balance</th></tr>"
        for r in rows:
            html += f"<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td></tr>"
        html += "</table>"

        return html

    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)

# =========================
# TELEGRAM COMMANDS
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO users (user_id, name, balance) VALUES (?,?,?)",
        (user.id, user.full_name, 0)
    )
    conn.commit()
    conn.close()

    await update.message.reply_text(
        f"Welcome!\nYour ID: {user.id}"
    )

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT balance FROM users WHERE user_id=?", (update.effective_user.id,))
    bal = cur.fetchone()[0]
    conn.close()

    await update.message.reply_text(f"Balance: {bal}")

async def give(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET balance = balance + 100 WHERE user_id=?",
        (update.effective_user.id,)
    )
    conn.commit()
    conn.close()

    await update.message.reply_text("Added 100.")

async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute("SELECT balance FROM users WHERE user_id=?", (update.effective_user.id,))
    bal = cur.fetchone()[0]

    if bal < TICKET_PRICE:
        conn.close()
        await update.message.reply_text("Not enough balance.")
        return

    cur.execute(
        "UPDATE users SET balance = balance - ? WHERE user_id=?",
        (TICKET_PRICE, update.effective_user.id)
    )
    conn.commit()
    conn.close()

    await update.message.reply_text("🎟 Ticket purchased!")

# =========================
# MAIN
# =========================
def main():
    threading.Thread(target=run_web, daemon=True).start()

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("give", give))
    app.add_handler(CommandHandler("join", join))

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
