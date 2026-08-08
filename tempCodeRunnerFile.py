from gmail.auth import GmailAuth
from gmail.labels import GmailLabels
from gmail.scanner import GmailScanner
from services.sheets_service import GoogleSheetsService

from services.slack_service import SlackService


def main():

    gmail_service, creds  = GmailAuth().authenticate()
    sheet = GoogleSheetsService(creds)

    label_id = GmailLabels(
        gmail_service
    ).get_or_create_label()

    scanner = GmailScanner(
        gmail_service
    )

    connections = scanner.get_connections()

    names = []

    for connection in connections:

        sheet.insert_connection(
            name=connection["name"],
            Profile=connection["profile_url"],
            date=connection["accepted_date"]
        )

        names.append(connection["name"])

        scanner.mark_processed(

            connection["message_id"],

            label_id

        )

    SlackService().send_new_connections(names)


if __name__ == "__main__":

    main()