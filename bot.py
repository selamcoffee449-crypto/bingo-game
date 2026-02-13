import os
import random
import sqlite3
import asyncio
import threading
from flask import Flask, request, redirect

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes


# ================= CONFIG =================
TOKEN = os.getenv("TOKEN")
ADMIN_PASSWORD = "1234"

TICKET_PRICE = 10
DRAW_DELAY = 4


# ================= DATABASE INIT =================
def init_db():
    conn = sqlite3.connect("bingo.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY,
        name TEXT,
        balance INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()


init_db()


# ================= MEMORY =================
game_running = False
drawn_numbers = []
players = {}
group_chat_id = None


# ================= CARD =================
def generate_card():
    nums = random.sample(range(1, 76), 25)
    nums[12] = "★"
    return nums


def format_card(card):
    text = "B I N G O\n"
    for i in range(5):
        row = card[i*5:(i+1)*5]
        text += " ".join(str(x) for x in row) + "\n"
    return text


# ================= WIN CHECK =================
def check_win(card):
    for i in range(5):
        row = card[i*5:(i+1)*5]
        if all(n == "★" or n in drawn_numbers for n in row):
            return True

    for i in range(5):
        col = [card[i+j*5] for j in range(5)]
        if all(n == "★" or n in drawn_numbers for n in col):
            return True

    return False


# ================= COMMANDS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    conn = sqlite3.connect("bingo.db")
    cur = conn.cursor()

    cur.execute(
        "INSERT OR IGNORE INTO users(user_id,name,balance) VALUES(?,?,0)",
        (user.id, user.first_name)
    )

    conn.commit()
    conn.close()

    await update.message.reply_text(f"Welcome!\nYour ID: {user.id}")


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect("bingo.db")
    cur = conn.cursor()

    cur.execute("SELECT balance FROM users WHERE user_id=?", (update.effective_user.id,))
    bal = cur.fetchone()

    conn.close()

    if bal:
        await update.message.reply_text(f"Balance: {bal[0]}")


async def give(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect("bingo.db")
    cur = conn.cursor()

    cur.execute("UPDATE users SET balance = balance + 100 WHERE user_id=?",
                (update.effective_user.id,))

    conn.commit()
    conn.close()

    await update.message.reply_text("Added 100.")


async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global players, group_chat_id

    user = update.effective_user.id
    group_chat_id = update.effective_chat.id

    conn = sqlite3.connect("bingo.db")
    cur = conn.cursor()

    cur.execute("SELECT balance FROM users WHERE user_id=?", (user,))
    bal = cur.fetchone()

    if not bal or bal[0] < TICKET_PRICE:
        conn.close()
        await update.message.reply_text("Not enough balance.")
        return

    cur.execute("UPDATE users SET balance = balance - ? WHERE user_id=?",
                (TICKET_PRICE, user))

    conn.commit()
    conn.close()

    card = generate_card()
    players[user] = card

    await update.message.reply_text(
        "🎟 Ticket purchased!\n\n" + format_card(card)
    )


# ================= ROUND ENGINE =================
async def run_round(app):
    global game_running, drawn_numbers, players

    drawn_numbers = []
    numbers = list(range(1, 76))
    random.shuffle(numbers)

    await app.bot.send_message(group_chat_id, "🎯 ROUND STARTED!")

    for n in numbers:
        if not game_running:
            break

        drawn_numbers.append(n)

        await app.bot.send_message(group_chat_id, f"🎱 {n}")

        winners = []
        for uid, card in players.items():
            if check_win(card):
                winners.append(uid)

        if winners:
            prize = 50

            conn = sqlite3.connect("bingo.db")
            cur = conn.cursor()

            for w in winners:
                cur.execute("UPDATE users SET balance = balance + ? WHERE user_id=?",
                            (prize, w))

            conn.commit()
            conn.close()

            await app.bot.send_message(
                group_chat_id,
                f"🏆 Winners: {len(winners)}"
            )

            break

        await asyncio.sleep(DRAW_DELAY)

    players = {}
    game_running = False


async def startround(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global game_running

    if game_running:
        await update.message.reply_text("Already running.")
        return

    if not players:
        await update.message.reply_text("No players.")
        return

    game_running = True
    asyncio.create_task(run_round(context.application))


# ================= ADMIN WEBSITE =================
def run_web():
    app = Flask(__name__)

    def check(pw):
        return pw == ADMIN_PASSWORD

    @app.route("/")
    def home():
        return "Bingo system online."

    @app.route("/admin")
    def admin():
        pw = request.args.get("pw")
        if not check(pw):
            return "Wrong password."

        return f"""
        <h1>🎯 Bingo Admin</h1>
        <a href='/admin/users?pw={pw}'>Users</a><br>
        <a href='/admin/stats?pw={pw}'>Stats</a><br>
        """

    @app.route("/admin/users")
    def users():
        pw = request.args.get("pw")
        if not check(pw):
            return "Wrong password."

        conn = sqlite3.connect("bingo.db")
        cur = conn.cursor()
        cur.execute("SELECT user_id,name,balance FROM users")
        rows = cur.fetchall()
        conn.close()

        text = f"<h1>Users</h1><a href='/admin?pw={pw}'>Back</a><br><br>"
        for u in rows:
            text += f"{u[0]} | {u[1]} | {u[2]}<br>"
        return text

    @app.route("/admin/stats")
    def stats():
        pw = request.args.get("pw")
        if not check(pw):
            return "Wrong password."

        conn = sqlite3.connect("bingo.db")
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users")
        users = cur.fetchone()[0]
        conn.close()

        return f"""
        <h1>Stats</h1>
        Users: {users}<br>
        <a href='/admin?pw={pw}'>Back</a>
        """

    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)


# ================= MAIN =================
def main():
    threading.Thread(target=run_web, daemon=True).start()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("give", give))
    app.add_handler(CommandHandler("join", join))
    app.add_handler(CommandHandler("startround", startround))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
