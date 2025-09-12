from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def get_product_detail(driver_or_element, by, locator, wait=None, index=None, numeric=False, default=None, split_index=None):
    """
    Generic utility to safely extract text or numbers from Selenium elements.

    Parameters:
        driver_or_element: WebDriver or WebElement to search from.
        by: Selenium By strategy (By.ID, By.CLASS_NAME, etc.).
        locator: The locator string.
        wait: Optional WebDriverWait instance to wait for the element.
        index: Optional index if multiple elements are found.
        numeric: Convert text to int or float if True.
        default: Value to return if element not found or conversion fails.
        split_index: If set, split text by space and return text at this index before conversion.

    Returns:
        str, int, float, or default value.
    """
    try:
        # Locate element(s)
        if wait:
            element = wait.until(EC.presence_of_element_located((by, locator)))
        else:
            element = driver_or_element.find_element(by, locator)

        # If multiple elements, select by index
        if index is not None:
            elements = driver_or_element.find_elements(by, locator)
            element = elements[index] if len(elements) > index else None

        if element:
            text = element.text.strip()
            if split_index is not None:
                parts = text.split()
                text = parts[split_index] if len(parts) > split_index else text

            if numeric:
                text = text.replace(",", "")
                try:
                    return int(text)
                except ValueError:
                    try:
                        return float(text)
                    except ValueError:
                        return default
            return text
        return default
    except Exception:
        return default
