import time
from selenium import webdriver
from chromedriver_py import binary_path
from bs4 import BeautifulSoup
from datetime import datetime
from itertools import combinations

from selenium.webdriver.support.wait import WebDriverWait

cities_codes_mapping = dict({
    'Kiev': 'iev',
    'Lviv': 'lwo',
    'Istanbul': 'ist'
})

def extract_ticket_price_for_date(driver):
    prices = driver.find_elements_by_class_name('calendar-day')
    print(prices)

# def flights_scrapper(event, context):
if __name__ == '__main__':
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1280x1696')
    chrome_options.add_argument('--user-data-dir=/tmp/user-data')
    chrome_options.add_argument('--hide-scrollbars')
    chrome_options.add_argument('--enable-logging')
    chrome_options.add_argument('--log-level=0')
    chrome_options.add_argument('--v=99')
    chrome_options.add_argument('--single-process')
    chrome_options.add_argument('--data-path=/tmp/data-path')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--homedir=/tmp')
    chrome_options.add_argument('--disk-cache-dir=/tmp/cache-dir')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument(
        'user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36')

    driver = webdriver.Chrome(executable_path=binary_path, options=chrome_options)

    start_url = "https://www.aviasales.ua/"
    # input_departure_class_name = "trip-duration__date-input"
    current_date_time = datetime.now()

    city_combinations = list(combinations(cities_codes_mapping, 2))

    response = driver.get(start_url)
    origin = driver.find_element_by_id("origin")
    destination = driver.find_element_by_id("destination")
    departure_date_input = driver.find_element_by_class_name("trip-duration__input-wrapper")
    for combination in city_combinations:
        origin.send_keys(combination[0])
        destination.send_keys(combination[1])
        departure_date_input.click()
        time.sleep(4)

        extract_ticket_price_for_date(driver)

        print(combination)

    print('response: ' + response)
