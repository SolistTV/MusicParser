import json
import time
import urllib.parse
import csv
import logging

from selenium import webdriver
from selenium_stealth import stealth
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.chrome.options import Options
from concurrent.futures import ThreadPoolExecutor

from src import config_5ka


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

"""
Парсер продуктов 5ки по ключевой фразе
"""


class Parser5ka:
    def run(self) -> None:
        logging.info('== Старт сбора данных ==')
        self.__clear_results()
        self.__source_processing()
        logging.info('== Завершение сбора данных ==')

    @staticmethod
    def __clear_results() -> None:
        with open(config_5ka.RESULTS_FILE, "w", newline="", encoding="UTF-8") as file:
            file.truncate(0)
            writer = csv.writer(file)
            writer.writerow(["Артикул", "Наименование", "Цена"])

    @staticmethod
    def __create_link(phrase: str, offset: int) -> str:
        encode_phrase = urllib.parse.quote(phrase)
        return f"{config_5ka.SEARCH_URL}&q={encode_phrase}&limit={config_5ka.LIMIT}&offset={offset}"

    @staticmethod
    def __browser_init() -> webdriver.Chrome:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920x1080")
        options.add_argument('"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"')
        options.add_argument("--disable-blink-features=AutomationControlled")
        driver = webdriver.Chrome(options=options)
        stealth(driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True)

        return driver

    @staticmethod
    def __collect_item_data(item: dict) -> list[str]:
        item_data = []
        for field in ['plu', 'name']:
            value = item.get(field) or ''
            if value == '':
                return []

            item_data.append(value)

        price = item.get('prices').get('regular') or ''
        if price == '':
            return []

        item_data.append(price)
        return item_data

    @staticmethod
    def __save_item(writer: csv.writer, item: list[str]) -> None:
        writer.writerow(item)

    def __source_processing(self) -> None:
        offset = 0
        processing = True
        urls = []

        drivers = [self.__browser_init() for _ in range(config_5ka.REQUESTS_LIMIT)]
        while processing:
            urls.append(self.__create_link(config_5ka.PHRASE, offset))
            if len(urls) == config_5ka.REQUESTS_LIMIT:
                processing = self.__urls_processing(urls, drivers)
                urls = []
                logging.info('Принудительная задержка для избегания бана')
                time.sleep(3)
            offset += config_5ka.LIMIT
        else:
            if len(urls) > 0:
                self.__urls_processing(urls, drivers)
            logging.info('данные собраны')

        for driver in drivers:
            driver.close()
            driver.quit()

    def __urls_processing(self, urls: list, drivers: list[webdriver.Chrome]) -> bool:
        processing = True
        counter_urls = len(urls)
        with ThreadPoolExecutor(max_workers=counter_urls) as executor:
            futures = [
                executor.submit(self.__get_data_from_source_by_phrase, url, driver)
                for url, driver in zip(urls, drivers)
            ]

            with open(config_5ka.RESULTS_FILE, "a", encoding="UTF-8", newline='') as file:
                writer = csv.writer(file)
                for future in futures:
                    if len(future.result()) < config_5ka.LIMIT:
                        processing = False
                    [self.__save_item(writer, item) for item in future.result() if item]

        return processing

    def __get_data_from_source_by_phrase(self, url: str, driver: webdriver.Chrome) -> list[list]:
        logging.info(f"Обработка страницы: {url}")
        driver.get(url)
        try:
            element = WebDriverWait(driver, 10).until(
                ec.presence_of_element_located((By.XPATH, '//pre'))
            )

            content = element.text
        except Exception as ex:
            logging.error('Не удалось найти блок с данными, отвалился браузер')
            logging.error(ex)
            return []

        if len(content) == 0:
            logging.error('Не удалось найти блок с данными, изменился формат ответа')
            return []

        logging.info(f"Страница обработана: {url}")
        return self.__collect_data(str(content))

    def __collect_data(self, content: str) -> list[list]:
        results = []
        data = json.loads(content)
        if len(data) == 0:
            logging.error('Не удалось получить данные из json')
            return results

        results = [result for item in data.get('products') if (result := self.__collect_item_data(item))]
        return results


if __name__ == '__main__':
    parser = Parser5ka()
    parser.run()
