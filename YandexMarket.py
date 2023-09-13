import time

from selenium.common import NoSuchElementException, TimeoutException

from driver import init_webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import Chrome
from dataclasses import dataclass, asdict
from urllib.parse import urlparse, urljoin
from benchmark import benchmark
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


def post_text_search(driver, text):
    detect_block(driver)
    # driver.save_screenshot('ya_search.png')
    search = WebDriverWait(driver, 30).until(EC.presence_of_element_located(
        (By.ID, 'header-search')))
    search.clear()
    search.send_keys(text)
    # driver.implicitly_wait(1)
    time.sleep(1)
    search.send_keys(Keys.ENTER)
    # driver.implicitly_wait(1)
    time.sleep(1)


def get_first_match(driver):
    # Первое совпадение в списке
    driver.implicitly_wait(1)
    one_card = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, '//*[@data-index="1"]')))
    url = one_card.find_element(By.XPATH, '//*[@data-autotest-id]/a').get_attribute('href')
    return url


def search_min_price_url(driver):
    lock_out_market_problem(driver)

    # Нажать сортировку по цене
    button_dprice = driver.find_element(By.XPATH, '//*[@data-autotest-id="dprice"]')
    button_dprice.click()
    # driver.implicitly_wait(1)
    time.sleep(1)
    # Предложения магазинов
    cards_xpath = '//*[@data-zone-name="snippetList"]/div'
    cards = WebDriverWait(driver, 30).until(EC.presence_of_all_elements_located(
        (By.XPATH, cards_xpath)))
    data = {'name': [], 'price': [], 'urls': []}
    for index in range(1, len(cards) + 1):
        name = driver.find_element(By.XPATH, f'{cards_xpath}[{index}]//*[@data-zone-name="title"]').text
        el = driver.find_element(By.XPATH, f'{cards_xpath}[{index}]//*[@data-zone-name="price"]/a')
        price = el.text.encode('ascii', 'ignore').decode("utf-8")
        if len(price.split('\n')) == 4:
            price = price.split('\n')[3]
        elif len(price.split('\n')) == 5:
            price = price.split('\n')[4]
        url = WebDriverWait(driver, 3).until(EC.presence_of_element_located((
            By.XPATH, f'{cards_xpath}[{index}]//*[@data-zone-name="price"]/a'))) \
            .get_attribute('href')
        data['name'].append(name)
        data['price'].append(int(price))
        data['urls'].append(url)
    min_value = min(data['price'])
    min_index = data['price'].index(min_value)
    min_url = data['urls'][min_index]
    min_name = data['name'][min_index]
    return min_value, min_url, min_name


def lock_out_market_problem(driver):
    if driver.title == 'На Маркете проблемы':
        while True:
            if driver.title != 'На Маркете проблемы':
                break
            driver.refresh()
            time.sleep(5)


def main(driver, text):
    detect_block(driver)

    start_url = driver.current_url
    post_text_search(driver, text)

    # Если не отработала post_text_search
    while True:
        post_text_search(driver, text)
        if start_url != driver.current_url:
            break

    detect_block(driver)
    try:
        url = get_first_match(driver)
    except:
        driver.save_screenshot('get_first_match.png')
        driver.refresh()
        url = get_first_match(driver)
    driver.get(url)

    try:
        # Все предложения
        url_all_offers = driver.find_element \
            (By.XPATH, '//*[@data-apiary-widget-name="@MarketNode/MorePricesLink"]//*[@href]') \
            .get_attribute('href')
        driver.get(url_all_offers)
        min_price, min_url, name = search_min_price_url(driver)
        return min_price, min_url, name
    except NoSuchElementException:
        # Других предложений нет
        min_url = url
        try:
            min_price = driver.find_elements(
                By.XPATH, '//*[@data-auto="price-value"]')[1] \
                .text.replace('\u2009', '')
        except IndexError:
            min_price = 'Нет в продаже'

        name = driver.find_element(By.XPATH, '//*[@data-additional-zone="title"]').text

        return min_price, min_url, name


def detect_block(driver):
    if driver.title == 'Ой!':
        while True:
            print('-' * 20, 'На сайте Яндекс Маркета подтвердите, что вы не робот!', '-' * 20)
            if driver.title != 'Ой!':
                break
            time.sleep(1)


if __name__ == '__main__':
    url = 'https://market.yandex.ru/'
    driver = init_webdriver(True)
    driver.get(url)

    text = 'Смартфон OnePlus 10T 16/256GB зелeный'
    print(text)
    print(main(driver, text))
