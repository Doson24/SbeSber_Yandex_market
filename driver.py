import os

from selenium.webdriver.chrome.options import Options
from selenium import webdriver
# !pip install webdriver-manager
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
# pip install undetected-chromedriver
import undetected_chromedriver as uc
from selenium.webdriver.chrome.service import Service as ChromeService
from chrome_driver_downloder import get_chromedriver_fp

import pickle


def save_cookies(driver, location):
    pickle.dump(driver.get_cookies(), open(location, "wb"))


def load_cookies(driver, location, url=None):
    # Проверить существует ли файл location
    if not os.path.exists(location):
        return False

    cookies = pickle.load(open(location, "rb"))
    driver.delete_all_cookies()
    # have to be on a page before you can add any cookies, any page - does not matter which
    driver.get("https://www.google.com" if url is None else url)
    for cookie in cookies:
        if 'expiry' in cookie:
            del cookie['expiry']
        driver.add_cookie(cookie)


def init_webdriver(headless=True):
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")  # Режим без интерфейса
    # chrome_options.add_argument('--start-fullscreen')
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("--disable-notifications")
    # стандартные аргументы для обхода защиты
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--no-sandbox")

    driver = uc.Chrome(
        # driver_executable_path=get_chromedriver_fp(),
        # driver_executable_path=os.getcwd() + r'\chromedriver.exe',
        # browser_executable_path=r'C:\install\chrome-win64\chrome.exe',
        # executable_path=ChromeDriverManager().install(),
        options=chrome_options,
        use_subprocess=False,
    )
    return driver
