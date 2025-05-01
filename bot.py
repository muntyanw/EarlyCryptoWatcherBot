import os
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient, events

from twitter_scanner import scan_twitter
from scoring        import score_account

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

@client.on(events.NewMessage(pattern='/scan'))
async def handler_scan(event):
    user = event.sender_id
    logger.info('Получена команда /scan от %s', user)

    await event.reply('🔍 Запускаю сканирование Twitter…')
    try:
        accounts = scan_twitter()
        logger.info('scan_twitter вернул %d записей', len(accounts))
        good = [acc for acc in accounts if score_account(acc) >= 4]
        logger.info('После скоринга осталось %d перспективных аккаунтов', len(good))

        if not good:
            await event.reply('❌ Перспективные новые проекты не найдены.')
            return

        parts = []
        for acc in good:
            text = (
                f"🔸 @{acc['username']} (Score: {score_account(acc)})\n"
                f"{acc['profile_url']}\n{acc['bio']}"
            )
            parts.append(text)
        message = '\n\n'.join(parts)[:4000]

        await event.reply(message)
        logger.info('Отправлено сообщение с %d аккаунтами', len(good))

    except Exception as e:
        logger.exception('Ошибка при /scan:')
        await event.reply('⚠️ Произошла ошибка при сканировании.')

def main():
    logger.info('Запускаем EarlyCryptoWatcherBot (Telethon)')
    logger.info('EarlyCryptoWatcherBot (Telethon) слушает команды ...')
    client.run_until_disconnected()

if __name__ == '__main__':
    main()