import os
import random
import sqlite3
import threading
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ==================================================
# SETTINGS
# ==================================================
TOKEN = os.getenv("BOT_TOKEN")  # put in Railway variables
ADMIN_PASSWORD = "1234"

game_running = False
current_number = None

# ==================================================
# DATABASE
# ==================================================
conn = sqlite3.connect("bingo.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    name TEXT,
    balance INTEGER DEFAULT 0
)
""")
conn.commit()

# ==================================================
# TELEGRAM COMMANDS
# ==================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    cur.execute("INSERT OR IGNORE INTO users(user_id,name,balance) VALUES(?,?,0)",
                (user.id, user.first_name))
    conn.commit()

    await update.message.reply_text("Welcome to Bingo bot!")

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    cur.execute("SELECT balance FROM users WHERE user_id=?",(user.id,))
    row = cur.fetchone()

    if row:
        await update.message.reply_text(f"Balance: {row[0]}")
    else:
        await update.message.reply_text("Use /start first.")

async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not game_running:
        await update.message.reply_text("Game not running.")
        return

    await update.message.reply_text("You joined the round!")

async def number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not game_running:
        await update.message.reply_text("Game not running.")
        return

    await update.message.reply_text(f"Current number: {current_number}")

# ==================================================
# ROUND ENGINE
# ==================================================
def game_loop(app):
    global current_number
    while True:
        if game_running:
            current_number = random.randint(1, 90)
        import time
        time.sleep(5)

# ==================================================
# WEBSITE
# ==================================================
def run_web():
    from flask import Flask, request

    app = Flask(__name__)

    # ================= HOME =================
    @app.route("/")
    def home():
        return "Bingo system online."

    # ================= ADMIN =================
    @app.route("/admin")
    def admin():
        pw = request.args.get("pw")
        if pw != ADMIN_PASSWORD:
            return "Wrong password."

        return f"""
        <h1>Bingo Admin</h1>
        <a href='/admin/stats?pw={pw}'>Stats</a><br>
        <a href='/admin/users?pw={pw}'>Users</a><br>
        <a href='/admin/start?pw={pw}'>Start Game</a><br>
        <a href='/admin/stop?pw={pw}'>Stop Game</a><br>
        """

    # ================= STATS =================
    @app.route("/admin/stats")
    def stats():
        pw = request.args.get("pw")
        if pw != ADMIN_PASSWORD:
            return "Wrong password."

        cur.execute("SELECT COUNT(*) FROM users")
        count = cur.fetchone()[0]

        return f"""
        <h1>Stats</h1>
        Users: {count}<br>
        Game running: {game_running}<br><br>
        <a href='/admin?pw={pw}'>Back</a>
        """

    # ================= USERS =================
    @app.route("/admin/users")
    def users():
        pw = request.args.get("pw")
        if pw != ADMIN_PASSWORD:
            return "Wrong password."

        cur.execute("SELECT user_id,name,balance FROM users")
        rows = cur.fetchall()

        text = "<h1>Users</h1>"
        for u in rows:
            text += f"{u[0]} | {u[1]} | {u[2]}<br>"

        text += f"<br><a href='/admin?pw={pw}'>Back</a>"
        return text

    # ================= START =================
    @app.route("/admin/start")
    def start_game():
        global game_running
        pw = request.args.get("pw")
        if pw != ADMIN_PASSWORD:
            return "Wrong password."

        game_running = True
        return f"Game started.<br><a href='/admin?pw={pw}'>Back</a>"

    # ================= STOP =================
    @app.route("/admin/stop")
    def stop_game():
        global game_running
        pw = request.args.get("pw")
        if pw != ADMIN_PASSWORD:
            return "Wrong password."

        game_running = False
        return f"Game stopped.<br><a href='/admin?pw={pw}'>Back</a>"

    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)

# ==================================================
# MAIN
# ==================================================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("join", join))
    app.add_handler(CommandHandler("number", number))

    # start game loop
    threading.Thread(target=game_loop, args=(app,), daemon=True).start()

    # start web in another thread
    threading.Thread(target=run_web, daemon=True).start()

    print("Bot + Web running...")
    app.run_polling()

if __name__ == "__main__":
    main()
