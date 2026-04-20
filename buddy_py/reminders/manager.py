import dateparser
from datetime import datetime
from typing import List, Optional
from reminders.models import ReminderTask, ReminderStatus
from reminders.storage import ReminderStorage
from reminders.scheduler import ReminderScheduler

class ReminderManager:
    def __init__(self, buddy_instance):
        self.buddy = buddy_instance
        self.storage = ReminderStorage()
        self.tasks: List[ReminderTask] = self.storage.load_all()
        
        # Initialize and start scheduler
        self.scheduler = ReminderScheduler(
            get_tasks_fn=self.get_active_tasks,
            on_trigger_fn=self._handle_trigger
        )
        self.scheduler.start()

    def add_task(self, text: str, time_string: str, repeat: str = "none") -> str:
        """Add a task using natural language time parsing."""
        trigger_time = dateparser.parse(
            time_string, 
            settings={'PREFER_DATES_FROM': 'future'}
        )
        
        if not trigger_time:
            raise ValueError(f"Could not parse time string: {time_string}")

        # Basic duplicate check: Don't add if an identical pending task exists within 1 minute
        for t in self.tasks:
            if t.status == ReminderStatus.PENDING and t.text == text:
                diff = abs((t.trigger_time - trigger_time).total_seconds())
                if diff < 60:
                    print(f"⚠️ Duplicate reminder detected for '{text}', skipping.")
                    return t.id

        new_task = ReminderTask(text=text, trigger_time=trigger_time, repeat=repeat)
        self.tasks.append(new_task)
        self.storage.save_all(self.tasks)
        
        print(f"📅 Reminder set: '{text}' at {trigger_time.strftime('%Y-%m-%d %H:%M')}")
        return new_task.id

    def remove_task(self, task_id: str):
        self.tasks = [t for t in self.tasks if t.id != task_id]
        self.storage.save_all(self.tasks)

    def list_tasks(self) -> List[ReminderTask]:
        return self.tasks

    def get_active_tasks(self) -> List[ReminderTask]:
        return [t for t in self.tasks if t.status == ReminderStatus.PENDING]

    def _handle_trigger(self, task: ReminderTask):
        """Called by scheduler thread when a reminder is due."""
        print(f"🔔 TRIGGERING REMINDER: {task.text}")
        
        # Update status
        task.status = ReminderStatus.TRIGGERED
        self.storage.save_all(self.tasks)
        
        # Integrate with Buddy's existing TaskQueue
        # We inject a specific query that Buddy can process and speak
        reminder_query = f"BUDDY_INTERNAL_REMINDER: {task.text}"
        
        # Adding to 'main' queue as per requirement
        self.buddy.add_task("main", reminder_query)
        
        # Mark as completed (or handle recurrence here)
        if task.repeat == "none":
            task.status = ReminderStatus.COMPLETED
            self.storage.save_all(self.tasks)
        else:
            self._handle_recurrence(task)

    def _handle_recurrence(self, task: ReminderTask):
        # Placeholder for future recurrence logic
        pass
