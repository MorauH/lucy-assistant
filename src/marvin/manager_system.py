from dataclasses import dataclass
import schedule
import logging
import asyncio
from typing import Dict, Callable
from datetime import datetime
import psutil
import os

@dataclass
class SystemStatus:
    memory_usage: float
    #workspace_size: int
    last_backup: datetime
    last_cleanup: datetime

class SystemManager:
    '''Manager for interacting with system and automation tasks'''
    def __init__(self, workspace_path: str):
        self.workspace_path = workspace_path
        self.scheduled_tasks: Dict[str, Callable] = {}
        self.system_status = SystemStatus(memory_usage=0.0, last_backup=datetime.now(), last_cleanup=datetime.now())

    async def run_scheduled_tasks(self):
        while True:
            schedule.run_pending()
            self.update_system_status()
            await asyncio.sleep(60)
        
    def update_system_status(self):
        process = psutil.Process()
        self.system_status.memory_usage = process.memory_percent()
        #self.system_status.workspace_size = self._get_workspace_size()

    def schedule_task(self, task_name: str, task: Callable, interval_minutes: int):
        schedule.every(interval_minutes).minutes.do(task)
        self.scheduled_tasks[task_name] = task
    
    def _get_workspace_size(self):
        """Calculate the total workspace size"""
        try:
            total = sum(os.path.getsize(os.path.join(self.workspace_path, path, file))
                        for path, dirs, files in os.walk(self.workspace_path)
                        for file in files)
            return total
        except (OSError, FileNotFoundError) as e:
            logging.warning(f"Error calculating workspace size: {e}")
            return 0