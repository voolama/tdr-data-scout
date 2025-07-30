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
from playwright.sync_api import sync_playwright

def scrape_cmswire():
    print("📡 Using Playwright to scrape CMSWire...")
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.cmswire.com/digital-asset-management/", timeout=60000)
        page.wait_for_timeout(5000)  # wait for JS to render

        # Extract the articles
        articles = page.locator("li.ArticleListingItem").all()[:5]

        for article in articles:
            try:
                title = article.locator("h2").inner_text()
                link = article.locator("h2 a").get_attribute("href")
                full_link = f"https://www.cmswire.com{link}" if link and not link.startswith("http") else link
                summary = article.locator("p").inner_text()
                date_text = article.locator("time").get_attribute("datetime")[:10] if article.locator("time") else datetime.today().strftime('%Y-%m-%d')

                results.append([
                    title,
                    full_link,
                    date_text,
                    summary,
                    "",  # Author
                    "",  # Notes
                    "CMSWire",
                    "Digital Asset Management",
                    "",  # Tags
                    ""   # AI Score
                ])
            except Exception as e:
                print(f"❌ Error parsing article: {e}")
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
    print("📡 Scraping CMSWire...")
    try:
        scraped_data = scrape_cmswire()
        write_to_sheet(scraped_data)
    except Exception as err:
        print(f"❌ Scraper error: {err}")
