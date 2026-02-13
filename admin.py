from config import ADMIN_IDS
from payments import deposit


def is_admin(user_id):
    return user_id in ADMIN_IDS


def admin_add_balance(user_id, target, amount):
    if not is_admin(user_id):
        return "Not admin."

    deposit(target, amount)
    return f"Added {amount}."