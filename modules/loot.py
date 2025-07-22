import time
import pydirectinput

from config import LOOT_KEY, LOOT_DELAY


def loot():
    """Press the loot key and wait for the delay."""
    pydirectinput.press(LOOT_KEY)
    time.sleep(LOOT_DELAY)
