import os
import time
import certifi
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from logger_config import setup_logger

# Ensure requests uses certifi's CA bundle for SSL verification
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

# Initialize logger for this module
logger = setup_logger(__name__)

def scan_twitter(days: int = 3, limit: int = 100) -> list[dict]:
    """
    Scrape recent crypto-related tweets from Nitter via HTML parsing,
    rotating through mirrors to handle rate limits.

    :param days: Number of days back to include tweets.
    :param limit: Maximum number of tweet results to process.
    :return: List of dicts with keys: username, tweet, date, profile_url.
    """
    # Nitter mirrors (comma-separated list in env var)
    mirrors = os.getenv('NITTER_URLS', 'https://nitter.net').split(',')
    since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    query = f"crypto OR web3 OR blockchain since:{since_date}"
    encoded = requests.utils.quote(query)

    soup = None
    for base in mirrors:
        base = base.rstrip('/')
        # Use f=tweets to match Nitter's Tweets tab
        search_url = f"{base}/search?f=tweets&q={encoded}"
        logger.info(f"scan_twitter: Trying mirror: {search_url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        try:
            resp = requests.get(
                search_url,
                headers=headers,
                timeout=10
            )
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
        logger.error("scan_twitter: All mirrors failed or rate-limited")
        return []

    # Select tweet items in timeline
    items = soup.select('div.timeline div.timeline-item')[:limit]
    logger.info(f"scan_twitter: Found {len(items)} items, processing up to {limit}")

    results = []
    for idx, item in enumerate(items, start=1):
        try:
            user_el = item.select_one('a.username')
            username = user_el.text.lstrip('@') if user_el else ''
            profile_path = user_el['href'] if user_el and user_el.has_attr('href') else ''

            content_el = item.select_one('div.tweet-content')
            tweet_text = content_el.get_text(' ', strip=True) if content_el else ''

            date_el = item.select_one('span.tweet-date a')
            tweet_date = date_el['title'] if date_el and date_el.has_attr('title') else ''

            logger.debug(f"Parsed item {idx}: @{username} at {tweet_date}")
            results.append({
                'username': username,
                'tweet': tweet_text,
                'date': tweet_date,
                'profile_url': f"{base}{profile_path}"
            })
        except Exception:
            logger.exception(f"scan_twitter: Error parsing item #{idx}")

    logger.info(f"scan_twitter: Returning {len(results)} parsed tweets")
    return results
