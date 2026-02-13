import os
import random
import asyncio
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# =========================
# CONFIG
# =========================
TOKEN = os.getenv("TOKEN")
ADMIN_ID = 6835994100  # change if needed
TICKET_PRICE = 10

# =========================
# RAILWAY WEB SERVER
# =========================
def run_web():
    web = Flask(__name__)

    @web.route("/")
    def home():
        return "Bingo bot running!"

    port = int(os.environ.get("PORT", 3000))
    web.run(host="0.0.0.0", port=port)


# =========================
# MEMORY DATABASE
# =========================
wallet = {}
players = {}

game_running = False
drawn_numbers = []
jackpot = 0


# =========================
# BINGO BOARD
# =========================
def generate_board():
    board = []
    ranges = [
        range(1, 16),
        range(16, 31),
        range(31, 46),
        range(46, 61),
        range(61, 76),
    ]

    for r in ranges:
        col = random.sample(list(r), 5)
        board.append(col)

    board[2][2] = "⭐"
    return board


def format_board(board):
    text = "B  I  N  G  O\n"
    for row in range(5):
        for col in range(5):
            text += f"{board[col][row]} ".rjust(4)
        text += "\n"
    return text


def mark_number(board, number):
    for col in range(5):
        for row in range(5):
            if board[col][row] == number:
                board[col][row] = "X"


def check_win(board):
    # horizontal
    for row in range(5):
        if all(board[col][row] in ("X", "⭐") for col in range(5)):
            return True

    # vertical
    for col in range(5):
        if all(board[col][row] in ("X", "⭐") for row in range(5)):
            return True

    return False


# =========================
# COMMANDS
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
    global jackpot

    user = update.effective_user.id

    if game_running:
        await update.message.reply_text("Game already running.")
        return

    if wallet.get(user, 0) < TICKET_PRICE:
        await update.message.reply_text("Not enough balance.")
        return

    wallet[user] -= TICKET_PRICE
    jackpot += TICKET_PRICE

    card = generate_board()
    players[user] = card

    await update.message.reply_text(
        "🎟 Ticket purchased!\n\nYour Bingo Card:\n\n" + format_board(card)
    )


# =========================
# ADMIN
# =========================
async def addbalance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if len(context.args) != 2:
        await update.message.reply_text("Usage: /addbalance user_id amount")
        return

    user_id = int(context.args[0])
    amount = int(context.args[1])

    wallet[user_id] = wallet.get(user_id, 0) + amount
    await update.message.reply_text(f"Added {amount} to {user_id}")


async def startgame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global game_running

    if update.effective_user.id != ADMIN_ID:
        return

    if game_running:
        await update.message.reply_text("Already running.")
        return

    if not players:
        await update.message.reply_text("No players.")
        return

    await update.message.reply_text("🎯 Game started!")
    asyncio.create_task(game_loop(context.application))


# =========================
# GAME LOOP
# =========================
async def game_loop(app):
    global game_running, drawn_numbers, jackpot

    game_running = True
    drawn_numbers = []

    while True:
        await asyncio.sleep(5)

        number = random.randint(1, 75)
        if number in drawn_numbers:
            continue

        drawn_numbers.append(number)

        for user, card in players.items():
            mark_number(card, number)

            if check_win(card):
                wallet[user] = wallet.get(user, 0) + jackpot

                await app.bot.send_message(
                    chat_id=user,
                    text=f"🏆 BINGO!\nYou won {jackpot}"
                )

                jackpot = 0
                players.clear()
                game_running = False
                return


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
    app.add_handler(CommandHandler("startgame", startgame))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
