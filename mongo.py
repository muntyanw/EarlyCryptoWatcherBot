from pymongo import MongoClient
import os
from pymongo.errors import PyMongoError

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
# 1) Подключаемся (без аутентификации)
client = MongoClient(MONGO_URI)

# Если включена авторизация:
# client = MongoClient("mongodb://admin:ваш_пароль@localhost:27017/admin")

db = client["twitter"]
coll_fault_usernames = db["fault_usernames"]
coll_subscribes = db["subscribes"]
coll_settings = db["settings"]

coll_fault_usernames.create_index("username", unique=True)
coll_subscribes.create_index("telegram_id", unique=True)

def save_user_fault(username: str, info: dict):
    """
    Сохраняет или обновляет документ по ключу username.
    Если документа не было — вставит новый, иначе обновит поля.
    """
    # Мы используем поле username как уникальный идентификатор
    coll_fault_usernames.update_one(
        {"username": username},           # фильтр поиска
        {"$set": info},                   # что обновляем / вставляем
        upsert=True                       # создать, если не найдено
    )
    
def get_fault_user(username: str) -> dict | None:
    """
    Возвращает словарь с данными пользователя или None, если не найден.
    """
    doc = coll_fault_usernames.find_one(
        {"username": username},   # ищем по полю username
        {"_id": 0}                # не возвращать служебное поле _id
    )
    return doc

def remove_all_fault_users() -> int:
    """
    Удаляет все документы из указанной коллекции.
    Возвращает количество удалённых документов.
    """
    try:
        result = coll_fault_usernames.delete_many({})
        return result.deleted_count
    except PyMongoError as e:
        return 0

def save_subscriber(telegram_id: int, info: dict) -> bool:
    """
    Сохраняет или обновляет подписчика с telegram_id.
    info — любой словарь (например, {'username': ..., 'joined': ..., ...}).
    Возвращает True при успехе, False при ошибке.
    """
    try:
        coll_subscribes.update_one(
            {"telegram_id": telegram_id},
            {"$set": info},
            upsert=True
        )
        return True
    except PyMongoError as e:
        # здесь можно логировать e
        return False

def get_subscriber(telegram_id: int) -> dict | None:
    """
    Возвращает документ подписчика по telegram_id или None, если нет.
    """
    return coll_subscribes.find_one({"telegram_id": telegram_id}, {"_id": 0})

def get_all_subscribers() -> list[dict]:
    """
    Возвращает список всех подписчиков без поля _id.
    """
    return list(coll_subscribes.find({}, {"_id": 0}))

def delete_subscriber(telegram_id: int) -> bool:
    """
    Удаляет подписчика по telegram_id.
    Возвращает True, если удалён (deleted_count == 1), иначе False.
    """
    result = coll_subscribes.delete_one({"telegram_id": telegram_id})
    return result.deleted_count == 1

def save_settings(key: str, settings: dict) -> bool:
    """
    Сохраняет или обновляет настройки.
    Если документа не было — вставит новый, иначе обновит поля.
    """
    # Мы используем поле username как уникальный идентификатор
    coll_settings.update_one(
        {"key": key},           # фильтр поиска
        {"$set": settings},                   # что обновляем / вставляем
        upsert=True                       # создать, если не найдено
    )
    
def get_settings(key: str) -> dict | None:
    """
    Возвращает словарь с settings.
    """
    doc = coll_settings.find_one(
        {"key": key},
        {"_id": 0}
    )
    return doc
    

