import os
from langchain_core.tools import tool

@tool
def read_file(file_path: str):
    """Reads the content of a local file. Useful for processing documents or data files."""
    print(f"📄 Reading file: {file_path}")
    if not os.path.exists(file_path):
        return f"Error: File {file_path} does not exist."
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            # Truncate if too large
            if len(content) > 5000:
                return content[:5000] + "\n... (truncated)"
            return content
    except Exception as e:
        return f"Error reading file: {e}"

@tool
def list_files(directory: str = "."):
    """Lists files in a directory to help find documents."""
    print(f"📂 Listing files in: {directory}")
    try:
        files = os.listdir(directory)
        return files
    except Exception as e:
        return f"Error listing files: {e}"
