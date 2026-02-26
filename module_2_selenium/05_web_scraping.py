"""
╔══════════════════════════════════════════════════════════════════╗
║     MODULE 2 — LESSON 5: WEB SCRAPING WITH SELENIUM             ║
╚══════════════════════════════════════════════════════════════════╝

WEB SCRAPING = Extracting data from websites automatically

SELENIUM vs BEAUTIFULSOUP:
  Selenium  → Dynamic pages (JavaScript-rendered), login required
  BeautifulSoup → Static HTML, faster, less resource-heavy

SCRAPING PIPELINE:
  1. Navigate → page
  2. Wait     → content loads
  3. Extract  → find elements, get text/attributes
  4. Clean    → strip whitespace, parse types
  5. Store    → save to CSV/JSON/DB
  6. Paginate → go to next page, repeat
"""

import csv
import json
import time
import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup  # pip install beautifulsoup4


# ─── 1. DATA EXTRACTION PATTERNS ──────────────────────────────────────────────

def extraction_patterns():
    """Common patterns for extracting data from elements."""
    driver = None

    print("── DATA EXTRACTION PATTERNS ─────────────────────────────────")
    code = """
    # ── Text content
    element = driver.find_element(By.CSS_SELECTOR, ".product-title")
    text = element.text                        # visible text
    inner = element.get_attribute("innerHTML") # raw HTML inside
    outer = element.get_attribute("outerHTML") # element + its HTML

    # ── Attributes
    link = driver.find_element(By.TAG_NAME, "a")
    href  = link.get_attribute("href")
    src   = link.get_attribute("src")    # for images
    data  = link.get_attribute("data-id")  # custom data attributes
    style = link.get_attribute("style")

    # ── Extract list of items
    items = driver.find_elements(By.CSS_SELECTOR, ".product-card")
    products = []
    for item in items:
        products.append({
            "name":  item.find_element(By.CLASS_NAME, "name").text,
            "price": item.find_element(By.CLASS_NAME, "price").text,
            "url":   item.find_element(By.TAG_NAME, "a").get_attribute("href"),
            "img":   item.find_element(By.TAG_NAME, "img").get_attribute("src"),
        })

    # ── Tables
    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    table_data = []
    for row in rows:
        cells = row.find_elements(By.TAG_NAME, "td")
        table_data.append([cell.text for cell in cells])

    # ── Get headers
    headers = [th.text for th in driver.find_elements(By.CSS_SELECTOR, "table th")]
    # Combine headers with rows
    records = [dict(zip(headers, row)) for row in table_data]
    """
    print(code)


# ─── 2. USING BEAUTIFULSOUP WITH SELENIUM ────────────────────────────────────

def beautifulsoup_integration():
    """
    Combine Selenium (JS rendering) with BeautifulSoup (fast parsing).
    This is faster than using Selenium to find every element.
    """
    print("\n── BEAUTIFULSOUP + SELENIUM ─────────────────────────────────")
    code = """
    from bs4 import BeautifulSoup

    # Let Selenium load the dynamic page
    driver.get("https://example.com/products")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".product"))
    )

    # Get the fully-rendered HTML
    page_html = driver.page_source

    # Parse with BeautifulSoup (much faster than Selenium's find_element)
    soup = BeautifulSoup(page_html, "lxml")  # pip install lxml

    # Now use BS4's powerful selectors
    products = []
    for card in soup.select(".product-card"):
        products.append({
            "title":  card.select_one(".product-title").get_text(strip=True),
            "price":  card.select_one(".price").get_text(strip=True),
            "rating": card.select_one(".rating")["data-score"],
            "url":    card.select_one("a")["href"],
        })

    print(f"Extracted {len(products)} products")
    """
    print(code)


# ─── 3. PAGINATION ────────────────────────────────────────────────────────────

def pagination_patterns():
    """Navigate through multiple pages of results."""
    print("\n── PAGINATION PATTERNS ──────────────────────────────────────")

    pattern_next_btn = """
    # ── Pattern 1: Click "Next" button
    all_data = []
    page = 1

    while True:
        print(f"Scraping page {page}...")

        # Extract data from current page
        items = driver.find_elements(By.CSS_SELECTOR, ".result-item")
        for item in items:
            all_data.append(extract_item(item))

        # Try to find and click Next button
        try:
            next_btn = driver.find_element(
                By.XPATH, "//a[contains(@class,'next') or text()='Next']"
            )
            if not next_btn.is_enabled():
                break  # Last page reached
            next_btn.click()
            WebDriverWait(driver, 10).until(
                EC.staleness_of(items[0])  # Wait for page to reload
            )
            page += 1
        except NoSuchElementException:
            print("No more pages.")
            break
    """

    pattern_url = """
    # ── Pattern 2: URL-based pagination
    base_url = "https://example.com/products?page={}"
    all_data = []

    for page_num in range(1, 11):  # Pages 1-10
        driver.get(base_url.format(page_num))
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".product"))
        )

        items = driver.find_elements(By.CSS_SELECTOR, ".product")
        if not items:  # No results = we've gone past the last page
            break

        for item in items:
            all_data.append({...})

        time.sleep(1)  # Be polite to the server!
    """

    pattern_scroll = """
    # ── Pattern 3: Infinite scroll (load more as you scroll)
    all_data = []
    last_count = 0

    while True:
        # Scroll to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # Wait for new content to load

        items = driver.find_elements(By.CSS_SELECTOR, ".post")
        current_count = len(items)

        if current_count == last_count:
            break  # No new items loaded, we're at the end

        last_count = current_count
        print(f"Loaded {current_count} items...")

        if current_count >= 100:  # Safety limit
            break
    """

    print("Pattern 1 - Next button:", pattern_next_btn)
    print("Pattern 2 - URL pagination:", pattern_url)
    print("Pattern 3 - Infinite scroll:", pattern_scroll)


