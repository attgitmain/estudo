import time
from modules.attack import attack
from modules.loot import loot
import keyboard

def main():
    print("🔁 Bot iniciado. Pressione F8 para parar.")
    running = True

    # Pressione F8 para parar
    keyboard.add_hotkey('F8', lambda: stop())

    while True:
        try:
            attack()
            loot()
        except Exception as e:
            print(f"Erro: {e}")
            break

def stop():
    print("🛑 Bot parado.")
    exit()

if __name__ == "__main__":
    main()
