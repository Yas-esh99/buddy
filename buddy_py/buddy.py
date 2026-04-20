import uuid
import threading
import os
from collections import deque
from enum import Enum

from colorama import init, Fore, Style
from graph import compiled
from tts import PiperTTSManager
from reminders import ReminderManager

# Initialize colorama
init(autoreset=True)

# Initialize TTS
# Path updated to look inside 'models' folder
MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "en_US-danny-low.onnx")

print(Fore.CYAN + f"🔍 Checking for TTS model at: {MODEL_PATH}")

if os.path.exists(MODEL_PATH):
    try:
        tts = PiperTTSManager(MODEL_PATH)
        print(Fore.GREEN + "🔊 TTS Initialized successfully with 'en_US-danny-low'")
    except Exception as e:
        print(Fore.RED + f"⚠️ TTS Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        tts = None
else:
    print(Fore.RED + f"❌ TTS Model not found at {MODEL_PATH}")
    print(Fore.YELLOW + "Please ensure the .onnx and .onnx.json files are in buddy_py/models/")
    tts = None

# =====================================
# STATUS ENUM
# =====================================
class Status(Enum):
    CREATED = "created"
    RUNNING = "running"
    STOPPED = "stopped"
    COMPLETE = "complete"


# =====================================
# TASK
# =====================================
class Task:
    def __init__(self, inp_state):
        self.id = str(uuid.uuid4())[:8]
        self.inp_state = inp_state
        if "messages" not in self.inp_state:
            self.inp_state["messages"] = []
            
        self.status = Status.CREATED
        self.output = deque()

        self.config = {
            "configurable": {
                "thread_id": "user_session" # Simplified for now, could use self.id for multiple sessions
            }
        }

    def run(self):

        self.status = Status.RUNNING

        print("\n" + Fore.CYAN + "=" * 60)
        print(Fore.GREEN + Style.BRIGHT + "🚀 TASK STARTED")
        print(Fore.YELLOW + f"ID      : {self.id}")
        print(Fore.YELLOW + f"QUERY   : {self.inp_state['query']}")
        print(Fore.CYAN + "=" * 60)

        final_ans = ""

        try:
            for chunk in compiled.stream(
                input=self.inp_state,
                config=self.config
            ):

                self.output.append(chunk)

                for node_name, node_output in chunk.items():

                    print(Fore.MAGENTA + "\n📦 STREAM CHUNK")
                    print(Fore.BLUE + f"├── NODE : {node_name}")

                    if node_output is None:
                        print(Fore.WHITE + "├── [No Output]")
                        continue

                    for key, value in node_output.items():
                        if key == "ans" and value:
                            final_ans = value
                        
                        # Handle messages and check for tool calls
                        if key == "messages":
                            print(Fore.WHITE + f"├── {key.upper():<6}: [Message history updated]")
                            last_msg = value[-1] if value else None
                            if last_msg and hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                                for tc in last_msg.tool_calls:
                                    print(Fore.YELLOW + f"├── TOOL : {tc['name']}({tc['args']})")
                        else:
                            if value: # Only print if there is a value
                                print(Fore.WHITE + f"├── {key.upper():<6}: {value}")

            self.status = Status.COMPLETE

            if final_ans and tts:
                print(Fore.YELLOW + f"\n🗣️ Speaking: {final_ans}")
                # Use a thread to speak so the task can finish immediately 
                # and the next task in the queue can start running
                threading.Thread(target=tts.speak, args=(final_ans,), daemon=True).start()

            print(Fore.CYAN + "\n" + "=" * 60)
            print(Fore.GREEN + Style.BRIGHT + f"✅ TASK {self.id} COMPLETED")
            print(Fore.CYAN + "=" * 60)

        except Exception as e:

            self.status = Status.STOPPED

            print(Fore.RED + "\n❌ TASK ERROR")
            print(Fore.RED + f"Task ID : {self.id}")
            print(Fore.RED + f"Error   : {e}")
            import traceback
            traceback.print_exc()

    def stop(self):
        self.status = Status.STOPPED


# =====================================
# TASK QUEUE
# =====================================
class TaskQueue:

    def __init__(self, name):

        self.name = name
        self.tasks = deque()

        self.condition = threading.Condition()

        self.running = False

        self.thread = None

    def add_task(self, task):

        with self.condition:

            self.tasks.append(task)

            print(
                Fore.YELLOW +
                f"\n📥 Added Task [{task.id}] to Queue [{self.name}]"
            )

            self.condition.notify()

    def _worker(self):

        self.running = True

        print(
            Fore.GREEN +
            Style.BRIGHT +
            f"⚙️ Worker Started for Queue [{self.name}]"
        )

        while self.running:

            with self.condition:

                while not self.tasks:
                    self.condition.wait()

                task = self.tasks.popleft()

            print(
                Fore.BLUE +
                f"\n⚡ Queue [{self.name}] Running Task [{task.id}]"
            )

            task.run()

    def start(self):

        self.thread = threading.Thread(
            target=self._worker,
            daemon=True
        )

        self.thread.start()


# =====================================
# BUDDY
# =====================================
class Buddy:

    def __init__(self):

        self.queues = {}
        # Initialize Reminder Manager (starts scheduler thread)
        self.reminder_manager = ReminderManager(self)

    def create_queue(self, name):

        self.queues[name] = TaskQueue(name)

        self.queues[name].start()

        print(
            Fore.GREEN +
            Style.BRIGHT +
            f"\n🧠 Queue [{name}] Created Successfully"
        )

    def add_task(self, queue_name, query):
        # Check for stop command
        if "stop speaking" in query.lower() or "shut up" in query.lower():
            if tts:
                print(Fore.RED + "🛑 Stopping TTS playback...")
                tts.stop()
            return

        self.queues[queue_name].add_task(
            Task({
                "query": query,
                "ans": ""
            })
        )


# =====================================
# GLOBAL INSTANCE
# =====================================
buddy = Buddy()

buddy.create_queue("main")
buddy.create_queue("background")