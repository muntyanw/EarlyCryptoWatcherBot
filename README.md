# EarlyCryptoWatcherBot

Telegram-бот для поиска новых криптоаккаунтов Twitter с потенциалом раннего проекта.


Запускается `bot.py` - процесс висит в памяти и ждет команды из телеграмма или  срабатывания по шедулеру

Логика работы программы:

настройки - файл .env

- по приходу команды /scan или срабатывания вызова из шедулера:
  1. ищутся живые зеркала нитера, на данный момент задан список из 25 ссылок (желательно добавлять и менять периодически) 
  2. формируется запрос на вывод твитеров по поисковому запросу, поисковый запрос формируется из FILTER_KEYWORDS + FILTER_FUNDS + SCORE_PLATFORMS + FILTER_AGE_TWEET_DAYS_MAX, т.е. ищутся твиты в текстах и био которых встречается хоть что то из этих списков и чтоб они не были старше указанного количества дней
  3. Полученные твиты и аккаунты проверяются на 
    FILTER_AGE_TWEET_DAYS_MAX - твит не стрше этих дней (уже учтено в запросе на вывод твитов - тут из принципа "не мешает")
    FILTER_ACCOUNT_AGE_MAX_DAYS - аккаунт не старше этих дней
    FILTER_TWEETS_MAX - максимальное кол-во твитов у аккаунта
    FILTER_FOLLOWERS_MAX - максимальное количество фоловеров у аккаунта

    - не удолетворяющие условию отметаются
    - при этом инфо об неудачных аккаунтах сохраняется в БД для того чтобы потом по ним не делать запрос на ниттер (чем реже тем лучше, спамить нельзя - забанят или придется платить)
    - при старте проверяются настройки программы с теми что были сохранены ранее, если настройки изменены инфо об неудачных аккаунтах удаляется, чтоб их перепроверяло соглано новым условиям ...


  4. оставшиеся твиты и аккаунты проходят скоринг согласно указанному алгоритму 
  - +2: если есть сайт
  - +2: найден что то из SCORE_PLATFORMS
  - +3: упоминается известный инвестор из SCORE_FAMOUS_INVESTORS
  - +3: трендовые ключевые слова (FILTER_KEYWORDS + FILTER_FUNDS + SCORE_PLATFORM) в bio/твитах

  
  с подсчетом баллов и неудолетворяющие (< SCORE_MIN) отметаются

  5. при получении команды /subscribe телеграмм аккаунт от которой пришла команда сохраняется в БД и на этот аккаунт будут отсылаться результаты команды /scan

  6. в настройках (файл .env) задается время в какой час и минуту в течении суток надо запускать сканирование -  например

  SHEDULER_HOUR=9
  SHEDULER_MINUTE=38
  TIMEZONE=Europe/Kyiv




  










