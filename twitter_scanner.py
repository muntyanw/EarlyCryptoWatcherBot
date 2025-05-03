import os
import time
import certifi
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from logger_config import setup_logger
from utils import parse_stat_number,dicts_equal
from mongo import save_user_fault,get_fault_user,get_settings,remove_all_fault_users,save_settings

# Ensure requests uses certifi's CA bundle for SSL verification
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

# Initialize logger for this module
logger = setup_logger(__name__)

headers = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    ),
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Referer': 'https://google.com',  # optional
    'Connection': 'keep-alive',
}

# List of known Nitter mirrors
ALL_NITTER_MIRRORS = [
    'https://nitter.privacydev.net',
    'https://nitter.aishiteiru.moe',
    'https://nitter.aosus.link',
    "https://nitter.poast.org",
    "https://nitter.pussthecat.org",
    "https://nitter.kavin.rocks",
    "https://nitter.moomoo.me",
    "https://nitter.42l.fr",
    "https://nitter.lunar.icu",
    "https://nitter.tiekoetter.com",
    "https://nitter.privacy.com.de",
    "https://nitter.fdn.fr",
    "https://nitter.1d4.us",
    "https://nitter.nixnet.services",
    "https://nitter.pek.li",
    "https://nitter.10qt.net",
    "https://nitter6.kabii.moe",
    "https://nitter.ahwx.org",
    "https://nitter.alt.biovictor.com",
    "https://nitter.anoxinon.de",
    "https://nitter.asmallr.tech",
    "https://nitter.batsense.net",
    "https://nitter.b.beene.org",
    "https://nitter.bierlefeld.com",
    "https://nitter.bird.froth.zone",
    "https://nitter.blahaj.land",
    "https://nitter.buntcomm.com",
    "https://nitter.cabletemple.net",
    "https://nitter.colibriste.org",
    "https://nitter.crabf.art",
    "https://nitter.eda.gay",
    "https://nitter.fullex.fr",
    "https://nitter.gl-pillet.fr",
    "https://nitter.gorb.lol",
    "https://nitter.grimneko.de",
    "https://nitter.jejik.nl",
    "https://nitter.leftic.club",
    "https://nitter.mint.lgbt",
    "https://nitter.moezx.cc",
    "https://nitter.my.id",
    "https://nitter.onion.love",
    "https://nitter.plutonic.tk",
    "https://nitter.schleuss.online",
    "https://nitter.shinonomelaboratory.com",
    "https://nitter.teamqq.de",
    "https://nitter.thekitten.space",
    "https://nitter.wisq.net",
    "https://nitter.zebes.info"
]

FILTER_FUNDS = os.getenv('FILTER_FUNDS', '').lower().split(',')
FILTER_KEYWORDS = os.getenv('FILTER_KEYWORDS', '').lower().split(',')
SCORE_FAMOUS_INVESTORS = os.getenv('SCORE_FAMOUS_INVESTORS', '').lower().split(',')
FILTER_ACCOUNT_AGE_MAX_DAYS = int(os.getenv('FILTER_ACCOUNT_AGE_MAX_DAYS'))
FILTER_TWEETS_MAX = int(os.getenv('FILTER_TWEETS_MAX'))
FILTER_FOLLOWERS_MAX = int(os.getenv('FILTER_FOLLOWERS_MAX'))
FILTER_AGE_TWEET_DAYS_MAX = int(os.getenv('FILTER_AGE_TWEET_DAYS_MAX'))
PAUSE_BETWEEN_MESSAGES = int(os.getenv('PAUSE_BETWEEN_MESSAGES'))
FILTER_AGE_TWEET_DAYS_MAX = int(os.getenv('FILTER_AGE_TWEET_DAYS_MAX'))

current_settings = {
    "FILTER_FUNDS": FILTER_FUNDS,
    "FILTER_KEYWORDS": FILTER_KEYWORDS,
    "SCORE_FAMOUS_INVESTORS": SCORE_FAMOUS_INVESTORS,
    "FILTER_ACCOUNT_AGE_MAX_DAYS": FILTER_ACCOUNT_AGE_MAX_DAYS,
    "FILTER_TWEETS_MAX": FILTER_TWEETS_MAX,
    "FILTER_FOLLOWERS_MAX": FILTER_FOLLOWERS_MAX,
    "FILTER_AGE_TWEET_DAYS_MAX": FILTER_AGE_TWEET_DAYS_MAX,
    "PAUSE_BETWEEN_MESSAGES": PAUSE_BETWEEN_MESSAGES,
    "FILTER_AGE_TWEET_DAYS_MAX": FILTER_AGE_TWEET_DAYS_MAX
}

