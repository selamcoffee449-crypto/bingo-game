import os
import threading
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import sqlite3


# =========================
# CONFIG
# =========================
TOKEN = os.getenv("TOKEN")
TICKET_PRICE = 10
ADMIN_PASSWORD = "1234"


# =========================
# DATABASE
# =========================
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


def add_user(user_id, name):
    cur.execute(
        "INSERT OR IGNORE INTO users(user_id,name,balance) VALUES(?,?,0)",
        (user_id, name),
    )
    conn.commit()


def get_balance(user_id):
    cur.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    return row[0] if row else 0


def add_balance(user_id, amount):
    cur.execute(
        "UPDATE users SET balance = balance + ? WHERE user_id=?",
        (amount, user_id),
    )
    conn.commit()


# =========================
# TELEGRAM COMMANDS
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id, user.first_name)
    await update.message.reply_text(f"Welcome!\nYour ID: {user.id}")


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.id
    bal = get_balance(user)
    await update.message.reply_text(f"Balance: {bal}")


async def give(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.id
    add_balance(user, 100)
    await update.message.reply_text("Added 100.")


async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.id
    bal = get_balance(user)

    if bal < TICKET_PRICE:
        await update.message.reply_text("Not enough balance.")
        return

    add_balance(user, -TICKET_PRICE)
    await update.message.reply_text("Ticket purchased.")


# =========================
# WEB ADMIN PANEL
# =========================
def run_web():
    app = Flask(__name__)

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
        <a href='/admin/users?pw=""" + pw + """'>Users</a><br>
        """

    @app.route("/admin/users")
    def users():
        pw = request.args.get("pw")
        if pw != ADMIN_PASSWORD:
            return "Wrong password."

        cur.execute("SELECT user_id,name,balance FROM users")
        rows = cur.fetchall()

        text = "<h1>Users</h1>"
        for u in rows:
            text += f"{u[0]} | {u[1]} | {u[2]} <br>"

        return text

    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)


# =========================
# MAIN
# =========================
def main():
    setup()

    # start web panel
    threading.Thread(target=run_web).start()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("give", give))
    app.add_handler(CommandHandler("join", join))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
