import base64
import html as html_module
import re
from bs4 import BeautifulSoup
from email.utils import parsedate_to_datetime
from urllib.parse import parse_qs, unquote, urlparse


class GmailParser:

    @staticmethod
    def _extract_subject(headers):

        for header in headers:

            if header["name"].lower() == "subject":
                return header["value"]

        return ""


    @staticmethod
    def _extract_date(headers):

        for header in headers:

            if header["name"].lower() == "date":

                try:
                    return parsedate_to_datetime(
                        header["value"]
                    ).strftime("%Y-%m-%d %H:%M:%S")

                except Exception:
                    return header["value"]

        return ""


    @staticmethod
    def _extract_html(payload):

        if payload.get("mimeType") == "text/html":

            data = payload.get("body", {}).get("data")

            if data:

                return base64.urlsafe_b64decode(
                    data + "=="
                ).decode("utf-8", errors="replace")

            return ""

        for part in payload.get("parts", []):

            html = GmailParser._extract_html(part)

            if html:

                return html

        return ""


    @staticmethod
    def _is_candidate_name(value):
        if not value:
            return False

        normalized = html_module.unescape(value).strip()
        if len(normalized.split()) < 2:
            return False

        lower = normalized.lower()
        generic_texts = {
            "view profile",
            "profile",
            "visit profile",
            "open profile",
            "view full profile",
            "view linkedin profile",
            "view linkedin",
            "linkedin"
        }

        if any(generic in lower for generic in generic_texts):
            return False

        return len(normalized) >= 5

    @staticmethod
    def _extract_name(subject, html=None):

        name = None
        if subject:
            match = re.search(
                r"^(.*?) accepted your invitation",
                subject
            )
            if match:
                name = match.group(1).strip()

        if html:
            html_name = GmailParser._extract_name_from_html(html)
            if html_name:
                if not name or len(html_name.split()) > len(name.split()):
                    return html_name
                if len(name.split()) == 1 and len(html_name.split()) >= 2:
                    return html_name

        return name

    @staticmethod
    def _extract_name_from_html(html):
        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        for a in soup.find_all("a", href=True):
            if GmailParser._extract_profile(a["href"]):
                text = a.get_text(" ", strip=True)
                if GmailParser._is_candidate_name(text):
                    return text

                title = a.get("title", "").strip()
                if GmailParser._is_candidate_name(title):
                    return title

                img = a.find("img")
                if img:
                    alt = img.get("alt", "").strip()
                    if GmailParser._is_candidate_name(alt):
                        return alt

                parent = a.parent
                if parent is not None:
                    parent_text = parent.get_text(" ", strip=True)
                    if GmailParser._is_candidate_name(parent_text):
                        return parent_text

        return None


    @staticmethod
    def _extract_profile(html):

        def find_linkedin(text):
            if not text:
                return None

            text = html_module.unescape(text)

            match = re.search(
                r'https?://[^\s"\'<>]*linkedin\.com/(?:in|pub|company|comm/in)/[^\s"\'<>]+',
                text,
                re.IGNORECASE
            )
            return match.group(0).split("?")[0] if match else None

        def decode_all(value):
            if not value:
                return value

            seen = set()
            while value and value not in seen:
                seen.add(value)
                decoded = unquote(value)
                if decoded == value:
                    break
                value = decoded
            return value

        def normalize_url(href):
            href = href.strip()
            if not href:
                return None

            direct = find_linkedin(href)
            if direct:
                return direct

            decoded = decode_all(href)
            direct = find_linkedin(decoded)
            if direct:
                return direct

            parsed = urlparse(href)
            query = parse_qs(parsed.query)
            for value_list in query.values():
                for value in value_list:
                    candidate = decode_all(value)
                    direct = find_linkedin(candidate)
                    if direct:
                        return direct

            return None

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        for a in soup.find_all("a", href=True):
            profile = normalize_url(a["href"])
            if profile:
                return profile

        # fallback: search the raw content for any LinkedIn URL
        return find_linkedin(html)

    @staticmethod
    def _extract_description(html):
        if not html:
            return None

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        profile_url = GmailParser._extract_profile(html)
        if not profile_url:
            return None

        generic_texts = {
            "view profile",
            "profile",
            "visit profile",
            "open profile",
            "view full profile",
            "view linkedin profile",
            "view linkedin"
        }

        for a in soup.find_all("a", href=True):
            href = html_module.unescape(a["href"])
            if profile_url in href:
                text = a.get_text(" ", strip=True)
                if text:
                    normalized = html_module.unescape(text).strip()
                    normalized_lower = normalized.lower()
                    if normalized_lower not in generic_texts and len(normalized) > 3:
                        return normalized

                title = a.get("title", "").strip()
                if title:
                    normalized = html_module.unescape(title)
                    if normalized.lower() not in generic_texts and len(normalized) > 3:
                        return normalized

                img = a.find("img")
                if img:
                    alt = img.get("alt", "").strip()
                    if alt:
                        normalized = html_module.unescape(alt)
                        if normalized.lower() not in generic_texts and len(normalized) > 3:
                            return normalized

                # direct child text only, not parent or siblings
                direct_texts = []
                for child in a.contents:
                    if hasattr(child, "get_text"):
                        child_text = child.get_text(" ", strip=True)
                    else:
                        child_text = str(child).strip()
                    if child_text:
                        direct_texts.append(child_text)
                combined = " ".join(direct_texts).strip()
                if combined:
                    normalized = html_module.unescape(re.sub(r"\s+", " ", combined)).strip()
                    if normalized.lower() not in generic_texts and len(normalized) > 3:
                        return normalized

        return None

    @staticmethod
    def _extract_description_from_text(text):
        if not text:
            return None

        text = html_module.unescape(re.sub(r"\s+", " ", text)).strip()
        if len(text) < 20:
            return None

        patterns = [
            r'(?i)(?P<desc>[A-Z][^\.\n]{10,200}?\bat\b[^\.\n]{0,200})',
            r'(?i)(?P<desc>[A-Z][^\.\n]{10,200}?\b(?:currently|working|serving|is|works|title|role|designation|founder|co-founder|CEO|CTO|CFO|COO|Director|Manager|Head)\b[^\.\n]{0,200})'
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                desc = match.group("desc").strip(" .,!;")
                if 15 < len(desc) <= 250:
                    return desc

        fragments = re.split(r"[\n\.]{1,2}", text)
        for fragment in fragments:
            fragment = fragment.strip()
            if " at " in fragment and 15 < len(fragment) <= 250:
                return fragment

        return None

    @staticmethod
    def _extract_description(html):
        if not html:
            return None

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        profile_link = GmailParser._extract_profile(html)
        if profile_link:
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if profile_link in href or profile_link in unquote(href):
                    text = a.get_text(" ", strip=True)
                    if text:
                        candidate = GmailParser._extract_description_from_text(text)
                        if candidate:
                            return candidate

                    parent = a.parent
                    if parent is not None:
                        candidate = GmailParser._extract_description_from_text(parent.get_text(" ", strip=True))
                        if candidate:
                            return candidate

                    grandparent = parent.parent if parent is not None else None
                    if grandparent is not None:
                        candidate = GmailParser._extract_description_from_text(grandparent.get_text(" ", strip=True))
                        if candidate:
                            return candidate

        full_text = soup.get_text(" ", strip=True)
        return GmailParser._extract_description_from_text(full_text)


    @classmethod
    def parse_email(cls, gmail_message):

        subject = cls._extract_subject(
            gmail_message["payload"]["headers"]
        )

        html = cls._extract_html(
            gmail_message["payload"]
        )

        return {

            "message_id": gmail_message["id"],

            "thread_id": gmail_message["threadId"],

            "subject": subject,

            "accepted_date": cls._extract_date(
                gmail_message["payload"]["headers"]
            ),

            "name": cls._extract_name(
                subject,
                html
            ),

            "profile_url": cls._extract_profile(
                html
            ),

            "description": cls._extract_description(
                html
            ),

            "html": html
        }