"""
╔══════════════════════════════════════════════════════════════════╗
║     PROJECT 1: PRODUCTION WEB SCRAPER BOT                       ║
╚══════════════════════════════════════════════════════════════════╝

TARGET: https://books.toscrape.com (legal practice site)

FEATURES:
  ✓ Multi-page scraping (all 50 pages)
  ✓ Category filtering
  ✓ Data cleaning & normalization
  ✓ Save to CSV and JSON
  ✓ Error handling & retry
  ✓ Rate limiting
  ✓ Progress reporting
  ✓ Structured logging
  ✓ Config from environment

RUN:
  python projects/project_1_web_scraper_bot.py
"""

import csv
import json
import logging
import time
import random
import datetime
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup


# ─── CONFIGURATION ────────────────────────────────────────────────────────────

@dataclass
class ScraperConfig:
    base_url: str = "https://books.toscrape.com"
    max_pages: int = 5          # Set to 50 for all pages
    headless: bool = True
    min_delay: float = 0.5
    max_delay: float = 1.5
    timeout: int = 15
    max_retries: int = 3
    output_dir: Path = Path("/tmp/books_scraper")
    min_rating: int = 0         # Filter: only books with rating >= N
    max_price: float = float("inf")  # Filter: only books under price N


# ─── DATA MODEL ───────────────────────────────────────────────────────────────

@dataclass
class Book:
    title: str
    price: float
    rating: int        # 1-5
    in_stock: bool
    category: str
    url: str
    scraped_at: str = ""

    def __post_init__(self):
        if not self.scraped_at:
            self.scraped_at = datetime.datetime.now().isoformat()

    def to_dict(self) -> dict:
        return asdict(self)


RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


# ─── SCRAPER CLASS ────────────────────────────────────────────────────────────