current_settings_bd = get_settings("current")

if not dicts_equal(current_settings, current_settings_bd):
    remove_all_fault_users()
    save_settings("current", current_settings)

# Cache of working mirrors
working_mirrors_cache = []

def get_working_mirrors(timeout=5):
    global working_mirrors_cache
    if working_mirrors_cache:
        return working_mirrors_cache

    logger.info("Проверка доступных зеркал Nitter...")
    test_query = "crypto"
    encoded = requests.utils.quote(test_query)

    for mirror in ALL_NITTER_MIRRORS:
        url = f"{mirror.rstrip('/')}/search?f=tweets&q={encoded}"
        try:
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=timeout)
            if r.status_code == 200 and '<div class="tweet-content media-body"' in r.text:
                logger.info(f"Рабочее зеркало: {mirror}")
                working_mirrors_cache.append(mirror)
        except Exception as e:
            logger.warning(f"Ошибка при проверке зеркала {mirror}: {e}")

    if not working_mirrors_cache:
        logger.error("Нет рабочих зеркал Nitter. Все зеркала недоступны или заблокированы.")
    return working_mirrors_cache

def fetch_profile_info(username, mirrors):
    for base in mirrors:
        url = f"{base}/{username.strip()}"
        logger.info(f"fetch_profile_info: Trying {url}")
        try:
            resp = requests.get(url, headers=headers, timeout=10, verify=False)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')

            # bio
            bio_el = soup.select_one('div.profile-bio p')
            bio = bio_el.get_text(strip=True) if bio_el else ''

            # created date (joined)
            date_el = soup.select_one('div.profile-joindate span[title]')
            created = None
            if date_el and date_el.has_attr('title'):
                try:
                    created = datetime.strptime(date_el['title'], '%I:%M %p - %d %b %Y')
                except ValueError:
                    created = None

            # tweets count
            tweet_stat_el = soup.select_one('li.posts span.profile-stat-num')
            tweets_count = parse_stat_number(tweet_stat_el.text) if tweet_stat_el else 0
            
            followers_el = soup.select_one('li.following span.profile-stat-num')
            followers_count = parse_stat_number(followers_el.text) if followers_el else 0

            logger.info(f"fetch_profile_info: bio='{bio[:30]}...', created={created}, tweets_count={tweets_count}")
            return {
                'bio': bio,
                'created': created,
                'tweets_count': tweets_count,
                'followers_count': followers_count,
            }

        except Exception as e:
            logger.warning(f"fetch_profile_info: Error on {base}: {e}")
            time.sleep(1)
            continue

    logger.error("fetch_profile_info: All mirrors failed")
    return {}

