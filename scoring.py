import os
from datetime import datetime
from utils import extract_urls

# Загружаем фильтры из ENV (с дефолтами)
TWEETS_MAX   = int(os.getenv("FILTER_TWEETS_MAX"))
KEYWORDS     = os.getenv("FILTER_KEYWORDS").lower().split(",")
FUNDS        = os.getenv("FILTER_FUNDS").lower().split(",")

def score_account(tw):
    
    text_acc = (tw["bio"] + " " + tw["tweet_text"]).lower()
    
    urls = extract_urls(text_acc)
    if len(urls) > 0:
        tw["urls"] = urls
        tw["score"] += 2
        return

    SCORE_PLATFORMS = os.getenv('SCORE_PLATFORMS', '').lower().split(',')
    if SCORE_PLATFORMS == ['']:
        tw["score"] += 2
    else:
        if any(val in text_acc for val in SCORE_PLATFORMS):
            tw["score"] += 2
        
    SCORE_FAMOUS_INVESTORS = os.getenv('SCORE_FAMOUS_INVESTORS', '').lower().split(',')
    if SCORE_FAMOUS_INVESTORS == ['']:
        tw["score"] += 3
    else:
        if any(val in text_acc for val in SCORE_FAMOUS_INVESTORS):
            tw["score"] += 3
        
    FILTER_KEYWORDS = os.getenv('FILTER_KEYWORDS', '').lower().split(',')
    FILTER_FUNDS = os.getenv('FILTER_FUNDS', '').lower().split(',')
    key_words = FILTER_KEYWORDS + FILTER_FUNDS
    
    if key_words == ['']:
        tw["score"] += 3
    else:
        if any(val in text_acc for val in key_words):
            tw["score"] += 3

    return tw
