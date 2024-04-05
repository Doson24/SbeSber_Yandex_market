import re
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

LIST_VIEW = True


def detect_block(driver):
    if 'Ой' in driver.title:
        while True:
            print('-' * 20, 'На сайте Яндекс Маркета подтвердите, что вы не робот!', '-' * 20)

            try:
                driver.find_element(By.XPATH, '//*[@class="CheckboxCaptcha-Anchor"]/input').click()
            except:
                pass
            time.sleep(20)

            if 'Ой' not in driver.title:
                break


def refresh_site(func):
    def wrapper(driver, *args):
        while True:
            try:
                func(driver, *args)
                break
            except Exception as ex:
                print('[?]Refresh')
                driver.refresh()
                # func(*args, **kwargs)
                time.sleep(5)

    return wrapper


def lock_out_market_problem(driver):
    if driver.title == 'На Маркете проблемы':
        while True:
            if driver.title != 'На Маркете проблемы':
                break
            driver.refresh()
            time.sleep(5)


@refresh_site
def post_text_search(driver, text):
    detect_block(driver)
    lock_out_market_problem(driver)

    # driver.save_screenshot('ya_search.png')
    search = WebDriverWait(driver, 5).until(EC.presence_of_element_located(
        (By.ID, 'header-search')))
    search.clear()
    search.send_keys(text)
    # driver.implicitly_wait(1)
    time.sleep(1)
    search.send_keys(Keys.ENTER)
    # driver.implicitly_wait(1)
    time.sleep(1)

    detect_block(driver)
    lock_out_market_problem(driver)


def get_first_match(driver, xpath_pattern):
    # Первое совпадение в списке
    driver.implicitly_wait(1)
    one_card = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
        (By.XPATH, xpath_pattern)))
    url = one_card.get_attribute('href')
    # first_match = driver.find_element(By.XPATH, '//*[@data-autotest-id]/a')
    # first_match.click()
    # match_windows = driver.window_handles[-1]
    # driver.switch_to.window(match_windows)

    return url


def search_min_price_url(driver):
    detect_block(driver)
    lock_out_market_problem(driver)

    # Нажать сортировку по цене
    button_dprice = driver.find_element(By.XPATH, '//*[@data-autotest-id="dprice"]')
    button_dprice.click()
    # driver.implicitly_wait(1)
    time.sleep(1)
    # Предложения магазинов
    cards_xpath = '//*[@data-zone-name="snippetList"]/div'
    cards = WebDriverWait(driver, 60).until(EC.presence_of_all_elements_located(
        (By.XPATH, cards_xpath)))

    # data = {'name': [], 'price': [], 'urls': []}

    # for index in range(1, len(cards) + 1):
    index = 1
    name = WebDriverWait(driver, 30).until(EC.visibility_of_element_located(
        (By.XPATH, f'{cards_xpath}[{index}]//*[@data-zone-name="title"]'))).text
    el = WebDriverWait(driver, 30).until(EC.visibility_of_element_located(
        (By.XPATH, f'{cards_xpath}[{index}]//*[@data-zone-name="price"]/a')))
    price = el.text.encode('ascii', 'ignore').decode("utf-8")
    lenght_price = len(price.split('\n'))

    if lenght_price == 4:
        price = price.split('\n')[3]
    elif lenght_price == 5:
        price = price.split('\n')[4]
    elif lenght_price == 9:
        price = price.split('\n')[3]
    url = WebDriverWait(driver, 3).until(EC.presence_of_element_located((
        By.XPATH, f'{cards_xpath}[{index}]//*[@data-zone-name="price"]/a'))) \
        .get_attribute('href')
    #     data['name'].append(name)
    #     data['price'].append(int(price))
    #     data['urls'].append(url)
    # min_value = min(data['price'])
    # min_index = data['price'].index(min_value)
    # min_url = data['urls'][min_index]
    # min_name = data['name'][min_index]
    return price, url, name


def main(driver, text, old_flag: str, logger):
    start_url = driver.current_url
    post_text_search(driver, text)
    driver.implicitly_wait(1)

    global LIST_VIEW
    if LIST_VIEW:
        driver.find_element(By.XPATH, '//*[@name="viewType"]').click()
        driver.implicitly_wait(1)
        LIST_VIEW = False

    if old_flag == 'False':
        if start_url == driver.current_url:
            post_text_search(driver, text)

    if old_flag == 'True':
        # Если не отработала post_text_search
        while True:
            post_text_search(driver, text)
            if start_url != driver.current_url:
                break

    # xpath_pattern = '//div[@data-auto="SerpList"]/div[@data-apiary-widget-name][2]//a[@data-auto and @href]'
    # xpath_pattern = '//article[@data-autotest-id="product-snippet"]//h3[@data-auto="snippet-price-current"]'
    xpath_pattern = '//article//a[@data-auto]'
    try:
        url = get_first_match(driver, xpath_pattern)
    except:
        logger.error('Не найдено совпадений')
        detect_block(driver)
        lock_out_market_problem(driver)
        driver.save_screenshot('get_first_match.png')
        driver.refresh()
        url = get_first_match(driver, xpath_pattern)

    lock_out_market_problem(driver)
    detect_block(driver)
    if old_flag == 'False':
        try:
            # Все предложения
            all_offers = driver.find_element(By.XPATH, '//*[@data-index="1"]//*[@data-zone-name="more-prices"]/a').text
            if 'от' in all_offers:
                all_offers = all_offers.split('от ')[-1]
                min_price = all_offers.encode('ascii', 'ignore').decode("utf-8")
            else:
                price = driver.find_element(By.XPATH, '//*[@data-index="1"]//*[@data-auto="price-value"]').text
                min_price = price.encode('ascii', 'ignore').decode("utf-8")
        except NoSuchElementException:
            # Других предложений нет
            try:
                price = driver.find_element(By.XPATH, '//*[@data-index="1"]//*[@data-auto="price-value"]').text
                min_price = price.encode('ascii', 'ignore').decode("utf-8")
            except NoSuchElementException:
                # Оплата яндекс картой
                price_text = driver.find_element(By.XPATH, xpath_pattern + '//span/span').text

                pattern = r'\d{1,3}(?:\s\d{3})*'
                matches = re.findall(pattern, price_text)
                prices = [int(match.encode('ascii', 'ignore').decode("utf-8").replace(' ', '')) for match in matches]
                min_price = prices[0]
        name = driver.find_element(By.XPATH, xpath_pattern+'//h3').text
        min_url = url

    elif old_flag == 'True':
        driver.get(url)
        lock_out_market_problem(driver)
        detect_block(driver)
        try:
            # Все предложения
            url_all_offers = driver.find_element \
                (By.XPATH, '//*[@data-apiary-widget-name="@MarketNode/MorePricesLink"]//*[@href]') \
                # .get_attribute('href')

            # driver.get(url_all_offers)
            url_all_offers.click()
            lock_out_market_problem(driver)
            detect_block(driver)

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

            try:
                name = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                    (By.XPATH, '//*[@data-additional-zone="title"]'))).text
            except TimeoutException:
                detect_block(driver)
                name = None

    return min_price, min_url, name


if __name__ == '__main__':
    url = 'https://market.yandex.ru/'
    driver = init_webdriver(True)
    driver.get(url)

    text = 'Смартфон OnePlus 10T 16/256GB зелeный'
    print(text)
    print(main(driver, text))
