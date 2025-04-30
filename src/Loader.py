import requests
import logging

"""Класс-помогатор для реализации конкретных запросов к источнику"""


def load_file(url: str, dest: str) -> None:
    logging.info('Скачивание файла ' + url)
    with requests.get(url, stream=True) as response:
        response.raise_for_status()
        with open(dest, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)

    logging.info('Файл сохранен ' + dest)


def get_cookies(url: str):
    # Отправка запроса
    response = requests.get(url)
    # Получение cookies
    return response.cookies
