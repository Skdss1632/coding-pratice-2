import time
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select

driver = webdriver.Edge()
driver.get("https://www.amazon.in/")
driver.maximize_window()
