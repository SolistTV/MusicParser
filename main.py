from src import Loader
from src import Tools
from bs4 import BeautifulSoup
import requests
import json

"""
Main end point.
"""

# TODO: Нужно реализовать класс обработчик с эндпоинтами для работы с урлами.
#   Определиться с формой возвращаемых значений и формировать соответствующие результаты.
#   По функционалу не реализована пажинация, ее можно выполнить в цикле передавая параметр page в урлу tracklist_url

DIR = "music/"  # директория для загрузки скачанных файлов
base_url = "https://zaycev.net"  # главная урла, с которой будем получать стартовые данные для доступа
playlist_url = "d9279fad-c23a-43da-ba32-41fb7dfa9494"  # id(hash) нужно получить с источника.
# Смотрим в запросы через devTools, вкладка Network, лучше через инкогнито

tracks_data_url = "https://zaycev.net/api/external/track/filezmeta"
limit = 3  # доступно 100

cookies = Loader.get_cookies(base_url)
print(cookies['user_id'])
playlist_url = "https://zaycev.net/api/external/playlist?globalId=" + cookies['user_id']

"""
урла для пажинации тут
"""
tracklist_url = ("https://zaycev.net/api/external/pages/index/top?page=1&limit="
                 + str(limit) + "&period=day&entity=track")

response = requests.get(tracklist_url)
tracks_data = json.loads(response.content)

play_url = "https://zaycev.net/api/external/track/play/d23cd9698875470a"

post = {
    "trackIds": tracks_data['trackIds'],
    "subscription": False,
}

response = requests.post(tracks_data_url, post)
streaming_data = json.loads(response.content)
for track_id, item_data, streaming_item in zip(tracks_data['trackIds'],
                                               tracks_data['tracksInfo'].items(),
                                               streaming_data['tracks']):
    track_info_url = "https://zaycev.net/api/external/track/play/" + streaming_item['streaming']
    response = requests.get(track_info_url)
    data = json.loads(response.content)
    track_name = Tools.escape_special_characters(item_data[1]['track'])
    print(track_name)

    name = DIR + track_name + ".mp3"
    Loader.load_file(data['url'], name)

print(json.dumps(tracks_data, indent=4, ensure_ascii=False))

exit()

# URL файла
url = "https://zaycev.limbo.zerocdn.com/37b775a45a3f97ceeec48e6213c1b892:2025041317/track/24999502.mp3"

# Локальный путь для сохранения файла
local_filename = DIR + "24999502.mp3"

Loader.load_file(url, local_filename)
