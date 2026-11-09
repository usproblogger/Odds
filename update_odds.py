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
    "soccer_uefa_champions_league"
]

# Comprehensive brand popularity baseline map (0-100 scale)
TEAM_BUZZ = {
    "chiefs": 95, "bills": 90, "cowboys": 88, "patriots": 85, "packers": 87,
    "celtics": 92, "lakers": 94, "warriors": 91, "heat": 85, "knicks": 87,
    "bucks": 86, "suns": 84, "nuggets": 88, "clippers": 83, "sixers": 85,
    "real madrid": 96, "barcelona": 95, "arsenal": 90, "bayern": 92,
    "maple leafs": 89, "rangers": 88, "oilers": 87, "blackhawks": 86
}

def get_buzz(team_name):
    name_lower = team_name.lower()
    for key, val in TEAM_BUZZ.items():
        if key in name_lower:
            return val
    return 75  # Clean default baseline instead of 0

def classify_timeframe(date_str):
    try:
        game_dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        delta_days = (game_dt - now).days
        
        # 0 to 7 days out falls into "this_weekend" / current week bucket
        if 0 <= delta_days <= 7:
            return "this_weekend"
        else:
            return "next_weekend"
    except Exception:
        return "this_weekend"

def fetch_odds():
    all_data = []
    if not API_KEY:
        print("Error: ODDS_API_KEY secret is missing.")
        return all_data

    for sport in SPORTS:
        url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds/?apiKey={API_KEY}&regions={REGION}&markets={MARKETS}&oddsFormat={ODDS_FORMAT}"
        response = requests.get(url)
        
        if response.status_code != 200:
            print(f"Failed to fetch {sport}: {response.status_code}")
            continue
            
        events = response.json()
        for event in events:
            commence_time = event.get("commence_time")
            home_team = event.get("home_team")
            away_team = event.get("away_team")
            
            timeframe = classify_timeframe(commence_time)
            
            sport_cat = "football" if "football" in sport else ("basketball" if "basketball" in sport else ("hockey" if "hockey" in sport else "soccer"))
            
            home_buzz = get_buzz(home_team)
            away_buzz = get_buzz(away_team)
            gap = abs(home_buzz - away_buzz)
            
            bookmakers = event.get("bookmakers", [])
            if not bookmakers:
                continue
                
            markets = bookmakers[0].get("markets", [])
            for market in markets:
                if market.get("key") == "h2h":
                    outcomes = market.get("outcomes", [])
                    if len(outcomes) == 2:
                        team1, team2 = outcomes[0], outcomes[1]
                        
                        # Identify favorite based on lower odds price
                        price1 = team1.get("price", 2.0)
                        price2 = team2.get("price", 2.0)
                        
                        if price1 < price2:
                            fav_name = team1.get("name")
                            dec_price = price1
                        else:
                            fav_name = team2.get("name")
                            dec_price = price2
                            
                        # Convert decimal odds to American moneyline format for the widget math
                        if dec_price >= 2.0:
                            lead_ml = int((dec_price - 1.0) * 100)
                        else:
                            lead_ml = int(-100 / (dec_price - 1.0))
                            
                        match_fmt = f"{away_team} vs {home_team}"
                        
                        all_data.append({
                            "isSpread": False,
                            "timeframe": timeframe,
                            "sport": sport_cat,
                            "gameDate": commence_time,
                            "matchFormatted": match_fmt,
                            "leadML": lead_ml,
                            "gap": max(gap, 15) # Ensures a healthy visible gap
                        })

    return all_data

if __name__ == "__main__":
    data = fetch_odds()
    with open("odds_data.json", "w") as f:
        json.dump(data, f, indent=2)
    print(f"Successfully updated odds_data.json with {len(data)} events.")
                            
