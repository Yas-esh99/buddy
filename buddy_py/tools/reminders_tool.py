from langchain_core.tools import tool
from typing import Optional

# This tool will be initialized with a ReminderManager instance
class ReminderTools:
    def __init__(self, manager):
        self.manager = manager

    def get_tools(self):
        @tool
        def set_reminder(text: str, time_string: str, repeat: str = "none"):
            """Sets a reminder for the user. 
            Example: text='drink water', time_string='at 5 PM', repeat='none'
            """
            try:
                task_id = self.manager.add_task(text, time_string, repeat)
                return f"Successfully set reminder for '{text}' at '{time_string}'. ID: {task_id}"
            except Exception as e:
                return f"Failed to set reminder: {str(e)}"

        @tool
        def list_reminders():
            """Lists all upcoming and active reminders."""
            tasks = self.manager.list_tasks()
            if not tasks:
                return "You have no reminders set."
            
            res = "Your Reminders:\n"
            for t in tasks:
                res += f"- [{t.status.value}] '{t.text}' at {t.trigger_time.strftime('%Y-%m-%d %H:%M')} (ID: {t.id})\n"
            return res

        @tool
        def cancel_reminder(task_id: str):
            """Cancels a specific reminder using its ID."""
            self.manager.remove_task(task_id)
            return f"Reminder {task_id} has been cancelled."

        return [set_reminder, list_reminders, cancel_reminder]
