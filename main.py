import time
import keyboard
import pyautogui
import psutil
import sys
import os

# Garante que a pasta 'modules' seja encontrada mesmo se executado de fora
sys.path.append(os.path.join(os.path.dirname(__file__), "modules"))

# Importa os módulos internos
from attack import attack
from loot import loot
from move import move

bot_running = False

def check_metin2_running():
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] and "NewMt2_com.exe" in proc.info['name']:
            return True
    return False

def start_bot():
    global bot_running
    bot_running = True
    print("✅ Bot iniciado! Pressione F9 para parar.")
    while bot_running:
        try:
            attack()
            loot()
            move()
        except Exception as e:
            print(f"❌ Erro no bot: {e}")
            stop_bot()
        time.sleep(0.1)

def stop_bot():
    global bot_running
    bot_running = False
    print("🛑 Bot parado.")

def main():
    print("🔍 Aguardando o Metin2 iniciar...")
    while not check_metin2_running():
        time.sleep(1)

    print("🎮 Cliente Metin2 detectado. Pressione F9 para INICIAR/PARAR o bot.")
    keyboard.add_hotkey('F9', lambda: start_bot() if not bot_running else stop_bot())

    while True:
        time.sleep(0.1)

if __name__ == "__main__":
    main()
