import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# Google Sheets setup
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
SERVICE_ACCOUNT_FILE = 'gcp_service_account.json'

# Authenticate and connect
creds = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=SCOPES
)
client = gspread.authorize(creds)

# Open the sheet
SPREADSHEET_NAME = "JobHunter_Applications"
SHEET = client.open(SPREADSHEET_NAME).worksheet("Applications")

def log_application(job_title, company, url, resume_path, cover_letter_path, status="Pending"):
    date_applied = datetime.now().strftime("%Y-%m-%d")
    row = [job_title, company, url, date_applied, resume_path, cover_letter_path, status]
    SHEET.append_row(row)
    print(f"[✅] Logged application for {job_title} at {company} to Google Sheets.")
