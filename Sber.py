import multiprocessing
import time
from undetectable import Undectable
from driver import init_webdriver, load_cookies, save_cookies
from selenium.webdriver.common.by import By
from datetime import datetime
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import Chrome
from dataclasses import dataclass, asdict
from urllib.parse import urlparse, urljoin
from benchmark import benchmark
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
import pandas as pd
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from save_DB import save_db
from YandexMarket import main as get_min_price
import configparser
from loguru import logger

config = configparser.ConfigParser()  # создаём объекта парсера
config.read("settings.ini", encoding='utf-8')  # читаем конфиг

old_flag = config['Yandex']['OLD_VERSION']
WAIT_COUNTRY = int(config['SBER']['WAIT_FOR_COUNTRY'])

logger.add("file.log", format="{time} {level} {message}", level="INFO")


@dataclass
class Card:
    name_sber: str
    name_ya: str
    price_sber: str
    price_ya: str
    bonus_percentage: str
    bonus_price: str
    sber_url: str
    yandex_url: str
    # money: str
    date_created: str = datetime.today().strftime("%d.%m.%Y")

    def __str__(self):
        return f'{self.name_sber} {self.price_sber} {self.bonus_percentage} ' \
               f'{self.price_ya}'


def close_promo(driver: Chrome):
    """
    Закрыть всплывающие окно с промокодом
    :param driver:
    :return:
    """
    logger.info("Attempting to close promo")
    try:
        iframe = driver.find_element(By.ID, 'fl-728255')
        driver.switch_to.frame(iframe)
        driver.find_elements(By.XPATH, '//*[@class="widget__close"]')
        close = driver.find_element(By.XPATH, '//*[@class="widget__close"]')
        close.click()
        driver.switch_to.default_content()
        logger.info("Promo closed successfully")
    except Exception as e:
        logger.error(f"Window promo not found")


@benchmark
def get_cards_category(driver_sber: Chrome, driver_ya, url: str, thanks_percentage: int):
    logger.info("get_cards_category function started")
    driver_sber.get(url)
    cards_path = '//*[contains(@class, "catalog-item ")]'
    cards = WebDriverWait(driver_sber, 15).until(EC.presence_of_all_elements_located(
        (By.XPATH, cards_path)))
    driver_sber.implicitly_wait(1)
    data = []
    for index in range(1, len(cards) + 1):
        try:
            money = WebDriverWait(driver_sber, 1).until(EC.presence_of_element_located(
                (By.XPATH, f'{cards_path}[{index}]//*[@class="item-money"]'))).text
            try:
                money = money.split('\n')
            except:
                pass
            price = money[0].replace(' ', '').replace('₽', '')
        except:
            logger.warning('Ошибка при получении данных Price')
            continue
        try:
            discount_percentage = money[1]
            if int(discount_percentage[:-1]) < thanks_percentage:
                continue
            price_discount = money[2]
        except IndexError:
            discount_percentage = None
            price_discount = None
            continue

        try:
            name = WebDriverWait(driver_sber, 1).until(EC.presence_of_element_located(
                (By.XPATH, f'{cards_path}[{index}]//*[@class="inner"]/div[@class="item-title"]'))).text
            link = WebDriverWait(driver_sber, 1).until(EC.presence_of_element_located(
                (By.XPATH, f'{cards_path}[{index}]//a'))).get_attribute('href')
        except:
            logger.error('Ошибка при получении данных Name, link')
            continue

        # Работа яднекс маркета
        try:
            yandex_price, yandex_url, name_ya = get_min_price(driver_ya, name, old_flag, logger)
        except Exception as ex:
            logger.error(f'Ошибка при получении данных с Яндекс Маркета {ex}')
            yandex_price, yandex_url, name_ya = None, None, None
        # yandex_price, yandex_url, name_ya = '','', name

        card = Card(name_sber=name,
                    name_ya=name_ya,
                    sber_url=link,
                    price_sber=price,
                    bonus_percentage=discount_percentage,
                    bonus_price=price_discount,
                    price_ya=yandex_price,
                    yandex_url=yandex_url
                    )
        logger.info(f"Card created: {card}")
        data.append(card)
    logger.info("get_cards_category function ended")
    return data


def get_next_url(driver):
    logger.info("get_next_url function started")
    try:
        url = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
            (By.XPATH, '//*[@class="next"]/a[@href]'))) \
            .get_attribute('href')
        logger.info(f"Next URL retrieved: {url}")
    except Exception as e:
        logger.error(f"An error occurred while getting next URL: {e}")
        url = None
    return url


def parse_url_filter(url):
    parsed_url = urlparse(url)
    return "?" + parsed_url.query + '#' + parsed_url.fragment


