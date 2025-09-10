from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time



def scroll_until_button(driver):
    wait = WebDriverWait(driver, 20)
    products_links = set()
    products_grid = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="virtuoso-item-list"]')))
    while True:
        time.sleep(2)
        product_card = products_grid.find_elements(By.CSS_SELECTOR, '[data-testid="product-card"]')
        products_links.update(product_card)
        try:
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ARROW_DOWN)
            # 2. If loading spinner is visible, wait for it to disappear
            spinner = driver.find_element(By.XPATH, "//div[contains(@class, 'a-spinner')]")
            if spinner.is_displayed():
                print("⏳ Loading... waiting to finish")
                wait.until(EC.invisibility_of_element_located((By.XPATH, spinner)))
                continue  # stop scrolling while loading
        except:
            pass

        try:
            # ✅ Now wait for the special button
            target_btn = driver.find_element(By.CSS_SELECTOR, '[data-testid="load-more-view-more-button"]')
            if target_btn.is_displayed():
                print("✅ Target button is now visible!")
                # target_btn.click()
                return products_links
        except:
            pass




