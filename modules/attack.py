import pyautogui
import time
from config import ATTACK_KEY, ATTACK_DELAY

def attack():
    pyautogui.press(ATTACK_KEY)
    time.sleep(ATTACK_DELAY)