@benchmark
def main(url, thanks_percentage, driver_sber=None, driver_ya=None, headless=True):
    logger.add("file.log", format="{time} {level} {message}", level="INFO")
    # refresh_flag = False
    driver_sber = init_webdriver(headless)
    driver_sber.get(url)
    driver_sber.set_window_size(1920, 1080)
    driver_sber.implicitly_wait(1)

    logger.info(f"Ожидание выбора региона (секунды): {WAIT_COUNTRY}")
    time.sleep(WAIT_COUNTRY)

    detect_blocked(driver_sber)

    url_ya = 'https://market.yandex.ru/'
    driver_ya = init_webdriver(headless)
    driver_ya.get(url_ya)
    driver_ya.set_window_size(1920, 1080)

    load_cookies(driver_sber, 'cookies_sber.pkl')
    load_cookies(driver_ya, 'cookies_ya.pkl')

    close_promo(driver_sber)

    try:
        filter = parse_url_filter(url)
    except Exception as ex:
        logger.error('Ошибка при выделения url фильтра')
        raise Exception(ex)

    cycle = 0
    data = []
    while True:
        try:
            cards = get_cards_category(driver_sber=driver_sber,
                                       driver_ya=driver_ya,
                                       url=url,
                                       thanks_percentage=thanks_percentage)
        except:
            logger.warning('[?] Обновление страницы')
            driver_sber.refresh()
            try:
                cards = get_cards_category(driver_sber=driver_sber,
                                           driver_ya=driver_ya,
                                           url=url,
                                           thanks_percentage=thanks_percentage)
            except Exception as ex:
                logger.error(f'Ошибка при получении данных товаров {ex}')
                cards = []
        try:
            next_url = get_next_url(driver_sber)
        except TimeoutException:
            logger.error(f'[-]Следующая ссылка не найдена')
            driver_sber.save_screenshot('get_next_url.png')
            break

        if next_url:
            if filter:
                url = next_url + filter
            else:
                url = next_url

        logger.info(f'Количество товаров: {len(cards)}')
        cycle += 1
        logger.info(f'Страница №{cycle}')

        save_cookies(driver_sber, 'cookies_sber.pkl')
        save_cookies(driver_ya, 'cookies_ya.pkl')
        logger.info('Cookies сохранены')

        if len(cards) > 0:
            data = pd.DataFrame(cards)
            save_db(data,
                    path='Sber.db',
                    table_name='Sber',
                    )


def detect_blocked(driver_sber):
    logger.info("detect_blocked function started")
    if driver_sber.title == 'Ой. Запросы с вашего устройства похожи на автоматически':
        logger.warning(f"{'-' * 20}Обранаружен блокировщик!!!{'-' * 20}\n"
                       "[?]На сайте Введите код с картинки \n ")
        driver_sber.save_screenshot('Block.png')
        while True:
            time.sleep(1)
            if driver_sber.title != 'Ой. Запросы с вашего устройства похожи на автоматически':
                logger.info("[+] Код с картинки успешно введен")
                break
    logger.info("detect_blocked function ended")


def init_driver(name_profile='Amazon 1.1 Windows Juan'):
    logger.info("init_driver function started")
    address = "127.0.0.1"  # Local API IP address (if you work from another PC on the same network or a port is open in the router settings, you can access the local API remotely and this address will need to be changed)
    port_from_settings_browser = '25325'  # Local API port (can be found in the program settings)
    chrome_driver_path = "chromedriver.exe"  # Path to chromedriver for v110

    logger.info(
        f"Initializing Undectable with address: {address}, port: {port_from_settings_browser}, and chrome driver path: {chrome_driver_path}")
    browser = Undectable(address, port_from_settings_browser, chrome_driver_path)
    profile_id = browser.get_id_by_name(name_profile)
    debug_port = browser.get_debug_port(profile_id)
    driver = browser.start_driver(debug_port)
    logger.info(f"Driver initialized with profile ID: {profile_id} and debug port: {debug_port}")
    logger.info("init_driver function ended")
    return driver, browser, profile_id


def use_undetecteble(url, thanks_percentage):
    logger.info("use_undetecteble function started")
    driver_sber, browser_sb, profile_id_sb = init_driver('Yandex 2.0')
    logger.info("Driver for Sber initialized")
    driver_ya, brower_ya, profile_id_ya = init_driver('Yandex 2.0 RU')
    logger.info("Driver for Yandex initialized")
    main(url, thanks_percentage, False, driver_sber=driver_sber, driver_ya=driver_ya, )

    logger.info("Sleeping for 60 seconds")
    time.sleep(60)
    browser_sb.stop_profile(profile_id_sb)
    logger.info("Profile for Sber stopped")
    brower_ya.stop_profile(profile_id_ya)
    logger.info("Profile for Yandex stopped")
    logger.info("use_undetecteble function ended")


if __name__ == '__main__':

    multiprocessing.freeze_support()
    # url = 'https://megamarket.ru/catalog/smartfony-android/#?filters=%7B%22EA7C286463713C534F6A892BFF2CE0D0%22%3A%7B%22min%22%3A128%7D%7D'
    url = str(input('Введите url адрес: '))
    thanks_percentage = int(input("Введите мин % СберСпасибо: "))
    logger.info(f"URL entered: {url}")
    logger.info(f"Minimum percentage entered: {thanks_percentage}")

    print('-' * 95)

    try:
        logger.info("Starting main function")
        main(url, thanks_percentage, headless=True)
        logger.info("Main function ended successfully")
        logger.info("Sleeping for 12 hours")
        time.sleep(60 * 60 * 12)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        logger.info("Sleeping for 12 hours")

        time.sleep(60 * 60 * 12)
