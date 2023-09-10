from selenium.webdriver.chrome.options import Options
from selenium import webdriver
# !pip install webdriver-manager
from webdriver_manager.chrome import ChromeDriverManager
# from fake_useragent import UserAgent
# pip install undetected-chromedriver
import undetected_chromedriver as uc
from selenium.webdriver.chrome.service import Service as ChromeService
from chrome_driver_downloder import get_chromedriver_fp


def init_webdriver(headless=True):
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")  # Режим без интерфейса
    # chrome_options.add_argument('--start-fullscreen')
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument("--log-level=3")

    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-crash-reporter")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-in-process-stack-traces")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--output=/dev/null")

    """
    Загрузка файлов в указаную директорию

    chrome_options.add_argument("download.default_directory=C:/install") # Возможно не работает
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": "C:\\Users\\user\\Desktop\\Projects\\Restate.ru\\data",
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing_for_trusted_sources_enabled": False,
        "safebrowsing.enabled": False
    })"""
    # в режиме headless без user-agent не загружает страницу

    """
    Fake user-agent

    ua = UserAgent()
    ua_random = ua.random
    chrome_options.add_argument(f"user-agent={ua_random}")
    """

    driver = uc.Chrome(driver_executable_path=get_chromedriver_fp(),
                       # executable_path=r'C:\install\chromedriver.exe',
                       # browser_executable_path=r'C:\install\chrome-win64\chrome.exe',
                       # executable_path=ChromeDriverManager(
                       #        latest_release_url='https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/116.0.5845.96/win64/chromedriver-win64.zip').install(),
                       options=chrome_options,
                       )
    return driver
