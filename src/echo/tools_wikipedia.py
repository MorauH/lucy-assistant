from langchain.utilities import WikipediaAPIWrapper

from langchain.tools import StructuredTool
from typing import List, Optional, Callable
from pydantic import BaseModel


wikipedia = WikipediaAPIWrapper()

# response = wikipedia.run('Tom Holland')
# print(response)


# define input models
class SearchInput(BaseModel):
    query: str

# Function implementations
def search_query(query: str) -> str:
    """Search for a query."""
    response = wikipedia.run(query)
    return response

# tool creation
def get_tools() -> List[StructuredTool]:
    tools = [
        StructuredTool.from_function(
            name="search_query",
            func=search_query,
            description="Search for a query on Wikipedia.",
            args_schema=SearchInput
        )
    ]
    return tools
