from ddgs import DDGS
from langchain_core.tools import tool
import json

@tool
def web_search(query: str):
    """Searches the web for information using DuckDuckGo."""
    print(f"🔍 Searching the web for: {query}...")
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=5)]
            if not results:
                return f"No results found for '{query}'."
            return json.dumps(results)
    except Exception as e:
        return f"Error during search: {str(e)}"
