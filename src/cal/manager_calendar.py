
# calandar manager class using google calandar api

import datetime
import calendar


class CalendarManager:
    def __init__(self, calendar_service, calendar_id):
        self.calendar_service = calendar_service
        self.calendar_id = calendar_id

    def get_events(self, start_date: datetime.date, end_date: datetime.date):

        # Expects time in iso format. Ex: "2021-10-10T10:00:00"

        events_result = self.calendar_service.events().list(
            calendarId=self.calendar_id,
            timeMin=start_date.isoformat() + 'T00:00:00Z',
            timeMax=end_date.isoformat() + 'T23:59:59Z',
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        print(events_result)

        events = events_result.get('items', [])
        return events

    def get_events_for_day(self, date: datetime.date):
        return self.get_events(date, date)

    def get_events_for_week(self, date: datetime.date):
        weekday = date.weekday()
        start_date = date - datetime.timedelta(days=weekday)
        end_date = start_date + datetime.timedelta(days=6)
        return self.get_events(start_date, end_date)

    def get_events_for_month(self, date: datetime.date):
        _, num_days = calendar.monthrange(date.year, date.month)
        start_date = datetime.date(date.year, date.month, 1)
        end_date = datetime.date(date.year, date.month, num_days)
        return self.get_events(start_date, end_date)

    def create_event(self, start_datetime: datetime.datetime, end_datetime: datetime.datetime, summary: str, description: str = None, location: str = None):
        event = {
            'summary': summary,
            'description': description,
            'location': location,
            'start': {
                'dateTime': start_datetime.isoformat(),
                'timeZone': 'Europe/Stockholm',
            },
            'end': {
                'dateTime': end_datetime.isoformat(),
                'timeZone': 'Europe/Stockholm',
            },
        }

        event = self.calendar_service.events().insert(calendarId=self.calendar_id, body=event).execute()
        return event
    
    def delete_event(self, event_id: str):
        self.calendar_service.events().delete(calendarId=self.calendar_id, eventId=event_id).execute()
        return f"Event {event_id} deleted successfully."
    
    def update_event(self, event_id: str, start_datetime: datetime.datetime, end_datetime: datetime.datetime, summary: str, description: str = None, location: str = None):
        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_datetime.isoformat(),
                'timeZone': 'Europe/Stockholm',
            },
            'end': {
                'dateTime': end_datetime.isoformat(),
                'timeZone': 'Europe/Stockholm',
            }
        }
        if location:
            event['location'] = location
        event = self.calendar_service.events().update(calendarId=self.calendar_id, eventId=event_id, body=event).execute()
        return event
