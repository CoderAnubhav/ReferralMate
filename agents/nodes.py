from .prompts import REFERRAL_PROMPT


def analyze_jd(state, llm):

    prompt = f"""
Analyze the following resume and job description.

Resume:
{state["resume"]}

Job Description:
{state["jd"]}

Identify only the candidate skills from the resume
that are relevant to this job description.

Return a comma-separated list of skills.
Do not invent skills.
"""

    result = llm.generate(prompt)

    skills = [
        skill.strip()
        for skill in result.split(",")
        if skill.strip()
    ]

    return {
        "matched_skills": skills
    }


def generate_referral(state, llm):

    prompt = REFERRAL_PROMPT.format(

        resume=state["resume"],

        company=state["company"],

        jd=state["jd"],

        matched_skills=", ".join(
            state["matched_skills"]
        )

    )

    message = llm.generate(prompt)

    return {
        "referral_message": message
    }


def validate_referral(state):

    message = state["referral_message"]

    word_count = len(
        message.split()
    )

    passed = (
        word_count <= 80
        and len(message.strip()) > 0
    )

    return {
        "validation_passed": passed
    }