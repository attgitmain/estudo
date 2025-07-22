# modules/move.py
import random
import time
import pydirectinput
from config import MOVE_KEYS

def move():
    key = random.choice(MOVE_KEYS)
    duration = random.uniform(0.2, 0.4)
    pydirectinput.keyDown(key)
    time.sleep(duration)
    pydirectinput.keyUp(key)
    time.sleep(0.4)
