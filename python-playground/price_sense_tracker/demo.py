from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time

DEALS_URL = "https://www.amazon.in/deals"  # or the regional Today's Deals URL
GRID = "div#grid-main-container"
DEAL_CARD_LINKS = "div#grid-main-container [data-testid='deal-card'] a[href]"  # deals card anchors

def scroll_until_stable(driver, selector, max_scrolls=12, pause=1.2):
    wait = WebDriverWait(driver, 15)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, GRID)))
    last = -1
    for _ in range(max_scrolls):
        elems = driver.find_elements(By.CSS_SELECTOR, selector)
        count = len(elems)
        if count == last:
            break
        last = count
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(pause)

def collect_deal_urls(driver):
    scroll_until_stable(driver, DEAL_CARD_LINKS)
    links = driver.find_elements(By.CSS_SELECTOR, DEAL_CARD_LINKS)
    urls = []
    seen = set()
    for a in links:
        href = a.get_attribute("href")
        if href and href.startswith("http") and href not in seen:
            urls.append(href)
            seen.add(href)
    return urls

def visit_each_product(driver, urls, max_items=None):
    wait = WebDriverWait(driver, 15)
    n = len(urls) if max_items is None else min(max_items, len(urls))
    for i in range(n):
        url = urls[i]
        driver.get(url)
        try:
            # Wait for a common product detail landmark
            wait.until(EC.presence_of_element_located((By.ID, "productTitle")))
        except TimeoutException:
            # Some deals open collections or different layouts; fall back to page load + title check
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        # Do any work needed here (scrape/click/etc.)
        # Optional: small pause between items
        time.sleep(1.0)

def run():
    driver = webdriver.Chrome()
    try:
        driver.get(DEALS_URL)
        urls = collect_deal_urls(driver)
        print(f"Collected {len(urls)} deal URLs")
        visit_each_product(driver, urls)  # set max_items=10 to limit
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
