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
DRAW_DELAY = 5   # seconds between numbers

# PUT YOUR GROUP ID HERE
GROUP_ID = -1001234567890   # change

# ================= WEB SERVER =================
def run_web():
    app = Flask(__name__)

    @app.route("/")
    def home():
        return "Bingo running!"

    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)

# ================= DATABASE (TEMP) =================
wallet = {}
players = {}
current_numbers = []
game_running = False


# ================= CARD GENERATOR =================
def generate_card():
    nums = random.sample(range(1, 76), 24)
    card = [nums[i:i+5] for i in range(0, 24, 5)]
    card.insert(2, card[2][:2] + ["⭐"] + card[2][2:])
    return card


def format_card(card):
    text = "B  I  N  G  O\n"
    for row in card:
        text += " ".join(str(x).rjust(2) for x in row) + "\n"
    return text


# ================= COMMANDS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.id
    wallet.setdefault(user, 0)
    await update.message.reply_text(f"Welcome!\nYour ID: {user}")


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.id
    await update.message.reply_text(f"Balance: {wallet.get(user,0)}")


async def give(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.id
    wallet[user] = wallet.get(user, 0) + 100
    await update.message.reply_text("Added 100.")


# buy ticket
async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global players
    user = update.effective_user.id

    if wallet.get(user, 0) < TICKET_PRICE:
        await update.message.reply_text("Not enough balance.")
        return

    wallet[user] -= TICKET_PRICE
    card = generate_card()
    players[user] = card

    await update.message.reply_text(
        "🎟 Ticket purchased!\n\nYour card:\n" + format_card(card)
    )


# ================= CHECK WIN =================
def is_winner(card):
    for row in card:
        ok = True
        for x in row:
            if x == "⭐":
                continue
            if x not in current_numbers:
                ok = False
                break
        if ok:
            return True
    return False


# ================= DRAW ENGINE =================
async def draw_loop(app):
    global current_numbers, game_running, players

    game_running = True
    current_numbers = []

    numbers = list(range(1, 76))
    random.shuffle(numbers)

    jackpot = len(players) * TICKET_PRICE

    await app.bot.send_message(GROUP_ID, f"🎉 GAME STARTED\nPlayers: {len(players)}\nJackpot: {jackpot}")

    for n in numbers:
        current_numbers.append(n)

        await app.bot.send_message(GROUP_ID, f"Number: {n}")

        # check winners
        for user, card in players.items():
            if is_winner(card):
                wallet[user] = wallet.get(user, 0) + jackpot
                await app.bot.send_message(GROUP_ID, f"🏆 Winner: {user}\nWon {jackpot}")
                players = {}
                game_running = False
                return

        await asyncio.sleep(DRAW_DELAY)

    players = {}
    game_running = False


# admin start in group
async def startround(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global game_running

    if game_running:
        await update.message.reply_text("Game already running.")
        return

    if not players:
        await update.message.reply_text("No players.")
        return

    asyncio.create_task(draw_loop(context.application))


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
