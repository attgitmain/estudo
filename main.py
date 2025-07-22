import keyboard
from modules.attack import attack
from modules.loot import loot


RUNNING = True


def stop():
    """Stop the bot loop."""
    global RUNNING
    RUNNING = False


def main():
    """Start the attack/loot loop until F8 is pressed."""
    print("🔁 Bot iniciado. Pressione F8 para parar.")

    keyboard.add_hotkey("F8", stop)

    try:
        while RUNNING:
            attack()
            loot()
    except Exception as e:
        print(f"Erro: {e}")
    finally:
        print("🛑 Bot parado.")


if __name__ == "__main__":
    main()
