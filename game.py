import random
from config import TICKET_PRICE, ROUND_TIME
from db import get_balance, remove_balance, add_balance

players = []
round_active = False


def join_game(user_id):
    global players
    if get_balance(user_id) < TICKET_PRICE:
        return False, "Not enough balance."

    remove_balance(user_id, TICKET_PRICE)
    players.append(user_id)
    return True, "Ticket purchased."


def draw_winner():
    global players
    if not players:
        return None

    winner = random.choice(players)
    pot = len(players) * TICKET_PRICE
    add_balance(winner, pot)
    players = []
    return winner, pot