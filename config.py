import os

# Telegram Bot Token (comes from Railway variables)
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN is missing!")

# Admin IDs
admin_raw = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(x) for x in admin_raw.split(",") if x.strip()]

# Game settings
TICKET_PRICE = int(os.getenv("TICKET_PRICE", 10))
ROUND_TIME = int(os.getenv("ROUND_TIME", 60))
