import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


class GmailAuth:

    SCOPES = [
        "https://www.googleapis.com/auth/gmail.modify",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    def __init__(
        self,
        credentials_file="credentials.json",
        token_file="token.json"
    ):

        self.credentials_file = credentials_file
        self.token_file = token_file

    def authenticate(self):

        creds = None

        # --------------------------------------------------
        # 1. Try to load existing OAuth token
        # --------------------------------------------------

        if os.path.exists(self.token_file):

            print("Loading existing Google OAuth token...")

            creds = Credentials.from_authorized_user_file(
                self.token_file,
                self.SCOPES
            )

        # --------------------------------------------------
        # 2. Refresh expired token
        # --------------------------------------------------

        if creds and creds.expired and creds.refresh_token:

            print("Google OAuth token expired.")
            print("Refreshing token...")

            try:

                creds.refresh(Request())

                print("Google OAuth token refreshed.")

            except Exception as e:

                print(
                    "Failed to refresh Google OAuth token:"
                )

                print(e)

                creds = None

        # --------------------------------------------------
        # 3. If no valid token exists
        # --------------------------------------------------

        if not creds or not creds.valid:

            # ----------------------------------------------
            # GitHub Actions cannot perform browser login
            # ----------------------------------------------

            if os.getenv("GITHUB_ACTIONS") == "true":

                raise RuntimeError(
                    "No valid Google OAuth token is available "
                    "in GitHub Actions. Please update the "
                    "GOOGLE_TOKEN_JSON GitHub secret with a "
                    "valid token.json."
                )

            # ----------------------------------------------
            # Local development
            # ----------------------------------------------

            print(
                "No valid Google OAuth token found."
            )

            print(
                "Starting browser-based Google authentication..."
            )

            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_file,
                self.SCOPES
            )

            creds = flow.run_local_server(
                port=0
            )

        # --------------------------------------------------
        # 4. Save token locally
        # --------------------------------------------------

        with open(
            self.token_file,
            "w"
        ) as token:

            token.write(
                creds.to_json()
            )

        print(
            "Google authentication successful."
        )

        return creds