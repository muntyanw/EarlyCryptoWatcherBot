from datetime import datetime

FUNDS    = ['a16z', 'binance labs', 'paradigm']
KEYWORDS = ['zealy', 'galxe', 'presale', 'whitelist']

def score_account(acc):
    score = 0
    age = (datetime.now() - acc['created']).days
    if age <= 7:           score += 2
    if acc['tweets_count'] <= 10: score += 1
    if any(kw in acc['bio'].lower()    for kw in KEYWORDS): score += 2
    if any(f  in acc['content'].lower() for f  in FUNDS):    score += 3
    return score
