import os
import random
import time
import logging
import requests
import mysql.connector
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core import driver
from enums import *
from utility import *

# ---------------- CONFIG ---------------- #
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
DB_NAME = os.getenv("MYSQL_DB")
STORE_ID = os.getenv("STORE_ID")

# ---------------- TELEGRAM ---------------- #
def send_telegram_message(message: str):
    if not BOT_TOKEN or not CHAT_ID:
        logging.warning("BOT_TOKEN or CHAT_ID not set. Skipping message.")
        return
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": message},
            timeout=10
        )
        if response.status_code == 200:
            logging.info("Telegram message sent successfully")
        else:
            logging.error(f"Failed to send Telegram message: {response.text}")
    except Exception as e:
        logging.error(f"Telegram send error: {e}")

# ---------------- DATABASE HELPERS ---------------- #
def ensure_database():
    conn = mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD
    )
    cur = conn.cursor()
    cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    conn.commit()
    cur.close()
    conn.close()


def get_connection():
    return mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=DB_NAME,
        autocommit = True
    )


def drop_database(db_name):
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD
        )
        cur = conn.cursor()
        cur.execute(f"DROP DATABASE IF EXISTS {db_name}")
        print(f"Database '{db_name}' dropped successfully!")
        cur.close()
        conn.close()
    except Exception as e:
        print("Error dropping database:", e)


def drop_table(table_name):
    """Drop a single table if it exists."""
    try:
        conn = get_connection()  # Connect to the DB
        cur = conn.cursor()
        cur.execute(f"DROP TABLE IF EXISTS {table_name}")
        print(f"Table '{table_name}' dropped successfully!")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error dropping table '{table_name}': {e}")



def init_db():
    ensure_database()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS product_urls (
            id INT AUTO_INCREMENT PRIMARY KEY,
            product_url TEXT NOT NULL,
            scraped MEDIUMINT DEFAULT 0,
            UNIQUE KEY (product_url(255))
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS product_details (
            id INT AUTO_INCREMENT PRIMARY KEY,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            product_name TEXT,
            current_price DECIMAL(10,2),
            discount_percentage VARCHAR(50),
            rating VARCHAR(50),
            product_url TEXT NOT NULL,
            deals_expired BOOLEAN DEFAULT FALSE,
            deal_posted BOOLEAN DEFAULT FALSE
        )
    """)
    conn.commit()
    cur.close()
    conn.close()


def store_product_urls(urls):
    if not urls:
        return
    conn = get_connection()
    cur = conn.cursor()
    for url in urls:
        try:
            cur.execute("INSERT IGNORE INTO product_urls (product_url) VALUES (%s)", (url,))
        except mysql.connector.IntegrityError:
            pass
    conn.commit()
    cur.close()
    conn.close()



# ---------------- SELENIUM ---------------- #
def make_browser():
    options = Options()
    options.add_experimental_option("detach", True)
    service = ChromeService(ChromeDriverManager().install())
    browser = webdriver.Chrome(service=service, options=options)
    browser.maximize_window()
    wait = WebDriverWait(browser, Delay.NORMAL.value)
    return browser, wait


# ---------------- SCRAPING ---------------- #
def test_scrape_product_details():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, product_url FROM product_urls WHERE scraped=0")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        print("No new URLs to scrape")
        return

    browser, wait = make_browser()
    conn = get_connection()
    cur = conn.cursor()
    for url_id, url in rows:
        try:
            browser.get(url)
        except WebDriverException:
            continue

        price_discount_widget = wait.until(
            EC.presence_of_element_located((By.ID, "corePriceDisplay_desktop_feature_div"))
        )
        product_name = product_name = get_product_detail(driver_or_element=browser, by=By.ID, locator="productTitle",
                                                         wait=wait)
        # Current Price
        current_price = get_product_detail(driver_or_element=price_discount_widget, by=By.CLASS_NAME,
                                           locator="a-price-whole", numeric=True)
        # Discount
        discount_percentage = get_product_detail(driver_or_element=price_discount_widget, by=By.TAG_NAME,
                                                 locator="span", index=1)
        # Rating
        rating = get_product_detail(driver_or_element=browser, by=By.ID, locator="acrPopover", wait=wait, numeric=True,
                                    split_index=0)

        # Persist
        cur.execute(
            """
            INSERT INTO product_details
            (timestamp, product_name, current_price, product_url, discount_percentage, rating)
            VALUES (NOW(), %s, %s, %s, %s, %s)
            """,
            (product_name, current_price, url, discount_percentage, rating),
        )
        cur.execute("UPDATE product_urls SET scraped=1 WHERE id=%s", (url_id,))
        # drop_table("product_urls")
    cur.close()
    conn.close()
    browser.quit()


def select_deal_type(deal_type: DealType):
    browser, wait = make_browser()
    if deal_type == DealType.TRENDING:
        trending_deals = browser.find_element(By.ID, "discount-bubble-trending-bubble")
        trending_deals.click()
    if deal_type == DealType.LIGHTNING:
        lightning_deals = browser.find_element(By.ID, "discount-bubble-deals-collection-lightning-deals")
        lightning_deals.click()

# ---------------- SCROLL & COLLECT URLs ---------------- #
def scroll_n_get_product_element(browser):
    wait = WebDriverWait(browser, 20)
    products_urls = set()
    products_grid = wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, '[data-testid="virtuoso-item-list"]')))
    while True:
        time.sleep(2)
        product_cards = products_grid.find_elements(By.CSS_SELECTOR, '[data-testid="product-card"]')
        for card in product_cards:
            try:
                url = card.find_element(By.TAG_NAME, "a").get_attribute("href")
                products_urls.add(url)
            except Exception:
                pass
        try:
            body_ele = browser.find_element(By.TAG_NAME, "body")
            for _ in range(5):
                body_ele.send_keys(Keys.ARROW_DOWN)
            spinner = browser.find_element(By.XPATH, "//div[contains(@class, 'a-spinner')]")
            if spinner.is_displayed():
                wait.until(EC.invisibility_of_element_located((By.XPATH, "//div[contains(@class, 'a-spinner')]")))
                continue
        except Exception:
            pass
        try:
            target_btn = browser.find_element(By.CSS_SELECTOR, '[data-testid="load-more-view-more-button"]')
            if target_btn.is_displayed():
                return list(products_urls)
        except Exception:
            pass


def format_deal_message(product_name, price, discount, rating, url):
    return f"""
🔥 Lowest Price Alert 🔥
🛒 {product_name}
💰 Price: ₹{price} ({discount} OFF)
⭐ Rating: {rating}
🔗 [Grab Deal]({url})
"""



def select_a_random_department(browser, wait):
    today_deals = wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Today's Deals")))
    today_deals.click()


# ---------------- MAIN ---------------- #
def main():
    init_db()
    browser, wait = make_browser()
    try:
        browser.get("https://www.amazon.in/")
        select_a_random_department(browser, wait)
        collected_urls = scroll_n_get_product_element(browser)
        print("Total URLs collected:", len(collected_urls))
    finally:
        browser.quit()

    store_product_urls(collected_urls)
    # scrape_product_details()

    # Drop DB at the end (optional)
    # drop_database(DB_NAME)


if __name__ == "__main__":
    main()
