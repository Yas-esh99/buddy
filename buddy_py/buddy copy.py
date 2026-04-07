from langgraph.graph import START, END, StateGraph, add_messages
from typing import Annotated, TypedDict, List
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    BaseMessage,
)
from langchain_core.runnables import RunnableConfig
import os
from dotenv import load_dotenv

load_dotenv()

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.environ["GROQ_API_KEY"],
    temperature=0,
)

# ---------------- STATE ----------------
# Renamed 'message' to 'messages' (LangGraph standard)
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    memory: str


# ---------------- THINKER ----------------
def thinker(state: AgentState):
    memory = state.get("memory", "").strip()

    system_prompt = f"""
    You are a persistent AI assistant.

    IMPORTANT RULES:
    - The memory below is TRUE and was saved from previous conversations.
    - You MUST use it when answering.
    - You are NOT allowed to say you lack memory or context.
    - Never say "I don't remember" or "each conversation is new".

    User memory:
    {memory if memory else "No stored facts yet."}
    """

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        *state["messages"]
    ])

    # Return as a list for the add_messages reducer
    return {"messages": [response]}

# ---------------- MEMORY UPDATER ----------------
def memory_updater(state: AgentState):
    memory = state.get("memory", "")
    # The last message (-1) is the AI's response, the one before it (-2) is the Human's
    last_user_msg = state["messages"][-2].content  

    # Use explicit System and Human messages instead of a raw string for better LLM compliance
    system_prompt = """You extract stable user facts.
    Rules:
    - Only store facts about the user (name, preferences)
    - If no new facts, return existing memory unchanged
    - Do NOT explain anything, just output the updated memory text.
    """

    user_prompt = f"""
    Existing memory:
    {memory if memory else "None"}

    User message:
    {last_user_msg}

    Updated memory:
    """

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ])
    
    updated_memory = response.content.strip()

    return {"memory": updated_memory}


# ---------------- GRAPH ----------------
graph = StateGraph(AgentState)
graph.add_node("thinker", thinker)
graph.add_node("memory_updater", memory_updater)

graph.add_edge(START, "thinker")
graph.add_edge("thinker", "memory_updater")
graph.add_edge("memory_updater", END)

# MemorySaver ONLY saves state while this specific python execution is running
checkpointer = MemorySaver()
buddy = graph.compile(checkpointer=checkpointer)

config: RunnableConfig = {
    "configurable": {"thread_id": "user1"}
}

# ---------------- TEST EXECUTION ----------------
# We must run it multiple times in the same script to see MemorySaver work.
"""
print("--- TURN 1 ---")
result1 = buddy.invoke(
    {"messages": [HumanMessage(content="Hi, my name is Yashesh and I love LangGraph!")]},
    config=config
)
print("AI:", result1["messages"][-1].content)
print("Saved Memory:", result1.get("memory"))

print("\n--- TURN 2 ---")
result2 = buddy.invoke(
    {"messages": [HumanMessage(content="What is my name and what do I like?")]},
    config=config
)
print("AI:", result2["messages"][-1].content)
print("Saved Memory:", result2.get("memory"))
"""