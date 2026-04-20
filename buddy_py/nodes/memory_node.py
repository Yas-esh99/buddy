from langchain_groq import ChatGroq
from memory import memory_manager
from langchain_core.messages import HumanMessage, AIMessage
import os
import json

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.environ["GROQ_API_KEY"],
    temperature=0
)

def memory_node(state):
    """Extracts important facts from the conversation and saves them."""
    messages = state.get("messages", [])
    if len(messages) < 2:
        return {}

    last_human = messages[-2].content
    last_ai = messages[-1].content

    extraction_prompt = f"""
    Analyze the following exchange and extract any persistent facts about the user (e.g., name, preferences, family, location, interests).
    If no new persistent information is found, return an empty JSON object {{}}.
    If information is found, return it as a JSON object with descriptive keys.

    User: {last_human}
    AI: {last_ai}

    JSON Output:
    """
    
    response = llm.invoke([HumanMessage(content=extraction_prompt)])
    try:
        # Basic cleanup in case of markdown blocks
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("{") and content.endswith("}"):
            pass
        else:
            # Try to find the first { and last }
            start = content.find("{")
            end = content.rfind("}")
            if start != -1 and end != -1:
                content = content[start:end+1]
        
        new_info = json.loads(content)
        for key, value in new_info.items():
            memory_manager.save_info(key, value)
            print(f"🧠 Memory Updated: {key} = {value}")
    except Exception as e:
        # It's okay if it fails, memory extraction is best-effort
        pass

    return {}
