from nodes.llm import llm_node
from nodes.memory_node import memory_node
from state import State
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
import threading
from langgraph.checkpoint.memory import MemorySaver

# Initialize memory saver for short-term history
checkpointer = MemorySaver()

# To avoid circular imports, we bind tools lazily
def get_all_tools():
    from tools.search import web_search
    from tools.files import read_file, list_files
    from tools.reminders_tool import ReminderTools
    from buddy import buddy
    reminder_tools_instance = ReminderTools(buddy.reminder_manager)
    return [web_search, read_file, list_files] + reminder_tools_instance.get_tools()

class LazyToolNode:
    def __init__(self):
        self._node = None
    def __call__(self, state, config=None):
        if self._node is None:
            self._node = ToolNode(get_all_tools())
        return self._node.invoke(state, config)

tool_node = LazyToolNode()

def should_continue(state):
    messages = state.get("messages", [])
    if messages and hasattr(messages[-1], "tool_calls") and messages[-1].tool_calls:
        return "tools"
    return "memory_extract"

graph = StateGraph(State)

graph.add_node("llm", llm_node)
graph.add_node("tools", tool_node)
graph.add_node("memory_extract", memory_node)

graph.set_entry_point("llm")

graph.add_conditional_edges(
    "llm",
    should_continue,
    {
        "tools": "tools",
        "memory_extract": "memory_extract"
    }
)

graph.add_edge("tools", "llm")
graph.add_edge("memory_extract", END)

compiled = graph.compile(checkpointer=checkpointer)
png_bytes = compiled.get_graph().draw_mermaid_png()

with open("langgraph.png", "wb") as f:
    f.write(png_bytes)