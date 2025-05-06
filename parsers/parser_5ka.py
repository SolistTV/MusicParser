import time

from src import config_5ka
from typing import Tuple

import json
import urllib.parse
import csv
import logging
import asyncio
from selenium import webdriver
from selenium_stealth import stealth
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.chrome.options import Options

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class Parser5ka:
    def __init__(self):
        self.base_url = config_5ka.BASE_URL

    async def run(self, search_phrase: str) -> None:
        logging.info('== Старт сбора данных ==')
        with open(config_5ka.RESULTS_FILE, "w", newline="", encoding="UTF-8") as file:
            file.truncate(0)
            writer = csv.writer(file)
            writer.writerow(["Артикул", "Наименование", "Цена"])

        # loop = asyncio.get_running_loop()
        driver = await self.__browser_init()
        offset = 0
        processing = True
        tasks = []
        while processing:
            tasks.append(asyncio.create_task(self.__get_data_from_source_by_phrase(driver, search_phrase, offset)))
            offset += config_5ka.LIMIT
            if len(tasks) == config_5ka.REQUESTS_LIMIT:
                tasks, processing = await self.__tasks_processing(tasks)
        else:
            if len(tasks) > 0:
                await self.__tasks_processing(tasks)
            logging.info('данные собраны')

        driver.close()
        driver.quit()

        logging.info('== Завершение сбора данных ==')

    @staticmethod
    async def __browser_init() -> webdriver.Chrome:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920x1080")
        options.add_argument('"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"')
        options.add_argument("--disable-blink-features=AutomationControlled")
        # без этого работает, но может пригодиться на некоторых ресурсах
        # options.add_argument(f"user-data-dir={main_config.USER_DIR}")
        loop = asyncio.get_running_loop()
        driver = await loop.run_in_executor(None, webdriver.Chrome, options)
        stealth(driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True)

        return driver

    async def __get_data_from_source_by_phrase(self, driver: webdriver.Chrome, phrase: str, offset: int) -> list:
        results = []
        encode_phrase = urllib.parse.quote(phrase)
        url = f"{config_5ka.SEARCH_URL}&q={encode_phrase}&limit={config_5ka.LIMIT}&offset={offset}"
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
            return results

        if len(content) == 0:
            logging.error('Не удалось найти блок с данными, изменился формат ответа')
            return results

        return self.__collect_data(str(content))

    def __collect_data(self, content: str) -> list:
        results = []
        data = json.loads(content)
        if len(data) == 0:
            logging.error('Не удалось получить данные из json')
            return results
        results = [result for item in data['products'] if (result := self.__collect_result(item))]
        return results

    @staticmethod
    def __collect_result(item: dict):
        article = item['plu'] or ''
        if article == '':
            return []

        name = item['name'] or ''
        if name == '':
            return []

        price = item['prices']['regular'] or ''
        if price == '':
            return []

        return [
            article,
            name,
            price,
        ]

    async def __tasks_processing(self, tasks) -> Tuple[list, bool]:
        processing = True
        try:
            current_data = await asyncio.gather(*tasks)
            with open(config_5ka.RESULTS_FILE, "a", encoding="UTF-8", newline='') as file:
                writer = csv.writer(file)
                [self.__save_item(writer, item) for result_items in current_data for item in result_items if item]

            if not current_data[-1]:
                processing = False
        except asyncio.exceptions.InvalidStateError:
            processing = False
        finally:
            tasks = []
            time.sleep(3)

        return tasks, processing

    @staticmethod
    def __save_item(writer, item) -> None:
        writer.writerow(item)


parser = Parser5ka()
asyncio.run(parser.run(config_5ka.PHRASE))
