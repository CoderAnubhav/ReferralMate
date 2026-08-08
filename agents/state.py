from typing import TypedDict


class ReferralState(TypedDict):

    candidate_name: str

    company: str

    resume: str

    jd: str

    matched_skills: list[str]

    referral_message: str

    validation_passed: bool