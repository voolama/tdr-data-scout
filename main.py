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

# Scrape CMSWire for DAM articles
def scrape_cmswire():
    url = "https://www.cmswire.com/digital-asset-management/"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    articles = soup.select('li.ArticleListingItem')[:5]  # Adjust if CMSWire changes its structure
    results = []

    for item in articles:
        title_tag = item.find('h2')
        if not title_tag:
            continue

        title = title_tag.get_text(strip=True)
        link_tag = title_tag.find('a')
        link = link_tag['href'] if link_tag else ''
        if not link.startswith("http"):
            link = f"https://www.cmswire.com{link}"

        date_tag = item.find('time')
        date_text = date_tag.get('datetime')[:10] if date_tag else datetime.today().strftime('%Y-%m-%d')

        summary_tag = item.find('p')
        summary = summary_tag.get_text(strip=True) if summary_tag else "No summary available."

        results.append([
            title,
            link,
            date_text,
            summary,
            "",  # Author
            "",  # Notes
            "CMSWire",  # Source
            "Digital Asset Management",  # Topic
            "",  # Tags
            ""   # AI Score
        ])
    return results

# Append rows to Google Sheet
def write_to_sheet(data, sheet_name="Research"):
    if not data:
        print("No data to write.")
        return

    try:
        body = {'values': data}
        result = service.spreadsheets().values().append(
            spreadsheetId=SHEET_ID,
            range=f"{sheet_name}!A:J",
            valueInputOption="RAW",
            body=body
        ).execute()
        print(f"✅ {result.get('updates').get('updatedCells')} cells written to Google Sheet.")
    except Exception as e:
        print(f"❌ Failed to write to sheet: {e}")

if __name__ == "__main__":
    print("📡 Scraping CMSWire...")
    try:
        scraped_data = scrape_cmswire()
        write_to_sheet(scraped_data)
    except Exception as err:
        print(f"❌ Scraper error: {err}")
