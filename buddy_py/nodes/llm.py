from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from memory import memory_manager
from tools.search import web_search
from tools.files import read_file, list_files
from tools.reminders_tool import ReminderTools
from datetime import datetime
import os

load_dotenv()

# Llama-3.3-70b-versatile seems to be the one currently active
llm = ChatGroq(
  model = "llama-3.3-70b-versatile",
  api_key = os.environ["GROQ_API_KEY"],
  temperature = 0.5,
  max_tokens = 500
)

# Function to get tools lazily to avoid circular imports
def get_llm_with_tools():
    from buddy import buddy
    reminder_tools_instance = ReminderTools(buddy.reminder_manager)
    tools = [web_search, read_file, list_files] + reminder_tools_instance.get_tools()
    return llm.bind_tools(tools)

def llm_node(state):
  user_context = memory_manager.get_all_context()
  now = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
  
  instructions = f"""You are Buddy, the ultimate AI assistant. 
You are helpful, witty, and proactive.

CURRENT TIME: {now}
USER CONTEXT:
{user_context}

INSTRUCTIONS:
1. You have ACCESS TO TOOLS. Use them whenever necessary.
2. Use 'set_reminder' to schedule tasks for the user. ALWAYS use this tool when asked for a reminder.
3. Use 'web_search' for real-time information (news, specific facts). You already know the current date and time.
4. Use 'read_file' or 'list_files' for local documents.
5. If the user tells you something important about themselves, acknowledge it; you will remember it for next time.
6. Keep your responses concise, friendly, and helpful.
7. DO NOT tell the user you are a text-based AI. You are a fully capable voice assistant.
"""

  # Prepare messages
  messages = [SystemMessage(content=instructions)]

  # Existing history from state
  history = state.get("messages", [])
  messages.extend(history)

  query = state.get("query", "")
  human_msg_to_add = []

  # Logic to avoid duplicating the HumanMessage in the history
  # We only add the query if it's not already the most recent HumanMessage in history
  last_human_query = next((m.content for m in reversed(history) if isinstance(m, HumanMessage)), None)

  if query and query != last_human_query:
      # Special handling for internal reminders
      if query.startswith("BUDDY_INTERNAL_REMINDER:"):
          reminder_text = query.replace("BUDDY_INTERNAL_REMINDER:", "").strip()
          prompt = f"INTERNAL TRIGGER: This is a scheduled reminder for the user: '{reminder_text}'. Please announce it to the user in a friendly way."
          current_human_msg = HumanMessage(content=prompt)
          # We don't save internal triggers to user history to keep it clean
      else:
          current_human_msg = HumanMessage(content=query)
          human_msg_to_add = [current_human_msg]

      messages.append(current_human_msg)

  try:
      llm_with_tools = get_llm_with_tools()
      response = llm_with_tools.invoke(input=messages)

      # Prepare updates to state
      # Return human_msg_to_add (empty if already in history) + the new AI response
      updates = {"messages": human_msg_to_add + [response]}

      if not (hasattr(response, "tool_calls") and response.tool_calls):
          updates["ans"] = response.content

      return updates
  except Exception as e:
      print(f"⚠️ Tool Call Error, falling back: {e}")
      response = llm.invoke(input=messages)
      return {"messages": human_msg_to_add + [response], "ans": response.content}