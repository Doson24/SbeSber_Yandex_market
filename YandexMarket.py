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
    driver.save_screenshot('ya_search.png')
    search = WebDriverWait(driver, 30).until(EC.presence_of_element_located(
        (By.ID, 'header-search')))
    search.send_keys(text)
    search.send_keys(Keys.ENTER)


def get_first_match(driver):
    # Первое совпадение в списке
    one_card = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.XPATH, '//*[@data-index="1"]')))
    url = one_card.find_element(By.XPATH, '//*[@data-autotest-id]/a').get_attribute('href')
    return url


def search_min_price(driver):
    # Предложения магазинов
    cards = WebDriverWait(driver, 30).until(EC.presence_of_all_elements_located(
        (By.XPATH, '//*[@data-zone-name="snippetList"]/div')))
    data = {'price': [], 'urls': []}
    for card in cards:
        el = card.find_element(By.XPATH, './/*[@data-zone-name="price"]/a')
        price = el.text.encode('ascii', 'ignore').decode("utf-8")
        if len(price.split('\n')) == 4:
            price = price.split('\n')[3]
        url = el.get_attribute('href')
        data['price'].append(int(price))
        data['urls'].append(url)
    min_value = min(data['price'])
    min_index = data['price'].index(min_value)
    min_url = data['urls'][min_index]
    return min_value, min_url


def main(driver, text):
    post_text_search(driver, text)
    url = get_first_match(driver)
    driver.get(url)

    # Все предложения
    url_all_offers = driver.find_element \
        (By.XPATH, '//*[@data-apiary-widget-name="@MarketNode/MorePricesLink"]//*[@href]') \
        .get_attribute('href')
    driver.get(url_all_offers)

    return search_min_price(driver)


if __name__ == '__main__':
    url = 'https://market.yandex.ru/'
    driver = init_webdriver(True)
    driver.get(url)

    text = 'Смартфон OnePlus 10T 16/256GB зелeный'
    print(main(driver, text))
