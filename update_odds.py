import os
import requests
import json
from datetime import datetime, timezone

API_KEY = os.environ.get("ODDS_API_KEY")
REGION = "us"
MARKETS = "h2h"
ODDS_FORMAT = "decimal"

SPORTS = [
    "americanfootball_nfl",
    "basketball_nba",
    "icehockey_nhl",
    "soccer_epl",
    "tennis_atp_challenger"
]

NAME_BUZZ = {
    "djokovic": 95, "alcaraz": 96, "sinner": 94, "medvedev": 90, 
    "zverev": 88, "tsitsipas": 85, "rublev": 83, "rune": 84,
    "swiatek": 95, "sabalenka": 93, "gauff": 94, "rybakina": 90,
    "chiefs": 95, "bills": 90, "cowboys": 88, "patriots": 85, "packers": 87,
    "celtics": 92, "lakers": 94, "warriors": 91, "heat": 85, "knicks": 87,
    "bucks": 86, "suns": 84, "nuggets": 88, "clippers": 83, "sixers": 85,
    "real madrid": 96, "barcelona": 95, "arsenal": 90, "bayern": 92,
    "maple leafs": 89, "rangers": 88, "oilers": 87, "blackhawks": 86
}

def get_buzz(name):
    if not name:
        return 75
    name_lower = name.lower()
    for key, val in NAME_BUZZ.items():
        if key in name_lower:
            return val
    return 75

def is_within_7_days(date_str):
    try:
        game_dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        delta_days = (game_dt - now).days
        return 0 <= delta_days <= 7
    except Exception:
        return False

def fetch_odds():
    all_data = []
    if not API_KEY:
        print("Error: ODDS_API_KEY secret is missing.")
        return all_data

    sports_url = f"https://api.the-odds-api.com/v4/sports?apiKey={API_KEY}"
    active_sports = []
    try:
        res = requests.get(sports_url, timeout=10)
        if res.status_code == 200:
            for s in res.json():
                if s.get("active") and not s.get("has_outrights"):
                    key = s.get("key", "")
                    if any(target in key for target in ["tennis", "nfl", "nba", "
