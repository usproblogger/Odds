import os
import requests
import json
from datetime import datetime, timezone

API_KEY = os.environ.get("ODDS_API_KEY")
REGION = "us"
MARKETS = "h2h"
ODDS_FORMAT = "decimal"

NAME_BUZZ = {
    # Tennis Stars
    "djokovic": 95, "alcaraz": 96, "sinner": 94, "medvedev": 90, 
    "zverev": 88, "tsitsipas": 85, "rublev": 83, "rune": 84,
    "swiatek": 95, "sabalenka": 93, "gauff": 94, "rybakina": 90,
    # Soccer Clubs
    "real madrid": 96, "barcelona": 95, "arsenal": 90, "bayern": 92,
    "manchester city": 94, "liverpool": 93, "psg": 91, "inter": 88,
    # US Major Teams
    "chiefs": 95, "bills": 90, "cowboys": 88, "patriots": 85, "packers": 87,
    "celtics": 92, "lakers": 94, "warriors": 91, "heat": 85, "knicks": 87,
    "bucks": 86, "suns": 84, "nuggets": 88, "clippers": 83, "sixers": 85,
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

    # Step 1: Discover all currently active sport keys directly from the API
    sports_url = f"https://api.the-odds-api.com/v4/sports?apiKey={API_KEY}"
    active_keys = []
    try:
        res = requests.get(sports_url, timeout=10)
        if res.status_code == 200:
            for item in res.json():
                if item.get("active") and not item.get("has_outrights"):
                    k = item.get("key", "")
                    # Match any tennis (ATP, WTA, Challengers), soccer (UEFA, EPL, etc.), NFL, NBA, NHL
                    if (k.startswith("tennis_") or 
                        k.startswith("soccer_") or 
                        k in ["americanfootball_nfl", "basketball_nba", "icehockey_nhl"]):
                        active_keys.append(k)
    except Exception as e:
        print(f"Error discovering sports: {e}")

    # Fallback list if discovery request fails
    if not active_keys:
        active_keys = [
            "americanfootball_nfl",
            "basketball_nba",
            "icehockey_nhl",
            "soccer_uefa_champions_league",
            "soccer_epl"
        ]

    # Step 2: Fetch matches for each active sport
    for sport in active_keys:
        url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds/?apiKey={API_KEY}&regions={REGION}&markets={MARKETS}&oddsFormat={ODDS_FORMAT}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                continue
                
            events = response.json()
            if not isinstance(events, list):
                continue
                
            for event in events:
                commence_time = event.get("commence_time")
                if not commence_time or not is_within_7_days(commence_time):
                    continue
                    
                home_team = event.get("home_team")
                away_team = event.get("away_team")
                if not home_team or not away_team:
                    continue
                
                # Tag category
                if sport.startswith("tennis_"):
                    sport_cat = "tennis"
                elif sport.startswith("soccer_"):
                    sport_cat = "soccer"
                elif "football" in sport:
                    sport_cat = "football"
                elif "basketball" in sport:
                    sport_cat = "basketball"
                else:
                    sport_cat = "hockey"
                
                home_buzz = get_buzz(home_team)
                away_buzz = get_buzz(away_team)
                gap = abs(home_buzz - away_buzz)
                
                bookmakers = event.get("bookmakers", [])
                if not bookmakers:
                    continue
                
                h2h_outcomes = []
                for bm in bookmakers:
                    for market in bm.get("markets", []):
                        if market.get("key") == "h2h":
                            h2h_outcomes = market.get("outcomes", [])
                            break
                    if len(h2h_outcomes) >= 2:
                        break
                
                if len(h2h_outcomes) < 2:
                    continue
                    
                p1 = h2h_outcomes[0].get("price")
                p2 = h2h_outcomes[1].get("price")
                name1 = h2h_outcomes[0].get("name")
                name2 = h2h_outcomes[1].get("name")
                
                if not p1 or not p2:
                    continue
                
                # Betting favorite has the lower decimal price
                if p1 < p2:
                    dec_price = p1
                    fav_team = name1
                else:
                    dec_price = p2
                    fav_team = name2
                    
                if dec_price >= 2.0:
                    lead_ml = int((dec_price - 1.0) * 100)
                else:
                    lead_ml = int(-100 / (dec_price - 1.0))
                
                all_data.append({
                    "sport": sport_cat,
                    "gameDate": commence_time,
                    "awayTeam": away_team,
                    "homeTeam": home_team,
                    "favTeam": fav_team,
                    "leadML": lead_ml,
                    "gap": max(gap, 14)
                })
        except Exception:
            continue

    # Cap at top 14 matchups across all sports to avoid clutter
    return all_data[:14]

if __name__ == "__main__":
    data = fetch_odds()
    with open("odds_data.json", "w") as f:
        json.dump(data, f, indent=2)
    print(f"Successfully updated odds_data.json with {len(data)} events.")
