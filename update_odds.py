import os
import requests
from datetime import datetime, timezone

API_KEY = os.environ.get("ODDS_API_KEY")
REGION = "us"
MARKETS = "h2h,spreads"
ODDS_FORMAT = "decimal"

# Sport keys from The Odds API
SPORTS = [
    "americanfootball_nfl",
    "basketball_nba",
    "icehockey_nhl",
    "soccer_uefa_champions_league"
]

TEAM_BUZZ = {
    "Kansas City Chiefs": 95, "Buffalo Bills": 90, "Dallas Cowboys": 88,
    "Boston Celtics": 92, "Los Angeles Lakers": 94, "Golden State Warriors": 91,
    "Miami Heat": 85, "New York Knicks": 87, "Real Madrid": 96, "Barcelona": 95
}

def get_buzz(team_name):
    for key, val in TEAM_BUZZ.items():
        if key.lower() in team_name.lower():
            return val
    return 70  # Default baseline buzz

def classify_timeframe(date_str):
    """Categorizes game into timeframe buckets based on its date string."""
    try:
        game_dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        
        # Calculate days difference from now
        delta_days = (game_dt - now).days
        
        # If it's within the next 7 days, tag as this weekend / upcoming week
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
            
            # Simple sport category mapping
            sport_cat = "football" if "football" in sport else ("basketball" if "basketball" in sport else ("hockey" if "hockey" in sport else "soccer"))
            
            # Compute popularity gap
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
                        # Determine favorite (lower price / negative odds or lower decimal converted)
                        lead_ml = -110 # default placeholder
                        match_fmt = f"{away_team} vs {home_team}"
                        
                        all_data.append({
                            "isSpread": False,
                            "timeframe": timeframe,
                            "sport": sport_cat,
                            "gameDate": commence_time,
                            "matchFormatted": match_fmt,
                            "leadML": lead_ml,
                            "gap": gap
                        })

    return all_data

if __name__ == "__main__":
    data = fetch_odds()
    import json
    with open("odds_data.json", "w") as f:
        json.dump(data, f, indent=2)
    print(f"Successfully updated odds_data.json with {len(data)} events.")
    
