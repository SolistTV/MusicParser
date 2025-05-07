import os
from src import main_config

PHRASE = 'Средство для мытья посуды'
BASE_URL = 'https://5ka.ru'
LIMIT = 30  # лимит можно поставить 1000 и собрать все данные за 1 запрос
REQUESTS_LIMIT = 3
SEARCH_URL = 'https://5d.5ka.ru/api/catalog/v3/stores/Y232/search?mode=delivery&include_restrict=true'
RESULTS_FILE = os.path.join(main_config.ROOT, 'results', '5ka.csv')
