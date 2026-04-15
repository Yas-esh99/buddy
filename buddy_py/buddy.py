import uuid
import threading
from collections import deque
from enum import Enum

from colorama import init, Fore, Style
from graph import compiled

# Initialize colorama
init(autoreset=True)


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
        self.status = Status.CREATED
        self.output = deque()

        self.config = {
            "configurable": {
                "thread_id": self.id
            }
        }

    def run(self):

        self.status = Status.RUNNING

        print("\n" + Fore.CYAN + "=" * 60)
        print(Fore.GREEN + Style.BRIGHT + "🚀 TASK STARTED")
        print(Fore.YELLOW + f"ID      : {self.id}")
        print(Fore.YELLOW + f"QUERY   : {self.inp_state['query']}")
        print(Fore.CYAN + "=" * 60)

        try:
            for chunk in compiled.stream(
                input=self.inp_state,
                config=self.config
            ):

                self.output.append(chunk)

                for node_name, node_output in chunk.items():

                    print(Fore.MAGENTA + "\n📦 STREAM CHUNK")
                    print(Fore.BLUE + f"├── NODE : {node_name}")

                    for key, value in node_output.items():
                        print(Fore.WHITE + f"├── {key.upper():<6}: {value}")

            self.status = Status.COMPLETE

            print(Fore.CYAN + "\n" + "=" * 60)
            print(Fore.GREEN + Style.BRIGHT + f"✅ TASK {self.id} COMPLETED")
            print(Fore.CYAN + "=" * 60)

        except Exception as e:

            self.status = Status.STOPPED

            print(Fore.RED + "\n❌ TASK ERROR")
            print(Fore.RED + f"Task ID : {self.id}")
            print(Fore.RED + f"Error   : {e}")

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

    def create_queue(self, name):

        self.queues[name] = TaskQueue(name)

        self.queues[name].start()

        print(
            Fore.GREEN +
            Style.BRIGHT +
            f"\n🧠 Queue [{name}] Created Successfully"
        )

    def add_task(self, queue_name, query):

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