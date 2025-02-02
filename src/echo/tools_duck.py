

from langchain.tools import StructuredTool
from typing import List, Optional, Callable
from pydantic import BaseModel

from langchain_community.tools import DuckDuckGoSearchRun
# DuckDuckGoSearchAPIWrapper, DuckDuckGoSearchResults

search = DuckDuckGoSearchRun()

#response = search.invoke('Tom Holland middle name?')
#print(response)


# define input models
class SearchInput(BaseModel):
    query: str


# Function implementations
def search_query(query: str) -> str:
    """Search for a query."""
    response = search.invoke(query)
    return response

# define tool
def get_tools() -> List[StructuredTool]:
    tools = [
        StructuredTool.from_function(
            name="search_query",
            func=search_query,
            description="Search for a query on DuckDuckGo.",
            args_schema=SearchInput
        )
    ]
    return tools