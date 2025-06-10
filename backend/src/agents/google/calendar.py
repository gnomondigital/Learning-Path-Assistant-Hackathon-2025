import logging
import os
import pickle
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import dateparser
import pytz
from dateutil.tz import gettz
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from semantic_kernel.functions import kernel_function

logger = logging.getLogger(__name__)


class GoogleCalendarPlugin:
    """
    A class to encapsulate Google Calendar API functionalities for creating and retrieving events.
    It handles authentication and provides semantic methods for calendar operations.
    """

    def __init__(
            self,
            credentials_file: str = 'credentials.json',
            token_file: str = 'token_calendar.pickle',
            scopes: Optional[List[str]] = None):
        """
        Initializes the GoogleCalendarPlugin.

        Args:
            credentials_file (str): Path to the Google API credentials JSON file.
            token_file (str): Path to the file where authentication tokens will be stored.
            scopes (list): List of OAuth scopes required for Calendar API access.
                           Defaults to ['https://www.googleapis.com/auth/calendar']
                           which allows read/write access to all calendars.
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        # Using the broader calendar scope for both read and write
        self.scopes = scopes if scopes else [
            'https://www.googleapis.com/auth/calendar']
        self.service = self._get_calendar_service()

    def _get_calendar_service(self):
        """
        Authenticates with the Google Calendar API and returns a service object.
        It handles token storage to avoid re-authentication on subsequent runs.
        """
        creds = None
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.scopes)
                    creds = flow.run_local_server(port=0)
                except FileNotFoundError:
                    logger.info(
                        f"Error: '{self.credentials_file}' not found. Please ensure your Google API credentials file is in the correct directory.")
                    return None
                except Exception as e:
                    logger.info(
                        f"An error occurred during authentication flow: {e}")
                    return None
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)

        try:
            service = build('calendar', 'v3', credentials=creds)
            logger.info(
                "Google Calendar API service initialized successfully.")
            return service
        except HttpError as error:
            logger.info(
                f"An error occurred while initializing Calendar service: {error}")
            return None

    @kernel_function(
        description="Creates a new calendar event.",
        name="CreateCalendarEvent"
    )
    def create_event(
        self,
        summary: str,
        start_datetime: str,
        end_datetime: str,
        timezone: str = "Europe/Paris"
    ) -> str:

        def to_iso(date_str: str, default_time: str) -> str:
            parsed = dateparser.parse(
                date_str,
                settings={
                    'TIMEZONE': timezone,
                    'RETURN_AS_TIMEZONE_AWARE': True,
                    'PREFER_DATES_FROM': 'future'
                }
            )
            if not parsed:
                raise ValueError(f"Could not parse date string: {date_str}")
            return parsed.isoformat()

        start_iso = to_iso(start_datetime, "start")
        end_iso = to_iso(end_datetime, "end")

        event_data = {
            "summary": summary,
            "start": {"dateTime": start_iso, "timeZone": timezone},
            "end": {"dateTime": end_iso, "timeZone": timezone},
        }

        created_event = self.service.events().insert(
            calendarId="primary", body=event_data).execute()
        return f"Event '{created_event.get('summary')}' created on {created_event.get('start').get('dateTime')}"

    @kernel_function(
        description="Retrieves calendar events within a specified time range.",
        name="ListCalendarEvents"
    )
    def list_events(self,
                    start_datetime_iso: str,
                    end_datetime_iso: str,
                    calendar_id: str = 'primary',
                    max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieves a list of events from the specified Google Calendar within a given time range.

        Args:
            start_datetime_iso (str): The start date and time in ISO 8601 format (e.g., '2025-05-23T00:00:00Z').
                                      Must be a datetime string with timezone (Z for UTC or +HH:MM/-HH:MM).
            end_datetime_iso (str): The end date and time in ISO 8601 format (e.g., '2025-05-24T00:00:00Z').
                                    Must be a datetime string with timezone.
            calendar_id (str): The ID of the calendar to list events from. 'primary' for the default calendar.
            max_results (int): The maximum number of events to retrieve.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each representing an event with 'summary',
                                  'start_time', 'end_time', 'location', 'description', and 'id'.
                                  Returns an empty list if no events are found or an error occurs.
        """
        if not self.service:
            logger.info(
                "Calendar service not initialized. Cannot list events.")
            return []

        try:
            events_result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=start_datetime_iso,
                timeMax=end_datetime_iso,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            events = events_result.get('items', [])

            if not events:
                logger.info(
                    f"No events found between {start_datetime_iso} and {end_datetime_iso}.")
                return []

            formatted_events = []
            logger.info(f"Found {len(events)} events:")
            for event in events:
                start = event['start'].get(
                    'dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))

                formatted_event = {
                    'id': event['id'],
                    'summary': event.get('summary', 'No Title'),
                    'start_time': start,
                    'end_time': end,
                    'location': event.get('location', 'N/A'),
                    'description': event.get('description', 'N/A')
                }
                formatted_events.append(formatted_event)
                logger.info(
                    f"- {formatted_event['summary']} ({formatted_event['start_time']} to {formatted_event['end_time']})")

            return formatted_events
        except HttpError as error:
            logger.info(f"An error occurred while listing events: {error}")
            return []
        except Exception as e:
            logger.info(f"An unexpected error occurred: {e}")
            return []

    def get_iso_datetime_for_today(self, time_of_day: str = "start"):
        """
        Returns the ISO 8601 datetime string for the start or end of today.
        time_of_day can be 'start' (00:00:00) or 'end' (23:59:59).
        """
        now = datetime.now()
        if time_of_day == "start":
            dt = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_of_day == "end":
            dt = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        else:
            raise ValueError("time_of_day must be 'start' or 'end'")
        return dt.astimezone(datetime.now().astimezone().tzinfo).isoformat() + 'Z'

    def get_iso_datetime_for_tomorrow(self, time_of_day: str = "start"):
        """
        Returns the ISO 8601 datetime string for the start or end of tomorrow.
        time_of_day can be 'start' (00:00:00) or 'end' (23:59:59).
        """
        tomorrow = datetime.now() + timedelta(days=1)
        if time_of_day == "start":
            dt = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_of_day == "end":
            dt = tomorrow.replace(hour=23, minute=59,
                                  second=59, microsecond=999999)
        else:
            raise ValueError("time_of_day must be 'start' or 'end'")
        return dt.astimezone(datetime.now().astimezone().tzinfo).isoformat() + 'Z'

    @kernel_function(
        name="GetCurrentDateTime",
        description="Returns the current date and time in ISO 8601 format with timezone."
    )
    def get_current_datetime(self, timezone: str = "Europe/Paris") -> str:
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        return now.isoformat()

    @kernel_function(
        name="GetCurrentDate",
        description="Returns the current date only (YYYY-MM-DD) based on the given timezone."
    )
    def get_current_date(self, timezone: str = "Europe/Paris") -> str:
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        return now.strftime("%Y-%m-%d")

    @kernel_function(
        name="GetCurrentTime",
        description="Returns the current time only (HH:MM:SS) based on the given timezone."
    )
    def get_current_time(self, timezone: str = "Europe/Paris") -> str:
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        return now.strftime("%H:%M:%S")
