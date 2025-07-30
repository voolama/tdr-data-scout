import requests
from bs4 import BeautifulSoup
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
import json
from datetime import datetime

# Google Sheets setup
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SHEET_ID = os.environ['GOOGLE_SHEET_ID']
SERVICE_ACCOUNT_INFO = json.loads(os.environ['GOOGLE_SERVICE_ACCOUNT_JSON'])
creds = service_account.Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
service = build('sheets', 'v4', credentials=creds)

# Scrape CMSWire
def scrape_cmswire():
    url = "https://www.cmswire.com/digital-asset-management/"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    articles = soup.select('.ArticleListingList li')[:5]  # Top 5 articles
    results = []

    for item in articles:
        title_tag = item.find('h2')
        title = title_tag.get_text(strip=True) if title_tag else "No title"
        link = "https://www.cmswire.com" + title_tag.find('a')['href'] if title_tag and title_tag.find('a') else "No link"
        date = item.find('time')
        date_text = date.get('datetime')[:10] if date else datetime.now().strftime('%Y-%m-%d')
        summary = item.find('p').text if item.find('p') else "No summary"
        
        row = [
            title,
            link,
            date_text,
            summary,
            "",  # Author (CMSWire often omits this on index pages)
            "",  # Notes
            "CMSWire",
            "Digital Asset Management",
            "",  # Tags
            ""   # AI Score placeholder
        ]
        results.append(row)
    
    return results

# Push to Google Sheet
def write_to_sheet(data, sheet_name="Research"):
    body = {
        'values': data
    }
    result = service.spreadsheets().values().append(
        spreadsheetId=SHEET_ID,
        range=f"{sheet_name}!A:J",
        valueInputOption="RAW",
        body=body
    ).execute()
    print(f"{result.get('updates').get('updatedCells')} cells appended.")

if __name__ == "__main__":
    print("Scraping CMSWire...")
    data = scrape_cmswire()
    write_to_sheet(data)
