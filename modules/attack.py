import keyboard
import time

from config import ATTACK_KEY, ATTACK_DELAY


def attack():
    """Trigger the attack key and wait for the delay."""
    keyboard.press_and_release(ATTACK_KEY)
    time.sleep(ATTACK_DELAY)
