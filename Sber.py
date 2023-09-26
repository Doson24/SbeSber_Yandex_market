import multiprocessing
import time

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
    name_sber: str
    name_ya:str
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
    iframe = driver.find_element(By.ID, 'fl-728255')
    driver.switch_to.frame(iframe)
    driver.find_elements(By.XPATH, '//*[@class="widget__close"]')
    close = driver.find_element(By.XPATH, '//*[@class="widget__close"]')
    close.click()
    driver.switch_to.default_content()


@benchmark
def get_cards_category(driver_sber: Chrome, driver_ya, url: str, thanks_percentage: int):
    driver_sber.get(url)
    cards_path = '//*[@class="catalog-listing__items catalog-listing__items_divider"]/div[@id]'
    cards = WebDriverWait(driver_sber, 30).until(EC.presence_of_all_elements_located(
        (By.XPATH, cards_path)))
    driver_sber.implicitly_wait(1)
    data = []
    for index in range(1, len(cards)+1):
        money = WebDriverWait(driver_sber, 1).until(EC.presence_of_element_located(
            (By.XPATH, f'{cards_path}[{index}]//*[@class="item-money"]'))).text
        money = money.split('\n')
        price = money[0].replace(' ', '').replace('₽', '')
        try:
            discount_percentage = money[1]
            if int(discount_percentage[:-1]) < thanks_percentage:
                continue
            price_discount = money[2]
        except IndexError:
            discount_percentage = None
            price_discount = None

        name = WebDriverWait(driver_sber, 1).until(EC.presence_of_element_located(
            (By.XPATH, f'{cards_path}[{index}]//*[@class="inner"]/div[@class="item-title"]'))).text
        link = WebDriverWait(driver_sber, 1).until(EC.presence_of_element_located(
            (By.XPATH, f'{cards_path}[{index}]//a'))).get_attribute('href')

        # Работа яднекс маркета
        yandex_price, yandex_url, name_ya = get_min_price(driver_ya, name)
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
    detect_blocked(driver_sber)

    url_ya = 'https://market.yandex.ru/'
    driver_ya = init_webdriver(headless)
    driver_ya.get(url_ya)
    driver_ya.set_window_size(1920, 1080)

    try:
        close_promo(driver_sber)
    except:
        pass
    filter = parse_url_filter(url)
    cycle = 0
    data = []
    while True:
        # try:
            cards = get_cards_category(driver_sber=driver_sber,
                                       driver_ya=driver_ya,
                                       url=url,
                                       thanks_percentage=thanks_percentage)
            # cards = get_cards_category(driver_sber=driver_sber,
            #                            url=url,
            #                            thanks_percentage=thanks_percentage)
            # data.extend(cards)
        # except:
            # driver_sber.refresh()
            # # print(f'[-] Error parse page {cycle}')
            # cards = get_cards_category(driver_sber, driver_ya, url, thanks_percentage)
            # driver_sber.save_screenshot('get_cards_category.png')
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

            if len(cards) > 0:
                data = pd.DataFrame(cards)
                save_db(data,
                        path='Sber.db',
                        table_name='Sber',
                        # print_column=['name', 'money']
                        )


def detect_blocked(driver_sber):
    if driver_sber.title == 'Ой. Запросы с вашего устройства похожи на автоматически':
        print(f"{'-' * 20}Обранаружен блокировщик!!!{'-' * 20}\n"
              "[?]На сайте Введите код с картинки \n ")
        while True:
            time.sleep(1)
            if driver_sber.title != 'Ой. Запросы с вашего устройства похожи на автоматически':
                print("[+] Код с картинки успешно введен")
                break


if __name__ == '__main__':
    multiprocessing.freeze_support()

    url = str(input('Введите url адрес: '))
    thanks_percentage = int(input("Введите мин % СберСпасибо: "))
    # url = 'https://megamarket.ru/catalog/noutbuki/page-11/'
    # url = "https://megamarket.ru/catalog/igrovye-naushniki/page-7/"
    # thanks_percentage = 0
    print('-'*95)


    try:
        main(url, thanks_percentage, False)
        time.sleep(60*60*12)
    except Exception as e:
        print(e)
        print(e.args)
        time.sleep(60*5)
