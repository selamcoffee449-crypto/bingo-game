import os
import threading
import random
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# =========================
# CONFIG
# =========================
TOKEN = os.getenv("TOKEN")
ADMIN_ID = 6835994100
TICKET_PRICE = 10


# =========================
# WEB SERVER (RAILWAY)
# =========================
def run_web():
    web = Flask(__name__)

    @web.route("/")
    def home():
        return "Bingo bot is running!"

    port = int(os.environ.get("PORT", 3000))
    web.run(host="0.0.0.0", port=port)


# =========================
# MEMORY
# =========================
wallet = {}
players = {}


# =========================
# BINGO BOARD
# =========================
def generate_board():
    board = []

    board.append(random.sample(range(1, 16), 5))
    board.append(random.sample(range(16, 31), 5))

    n = random.sample(range(31, 46), 5)
    n[2] = "⭐"
    board.append(n)

    board.append(random.sample(range(46, 61), 5))
    board.append(random.sample(range(61, 76), 5))

    return board


def format_board(board):
    text = "B   I   N   G   O\n"
    for row in range(5):
        for col in range(5):
            value = board[col][row]
            text += f"{str(value).rjust(2)}  "
        text += "\n"
    return text


# =========================
# USER COMMANDS
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.id
    wallet.setdefault(user, 0)
    await update.message.reply_text(f"Welcome!\nYour ID: {user}")


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.id
    await update.message.reply_text(f"Balance: {wallet.get(user, 0)}")


async def give(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.id
    wallet[user] = wallet.get(user, 0) + 100
    await update.message.reply_text("Added 100.")


async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.id

    if wallet.get(user, 0) < TICKET_PRICE:
        await update.message.reply_text("Not enough balance.")
        return

    wallet[user] -= TICKET_PRICE

    card = generate_board()
    players[user] = card

    await update.message.reply_text(
        "🎟 Ticket purchased!\n\nYour Bingo Card:\n\n" + format_board(card)
    )


# =========================
# ADMIN COMMAND
# =========================
async def addbalance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Admin only.")
        return

    try:
        user_id = int(context.args[0])
        amount = int(context.args[1])
    except:
        await update.message.reply_text("Usage: /addbalance user_id amount")
        return

    wallet[user_id] = wallet.get(user_id, 0) + amount
    await update.message.reply_text(f"Added {amount} to {user_id}.")


# =========================
# MAIN
# =========================
def main():
    threading.Thread(target=run_web).start()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("give", give))
    app.add_handler(CommandHandler("join", join))
    app.add_handler(CommandHandler("addbalance", addbalance))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
