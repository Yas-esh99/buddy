from typing import TypedDict, Annotated, List
from langchain_core.messages import BaseMessage
import operator

class State(TypedDict):
  query: str
  ans: str
  messages: Annotated[List[BaseMessage], operator.add]
