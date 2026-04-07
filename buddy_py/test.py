from multiprocessing import Process, Queue as MPQueue
from queue import Queue as ThreadQueue
import threading
import time
import uuid


# 🔷 TASK CLASS
class Task:
    def __init__(self, input_text):
        self.id = str(uuid.uuid4())[:8]
        self.input = input_text
        self.status = "waiting"

        self.process = None
        self.control_queue = MPQueue()
        self.start_time = None


# 🔷 QUEUE CLASS
class TaskQueue:
    def __init__(self, name, controller):
        self.id = str(uuid.uuid4())[:6]
        self.name = name
        self.controller = controller

        self.tasks = ThreadQueue()   # FIFO
        self.worker = threading.Thread(target=self._worker, daemon=True)
        self.worker.start()

    # 🔥 Worker loop
    def _worker(self):
        while True:
            task = self.tasks.get()

            if task is None:
                break

            task.status = "running"
            task.start_time = time.time()

            print(f"🚀 [{self.name}] Running {task.id}")

            p = Process(
                target=self.controller._run_task,
                args=(task,)
            )
            task.process = p
            p.start()

            p.join()

            # Update status
            if task.status == "stopping":
                task.status = "stopped"
            else:
                task.status = "complete"

            print(f"✅ [{self.name}] Done {task.id}")

    # 🔷 Add task
    def add_task(self, task):
        self.tasks.put(task)

    # 🔷 Remove task (only waiting)
    def remove_task(self, task_id):
        new_q = ThreadQueue()

        while not self.tasks.empty():
            t = self.tasks.get()
            if t.id != task_id:
                new_q.put(t)
            else:
                t.status = "stopped"

        self.tasks = new_q

    # 🔷 Get all waiting tasks
    def get_tasks(self):
        return list(self.tasks.queue)
    
class BuddyController:
    def __init__(self, max_queues=5):
        self.queues = {}
        self.tasks = {}

        self.max_queues = max_queues

        # 🔥 Default queue
        self.create_queue("main")

    # 🔷 Create queue
    def create_queue(self, name):
        if len(self.queues) >= self.max_queues:
            raise Exception("Max queues reached")

        q = TaskQueue(name, self)
        self.queues[q.id] = q
        return q.id

    # 🔷 Get queue by name
    def get_queue(self, name):
        for q in self.queues.values():
            if q.name == name:
                return q
        return None

    # 🔷 Add task
    def add_task(self, input_text, queue_name="main"):
        task = Task(input_text)

        q = self.get_queue(queue_name)
        if not q:
            raise Exception("Queue not found")

        self.tasks[task.id] = task
        q.add_task(task)

        print(f"🧾 Task {task.id} added to {queue_name}")
        return task.id

    # 🔷 Run task (process side)
    def _run_task(self, task):
        try:
            for i in range(10):
                time.sleep(0.5)

                if not task.control_queue.empty():
                    if task.control_queue.get() == "STOP":
                        task.status = "stopping"
                        return

                print(f"[{task.id}] step {i}")

        finally:
            pass

    # 🔷 Stop task
    def stop_task(self, task_id):
        if task_id in self.tasks:
            t = self.tasks[task_id]
            if t.process and t.process.is_alive():
                t.status = "stopping"
                t.control_queue.put("STOP")

    # 🔷 Force stop
    def force_stop(self, task_id):
        if task_id in self.tasks:
            t = self.tasks[task_id]
            if t.process and t.process.is_alive():
                t.process.terminate()
                t.process.join()
                t.status = "stopped"

    # 🔷 Delete task (only waiting)
    def delete_task(self, task_id):
        for q in self.queues.values():
            q.remove_task(task_id)

    # 🔷 Status
    def status(self):
        return {
            tid: {
                "status": t.status,
                "queue": self._find_queue_of_task(tid)
            }
            for tid, t in self.tasks.items()
        }

    def _find_queue_of_task(self, task_id):
        for q in self.queues.values():
            if any(t.id == task_id for t in q.get_tasks()):
                return q.name
        return "running/finished"
    
controller = BuddyController()

# add tasks
t1 = controller.add_task("task 1")
t2 = controller.add_task("task 2")

# new queue
controller.create_queue("background")
t3 = controller.add_task("bg task", queue_name="background")

# stop task
controller.stop_task(t1)

# delete waiting task
controller.delete_task(t2)

print(controller.status())