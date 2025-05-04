import os
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient, events
from twitter_scanner import command_scan
from mongo import save_subscriber, get_all_subscribers
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.executors.asyncio import AsyncIOExecutor
import pytz

load_dotenv()

from logger_config import setup_logger
logger = setup_logger(__name__)

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
API_ID    = int(os.getenv('TELEGRAM_API_ID'))
API_HASH  = os.getenv('TELEGRAM_API_HASH')
SHEDULER_HOUR  = os.getenv('SHEDULER_HOUR')
SHEDULER_MINUTE  = os.getenv('SHEDULER_MINUTE')
TIMEZONE  = os.getenv('TIMEZONE')

logger.info('Инициализация TelegramClient...')
client = TelegramClient('ecwbot', API_ID, API_HASH)

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
    await command_scan(client)

    
async def broadcast_to_subscribers(client: TelegramClient, message: str) -> None:
    """
    Асинхронно рассылает сообщение всем подписчикам.
    """
    subscribers = get_all_subscribers()
    
    # Собираем корутины в список
    tasks = [
        send_message_to_user(client, sub["telegram_id"], message)
        for sub in subscribers
    ]
    
    # Параллельно запускаем и ждём всех
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Логируем провалы
    for sub, res in zip(subscribers, results):
        if isinstance(res, Exception):
            print(f"Не удалось отправить {sub['telegram_id']}: {res}")

        
async def send_message_to_user(client, user_id: int, text: str):
    """
    Отправляет текстовое сообщение пользователю или чату по его user_id/chat_id.
    """
    try:
        await client.send_message(entity=user_id, message=text)
        logger.info(f"Сообщение успешно отправлено {user_id}: {text!r}")
    except Exception as e:
        logger.exception(f"Не удалось отправить сообщение {user_id}: {e}")


def main():
    logger.info('Запускаем bot…')
    client.start(bot_token=BOT_TOKEN)  
     # получим свои данные и залогируем
    me = client.loop.run_until_complete(client.get_me())
    logger.info('Успешный вход под @%s (id=%s)', me.username, me.id)
    
    # здесь Telethon инициализирует client.loop
    sched = AsyncIOScheduler(
        event_loop=client.loop,
        timezone=pytz.timezone(TIMEZONE),
        executors={'default': AsyncIOExecutor()}
    )
    sched.add_job(
        command_scan,                     # async def command_scan(client)
        'cron',
        hour=SHEDULER_HOUR,
        minute=SHEDULER_MINUTE,
        kwargs={'client': client}
    )
    sched.start()                                  # теперь найдёт client.loop и запустится
    logger.info(f'Scheduler запущен, будет выполняться ежедневно в {SHEDULER_HOUR}:{SHEDULER_MINUTE} UTC')

    client.run_until_disconnected()                # стартует цикл client.loop

if __name__ == '__main__':
    import debugpy
    debugpy.listen(("0.0.0.0", 5678))  # или ("localhost", 5678)
    print("⏳ Waiting for debugger attach...")
    debugpy.wait_for_client()

    main()