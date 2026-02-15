import os

# Telegram Bot Token (set in Railway Variables)
TOKEN = os.getenv("8496790065:AAHc1nCLXu6MyhzIce_B_aylJzq_UOyoiWI")

# Admin IDs (comma separated numbers in Railway)
# example: 123,456,789
admin_raw = os.getenv("6835994100", "")
ADMIN_IDS = [int(x) for x in admin_raw.split(",") if x.strip()]

# Game settings (you can still override from Railway if you want)
TICKET_PRICE = int(os.getenv("TICKET_PRICE", 10))
ROUND_TIME = int(os.getenv("ROUND_TIME", 60))
