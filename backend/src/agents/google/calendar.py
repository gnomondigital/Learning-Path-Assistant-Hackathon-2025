import logging
import os
import pickle
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

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
    def create_event(self,
                     summary: str,
                     start_datetime: str,
                     end_datetime: str,
                     description: Optional[str] = "",
                     location: Optional[str] = "",
                     attendees: Optional[str] = "",  # Comma-separated emails
                     calendar_id: str = 'primary') -> str:
        """
        Creates a new event on the specified Google Calendar.

        Args:
            summary (str): The summary (title) of the event.
            start_datetime (str): The start date and time of the event in ISO 8601 format (e.g., '2025-05-23T10:00:00+02:00').
                                  If it's an all-day event, use 'YYYY-MM-DD' (e.g., '2025-05-23').
            end_datetime (str): The end date and time of the event in ISO 8601 format (e.g., '2025-05-23T11:00:00+02:00').
                                If it's an all-day event, use 'YYYY-MM-DD'.
            description (Optional[str]): A description of the event.
            location (Optional[str]): The location of the event.
            attendees (Optional[str]): Comma-separated list of attendee email addresses (e.g., 'john@example.com,jane@example.com').
            calendar_id (str): The ID of the calendar to create the event on. 'primary' for the default calendar.

        Returns:
            str: The URL of the created event, or an error message if creation fails.
        """
        if not self.service:
            return "Calendar service not initialized. Cannot create event."

        event_data = {
            'summary': summary,
            'location': location,
            'description': description,
            'start': {},
            'end': {},
        }

        # Determine if it's an all-day event or specific time event
        if 'T' in start_datetime and 'T' in end_datetime:
            # Assuming Paris timezone as default
            event_data['start'] = {
                'dateTime': start_datetime, 'timeZone': 'Europe/Paris'}
            event_data['end'] = {'dateTime': end_datetime,
                                 'timeZone': 'Europe/Paris'}
        else:
            event_data['start'] = {'date': start_datetime}
            event_data['end'] = {'date': end_datetime}

        if attendees:
            attendees_list = [{'email': email.strip()}
                              for email in attendees.split(',')]
            event_data['attendees'] = attendees_list

        try:
            event = self.service.events().insert(
                calendarId=calendar_id, body=event_data).execute()
            logger.info(f"Event created: {event.get('htmlLink')}")
            return event.get('htmlLink')
        except HttpError as error:
            error_message = f"An error occurred while creating event: {error}"
            logger.info(error_message)
            return error_message
        except Exception as e:
            error_message = f"An unexpected error occurred: {e}"
            logger.info(error_message)
            return error_message

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
                singleEvents=True,  # Expand recurring events into single events
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

    # --- Helper functions for common date ranges ---
    # These are not kernel_functions themselves, but can be used by the Semantic Kernel
    # or other parts of your application to prepare inputs for list_events.

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
        # Current location is Paris, Île-de-France, France, so using Europe/Paris timezone
        # For simplicity, returning a naive datetime and indicating UTC for API calls,
        # but in a production system, use a proper timezone library like pytz or zoneinfo.
        # Google Calendar API often prefers UTC (ending with Z) or explicit timezone.
        # For 'T' in datetime, ensure correct timezone suffix.
        # Example: '2025-05-23T00:00:00+02:00' for Paris time.
        # For simplicity, convert to UTC and add 'Z' for API.
        # Converts to local timezone, then to ISO with Z
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
