import uuid
import time
import threading
from collections import deque
from enum import Enum

from graph import compiled


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

        self.start_time = None

        self.config = {
            "configurable": {
                "thread_id": self.id
            }
        }

    def run(self):
        self.status = Status.RUNNING
        self.start_time = time.time()

        print(f"\n[TASK {self.id}] STARTED")
        print(f"[TASK {self.id}] INPUT: {self.inp_state}")

        try:
            for chunk in compiled.stream(
                input=self.inp_state,
                config=self.config
            ):

                if self.status != Status.RUNNING:
                    print(f"[TASK {self.id}] INTERRUPTED")
                    return

                self.output.append(chunk)

                print(f"[TASK {self.id}] CHUNK -> {chunk}")

            self.status = Status.COMPLETE

            print(f"[TASK {self.id}] COMPLETED")

        except Exception as e:
            self.status = Status.STOPPED
            print(f"[TASK {self.id}] ERROR:", e)

    def stop(self):
        self.status = Status.STOPPED


# =====================================
# TASK QUEUE
# =====================================
class TaskQueue:
    def __init__(self, name):
        self.name = name

        self.tasks = deque()

        self.thread = None

        self.running = False

        self.current_task = None

        self.lock = threading.Lock()

        self.condition = threading.Condition(self.lock)

    def add_task(self, task):
        with self.condition:
            self.tasks.append(task)

            print(f"[QUEUE {self.name}] Added Task {task.id}")

            self.condition.notify()

    def _worker(self):

        self.running = True

        print(f"[QUEUE {self.name}] Worker Started")

        while self.running:

            with self.condition:

                while not self.tasks and self.running:
                    self.condition.wait()

                if not self.running:
                    break

                self.current_task = self.tasks.popleft()

            print(f"[QUEUE {self.name}] Running Task {self.current_task.id}")

            self.current_task.run()

            self.current_task = None

    def start(self):

        if self.thread is None or not self.thread.is_alive():

            self.thread = threading.Thread(
                target=self._worker,
                daemon=True
            )

            self.thread.start()

    def stop(self):

        self.running = False

        with self.condition:
            self.condition.notify_all()

    def stop_current_task(self):

        if self.current_task:
            self.current_task.stop()


# =====================================
# BUDDY CONTROLLER
# =====================================
class Buddy:
    def __init__(self):

        self.queues = {}

    def create_queue(self, name):

        if name not in self.queues:

            self.queues[name] = TaskQueue(name)

            self.queues[name].start()

            print(f"[BUDDY] Queue '{name}' created")

    def add_task(self, queue_name, query):

        task = Task({
            "query": query,
            "ans": ""
        })

        self.queues[queue_name].add_task(task)

        return task.id

    def stop_current_task(self, queue_name):

        self.queues[queue_name].stop_current_task()

buddy = Buddy()
# =====================================
# DEMO
# =====================================
if __name__ == "__main__":

    buddy = Buddy()

    buddy.create_queue("main")

    buddy.create_queue("background")

    # MAIN QUEUE TASKS
    buddy.add_task("main", "Hello buddy")
    buddy.add_task("main", "What is AI?")

    # BACKGROUND QUEUE TASKS
    buddy.add_task("background", "Tell me joke")
    buddy.add_task("background", "Weather today")

    while True:
        time.sleep(1)