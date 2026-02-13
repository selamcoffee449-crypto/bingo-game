from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from config import TOKEN, ROUND_TIME
import db
import game
import admin
import asyncio


# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.id
    db.get_user(user)
    await update.message.reply_text("Welcome to Bingo Bot!")


# /balance
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.id
    bal = db.get_balance(user)
    await update.message.reply_text(f"Balance: {bal}")


# /join
async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.id
    ok, msg = game.join_game(user)
    await update.message.reply_text(msg)


# admin give money
async def give(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = update.effective_user.id

    if len(context.args) != 2:
        await update.message.reply_text("/give user_id amount")
        return

    target = int(context.args[0])
    amount = int(context.args[1])

    msg = admin.admin_add_balance(admin_id, target, amount)
    await update.message.reply_text(msg)


# automatic round
async def auto_round(context: ContextTypes.DEFAULT_TYPE):
    result = game.draw_winner()
    if result:
        winner, pot = result
        try:
            await context.bot.send_message(
                winner, f"You won {pot}!"
            )
        except:
            pass


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("join", join))
    app.add_handler(CommandHandler("give", give))

    # job queue instead of create_task
    app.job_queue.run_repeating(auto_round, interval=ROUND_TIME, first=ROUND_TIME)

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()