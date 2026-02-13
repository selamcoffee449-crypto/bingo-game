import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# =========================
# CONFIG
# =========================
TOKEN = os.getenv("TOKEN")  # from Railway
TICKET_PRICE = 10

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
# MAIN
# =========================
def main():
    # start Railway web server
    threading.Thread(target=run_web).start()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("give", give))
    app.add_handler(CommandHandler("join", join))
    from admin import add_balance
application.add_handler(CommandHandler("addbalance", add_balance))
    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
