import threading
import time
import sys
import os
from colorama import Fore, Style, init
from buddy import buddy
import stt

# Initialize colorama
init(autoreset=True)

def run_stt():
    """Runs the Speech-to-Text listener in a background thread."""
    print(Fore.CYAN + "🎙️ Starting Voice Listener...")
    try:
        stt.main()
    except Exception as e:
        print(Fore.RED + f"❌ STT Error: {e}")

def main():
    print(Fore.BLUE + Style.BRIGHT + "="*60)
    print(Fore.BLUE + Style.BRIGHT + "       🤖 THE ULTIMATE AI BUDDY IS ONLINE 🤖       ")
    print(Fore.BLUE + Style.BRIGHT + "="*60)

    # Start STT in background
    stt_thread = threading.Thread(target=run_stt, daemon=True)
    stt_thread.start()

    print(Fore.GREEN + "\nCommands:")
    print(Fore.WHITE + "- Just type your query and press Enter.")
    print(Fore.WHITE + "- Type 'exit' or 'quit' to stop.")
    print(Fore.WHITE + "- Speak 'Buddy [your query]' to use voice.")
    print(Fore.CYAN + "-"*60)

    try:
        while True:
            query = input(Fore.YELLOW + "You: " + Style.RESET_ALL).strip()
            
            if not query:
                continue
                
            if query.lower() in ["exit", "quit"]:
                print(Fore.RED + "Goodbye!")
                break
                
            # Add task to main queue
            buddy.add_task("main", query)
            
            # Small sleep to allow logs to print neatly
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print(Fore.RED + "\nShutting down...")
    except Exception as e:
        print(Fore.RED + f"An error occurred: {e}")

if __name__ == "__main__":
    main()
