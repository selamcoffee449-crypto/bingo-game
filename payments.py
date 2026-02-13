from db import add_balance

def deposit(user_id, amount):
    add_balance(user_id, amount)


def withdraw(user_id, amount):
    # later connect real payment
    add_balance(user_id, -amount)