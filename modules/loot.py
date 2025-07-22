import pyautogui
import time
from config import LOOT_KEY, LOOT_DELAY

def loot():
    pyautogui.press(LOOT_KEY)
    time.sleep(LOOT_DELAY)
