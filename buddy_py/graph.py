from nodes.llm import llm_node
from state import State
from langgraph.graph import StateGraph,END
from pprint import pprint
import threading

graph = StateGraph(State)

graph.add_node("llm",llm_node)

graph.set_entry_point("llm")
graph.add_edge("llm",END)



buddy = graph.compile()




      