class BooksScraperBot:
    """
    Production-quality scraper for books.toscrape.com.
    Inherits architecture from Module 1 BaseBot pattern.
    """

    def __init__(self, config: ScraperConfig):
        self.config = config
        self.config.output_dir.mkdir(parents=True, exist_ok=True)

        # Logger
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%H:%M:%S"
        )
        self.logger = logging.getLogger("BooksScraperBot")

        self.driver: Optional[webdriver.Chrome] = None
        self.books: list[Book] = []
        self.stats = {
            "pages_scraped": 0,
            "books_found": 0,
            "books_filtered": 0,
            "errors": 0,
        }

    def _create_driver(self) -> webdriver.Chrome:
        """Create configured Chrome driver."""
        options = Options()
        if self.config.headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--window-size=1920,1080")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        )
        options.add_experimental_option("excludeSwitches", ["enable-automation"])

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        return driver

    def _wait_for_books(self):
        """Wait for book articles to be present."""
        wait = WebDriverWait(self.driver, self.config.timeout)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "article.product_pod")))

    def _parse_price(self, price_text: str) -> float:
        """Parse price string '£12.99' → 12.99"""
        try:
            return float(price_text.replace("£", "").replace("Â", "").strip())
        except ValueError:
            return 0.0

    def _scrape_page(self, page_html: str, category: str = "") -> list[Book]:
        """Parse a single page's HTML and extract books."""
        soup = BeautifulSoup(page_html, "lxml")
        books = []

        for article in soup.select("article.product_pod"):
            try:
                title_tag = article.select_one("h3 a")
                title    = title_tag["title"]
                price    = self._parse_price(article.select_one(".price_color").text)
                rating   = RATING_MAP.get(article.select_one(".star-rating")["class"][1], 0)
                in_stock = "In stock" in article.select_one(".availability").text
                rel_url  = title_tag["href"].replace("../", "")
                url      = f"{self.config.base_url}/catalogue/{rel_url}"

                book = Book(
                    title=title,
                    price=price,
                    rating=rating,
                    in_stock=in_stock,
                    category=category,
                    url=url,
                )
                books.append(book)
            except (KeyError, AttributeError, TypeError) as e:
                self.logger.warning(f"  Failed to parse book: {e}")
                self.stats["errors"] += 1

        return books

    def _apply_filters(self, books: list[Book]) -> list[Book]:
        """Apply configured filters."""
        filtered = [
            b for b in books
            if b.rating >= self.config.min_rating
            and b.price <= self.config.max_price
        ]
        removed = len(books) - len(filtered)
        if removed:
            self.stats["books_filtered"] += removed
        return filtered

    def _scrape_all_pages(self) -> list[Book]:
        """Scrape all pages with retry logic."""
        all_books = []
        base_catalogue_url = f"{self.config.base_url}/catalogue/page-{{}}.html"

        for page_num in range(1, self.config.max_pages + 1):
            url = base_catalogue_url.format(page_num)
            page_books = self._scrape_page_with_retry(url, page_num)

            if page_books is None:  # Failed after retries
                break

            if not page_books:  # Empty page = end of catalogue
                self.logger.info(f"  No books on page {page_num} — end of catalogue")
                break

            filtered = self._apply_filters(page_books)
            all_books.extend(filtered)

            self.stats["pages_scraped"] += 1
            self.stats["books_found"] += len(page_books)

            self.logger.info(
                f"  Page {page_num:2d}/{self.config.max_pages}: "
                f"{len(page_books)} books found, {len(filtered)} kept "
                f"(total: {len(all_books)})"
            )

            # Random polite delay
            if page_num < self.config.max_pages:
                delay = random.uniform(self.config.min_delay, self.config.max_delay)
                time.sleep(delay)

        return all_books

    def _scrape_page_with_retry(self, url: str, page_num: int) -> Optional[list[Book]]:
        """Scrape a single page with retry logic."""
        for attempt in range(1, self.config.max_retries + 1):
            try:
                self.driver.get(url)
                self._wait_for_books()
                books = self._scrape_page(self.driver.page_source)
                return books

            except TimeoutException:
                self.logger.warning(
                    f"  Page {page_num} timeout (attempt {attempt}/{self.config.max_retries})"
                )
                if attempt < self.config.max_retries:
                    time.sleep(2 ** attempt)

            except Exception as e:
                self.logger.error(f"  Page {page_num} error: {e}")
                self.stats["errors"] += 1
                if attempt < self.config.max_retries:
                    time.sleep(2 ** attempt)

        return None

    def _save_results(self) -> dict[str, Path]:
        """Save scraped books to CSV and JSON."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        # CSV
        csv_path = self.config.output_dir / f"books_{timestamp}.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            if self.books:
                writer = csv.DictWriter(f, fieldnames=self.books[0].to_dict().keys())
                writer.writeheader()
                writer.writerows(b.to_dict() for b in self.books)

        # JSON
        json_path = self.config.output_dir / f"books_{timestamp}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(
                {"scraped_at": timestamp, "count": len(self.books),
                 "books": [b.to_dict() for b in self.books]},
                f, indent=2
            )

        return {"csv": csv_path, "json": json_path}

    def _print_summary(self, output_paths: dict):
        """Print final run summary."""
        avg_price = sum(b.price for b in self.books) / max(len(self.books), 1)
        avg_rating = sum(b.rating for b in self.books) / max(len(self.books), 1)

        top_rated = sorted(self.books, key=lambda b: (-b.rating, b.price))[:5]
        cheapest = sorted(self.books, key=lambda b: b.price)[:5]

        print(f"\n{'═'*60}")
        print(f"  SCRAPER RESULTS — BooksToScrape.com")
        print(f"{'═'*60}")
        print(f"  Pages scraped  : {self.stats['pages_scraped']}")
        print(f"  Books found    : {self.stats['books_found']}")
        print(f"  Books kept     : {len(self.books)}")
        print(f"  Filtered out   : {self.stats['books_filtered']}")
        print(f"  Errors         : {self.stats['errors']}")
        print(f"  Avg price      : £{avg_price:.2f}")
        print(f"  Avg rating     : {avg_rating:.1f}/5")
        print(f"\n  TOP RATED BOOKS:")
        for book in top_rated:
            print(f"    {'★'*book.rating}{'☆'*(5-book.rating)} £{book.price:.2f} — {book.title[:45]}")
        print(f"\n  CHEAPEST BOOKS:")
        for book in cheapest:
            print(f"    £{book.price:.2f} — {book.title[:50]}")
        print(f"\n  OUTPUT FILES:")
        for fmt, path in output_paths.items():
            print(f"    {fmt.upper()}: {path}")
        print(f"{'═'*60}")

    def run(self) -> list[Book]:
        """Main entry point."""
        self.logger.info("=" * 50)
        self.logger.info("  BooksScraperBot STARTED")
        self.logger.info(f"  Target: {self.config.base_url}")
        self.logger.info(f"  Pages:  up to {self.config.max_pages}")
        self.logger.info("=" * 50)

        start = time.time()

        try:
            self.driver = self._create_driver()
            self.books = self._scrape_all_pages()

        except Exception as e:
            self.logger.critical(f"  BOT CRASHED: {e}")
            raise

        finally:
            if self.driver:
                self.driver.quit()
                self.logger.info("  Browser closed.")

        output_paths = self._save_results()
        self._print_summary(output_paths)

        elapsed = time.time() - start
        self.logger.info(f"  Completed in {elapsed:.1f}s")

        return self.books


# ─── MAIN ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    config = ScraperConfig(
        max_pages=3,         # Scrape 3 pages (60 books)
        headless=True,
        min_rating=3,        # Only 3+ star books
        max_price=50.0,      # Under £50
    )

    bot = BooksScraperBot(config)

    try:
        books = bot.run()
        print(f"\nDone! Scraped {len(books)} books.")
    except Exception as e:
        print(f"Bot failed: {e}")
