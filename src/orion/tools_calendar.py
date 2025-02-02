
from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime

from typing import List, Optional, Callable
from pydantic import BaseModel
from langchain.tools import StructuredTool

from .manager_calendar import CalendarManager



# Path to Service Account JSON key file
SERVICE_ACCOUNT_FILE = 'tokens/calendar.json'
CALENDAR_ID = 'eb83e5c1be04baa73b785d65d935a67424cb15440ada0e5a22f75268d400e3b8@group.calendar.google.com'

SCOPES = ['https://www.googleapis.com/auth/calendar']

credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
cal_service = build('calendar', 'v3', credentials=credentials)
calendar_manager = CalendarManager(cal_service, CALENDAR_ID)


# define input models
class DateInput(BaseModel):
    date: str

class EventInput(BaseModel):
    start_datetime: str
    end_datetime: str
    summary: str
    description: Optional[str] = None
    location: Optional[str] = None

class UpdateEventInput(BaseModel):
    event_id: str
    start_datetime: str
    end_datetime: str
    summary: str
    description: Optional[str] = None
    location: Optional[str] = None

class EventIdInput(BaseModel):
    event_id: str

# Function implementations
def get_events_for_day(date: str) -> List[str]:
    """Get events for a specific day."""
    date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    events = calendar_manager.get_events_for_day(date)
    return events
def get_events_for_week(date: str) -> List[str]:
    """Get events for a specific week."""
    date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    events = calendar_manager.get_events_for_week(date)
    return events
def get_events_for_month(date: str) -> List[str]:
    """Get events for a specific month."""
    date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    events = calendar_manager.get_events_for_month(date)
    return events

def create_event(start_datetime: str, end_datetime: str, summary: str, description: str = None, location: str = None):
    """Create an event with the specified details."""
    start_time = datetime.datetime.strptime(start_datetime, "%Y-%m-%dT%H:%M:%S")
    end_time = datetime.datetime.strptime(end_datetime, "%Y-%m-%dT%H:%M:%S")
    event = calendar_manager.create_event(start_time, end_time, summary, description, location)
    return event

def update_event(event_id: str, start_datetime: str, end_datetime: str, summary: str, description: str = None, location: str = None):
    """Update an existing event with the specified details."""
    start_time = datetime.datetime.strptime(start_datetime, "%Y-%m-%dT%H:%M:%S")
    end_time = datetime.datetime.strptime(end_datetime, "%Y-%m-%dT%H:%M:%S")
    event = calendar_manager.update_event(event_id, start_time, end_time, summary, description, location)
    return event

def delete_event(event_id: str):
    """Delete an event with the specified ID."""
    return calendar_manager.delete_event(event_id)

# Structured tool creation
def get_tools() -> List[StructuredTool]:
    tools = [
        StructuredTool.from_function(
            name="get_events_for_day",
            func=get_events_for_day,
            description="Get events for a specific day. Date format: 'YYYY-MM-DD'",
            args_schema=DateInput,
        ),
        StructuredTool.from_function(
            name="get_events_for_week",
            func=get_events_for_week,
            description="Get events for a specific week. Date format: 'YYYY-MM-DD'",
            args_schema=DateInput,
        ),
        StructuredTool.from_function(
            name="get_events_for_month",
            func=get_events_for_month,
            description="Get events for a specific month. Date format: 'YYYY-MM-DD'",
            args_schema=DateInput,
        ),
        StructuredTool.from_function(
            name="create_event",
            func=create_event,
            description="Create an event. Date time format: 'YYYY-MM-DDTHH:MM:SS'",
            args_schema=EventInput,
        ),
        StructuredTool.from_function(
            name="update_event",
            func=update_event,
            description="Update an existing event. Date time format: 'YYYY-MM-DDTHH:MM:SS'",
            args_schema=UpdateEventInput,
        ),
        StructuredTool.from_function(
            name="delete_event",
            func=delete_event,
            description="Delete an event with the specified ID.",
            args_schema=EventIdInput,
        ),

    ]
    return tools