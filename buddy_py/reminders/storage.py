import json
import os
import threading
from typing import List, Dict
from reminders.models import ReminderTask

class ReminderStorage:
    def __init__(self, file_path: str = "buddy_reminders.json"):
        self.file_path = file_path
        self.lock = threading.Lock()
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w") as f:
                json.dump([], f)

    def load_all(self) -> List[ReminderTask]:
        with self.lock:
            try:
                with open(self.file_path, "r") as f:
                    data_list = json.load(f)
                    return [ReminderTask.from_dict(d) for d in data_list]
            except (json.JSONDecodeError, FileNotFoundError):
                return []

    def save_all(self, tasks: List[ReminderTask]):
        with self.lock:
            with open(self.file_path, "w") as f:
                json.dump([task.to_dict() for task in tasks], f, indent=4)
