import time
import random
import csv
import requests
import pandas as pd
import datetime
from dotenv import load_dotenv
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from utility import *
from selenium.webdriver.common.action_chains import ActionChains


# Load Telegram bot credentials from .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


# ---------------- TELEGRAM ---------------- #
def send_telegram_message(message: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=data)


# ---------------- SCRAPER ---------------- #
def get_price_amazon(product_url: str):
    """Extract product name and price from Amazon"""
    chrome_options = Options()

    # chrome_options.add_argument("--headless") # run without opening a window
    # chrome_options.add_argument("--disable-gpu")
    service = Service(ChromeDriverManager().install())
    chrome_options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    wait = WebDriverWait(driver, 10)
    driver.maximize_window()
    driver.get(product_url)
    time.sleep(3)  # wait for page load

    today_deals = driver.find_element(By.LINK_TEXT, "Today's Deals")
    today_deals.click()

    see_more = driver.find_element(By.LINK_TEXT, "See more")
    see_more.click()

    product_type = driver.find_element(By.CSS_SELECTOR, "div[role='radiogroup']")
    radio_spans = product_type.find_elements(By.TAG_NAME, "span")

    # pick a random span
    while True:
        random_span = random.choice(radio_spans)
        if random_span.text not in ["Software", "Video Games"]:
            random_span.click()
            break

    products_grid = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="virtuoso-item-list"]')))
    ActionChains(driver).move_to_element(products_grid).click().perform()

    # scroll to bottom
    products_links = scroll_until_button(driver=driver)

    print("products total--",len(products_links), products_links)

    product_name = driver.find_element(By.ID, "productTitle").text.strip()
    price_text = driver.find_element(By.CLASS_NAME, "a-price-whole").text
    current_price = int(price_text.replace(",", "").strip())

    return product_name, current_price


# ---------------- TRACKER ---------------- #
def track_multiple_products(input_csv="products.csv", history_csv="price_history.csv"):
    df = pd.read_csv(input_csv)
    print(df)

    for index, row in df.iterrows():
        product_url = row['url']
        target_price = int(row['target_price'])

        product_name, current_price = get_price_amazon(product_url)

        if current_price is None:
            print(f"❌ Failed to fetch price for {product_url}")
            continue

        print(f"🔎 {product_name} → Current Price: ₹{current_price}")

        # Save history in CSV
        with open(history_csv, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), product_name, current_price, product_url])

            msg = (
                f"🔥 Price Alert!\n\n"
                f"Product: {product_name}\n"
                f"Current Price: ₹{current_price}\n"
                f"Target Price: ₹{target_price}\n"
                f"Link: {product_url}"
            )
            send_telegram_message(msg)

        # Send alert if price drops
        # if current_price <= target_price:
        #
        #     print("✅ Alert sent to Telegram!")
        # else:
        #     print("📉 No alert, price is still higher.")


# ---------------- RUN LOOP ---------------- #
if __name__ == "__main__":
    # # User settings
    # interval_minutes = 1   # how often to check (change this)
    # # end_hour = 21          # stop at 9 PM (change this)
    #
    # print(f"📌 Price tracker started... running every {interval_minutes} min until {'none'}:00")
    #
    # while True:
    #     now = datetime.datetime.now()
    #
    #     # Stop if current time >= end time
    #     # if now.hour >= end_hour:
    #     #     print("🛑 End time reached. Stopping tracker.")
    #     #     break
    #
    #     # Run tracking
    #     print(f"\n⏰ Running check at {now.strftime('%H:%M:%S')}")
    track_multiple_products()
    #
    #     # Wait until next interval
    #     time.sleep(interval_minutes * 60)
