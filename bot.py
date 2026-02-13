import os
import random
import sqlite3
import asyncio
import threading
from flask import Flask, request

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes


# ================= CONFIG =================
TOKEN = os.getenv("TOKEN")
ADMIN_PASSWORD = "1234"

TICKET_PRICE = 10
DRAW_DELAY = 5  # seconds between numbers


# ================= DATABASE =================
conn = sqlite3.connect("bingo.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    name TEXT,
    balance INTEGER DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS tickets(
    user_id INTEGER,
    numbers TEXT
)
""")

conn.commit()


# ================= MEMORY =================
game_running = False
drawn_numbers = []
players = {}  # user_id -> card


# ================= BINGO CARD =================
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


# ================= COMMANDS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    cur.execute("INSERT OR IGNORE INTO users(user_id,name,balance) VALUES(?,?,0)",
                (user.id, user.first_name))
    conn.commit()

    await update.message.reply_text(f"Welcome!\nYour ID: {user.id}")


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.id
    cur.execute("SELECT balance FROM users WHERE user_id=?", (user,))
    bal = cur.fetchone()

    if bal:
        await update.message.reply_text(f"Balance: {bal[0]}")


async def give(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.id
    cur.execute("UPDATE users SET balance = balance + 100 WHERE user_id=?", (user,))
    conn.commit()
    await update.message.reply_text("Added 100.")


async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global players

    user = update.effective_user.id

    cur.execute("SELECT balance FROM users WHERE user_id=?", (user,))
    bal = cur.fetchone()

    if not bal or bal[0] < TICKET_PRICE:
        await update.message.reply_text("Not enough balance.")
        return

    cur.execute("UPDATE users SET balance = balance - ? WHERE user_id=?",
                (TICKET_PRICE, user))
    conn.commit()

    card = generate_card()
    players[user] = card

    cur.execute("INSERT INTO tickets VALUES(?,?)", (user, str(card)))
    conn.commit()

    await update.message.reply_text(
        "🎟 Ticket purchased!\n\nYour card:\n" + format_card(card)
    )


# ================= CHECK WIN =================
def check_win(card):
    # rows
    for i in range(5):
        row = card[i*5:(i+1)*5]
        if all(n == "★" or n in drawn_numbers for n in row):
            return True

    # columns
    for i in range(5):
        col = [card[i+j*5] for j in range(5)]
        if all(n == "★" or n in drawn_numbers for n in col):
            return True

    return False


# ================= ROUND ENGINE =================
async def run_round(app):
    global game_running, drawn_numbers, players

    chat_id = list(players.keys())
    if not chat_id:
        game_running = False
        return

    drawn_numbers = []
    numbers = list(range(1, 76))
    random.shuffle(numbers)

    await app.bot.send_message(
        chat_id=update_chat_id,
        text="🎯 ROUND STARTED!"
    )

    for n in numbers:
        if not game_running:
            break

        drawn_numbers.append(n)

        await app.bot.send_message(
            chat_id=update_chat_id,
            text=f"🎱 Number: {n}"
        )

        winners = []
        for uid, card in players.items():
            if check_win(card):
                winners.append(uid)

        if winners:
            prize = 50
            for w in winners:
                cur.execute("UPDATE users SET balance = balance + ? WHERE user_id=?",
                            (prize, w))
            conn.commit()

            await app.bot.send_message(
                chat_id=update_chat_id,
                text=f"🏆 Winners: {len(winners)} players!"
            )

            break

        await asyncio.sleep(DRAW_DELAY)

    players = {}
    game_running = False


update_chat_id = None


async def startround(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global game_running, update_chat_id

    if game_running:
        await update.message.reply_text("Game already running.")
        return

    if not players:
        await update.message.reply_text("No players joined.")
        return

    update_chat_id = update.effective_chat.id
    game_running = True

    asyncio.create_task(run_round(context.application))


# ================= ADMIN COMMAND =================
async def addbalance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) != 2:
        await update.message.reply_text("Usage: /addbalance user amount")
        return

    uid = int(args[0])
    amount = int(args[1])

    cur.execute("UPDATE users SET balance = balance + ? WHERE user_id=?",
                (amount, uid))
    conn.commit()

    await update.message.reply_text("Balance updated.")


# ================= WEBSITE =================
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

        return f"""
        <h1>Bingo Admin</h1>
        <a href='/admin/users?pw={pw}'>Users</a><br>
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


# ================= MAIN =================
def main():
    threading.Thread(target=run_web).start()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("give", give))
    app.add_handler(CommandHandler("join", join))
    app.add_handler(CommandHandler("startround", startround))
    app.add_handler(CommandHandler("addbalance", addbalance))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
