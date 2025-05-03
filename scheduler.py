import os, asyncio
from dotenv import load_dotenv
from telethon import TelegramClient

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from twitter_scanner import scan_twitter
from scoring        import score_account

load_dotenv()

from logger_config import setup_logger
logger = setup_logger(__name__)

BOT_TOKEN   = os.getenv('TELEGRAM_BOT_TOKEN')
API_ID      = int(os.getenv('TELEGRAM_API_ID'))
API_HASH    = os.getenv('TELEGRAM_API_HASH')
CHAT_ID     = int(os.getenv('TELEGRAM_CHAT_ID'))

logger.info('Инициализация клиента для планировщика...')
client = TelegramClient('ecwbot-sched', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

async def daily_task():
    logger.info('Запуск ежедневного задания: scan_twitter()')
    try:
        accounts = scan_twitter()
        logger.info('scan_twitter вернул %d записей', len(accounts))
        good = [acc for acc in accounts if score_account(acc) >= 4]
        logger.info('%d аккаунтов после фильтра и скоринга', len(good))

        if not good:
            text = 'Сегодня новых перспективных проектов нет.'
        else:
            texts = [
                f"🔸 @{acc['username']} (Score: {score_account(acc)})\n"
                #f"{acc['profile_url']}\n{acc['bio']}"
                for acc in good
            ]
            text = '\n\n'.join(texts)[:4000]

        await client.send_message(CHAT_ID, text)
        logger.info('Отправлено сообщение в чат %s', CHAT_ID)

    except Exception as e:
        logger.exception('Ошибка в ежедневном задании:')
        # можно уведомить админа или написать в лог

def main():
    sched = AsyncIOScheduler()
    # 06:00 UTC = 09:00 EET
    sched.add_job(lambda: asyncio.create_task(daily_task()),
                  'cron', hour=6, minute=0)
    sched.start()
    logger.info('Scheduler запущен, будет выполняться ежедневно в 06:00 UTC')
    client.run_until_disconnected()

if __name__ == '__main__':
    main()