REFERRAL_PROMPT = """
You are writing a LinkedIn referral request for a candidate.

Candidate Resume:
{resume}

Company:
{company}

Job Description:
{jd}

Relevant skills identified from the resume:
{matched_skills}

Write a short, natural LinkedIn referral request.

Rules:

1. Maximum 80 words.
2. Mention only skills that are genuinely present in the resume.
3. Mention the company and role naturally.
4. Do not exaggerate the candidate's experience.
5. Do not invent achievements.
6. Do not use bullet points.
7. Do not sound like an AI-generated template. It should sound like a human wrote it.It should be natural.
8. Be polite and concise.
9. The request should directly ask for a referral.
10. Do not mention the analysis process.
11. If any Job Id or Requisition id is present that uniquely identifies the job, include it in the request.
12. Let them know that the resume is attached in case they need to review it.
13. Job ID must always be explicitly extracted and included. If not present dont invent one.
14. Don't say "I believe my background fits well" or similar self-evaluative language.
15. Also ask them to let you know if they need any additional information or documents from the candidate in a polite manner.
Return only the referral message.
"""