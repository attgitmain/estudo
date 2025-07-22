import pyautogui
import time

from config import LOOT_KEY, LOOT_DELAY


def loot():
    """Press the loot key and wait for the delay."""
    pyautogui.press(LOOT_KEY)
    time.sleep(LOOT_DELAY)
