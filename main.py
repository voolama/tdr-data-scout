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

# Scrape Martech for DAM articles
def scrape_martech():
    print("📡 Scraping MarTech.org...")
    url = "https://martech.org/category/digital-asset-management/"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')

    articles = soup.select("article")[:10]  # Top 10 entries
    results = []

    for item in articles:
        try:
            title_tag = item.find("h2", class_="entry-title")
            title = title_tag.get_text(strip=True)
            link = title_tag.find("a")["href"]

            date_tag = item.find("time", class_="entry-date")
            date = date_tag["datetime"][:10] if date_tag else datetime.now().strftime('%Y-%m-%d')

            summary_tag = item.find("div", class_="entry-excerpt") or item.find("p")
            summary = summary_tag.get_text(strip=True) if summary_tag else "No summary available"

            author_tag = item.find("span", class_="author-name")
            author = author_tag.get_text(strip=True) if author_tag else ""

            row = [
                title,
                link,
                date,
                summary,
                author,
                "",  # Notes
                "MarTech.org",
                "Digital Asset Management",
                "",  # Tags
                ""   # AI Score placeholder
            ]
            results.append(row)

        except Exception as e:
            print(f"❌ Error parsing article: {e}")
            continue

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
    print("📡 Running TdR Data Scout: MarTech.org")
    data = scrape_martech()
    if data:
        write_to_sheet(data)
    else:
        print("⚠️ No data to write.")