# ─── 4. DATA STORAGE ──────────────────────────────────────────────────────────

def data_storage_patterns():
    """Save scraped data in various formats."""
    print("\n── DATA STORAGE PATTERNS ────────────────────────────────────")
    code = '''
    import csv
    import json
    from pathlib import Path

    # Sample scraped data
    products = [
        {"name": "Laptop", "price": "$999", "stock": "In Stock"},
        {"name": "Mouse",  "price": "$29",  "stock": "Out of Stock"},
    ]

    # ── Save to CSV
    output_file = Path("output") / f"products_{datetime.date.today()}.csv"
    output_file.parent.mkdir(exist_ok=True)

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=products[0].keys())
        writer.writeheader()
        writer.writerows(products)
    print(f"Saved {len(products)} products to {output_file}")

    # ── Save to JSON
    json_file = output_file.with_suffix(".json")
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)

    # ── Append to existing CSV (for running bot multiple times)
    with open(output_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=products[0].keys())
        # Don't write header again when appending
        writer.writerows(new_products)

    # ── Save to Excel with pandas
    import pandas as pd
    df = pd.DataFrame(products)
    df.to_excel("products.xlsx", index=False)
    '''
    print(code)


# ─── 5. ANTI-SCRAPING EVASION ────────────────────────────────────────────────

def anti_scraping_techniques():
    """
    Legitimate techniques to avoid bot detection.
    Use only on sites you have permission to scrape.
    """
    print("\n── ANTI-DETECTION TECHNIQUES (for authorized scraping) ──────")
    code = """
    # ── 1. Random delays between requests (most important!)
    import random
    time.sleep(random.uniform(1.5, 3.5))  # Random 1.5-3.5 second delay

    # ── 2. Rotate User Agents
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    ]
    options.add_argument(f"user-agent={random.choice(user_agents)}")

    # ── 3. Remove webdriver fingerprint
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    # ── 4. Respect robots.txt (check before scraping!)
    import urllib.robotparser
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url("https://example.com/robots.txt")
    rp.read()
    can_scrape = rp.can_fetch("*", "https://example.com/products")
    print(f"Can scrape /products: {can_scrape}")

    # ── 5. Add realistic browser headers
    # (done via Selenium's browser options, not requests headers)

    # ── 6. Handle CAPTCHAs
    # Option A: Manual intervention (pause bot, human solves)
    # Option B: 2captcha or anti-captcha services (paid)
    # Option C: Use API instead (preferred!)
    """
    print(code)


# ─── 6. COMPLETE SCRAPER EXAMPLE ─────────────────────────────────────────────

COMPLETE_SCRAPER = '''
"""
COMPLETE SCRAPER: Books to Scrape (books.toscrape.com — legal practice site)
Extracts: title, price, rating, availability across all pages
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import csv, time, random
from pathlib import Path

RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}

def create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def scrape_page(soup) -> list[dict]:
    books = []
    for article in soup.select("article.product_pod"):
        title    = article.select_one("h3 a")["title"]
        price    = article.select_one(".price_color").text.strip()
        rating   = RATING_MAP.get(article.select_one(".star-rating")["class"][1], 0)
        in_stock = "In stock" in article.select_one(".availability").text
        url      = article.select_one("h3 a")["href"]
        books.append({
            "title": title, "price": price,
            "rating": rating, "in_stock": in_stock, "url": url
        })
    return books

def scrape_all_books(max_pages=5):
    driver = create_driver()
    all_books = []

    try:
        base_url = "https://books.toscrape.com/catalogue/page-{}.html"

        for page in range(1, max_pages + 1):
            driver.get(base_url.format(page))
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "article.product_pod"))
            )

            soup = BeautifulSoup(driver.page_source, "lxml")
            books = scrape_page(soup)
            all_books.extend(books)
            print(f"  Page {page}: {len(books)} books (total: {len(all_books)})")

            time.sleep(random.uniform(0.5, 1.5))  # Be polite!

    finally:
        driver.quit()

    return all_books

def save_books(books: list[dict], filename="books.csv"):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=books[0].keys())
        writer.writeheader()
        writer.writerows(books)
    print(f"Saved {len(books)} books to {filename}")

if __name__ == "__main__":
    books = scrape_all_books(max_pages=3)
    save_books(books, "/tmp/books.csv")
'''


# ─── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "█" * 60)
    print("  SELENIUM — LESSON 5: WEB SCRAPING")
    print("█" * 60)

    extraction_patterns()
    beautifulsoup_integration()
    pagination_patterns()
    data_storage_patterns()
    anti_scraping_techniques()

    print("\n── COMPLETE SCRAPER EXAMPLE ─────────────────────────────────")
    print(COMPLETE_SCRAPER)

    print("\n" + "─" * 55)
    print("  SCRAPING BEST PRACTICES:")
    print("  ► Check robots.txt before scraping")
    print("  ► Add delays between requests (1-3 seconds)")
    print("  ► Store raw data before processing")
    print("  ► Use BS4 for parsing, Selenium for rendering")
    print("  ► Handle pagination edge cases (empty pages)")
    print("─" * 55)
    print("  NEXT: python module_2_selenium/06_advanced_selenium.py")
