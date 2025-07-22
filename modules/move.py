# modules/move.py
import keyboard
import random
import time
from config import MOVE_KEYS

def move():
    key = random.choice(MOVE_KEYS)
    duration = random.uniform(0.2, 0.4)
    keyboard.press(key)
    time.sleep(duration)
    keyboard.release(key)
    time.sleep(0.4)
