import keyboard
import time

from config import LOOT_KEY, LOOT_DELAY


def loot():
    """Press the loot key and wait for the delay."""
    keyboard.press_and_release(LOOT_KEY)
    time.sleep(LOOT_DELAY)
