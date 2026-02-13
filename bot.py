import os
import random
import asyncio
import threading
from flask import Flask

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ================= CONFIG =================
TOKEN = os.getenv("TOKEN")
TICKET_PRICE = 10
DRAW_DELAY = 5
MIN_PLAYERS = 2
START_DELAY = 20


# ================= RAILWAY KEEP ALIVE =================
def run_web():
    app = Flask(__name__)

    @app.route("/")
    def home():
        return "Bingo running!"

    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)


# ================= GLOBAL DATA =================
wallet = {}
players = {}
jackpot = 0
game_running = False
drawn_numbers = []
start_task = None


# ================= CARD =================
def generate_card():
    card = []
    ranges = [
        range(1, 16),
        range(16, 31),
        range(31, 46),
        range(46, 61),
        range(61, 76),
    ]

    for r in ranges:
        card.append(random.sample(list(r), 5))

    card = list(map(list, zip(*card)))
    card[2][2] = "★"
    return card


# ================= WIN CHECK =================
def check_win(card):
    # rows
    for row in card:
        if all(n in drawn_numbers or n == "★" for n in row):
            return True

    # columns
    for col in range(5):
        if all(card[row][col] in drawn_numbers or card[row][col] == "★" for row in range(5)):
            return True

    # diagonals
    if all(card[i][i] in drawn_numbers or card[i][i] == "★" for i in range(5)):
        return True

    if all(card[i][4-i] in drawn_numbers or card[i][4-i] == "★" for i in range(5)):
        return True

    return False


# ================= COMMANDS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    wallet.setdefault(user.id, 0)
    await update.message.reply_text(f"Welcome!\nYour ID: {user.id}")


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.id
    await update.message.reply_text(f"Balance: {wallet.get(user, 0)}")


async def give(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.id
    wallet[user] = wallet.get(user, 0) + 100
    await update.message.reply_text("Added 100.")


# ================= JOIN =================
async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global jackpot, start_task

    user = update.effective_user

    if game_running:
        await update.message.reply_text("Round already running.")
        return

    if wallet.get(user.id, 0) < TICKET_PRICE:
        await update.message.reply_text("Not enough balance.")
        return

    if user.id in players:
        await update.message.reply_text("Already joined.")
        return

    wallet[user.id] -= TICKET_PRICE
    jackpot += TICKET_PRICE

    players[user.id] = {
        "name": user.first_name,
        "card": generate_card()
    }

    await update.message.reply_text(
        f"🎟 {user.first_name} joined!\n"
        f"👥 Players: {len(players)}\n"
        f"💰 Jackpot: {jackpot}"
    )

    context.bot_data["chat"] = update.effective_chat.id

    # auto countdown
    if len(players) >= MIN_PLAYERS and start_task is None:
        start_task = asyncio.create_task(countdown_start(context))


# ================= COUNTDOWN =================
async def countdown_start(context: ContextTypes.DEFAULT_TYPE):
    global start_task

    chat_id = context.bot_data["chat"]

    for i in range(START_DELAY, 0, -5):
        await context.bot.send_message(chat_id, f"⏳ Starting in {i} sec")
        await asyncio.sleep(5)

    await context.bot.send_message(chat_id, "🎯 ROUND STARTING!")
    asyncio.create_task(run_round(context))

    start_task = None


# ================= ROUND ENGINE =================
async def run_round(context: ContextTypes.DEFAULT_TYPE):
    global game_running, drawn_numbers, jackpot, players

    chat_id = context.bot_data["chat"]

    numbers = list(range(1, 76))
    random.shuffle(numbers)

    drawn_numbers = []
    game_running = True

    await context.bot.send_message(chat_id, f"🎯 ROUND STARTED\n💰 Jackpot: {jackpot}")

    for n in numbers:
        if not game_running:
            break

        drawn_numbers.append(n)

        draw_list = " ".join(str(x) for x in sorted(drawn_numbers))
        left = 75 - len(drawn_numbers)

        await context.bot.send_message(
            chat_id,
            f"🎱 New: {n}\n\n📋 {draw_list}\n⏳ Left: {left}"
        )

        winners = []

        for uid, data in players.items():
            if check_win(data["card"]):
                winners.append(uid)

        if winners:
            prize_each = jackpot // len(winners)

            for uid in winners:
                wallet[uid] += prize_each
                await context.bot.send_message(
                    chat_id,
                    f"🏆 {players[uid]['name']} wins {prize_each}"
                )

            game_running = False
            break

        await asyncio.sleep(DRAW_DELAY)

    await context.bot.send_message(chat_id, "🔄 Round ended.")

    players = {}
    jackpot = 0
    drawn_numbers = []

    await asyncio.sleep(10)
    game_running = False


# ================= MANUAL START =================
async def startround(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.bot_data["chat"] = update.effective_chat.id
    asyncio.create_task(run_round(context))


# ================= MAIN =================
def main():
    threading.Thread(target=run_web).start()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("give", give))
    app.add_handler(CommandHandler("join", join))
    app.add_handler(CommandHandler("startround", startround))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
