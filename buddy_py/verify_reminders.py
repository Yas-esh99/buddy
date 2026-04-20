from buddy import buddy
from reminders import ReminderManager
import time
from datetime import datetime, timedelta

def verify_reminders():
    print("🚀 Verifying Reminder System...")
    
    manager = buddy.reminder_manager
    
    # 1. Test Natural Language Parsing
    print("\n--- Testing Parsing ---")
    try:
        task_id = manager.add_task("Drink Water", "in 5 seconds")
        print(f"✅ Task created successfully with ID: {task_id}")
    except Exception as e:
        print(f"❌ Parsing failed: {e}")
        return

    # 2. List Tasks
    print("\n--- Listing Tasks ---")
    tasks = manager.list_tasks()
    for t in tasks:
        print(f"- {t.text} at {t.trigger_time} (Status: {t.status.value})")

    # 3. Wait for Trigger
    print("\n--- Waiting for trigger (should take ~10-15s due to sleep loop) ---")
    # We wait long enough for the 10s sleep in scheduler to hit
    timeout = 30
    start = time.time()
    triggered = False
    
    while time.time() - start < timeout:
        # Check if a task was added to the main queue
        if len(buddy.queues["main"].tasks) > 0:
            print("✅ TRIGGER DETECTED! Task added to Buddy's main queue.")
            triggered = True
            break
        time.sleep(1)
    
    if not triggered:
        print("❌ Trigger failed or timed out.")
    else:
        # Check the task content
        task = buddy.queues["main"].tasks[0]
        print(f"✅ Task Content: {task.inp_state['query']}")

if __name__ == "__main__":
    verify_reminders()
