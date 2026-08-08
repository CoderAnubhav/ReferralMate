from config import GMAIL_LABEL_NAME


class GmailLabels:

    def __init__(self, service):

        self.service = service

    def get_or_create_label(self):

        labels = self.service.users().labels().list(
            userId="me"
        ).execute()

        for label in labels["labels"]:

            if label["name"] == GMAIL_LABEL_NAME:
                return label["id"]

        body = {

            "name": GMAIL_LABEL_NAME,

            "labelListVisibility": "labelShow",

            "messageListVisibility": "show"

        }

        label = self.service.users().labels().create(
            userId="me",
            body=body
        ).execute()

        return label["id"]