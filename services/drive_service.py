import os

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload


class GoogleDriveService:

    def __init__(self, creds):

        self.service = build(
            "drive",
            "v3",
            credentials=creds
        )

    def download_file(
        self,
        file_id,
        destination
    ):

        request = self.service.files().get_media(
            fileId=file_id
        )

        with open(destination, "wb") as file:

            downloader = MediaIoBaseDownload(
                file,
                request
            )

            done = False

            while not done:

                status, done = downloader.next_chunk()

                if status:

                    print(
                        f"Downloading resume: "
                        f"{int(status.progress() * 100)}%"
                    )

        print(
            f"Resume downloaded to {destination}"
        )

        return destination