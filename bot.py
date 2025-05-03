import os
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient, events
from datetime import datetime
from twitter_scanner import scan_twitter
from scoring        import score_account
from mongo import save_subscriber, get_all_subscribers, save_user_good
import asyncio

load_dotenv()

from logger_config import setup_logger
logger = setup_logger(__name__)

import debugpy
debugpy.listen(("0.0.0.0", 5678))  # или ("localhost", 5678)
print("⏳ Waiting for debugger attach...")
debugpy.wait_for_client()

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
API_ID    = int(os.getenv('TELEGRAM_API_ID'))
API_HASH  = os.getenv('TELEGRAM_API_HASH')
SCORE_MIN = int(os.getenv('SCORE_MIN', 0))

logger.info('Инициализация TelegramClient...')
client = TelegramClient('ecwbot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# получим свои данные и залогируем
me = client.loop.run_until_complete(client.get_me())
logger.info('Успешный вход под @%s (id=%s)', me.username, me.id)

@client.on(events.NewMessage(pattern='/start'))
async def handler_start(event):
    user = event.sender_id
    logger.info('Получена команда /start от %s', user)
    await event.reply('👋 Добро пожаловать! Используйте /scan для поиска.')

@client.on(events.NewMessage(pattern='/subscribe'))
async def handler_subscribe(event):
    sender_id = event.sender_id
    logger.info('Получена команда /subscribe от %s', sender_id)
    save_subscriber(sender_id,{})
    await event.reply('✅ Вы подписаны на обновления.')


@client.on(events.NewMessage(pattern='/scan'))
async def handler_scan(event):
    user = event.sender_id
    logger.info('Получена команда /scan от %s', user)

    await event.reply('🔍 Запускаю сканирование Twitter…')
    try:
        tws = scan_twitter()
        if len(tws) == 0:
            await event.reply('❌ Перспективные новые проекты не найдены.')
            return
        
        logger.info('scan_twitter вернул %d записей', len(tws))
        await event.reply(f'scan_twitter вернул {len(tws)} записей')

        good = []
        for tw in tws:
            tw = score_account(tw)
            logger.info(f"Оценка @{tw['username']}: {tw['score']}")
            if tw['score'] >= SCORE_MIN:
                good.append(tw)
                save_user_good(tw["username"], tw)

        logger.info('После скоринга осталось %d перспективных аккаунтов', len(good))
        await event.reply(f'После скоринга осталось {len(good)} перспективных аккаунтов')

        if not good:
            await event.reply('❌ Перспективные новые проекты не найдены.')
            return

        parts = []
        for tw in good:
            text = (
                f"Проект: @{tw['username']} (создан {tw['created'].strftime('%d.%m.%Y %H:%M')})\n"
                f"Рейтинг: {tw['score']}/10\n"
                f"Bio: {tw['bio']}\n"
                f"Твитов: {tw['tweets_count']} | Подписчиков: {tw['followers_count']}\n"
                f"{'Ссылки: ' + ', '.join(tw['urls']) if len(tw.get('urls',[]))>0 else ''}\n\n"
            )
            parts.append(text)
        message = '\n\n'.join(parts)[:4000]

        await event.reply(message)
        
        await broadcast_to_subscribers(message)
        
        logger.info('Отправлено сообщение с %d аккаунтами', len(good))

    except Exception as e:
        logger.exception('Ошибка при /scan:')
        await event.reply('⚠️ Произошла ошибка при сканировании.')
 
async def broadcast_to_subscribers(message: str) -> None:
    """
    Асинхронно рассылает сообщение всем подписчикам.
    """
    subscribers = get_all_subscribers()
    
    # Собираем корутины в список
    tasks = [
        send_message_to_user(sub["telegram_id"], message)
        for sub in subscribers
    ]
    
    # Параллельно запускаем и ждём всех
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Логируем провалы
    for sub, res in zip(subscribers, results):
        if isinstance(res, Exception):
            print(f"Не удалось отправить {sub['telegram_id']}: {res}")

        
async def send_message_to_user(user_id: int, text: str):
    """
    Отправляет текстовое сообщение пользователю или чату по его user_id/chat_id.
    """
    try:
        await client.send_message(entity=user_id, message=text)
        logger.info(f"Сообщение успешно отправлено {user_id}: {text!r}")
    except Exception as e:
        logger.exception(f"Не удалось отправить сообщение {user_id}: {e}")


def main():
    logger.info('Запускаем EarlyCryptoWatcherBot (Telethon)')
    logger.info('EarlyCryptoWatcherBot (Telethon) слушает команды ...')
    client.run_until_disconnected()

if __name__ == '__main__':
    main()