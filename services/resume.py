from pathlib import Path


def load_resume():

    path = Path(
        "/Users/anubhavmisra/Referral Assistant/resume/resume.txt"
    )

    return path.read_text(
        encoding="utf-8"
    )