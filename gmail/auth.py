import os

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

from google_auth_oauthlib.flow import InstalledAppFlow

from googleapiclient.discovery import build


class GmailAuth:

    SCOPES = [
        "https://www.googleapis.com/auth/gmail.modify",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.readonly"
    ]

    def __init__(self):

        self.creds = None

    def authenticate(self):

        if os.path.exists("token.json"):

            self.creds = Credentials.from_authorized_user_file(
                "token.json",
                self.SCOPES
            )

        if not self.creds or not self.creds.valid:

            if self.creds and self.creds.expired and self.creds.refresh_token:

                self.creds.refresh(Request())

            else:

                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json",
                    self.SCOPES
                )

                self.creds = flow.run_local_server(port=0)

            with open("token.json", "w") as token:

                token.write(self.creds.to_json())

        gmail_service=build(
            "gmail",
            "v1",
            credentials=self.creds
        )
        print("Granted Scopes:", self.creds.scopes)
        return gmail_service, self.creds
        