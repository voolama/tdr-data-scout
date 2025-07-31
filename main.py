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
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from datetime import datetime

def scrape_cmswire():
    print("📡 Using Playwright to scrape CMSWire...")
    results = []
    seen_links = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.cmswire.com/digital-asset-management/", timeout=60000)
        page.wait_for_timeout(6000)  # Let JS finish rendering

        cards = page.locator("article").all()
        print(f"🧾 Found {len(cards)} article cards")

        for i, card in enumerate(cards[:12]):  # Top 12 max
            try:
                # Skip sponsored or duplicated articles
                if "sponsored" in card.inner_html().lower():
                    continue

                title_el = card.locator("h3").nth(0)
                link_el = card.locator("a").nth(0)
                date_el = card.locator("time").nth(0)
                summary_el = card.locator("p").nth(0)

                title = title_el.text_content().strip() if title_el else "Untitled"
                link = link_el.get_attribute("href")
                if not link.startswith("http"):
                    link = "https://www.cmswire.com" + link

                if link in seen_links:
                    continue  # skip duplicates
                seen_links.add(link)

                date = date_el.get_attribute("datetime") if date_el else datetime.now().strftime('%Y-%m-%d')
                summary = summary_el.text_content().strip() if summary_el else "No summary"

                # Clean title
                for bad_word in ["Sponsored Article", "Feature24", "Digital Asset Management"]:
                    title = title.replace(bad_word, "").strip()

                row = [
                    title,
                    link,
                    date[:10],
                    summary,
                    "",  # Author
                    "",  # Notes
                    "CMSWire",
                    "Digital Asset Management",
                    "",  # Tags
                    ""   # AI Score
                ]
                results.append(row)

            except Exception as e:
                print(f"❌ Error parsing card {i}: {e}")
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
    print("📡 Scraping CMSWire...")
    try:
        scraped_data = scrape_cmswire()
        write_to_sheet(scraped_data)
    except Exception as err:
        print(f"❌ Scraper error: {err}")
