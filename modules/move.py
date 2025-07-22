# modules/move.py
import pyautogui
import random
import time
from config import MOVE_KEYS

def move():
    key = random.choice(MOVE_KEYS)
    duration = random.uniform(0.2, 0.5)
    pyautogui.keyDown(key)
    time.sleep(duration)
    pyautogui.keyUp(key)
    time.sleep(0.5)
