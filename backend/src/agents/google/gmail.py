import base64
import logging
import os
import pickle
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from semantic_kernel.functions import kernel_function

logger = logging.getLogger(__name__)


class GmailPlugin:
    def __init__(
            self, credentials_file='credentials.json',
            token_file='token.pickle', scopes=None):
        """
        Initializes the GmailPlugin.

        Args:
            credentials_file (str): Path to the Google API credentials JSON file.
            token_file (str): Path to the file where authentication tokens will be stored.
            scopes (list): List of OAuth scopes required for Gmail API access.
                           Defaults to ['https://www.googleapis.com/auth/gmail.modify']
                           which allows reading, writing, and deleting emails.
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.scopes = scopes if scopes else [
            'https://www.googleapis.com/auth/gmail.modify']
        self.service = self._get_gmail_service()
        self.user_id = 'me'  # 'me' refers to the authenticated user

    def _get_gmail_service(self):
        """
        Authenticates with the Gmail API and returns a service object.
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
                        f"Error: '{self.credentials_file}' not found. Please ensure your Gmail API credentials file is in the correct directory.")
                    return None
                except Exception as e:
                    logger.info(
                        f"An error occurred during authentication flow: {e}")
                    return None
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)

        try:
            service = build('gmail', 'v1', credentials=creds)
            logger.info("Gmail API service initialized successfully.")
            return service
        except HttpError as error:
            logger.info(
                f"An error occurred while initializing Gmail service: {error}")
            return None

    @kernel_function(
        name="create_message",
        description="Create a message for an email. The message is base64url encoded.",
    )
    def create_message(self, to: str, subject: str, message_text: str) -> dict:
        """
        Create a message for an email.

        Args:
            to (str): Email address of the receiver.
            subject (str): Subject of the email.
            message_text (str): The text of the email message.

        Returns:
            dict: An object containing a base64url encoded email object, or None if service is not available.
        """
        if not self.service:
            logger.info(
                "Gmail service not initialized. Cannot create message.")
            return None
        message = MIMEText(message_text)
        message['to'] = to
        message['from'] = self.user_id  # Sender is the authenticated user
        message['subject'] = subject
        return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}

    @kernel_function(
        name="create_message_with_attachment",
        description="Create a message with an attachment. The message is base64url encoded.",
    )
    def create_message_with_attachment(self, to: str, subject: str, message_text: str, file_path: str) -> dict:
        """
        Create a message with an attachment.

        Args:
            to (str): Email address of the receiver.
            subject (str): Subject of the email.
            message_text (str): The text of the email message.
            file_path (str): Path to the file to be attached.

        Returns:
            dict: An object containing a base64url encoded email object, or None if service is not available.
        """
        if not self.service:
            logger.info(
                "Gmail service not initialized. Cannot create message with attachment.")
            return None
        message = MIMEMultipart()
        message['to'] = to
        message['from'] = self.user_id  # Sender is the authenticated user
        message['subject'] = subject

        msg = MIMEText(message_text)
        message.attach(msg)

        try:
            with open(file_path, 'rb') as f:
                part = MIMEApplication(
                    f.read(), name=os.path.basename(file_path))
            part['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
            message.attach(part)
        except FileNotFoundError:
            logger.info(f"Error: Attachment file not found at '{file_path}'.")
            return None
        except Exception as e:
            logger.info(f"An error occurred while attaching file: {e}")
            return None

        return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}

    @kernel_function(
        name="send_email",
        description="Send an email message. The message must be created using create_message or create_message_with_attachment.",
    )
    def send_email(self, message: dict) -> dict:
        """
        Send an email message.

        Args:
            message (dict): Message object to be sent (created by create_message or create_message_with_attachment).

        Returns:
            dict: Sent Message object, or None if sending failed.
        """
        if not self.service:
            logger.info("Gmail service not initialized. Cannot send email.")
            return None
        try:
            sent_message = self.service.users().messages().send(
                userId=self.user_id, body=message).execute()
            logger.info(f"Message Id: {sent_message['id']} sent successfully!")
            return sent_message
        except HttpError as error:
            logger.info(f"An error occurred while sending message: {error}")
            return None
