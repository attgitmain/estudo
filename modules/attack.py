import time
try:
    import pydirectinput
except ImportError:  # fallback if pydirectinput is missing
    import pyautogui as pydirectinput

from config import ATTACK_KEY, ATTACK_DELAY


def attack():
    """Trigger the attack key and wait for the delay."""
    pydirectinput.press(ATTACK_KEY)
    time.sleep(ATTACK_DELAY)
