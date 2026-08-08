from gmail.auth import GmailAuth
from gmail.labels import GmailLabels
from gmail.scanner import GmailScanner
from services.sheets_service import GoogleSheetsService
from services.slack_service import SlackService


def main():
    gmail_service, creds = GmailAuth().authenticate()
    sheet = GoogleSheetsService(creds)

    label_id = GmailLabels(
        gmail_service
    ).get_or_create_label()

    scanner = GmailScanner(
        gmail_service
    )

    connections = scanner.get_connections(processed_label_id=label_id)

    notify_connections = []

    for connection in connections:
        print(
            f"Name: {connection['name']}, "
            f"Profile: {connection['profile_url']}, "
            f"Date: {connection['accepted_date']}"
        )
        sheet.insert_connection(
            name=connection["name"],
            profile_url=connection["profile_url"],
            designation=connection.get("description", ""),
            company="",
            date=connection["accepted_date"]
        )
        print("Connection inserted")

        notify_connections.append({
            "name": connection.get("name", "Unknown"),
            "profile_url": connection.get("profile_url", "")
        })

        scanner.mark_processed(
            connection["message_id"],
            label_id
        )

    slack_service = SlackService()
    slack_service.send_new_connections(notify_connections)

    oldest = sheet.get_slack_last_fetch_timestamp()
    messages = slack_service.fetch_new_messages(oldest=oldest)

    for message in messages:
        slack_service.process_company_message(
            message,
            sheet
        )


    if messages:
        newest_ts = messages[-1]["timestamp"]
        sheet.set_slack_last_fetch_timestamp(newest_ts)


if __name__ == "__main__":
    main()
