import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# =========================
# CONFIG
# =========================
TOKEN = os.getenv("TOKEN")  # set in Railway variables
TICKET_PRICE = 10

# your telegram id here
ADMIN_IDS = [6835994100]

# =========================
# WEB SERVER FOR RAILWAY
# =========================
def run_web():
    web = Flask(__name__)

    @web.route("/")
    def home():
        return "Bingo bot is running!"

    port = int(os.environ.get("PORT", 3000))
    web.run(host="0.0.0.0", port=port)


# =========================
# SIMPLE MEMORY DATABASE
# =========================
wallet = {}


# =========================
# COMMANDS
# =========================
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
    await update.message.reply_text("Ticket purchased.")


# =========================
# ADMIN COMMAND
# =========================
async def addbalance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = update.effective_user.id

    if sender not in ADMIN_IDS:
        await update.message.reply_text("Admin only.")
        return

    if len(context.args) != 2:
        await update.message.reply_text("Usage: /addbalance user_id amount")
        return

    user_id = int(context.args[0])
    amount = int(context.args[1])

    wallet[user_id] = wallet.get(user_id, 0) + amount
    await update.message.reply_text(f"Added {amount} to {user_id}.")


# =========================
# MAIN
# =========================
def main():
    # Railway needs a web server
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
