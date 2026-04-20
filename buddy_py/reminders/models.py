import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any

class ReminderStatus(Enum):
    PENDING = "pending"
    TRIGGERED = "triggered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    SNOOZED = "snoozed"

class ReminderTask:
    def __init__(
        self,
        text: str,
        trigger_time: datetime,
        repeat: str = "none",
        priority: int = 1,
        task_id: str = None,
        status: ReminderStatus = ReminderStatus.PENDING
    ):
        self.id = task_id or str(uuid.uuid4())
        self.text = text
        self.trigger_time = trigger_time
        self.repeat = repeat  # none, daily, weekly
        self.priority = priority
        self.status = status

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "trigger_time": self.trigger_time.isoformat(),
            "repeat": self.repeat,
            "priority": self.priority,
            "status": self.status.value
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(
            text=data["text"],
            trigger_time=datetime.fromisoformat(data["trigger_time"]),
            repeat=data.get("repeat", "none"),
            priority=data.get("priority", 1),
            task_id=data["id"],
            status=ReminderStatus(data["status"])
        )
