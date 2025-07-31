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
from playwright.sync_api import sync_playwright

def scrape_martech():
    print("📡 Scraping MarTech.org with Playwright...")
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://martech.org/category/digital-asset-management/", timeout=60000)
        page.wait_for_timeout(3000)  # wait for JS content

        articles = page.locator("article").all()

        print(f"🧾 Found {len(articles)} article cards")

        for i, article in enumerate(articles[:10]):  # top 10
            try:
                title = article.locator("h2 a").first.inner_text(timeout=3000)
                url = article.locator("h2 a").first.get_attribute("href")
                date = article.locator("time").first.get_attribute("datetime")[:10]
                summary = article.locator("div.entry-excerpt, p").first.inner_text(timeout=2000)
                author = article.locator("span.author-name").first.inner_text(timeout=2000)

                row = [
                    title.strip(),
                    url,
                    date,
                    summary.strip(),
                    author.strip() if author else "",
                    "",  # Notes
                    "MarTech.org",
                    "Digital Asset Management",
                    "",  # Tags
                    ""   # AI Score placeholder
                ]
                results.append(row)
            except Exception as e:
                print(f"❌ Error parsing article {i}: {e}")
                continue

        browser.close()

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
