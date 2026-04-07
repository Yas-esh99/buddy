from dotenv import load_dotenv
from langchain_groq import ChatGroq
import os

load_dotenv()

llm = ChatGroq(
  model = "llama-3.1-8b-instant",
  api_key = os.environ["GROQ_API_KEY"],
  temperature = 0.5
)

def llm_node(state):
  response = llm.invoke(input=state["query"])
  ans = response.content
  return {"ans" : ans}