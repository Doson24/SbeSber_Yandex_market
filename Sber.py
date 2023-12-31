from driver import init_webdriver
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


@dataclass
class Card:
    name: str
    sber_url: str
    price: str
    bonus_percentage: str
    bonus_price: str
    yandex_price: str = 0
    yandex_url: str = ""
    # money: str
    date_created: str = datetime.today().strftime("%d-%m-%Y")

    def __str__(self):
        return f'{self.name} {self.price} {self.bonus_percentage} ' \
               # f'{self.yandex_price}'


def close_promo(driver: Chrome):
    """
    Закрыть всплывающие окно с промокодом
    :param driver:
    :return:
    """
    iframe = driver.find_element(By.ID, 'fl-728255')
    driver.switch_to.frame(iframe)
    driver.find_elements(By.XPATH, '//*[@class="widget__close"]')
    close = driver.find_element(By.XPATH, '//*[@class="widget__close"]')
    close.click()
    driver.switch_to.default_content()


@benchmark
def get_cards_category(driver_sber: Chrome, url: str, thanks_percentage: int):
    driver_sber.get(url)
    driver_sber.implicitly_wait(1)
    cards = WebDriverWait(driver_sber, 30).until(EC.presence_of_all_elements_located(
        (By.XPATH, '//*[@class="catalog-listing__items '
                   'catalog-listing__items_divider"]/div[@id]')))
    data = []
    for card in cards:
        money = WebDriverWait(card, 0.5).until(EC.presence_of_element_located(
            (By.CLASS_NAME, 'item-money'))).text
        money = money.split('\n')
        try:
            price = money[0]
            discount_percentage = money[1]
            if int(discount_percentage[:-1]) < thanks_percentage:
                continue
            price_discount = money[2]
        except IndexError:
            continue
        name = WebDriverWait(card, 0.5).until(EC.presence_of_element_located(
            (By.XPATH, './/*[@class="inner"]/div[@class="item-title"]'))).text
        link = WebDriverWait(card, 0.5).until(EC.presence_of_element_located(
            (By.TAG_NAME, 'a'))).get_attribute('href')

        # yandex_price, yandex_url = get_min_price(driver_ya, name)

        card = Card(name, link, price, discount_percentage, price_discount,
                    # yandex_price, yandex_url
                    )
        # card = Card(name.text, link, money)
        print(card)
        data.append(card)
    return data


def get_next_url(driver):
    url = WebDriverWait(driver, 30).until(EC.presence_of_element_located(
        (By.XPATH, '//*[@class="next"]/a[@href]'))) \
        .get_attribute('href')
    return url


def parse_url_filter(url):
    parsed_url = urlparse(url)
    return parsed_url.fragment


@benchmark
def main(url, thanks_percentage, headless=True):
    driver_sber = init_webdriver(headless)
    driver_sber.get(url)
    driver_sber.set_window_size(1920, 1080)
    # driver.implicitly_wait(1)

    # url_ya = 'https://market.yandex.ru/'
    # driver_ya = init_webdriver(headless)
    # driver_ya.get(url_ya)
    # driver_ya.set_window_size(1920, 1080)

    try:
        close_promo(driver_sber)
    except:
        pass
    filter = parse_url_filter(url)
    cycle = 0
    data = []
    while True:
        try:
            # cards = get_cards_category(driver_sber, driver_ya, url, thanks_percentage)
            cards = get_cards_category(driver_sber=driver_sber,
                                       url=url,
                                       thanks_percentage=thanks_percentage)
            data.extend(cards)
        except:
            driver_sber.refresh()
            # print(f'[-] Error parse page {cycle}')
            cards = []
        driver_sber.save_screenshot('get_cards_category.png')
        try:
            next_url = get_next_url(driver_sber)
        except TimeoutException:
            print(f'Страница №{cycle}')
            driver_sber.save_screenshot('get_next_url.png')
            break

        url = next_url + '#' + filter
        print('Количество товаров:', len(cards))
        cycle += 1
        print(f'Страница №{cycle}')

    data = pd.DataFrame(data)
    save_db(data,
            path='Sber.db',
            table_name='Sber',
            # print_column=['name', 'money']
            )


if __name__ == '__main__':
    url = str(input('Введите url адрес вместе с фильтрами: '))
    thanks_percentage = int(input("Введите мин % СберСпасибо: "))
    # url = 'https://megamarket.ru/catalog/smartfony-android/#?filters=%7B%221B3347144BD148AF9B0CE4AFF47710F7%22%3A%5B%221%22%5D%7D'
    # thanks_percentage = 35
    main(url, thanks_percentage, True)
