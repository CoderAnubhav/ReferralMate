import gspread
from datetime import datetime, timedelta
from gspread.exceptions import WorksheetNotFound


class GoogleSheetsService:

    def __init__(self, creds):

        self.job_cache = None
        self.client = gspread.authorize(creds)

        self.sheet = (
            self.client
            .open("Referral Tracker")
            .sheet1
        )

         # Job List workbook
        self.job_sheet = (
            self.client
            .open("Job Listings")
            .sheet1
        )

    def get_all_names(self):

        return self.sheet.col_values(1)

    def name_exists(self, name):

        if not name:
            return False

        names = self.get_all_names()
        # skip header if present
        if names and names[0].strip().lower() == "name":
            names = names[1:]

        lowered = [n.strip().lower() for n in names if n and n.strip()]
        return name.strip().lower() in lowered

    def insert_connection(self, name, date, profile_url, description="", designation="", company=""):

        if self.name_exists(name):
            return

        row_values = [
            name,
            designation,
            profile_url,
            company,
            description,
            "",         # Status
            "",         # Job Link
            date
        ]

        # Determine the next row index reliably and write to A..H of that row
        rows = self.sheet.get_all_values()
        next_row = len(rows) + 1

        # Build range like A10:H10
        end_col = chr(ord('A') + len(row_values) - 1)
        target_range = f"A{next_row}:{end_col}{next_row}"

        # Use update to write the full row in one request
        self.sheet.update(target_range, [row_values])

    def get_slack_last_fetch_timestamp(self):
        cell = self.sheet.acell("O2")
        if cell and cell.value:
            return cell.value.strip()
        return None

    def set_slack_last_fetch_timestamp(self, timestamp):
        self.sheet.update_acell("O2", timestamp or "")

    def update_company(
        self,
        name,
        company
    ):

        rows = self.sheet.get_all_values()

        for row_number, row in enumerate(rows[1:], start=2):

            if row[0].strip().lower() == name.strip().lower():

                self.sheet.update_cell(
                    row_number,
                    4,
                    company
                )

                print(
                    f"Updated {name} -> {company}"
                )

                return True

        return False

    def update_company_by_row(
        self,
        row,
        company
    ):

        # Company is column D
        self.sheet.update_cell(
            row,
            4,
            company
        )

        return row

    def get_company_by_row(self, row):

        values = self.sheet.row_values(row)

        if len(values) >= 4:
            return values[3]

        return ""

    def update_jd_by_row(

                self,

                row,

                descriptions

        ):

            text = "\n\n==========\n\n".join(

                descriptions

            )

            self.sheet.update_cell(

                row,

                7,

                text

            )

    def update_generated_message(
        self,
        row,
        messages
    ):

        self.sheet.update_cell(

            row,

            8,

            "\n\n==========\n\n".join(messages)

        )

    def find_by_name(self, name):

        rows = self.sheet.get_all_values()
        if not rows:
            return []

        headers = [cell.strip().lower() for cell in rows[0]]
        name_idx = None
        profile_idx = None
        company_idx = None

        for i, header in enumerate(headers):
            if header == "name":
                name_idx = i
            elif header in ("linkedin profile", "profile"):
                profile_idx = i
            elif header == "company":
                company_idx = i

        if name_idx is None:
            name_idx = 0
        if profile_idx is None:
            profile_idx = 2 if len(headers) > 2 else None
        if company_idx is None:
            company_idx = 3 if len(headers) > 3 else None

        matches = []

        for index, row in enumerate(rows[1:], start=2):
            if len(row) <= name_idx:
                continue

            if row[name_idx].strip().lower() == name.strip().lower():
                profile = row[profile_idx].strip() if profile_idx is not None and profile_idx < len(row) else ""
                company = row[company_idx].strip() if company_idx is not None and company_idx < len(row) else ""
                matches.append({
                    "row": index,
                    "name": row[name_idx].strip(),
                    "profile": profile,
                    "company": company
                })

        return matches


    def build_job_dictionary(self):

        if self.job_cache is not None:
            return self.job_cache

        rows = self.job_sheet.get_all_records()
        print(f"Loaded {len(rows)} job rows")

        cutoff = datetime.today() - timedelta(days=15)

        jobs = {}

        for row in rows:

            company = str(
                row.get("Company", "")
            ).strip().lower()

            link = str(
                row.get("Job Link", "")
            ).strip()

            if not company or not link:
                continue

            raw_date = str(row.get("Date Added", "") or row.get("Date", "") or "").strip()
            if not raw_date:
                continue

            job_date = None
            for fmt in (
                "%Y-%m-%d %H:%M",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d",
                "%d-%m-%Y",
                "%m/%d/%Y",
                "%Y/%m/%d",
                "%d %b %Y",
                "%d %B %Y",
                "%d-%m-%Y %H:%M",
                "%d-%m-%Y %H:%M:%S",
                "%m/%d/%Y %H:%M",
                "%m/%d/%Y %H:%M:%S"
            ):
                try:
                    job_date = datetime.strptime(raw_date, fmt)
                    break
                except ValueError:
                    continue

            if job_date is None:
                print(f"Skipping job with unparsable date: {raw_date}")
                continue

            print(f"Parsed date for {company}: {job_date.date()} (cutoff {cutoff.date()})")
            if job_date.date() < cutoff.date():
                continue

            jobs.setdefault(company, set())
            jobs[company].add(link)

        self.job_cache = jobs
        print(f"Built job dict with {len(jobs)} companies")
        return jobs

    
    def populate_job_links_for_row(self, row_number):

        jobs = self.build_job_dictionary()

        #self.job_cache = jobs  # Cache the job dictionary for future use

        row = self.sheet.row_values(row_number)

        if len(row) < 4:
            return

        company = row[3].strip().lower()

        if not company:
            return

        if company not in jobs:
            print(f"No recent jobs found for {company}")
            return

        links = sorted(jobs[company])

        self.sheet.update_cell(
            row_number,
            6,
            "\n".join(links)
        )

        print(f"Updated job links for row {row_number}")
        return links

    def update_generated_message(

            self,

            row,

            message

    ):

        self.referral_sheet.update_cell(

            row,

            8,

            message

        )

    def find_generated_referral_by_company(self, company):

        rows = self.referral_sheet.get_all_values()

        if not rows:
            return None

        headers = [
            cell.strip().lower()
            for cell in rows[0]
        ]

        name_idx = headers.index("name")
        company_idx = headers.index("company")
        referral_idx = headers.index("referral text")
        status_idx = headers.index("status")

        for row in rows[1:]:

            if len(row) <= max(
                company_idx,
                referral_idx,
                status_idx
            ):
                continue

            row_company = row[company_idx].strip()

            status = row[status_idx].strip()

            referral = row[referral_idx].strip()

            if (
                row_company.lower()
                == company.strip().lower()
                and status == "REFERRAL_GENERATED"
                and referral
            ):

                return {
                    "name": row[name_idx].strip(),
                    "company": row_company,
                    "referral": referral
                }

        return None

    def update_status(self, row, status):

    # Status = column 5
        self.referral_sheet.update_cell(
            row,
            5,
            status
        )