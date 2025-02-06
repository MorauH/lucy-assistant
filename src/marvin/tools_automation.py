

from langchain.tools import StructuredTool
from typing import List, Optional, Callable
from pydantic import BaseModel

from .manager_system import SystemManager

# define input models
class SystemStatusInput(BaseModel):
    pass # input provided by get_tools



# define function implementations
def get_system_status(system_manager: SystemManager) -> str:
    """Get system status."""
    system_status = system_manager.system_status
    return f"Memory Usage: {system_status.memory_usage:.2f}%"

def schedule_task(system_manager: SystemManager, task_name: str, task: Callable, interval_minutes: int) -> str:
    """Schedule a task."""
    system_manager.schedule_task(task_name, task, interval_minutes)
    return f"Task '{task_name}' scheduled every {interval_minutes} minutes."


# define tools
def get_tools(system_manager: SystemManager) -> List[StructuredTool]:
    tools = [
        StructuredTool.from_function(
            name="get_system_status",
            func= lambda: get_system_status(system_manager),
            description="Get system memory usage.", # TODO: Add more system status info
            args_schema=SystemStatusInput
        )
    ]
    return tools