from typing import List, Optional, Callable
from pydantic import BaseModel
from langchain.tools import StructuredTool
import os

from .manager_workspace import WorkspaceManager

# Define input models
class ListFilesInput(BaseModel):
    path: Optional[str] = None

class WriteFileInput(BaseModel):
    relative_path: str
    content: Optional[str] = ''

class FilePathInput(BaseModel):
    file_name: str

class ToolCreationInput(BaseModel):
    name: str
    description: str
    func: str
    # args_schema: str

class ExecuteStringInput(BaseModel):
    code: str


ROOT_DIRECTORY = os.getcwd() + '/root'

workspace = WorkspaceManager(ROOT_DIRECTORY)




# Function implementations

def list_directory(path: Optional[str] = None) -> List[str]:
    """List files and directories in the specified path relative to root directory."""
    # If path is None, use the current working directory

    path = path or '.'
    return workspace.list_directory(path)

def write_file(relative_path: str, content: str = '') -> str:
    """Write a file with specified content."""
    return workspace.write_file(relative_path, content)

def read_file(file_name: str) -> str:
    """Read and return the content of a file."""
    return workspace.read_file(file_name)

def delete_file(file_name: str) -> str:
    """Delete file or directory."""
    return workspace.delete_file(file_name)

# Structured tool creation for each function
def get_tools(execute_string_callable: Callable, create_tool_callable: Callable) -> List[StructuredTool]:
    tools = [
        StructuredTool.from_function(
            func=list_directory,
            name="list_directory",
            description="""
            lists files and directories within the file system.
            If path is provided, lists files and directories for the path relative to the current directory.
            similar to the os.listdir() function.
            """,
            args_schema=ListFilesInput
        ),
        StructuredTool.from_function(
            func=write_file,
            name="Write_File",
            description="Create a new file or overwrite existing file. Directory will be created if it does not exist.",
            args_schema=WriteFileInput
        ),
        StructuredTool.from_function(
            func=read_file,
            name="Read_File",
            description="Read and return the content of a file.",
            args_schema=FilePathInput
        ),
        StructuredTool.from_function(
            func=delete_file,
            name="Delete_File",
            description="Delete file or directory.",
            args_schema=FilePathInput
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
            func may be empty if a function with exact name is already defined.
            def func(<args>):
                <code>
                """,
            args_schema=ToolCreationInput
        )
    ]
    
    return tools