def scan_twitter(limit: int = 100) -> list[dict]:
    """
    Scrape recent crypto-related tweets from Nitter via HTML parsing,
    rotating through mirrors to handle rate limits.

    :param days: Number of days back to include tweets.
    :param limit: Maximum number of tweet results to process.
    :return: List of dicts with keys: username, tweet, date, profile_url.
    """
    mirrors = get_working_mirrors()
    if not mirrors:
        return []

    since_date = (datetime.now() - timedelta(days=FILTER_AGE_TWEET_DAYS_MAX)).strftime('%Y-%m-%d')
    filter_founds_to_query = ' OR '.join([f"'{f}'" for f in FILTER_FUNDS])
    filter_keywords_to_query = ' OR '.join([f"'{f}'" for f in FILTER_KEYWORDS])
    famous_investors_to_query = ' OR '.join([f"'{f}'" for f in SCORE_FAMOUS_INVESTORS])
    
    query = ""
    if len(filter_founds_to_query):
        query += f"{filter_founds_to_query}"
        
    if len(filter_keywords_to_query):
        query += f" OR {filter_keywords_to_query}"
        
    if len(famous_investors_to_query.replace("''", "")):
        query += f" OR {famous_investors_to_query}"
        
    query += f" since:{since_date}"
    
    encoded = requests.utils.quote(query)

    soup = None
    base = None
    for base in mirrors:
        search_url = f"{base}/search?f=tweets&q={encoded}"
        logger.info(f"scan_twitter: Trying mirror: {search_url}")
        try:
            resp = requests.get(
                search_url,
                headers=headers,
                timeout=10,
                verify=certifi.where()
            )
            logger.info(f"scan_twitter: Status code: {resp.status_code}")
            logger.info(f"scan_twitter: Headers: {resp.headers}")
            logger.info(f"scan_twitter: Text length: {len(resp.text)}")
            if resp.status_code == 429:
                logger.warning(f"429 Too Many Requests on {base}, skipping")
                continue
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            logger.info(f"scan_twitter: Successfully fetched from {base}")
            break
        except Exception as e:
            logger.warning(f"Error fetching from {base}: {e}")
            time.sleep(1)
            continue

    if soup is None:
        logger.error("scan_twitter: Все зеркала недоступны или ограничены")
        return []

    items = soup.select('div.timeline div.timeline-item')[:limit]
    logger.info(f"scan_twitter: Found {len(items)} items, processing up to {limit}")

    results = []
    usernames = {}
    for idx, item in enumerate(items, start=1):
        try:
            tw = {}
            
            user_el = item.select_one('a.username')
            tw["username"] = user_el.text.lstrip('@') if user_el else ''
            profile_path = user_el['href'] if user_el and user_el.has_attr('href') else ''
            
            date_el = item.select_one('span.tweet-date a')
            tw["tweet_date"] = date_el['title'] if date_el and date_el.has_attr('title') else ''
            
            cleaned = tw["tweet_date"].split('·')[0].strip() + ' ' + tw["tweet_date"].split('·')[1].replace('UTC', '').strip()
            tweet_datetime = datetime.strptime(cleaned, '%b %d, %Y %I:%M %p')
            age_tweet_days = (datetime.now() - tweet_datetime).days
            if age_tweet_days > FILTER_AGE_TWEET_DAYS_MAX:
                logger.debug(f"age tweet days: {age_tweet_days}, FILTER_AGE_TWEET_DAYS_MAX: {FILTER_AGE_TWEET_DAYS_MAX} - account rejected")
                continue
            tw["age_tweet_days"] = age_tweet_days
            
            user_fault = get_fault_user(tw["username"])
            if user_fault:
                logger.debug(f"user {tw['username'] } - user fault in BD")
                continue
            
            time.sleep(PAUSE_BETWEEN_MESSAGES)
            if not usernames.get(tw["username"]):
                profile_info = fetch_profile_info(tw["username"], mirrors)
                usernames[tw["username"]] = profile_info
            else:
                profile_info = usernames[tw["username"]]
                
                
            tw["bio"] = profile_info.get('bio', '')
            tw["created"] = profile_info.get('created', None)
            tw["tweets_count"] = profile_info.get('tweets_count', 0)
            tw["followers_count"] = profile_info.get('followers_count', 0)
            
            age_days = (datetime.now() - tw["created"]).days
            if age_days > FILTER_ACCOUNT_AGE_MAX_DAYS:
                logger.debug(f"account age days: {age_days}, FILTER_ACCOUNT_AGE_MAX_DAYS: {FILTER_ACCOUNT_AGE_MAX_DAYS} - account rejected")
                save_user_fault(tw["username"], profile_info)
                continue
                
            if tw["tweets_count"] > FILTER_TWEETS_MAX:
                logger.debug(f"tweets count: {tw['tweets_count']}, FILTER_TWEETS_MAX: {FILTER_TWEETS_MAX} - account rejected")
                save_user_fault(tw["username"], profile_info)
                continue
                
            if tw["followers_count"] > FILTER_FOLLOWERS_MAX:
                logger.debug(f"tweets count: {tw['followers_count']}, FILTER_FOLLOWERS_MAX: {FILTER_FOLLOWERS_MAX} - account rejected")
                save_user_fault(tw["username"], profile_info)
                continue
            
            fullname_el = item.select_one('a.fullname')
            tw["fullname"] = fullname_el.get_text(strip=True) if fullname_el else ''

            content_el = item.select_one('div.tweet-content')
            tw["tweet_text"] = content_el.get_text(' ', strip=True) if content_el else ''
            
            tw["profile_url"] = f"{base}{profile_path}"
            
            tw["score"] = 0

            logger.debug(f"Parsed item {idx}: @{tw['username']} at {tw['tweet_date']}")
            
            results.append(tw)
            
        except Exception as e:
            error_text = str(e)
            logger.exception(f"scan_twitter: Error parsing item #{idx} - {error_text}")

    logger.info(f"scan_twitter: Returning {len(results)} parsed tweets")
    return results
