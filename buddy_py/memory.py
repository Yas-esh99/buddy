import json
import os

class MemoryManager:
    def __init__(self, storage_file="buddy_memory.json"):
        self.storage_file = storage_file
        self.memory = self._load_memory()

    def _load_memory(self):
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, "r") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_memory(self):
        with open(self.storage_file, "w") as f:
            json.dump(self.memory, f, indent=2)

    def get_info(self, key):
        return self.memory.get(key)

    def save_info(self, key, value):
        self.memory[key] = value
        self._save_memory()

    def get_all_context(self):
        if not self.memory:
            return ""
        context = "Relevant information about the user:\n"
        for key, value in self.memory.items():
            context += f"- {key}: {value}\n"
        return context

memory_manager = MemoryManager()
