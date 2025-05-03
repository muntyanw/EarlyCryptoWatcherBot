import re
from typing import List

def contains_url(text: str) -> bool:
    # Регулярное выражение для поиска URL
    url_pattern = re.compile(
        r'(https?://[^\s]+)|(www\.[^\s]+)',
        re.IGNORECASE
    )
    return bool(url_pattern.search(text))

def extract_urls(text: str) -> List[str]:
    """
    Ищет в тексте все URL и возвращает их списком.
    """
    url_pattern = re.compile(
        r'(https?://[^\s]+)|(www\.[^\s]+)',
        re.IGNORECASE
    )
    return [match.group(0) for match in url_pattern.finditer(text)]


def parse_stat_number(text):
    """Преобразует строку '28,657' в int 28657"""
    return int(text.replace(',', '').strip()) if text else 0

def dicts_equal(d1: dict, d2: dict) -> bool:
    """
    Рекурсивно проверяет, что два словаря d1 и d2 равны:
    - у них одинаковый набор ключей
    - значения по каждому ключу одинаковы,
      при этом вложенные словари сравниваются рекурсивно
    """
    
    if not isinstance(d1, dict) or not isinstance(d2, dict):
        return False
    
    # Сравниваем наборы ключей
    if d1.keys() != d2.keys():
        return False

    for key in d1:
        v1, v2 = d1[key], d2[key]

        # Если оба значения — словари, спускаемся рекурсивно
        if isinstance(v1, dict) and isinstance(v2, dict):
            if not dicts_equal(v1, v2):
                return False
        else:
            # Обычное сравнение (работает для int, str, list, tuple и пр.)
            if v1 != v2:
                return False

    return True


