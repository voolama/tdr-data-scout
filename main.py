from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import json
import os
import datetime

# Load credentials from the GitHub Secret
SERVICE_ACCOUNT_INFO = json.loads(os.environ['GOOGLE_SERVICE_ACCOUNT_JSON'])
SPREADSHEET_ID = os.environ['GOOGLE_SHEET_ID']

# Authenticate
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
service = build('sheets', 'v4', credentials=creds)

# Select sheet and range
sheet = service.spreadsheets()

# Dummy test data (replace this with actual scraping logic later)
now = datetime.datetime.utcnow().strftime("%B %d, %Y %H:%M UTC")
values = [
    ["Reddit", "https://reddit.com/r/DAM", "Jul 29, 2025", "Reddit user reports new AI tagging feature from Brandfolder", "N/A", "Moderator", "N/A"]
]

body = {
    'values': values
}

# Write to the 'Research' tab
sheet.values().append(
    spreadsheetId=SPREADSHEET_ID,
    range="Research!A:G",
    valueInputOption="RAW",
    body=body
).execute()

print("✅ Data written to sheet.")
