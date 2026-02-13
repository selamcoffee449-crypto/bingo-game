import os
import random
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("TOKEN")
TICKET_PRICE = 10

wallet = {}
players = {}

# ---------------- WEB (for Railway) ----------------
def run_web():
    web = Flask(__name__)

    @web.route("/")
    def home():
        return "Bingo running"

    port = int(os.environ.get("PORT", 3000))
    web.run(host="0.0.0.0", port=port)


# ---------------- BINGO BOARD ----------------
def generate_board():
    nums = random.sample(range(1, 76), 25)
    nums[12] = "FREE"
    return [nums[i:i+5] for i in range(0, 25, 5)]


def board_to_text(board):
    text = ""
    for row in board:
        text += " ".join(str(x).rjust(2) for x in row) + "\n"
    return text


# ---------------- COMMANDS ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.id
    wallet.setdefault(user, 0)
    await update.message.reply_text("Welcome to Bingo Bot!")


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
    players[user] = {
        "board": generate_board(),
        "marked": set()
    }

    await update.message.reply_text("Ticket purchased.")
    await update.message.reply_text(board_to_text(players[user]["board"]))


async def board(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.id

    if user not in players:
        await update.message.reply_text("You are not in game.")
        return

    await update.message.reply_text(board_to_text(players[user]["board"]))


# ---------------- MAIN ----------------
def main():
    threading.Thread(target=run_web).start()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("give", give))
    app.add_handler(CommandHandler("join", join))
    app.add_handler(CommandHandler("board", board))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
