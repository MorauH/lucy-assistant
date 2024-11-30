from typing import List, Optional, Callable
from pydantic import BaseModel
from langchain.tools import StructuredTool

# Define input models
class ListFilesInput(BaseModel):
    pass

class CreateFileInput(BaseModel):
    file_name: str
    content: Optional[str] = ''

class ReadFileInput(BaseModel):
    file_name: str


class ToolCreationInput(BaseModel):
    name: str
    description: str
    func: str
    # args_schema: str

class ExecuteStringInput(BaseModel):
    code: str




# Function implementations
def list_files_and_directories() -> List[str]:
    """List all files and directories in the current directory."""
    import os
    return os.listdir(os.getcwd())

def create_python_file(file_name: str, content: str = '') -> str:
    """Create a Python file with specified content."""
    with open(file_name, 'w') as file:
        file.write(content)
    return f'{file_name} created successfully.'

def read_file(file_name: str) -> str:
    """Read and return the content of a file."""
    with open(file_name, 'r') as file:
        return file.read()


# Structured tool creation for each function
def get_tools(execute_string_callable: Callable, create_tool_callable: Callable) -> List[StructuredTool]:
    tools = [
        StructuredTool.from_function(
            func=list_files_and_directories,
            name="List_Files_And_Directories",
            description="List all files and directories in the current directory.",
            args_schema=ListFilesInput
        ),
        StructuredTool.from_function(
            func=create_python_file,
            name="Create_Python_File",
            description="Create a Python file with specified content.",
            args_schema=CreateFileInput
        ),
        StructuredTool.from_function(
            func=read_file,
            name="Read_File",
            description="Read and return the content of a file.",
            args_schema=ReadFileInput
        ),
        StructuredTool.from_function(
            func=execute_string_callable,
            name="Execute_Python_Code",
            description="""Execute Python code from a string.
            The code should be complete and fully working.
            It has access to the current context and will modify it.
            """,
            args_schema=ExecuteStringInput
        ),
        StructuredTool.from_function(
            func=create_tool_callable,
            name="Create_Tool",
            description="""
            Create a new tool that are then available for assistant.
            Name should match the functions name.
            func is python code as a function that defines the tool.
            The code may use references to the current context.
            func may be empty if a function with name is already defined.
            def func(<args>):
                <code>
                """,
            args_schema=ToolCreationInput
        )
    ]
    
    return tools
