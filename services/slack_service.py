from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from services.llm_service import LLMService
from services.resume import load_resume

from agents.graph import build_referral_graph

from config import (
    SLACK_BOT_TOKEN,
    SLACK_CHANNEL_ID
)
import re

class SlackParser:

        @staticmethod
        def parse(message):

            message = message.strip()

            # -------------------------------
            # JD COMMAND
            # -------------------------------

            jd_pattern = r"^jd\s+(.+?)\n([\s\S]+)$"

            match = re.match(
                jd_pattern,
                message,
                re.IGNORECASE
            )

            if match:

                descriptions = [

                    jd.strip()

                    for jd in re.split(

                        r"\n\s*---\s*\n",

                        match.group(2)

                    )

                    if jd.strip()

                ]

                return {

                    "command": "jd",

                    "name": match.group(1).strip(),

                    "descriptions": descriptions

                }

            # -------------------------------
            # COMPANY COMMAND
            # -------------------------------

            company_pattern = r"^company\s+(.+?)\s*,\s*(.+)$"

            match = re.match(
                company_pattern,
                message,
                re.IGNORECASE
            )

            if match:

                return {

                    "command": "company",

                    "name": match.group(1).strip(),

                    "company": match.group(2).strip()

                }

            return None


class SlackService:

    def __init__(self):

        self.client = WebClient(
            token=SLACK_BOT_TOKEN
        )
        self.channel =  SLACK_CHANNEL_ID

        self.llm = LLMService()
        self.referral_agent = build_referral_graph(
            self.llm
        )

    def send_new_connections(self, connections):

        if not connections:

            return

        message = "*🎉 New LinkedIn Connections*\n\n"

        for connection in connections:

            name = connection.get("name", "Unknown")
            profile_url = connection.get("profile_url")

            if profile_url:
                message += f"• <{profile_url}|{name}>\n"
            else:
                message += f"• {name}\n"

        message += (
            "\nReply with:\n"
            "`Name | Company`\n\n"
            "Example:\n"
            "`John Doe | Microsoft`"
        )

        self.client.chat_postMessage(

            channel=SLACK_CHANNEL_ID,

            text=message

        )

    def send_message(self, message):
        self.client.chat_postMessage(
            channel=self.channel,
            text=message
        )

    '''
    def process_company_message(
        self,
        message,
        sheet
    ):

        parsed = SlackParser.parse(

            message["text"]

        )

        if parsed is None:

            return

        sheet.update_company(

            parsed["name"],

            parsed["company"]

        )'''

    def process_company_message(
        self,
        message,
        sheet
    ):

        parsed = SlackParser.parse(
            message["text"]
        )

        if parsed is None:
            return

        if parsed["command"] == "jd":

            matches = sheet.find_by_name(

                parsed["name"]

            )

            if len(matches) == 0:

                self.send_message(

                    f"No connection found with name '{parsed['name']}'."

                )

                return

            if len(matches) == 1:

                row = matches[0]["row"]

                # Store JD in Google Sheet
                sheet.update_jd_by_row(

                    row,

                    parsed["descriptions"]

                )

                # Read company from the same row
                company = sheet.get_company_by_row(row)

                existing_referral = (
                    sheet.find_generated_referral_by_company(
                        company
                    )
                )

                if existing_referral:

                    # ----------------------------
                    # Reuse existing referral
                    # ----------------------------


                    sheet.update_referral_text(
                        row,
                        existing_referral["referral"]
                    )

                    sheet.update_status(
                        row,
                        "REFERRAL_REUSED"
                    )

                    self.send_message(
                        f"*♻️ Reused existing {company} referral "
                        f"message:*\n\n"
                        f"{existing_referral['referral']}"
                    )

                    return

                # ----------------------------
                # No referral exists yet
                # ----------------------------
                
                # Load resume
                resume = load_resume()

                generated_messages = []

                # Generate one referral message per JD
                for jd in parsed["descriptions"]:

                    initial_state = {

                        "candidate_name":
                            parsed["name"],

                        "company":
                            company,

                        "resume":
                            resume,

                        "jd":
                            jd,

                        "matched_skills": [],

                        "referral_message": "",

                        "validation_passed": False
                    }

                    result = self.referral_agent.invoke(
                        initial_state
                    )

                    generated_messages.append(
                        result["referral_message"]
                    )


                # Store generated messages in Google Sheet
                sheet.update_generated_message(

                    row,

                    generated_messages

                )

                # Send to Slack
                reply = "*Generated Referral Message(s)*\n\n"

                for i, msg in enumerate(generated_messages, start=1):

                    reply += f"*Job {i}*\n{msg}\n\n"

                self.send_message(reply)

                return
            

            reply = (

                f"I found {len(matches)} people named "

                f"{parsed['name']}.\n\n"

            )

            for i, match in enumerate(matches, start=1):

                reply += (

                    f"{i}.\n"

                    f"LinkedIn: {match['profile']}\n\n"

                )

            reply += (

                "Please resend using the LinkedIn profile link."

            )

            self.send_message(reply)

            return

        matches = sheet.find_by_name(
            parsed["name"]
        )

        if len(matches) == 0:

            self.send_message(
                f"No connection found with name '{parsed['name']}'."
            )

            return

        if len(matches) == 1:

            row = sheet.update_company_by_row(

                matches[0]["row"],

                parsed["company"]

            )

            links = sheet.populate_job_links_for_row(row)

            if links:
                link_lines = "\n".join(
                    f"• <{link}|{parsed['company']}>" for link in links
                )
                self.send_message(
                    f"Updated company for {parsed['name']} ({parsed['company']}).\n"
                    f"Recent job links:\n{link_lines}"
                )
            else:
                self.send_message(
                    f"Updated company for {parsed['name']} ({parsed['company']}). "
                    "No recent job links were found."
                )

            return

        # Duplicate names
        reply = (
            f"I found {len(matches)} people named "
            f"{parsed['name']}.\n\n"
        )

        for i, match in enumerate(matches, start=1):

            current_company = match["company"] or "-"

            reply += (
                f"{i}.\n"
                f"Current Company: {current_company}\n"
                f"LinkedIn: {match['profile']}\n\n"
            )

        reply += (
            "Reply using:\n\n"
            f"company <number>, {parsed['company']}"
        )

        self.send_message(reply)

    def fetch_new_messages(self, oldest=None):

        """
        Returns a normalized list of Slack messages.

        Example
        -------
        [
            {
                "text": "...",
                "timestamp": "...",
                "user": "..."
            }
        ]
        """

        try:

            response = self.client.conversations_history(

                channel=self.channel,

                oldest=oldest,

                inclusive=False,

                limit=100

            )

            messages = []

            for msg in response["messages"]:

                messages.append({

                    "text": msg.get("text", ""),

                    "timestamp": msg.get("ts"),

                    "user": msg.get("user")

                })

            messages.reverse()

            return messages

        except SlackApiError as e:

            print(e.response["error"])

            return []

    