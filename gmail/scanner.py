import json
import re

from gmail.parser import GmailParser


class GmailScanner:

    QUERY = (
        'from:invitations@linkedin.com '
        'subject:"accepted your invitation" '
        'newer_than:30d'
    )

    def __init__(self, service):

        self.service = service

    def mark_processed(self, message_id, label_id):

        self.service.users().messages().modify(
            userId="me",
            id=message_id,
            body={
                "addLabelIds": [label_id]
            }
        ).execute()

    def _debug_message(self, gmail_message):

        html = GmailParser._extract_html(gmail_message["payload"])
        subject = GmailParser._extract_subject(gmail_message["payload"]["headers"])
        links = re.findall(r'href=["\']([^"\']+)["\']', html or "", re.IGNORECASE)
        '''
        print("--- DEBUG GMAIL MESSAGE ---")
        print("message_id:", gmail_message.get("id"))
        print("subject:", subject)
        print("snippet:", gmail_message.get("snippet"))
        print("profile_url extracted:", GmailParser._extract_profile(html))
        print("html length:", len(html or ""))
        print("HTML preview:\n", (html or "")[:2000])
        print("links found:")
        for link in links[:50]:
            print(link)
        print("--- END DEBUG ---")'''


    def get_connections(self, processed_label_id=None):

        response = self.service.users().messages().list(
            userId="me",
            q=self.QUERY
        ).execute()

        messages = response.get("messages", [])

        results = []

        for message in messages:

            gmail_message = self.service.users().messages().get(
                userId="me",
                id=message["id"],
                format="full"
            ).execute()

            # skip messages that already have the processed label
            label_ids = gmail_message.get("labelIds", []) or []
            if processed_label_id and processed_label_id in label_ids:
                continue

            self._debug_message(gmail_message)

            parsed = GmailParser.parse_email(gmail_message)
            results.append(parsed)

        return results