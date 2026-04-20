import threading
import time
from datetime import datetime
from typing import List, Callable
from reminders.models import ReminderTask, ReminderStatus

class ReminderScheduler:
    def __init__(self, get_tasks_fn: Callable[[], List[ReminderTask]], on_trigger_fn: Callable[[ReminderTask], None]):
        self.get_tasks = get_tasks_fn
        self.on_trigger = on_trigger_fn
        self.running = False
        self.thread = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()

    def _run_loop(self):
        while self.running:
            now = datetime.now()
            tasks = self.get_tasks()
            
            for task in tasks:
                if task.status == ReminderStatus.PENDING and now >= task.trigger_time:
                    self.on_trigger(task)
            
            # Check every 10 seconds to save CPU, but accurate enough for general reminders
            time.sleep(10)
