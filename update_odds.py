import os
import json
import requests

API_KEY = os.environ.get("ODDS_API_KEY")

BUZZ_DICT = {
    "Dallas Cowboys": 95, "Kansas City Chiefs": 93, "Baltimore Ravens": 85,
    "Indianapolis Colts": 57, "Jacksonville Jaguars": 51, "New York Jets": 72,
    "Boston Celtics": 92, "Los Angeles Lakers": 96, "Golden State Warriors": 90,
    "Charlotte Hornets": 50, "Memphis Grizzlies": 61, "Houston Rockets": 62,
    "Real Madrid": 98, "Arsenal": 91, "Liverpool": 93, "Slavia Prague": 47,
    "Edmonton Oilers": 82, "Toronto Maple Leafs": 88, "Chicago Blackhawks": 78
}

SPORTS = [
    "americanfootball_nfl",
    "basketball_nba",
    "icehockey_nhl",
    "soccer_uefa_champs_league"
]

def get_sport_category(key):
    if "football" in key: return "football"
    if "basketball" in key: return "basketball"
    if "hockey" in key: return "hockey"
    if "soccer" in key: return "soccer"
    return "other"

def fetch_and_process():
    output_data = []

    for sport_key in SPORTS:
        url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/"
        params = {
            "apiKey": API_KEY,
            "regions": "us",
            "markets": "h2h",
            "oddsFormat": "american"
        }
        try:
            res = requests.get(url, params=params)
            games = res.json()
            if not isinstance(games, list):
                continue

            for g in games[:4]:
                home = g.get("home_team")
                away = g.get("away_team")
                
                bms = g.get("bookmakers", [])
                if not bms:
                    continue
                outcomes = bms[0]["markets"][0]["outcomes"]
                if len(outcomes) < 2:
                    continue

                t1, p1 = outcomes[0]["name"], outcomes[0]["price"]
                t2, p2 = outcomes[1]["name"], outcomes[1]["price"]

                if p1 < p2:
                    fav, fav_ml, dog, dog_ml = t1, p1, t2, p2
                else:
                    fav, fav_ml, dog, dog_ml = t2, p2, t1, p1

                buzz_fav = BUZZ_DICT.get(fav, 75)
                buzz_dog = BUZZ_DICT.get(dog, 50)
                gap = abs(buzz_fav - buzz_dog)

                match_formatted = f"{dog} ({'+' if dog_ml > 0 else ''}{dog_ml}) vs. {fav} ({'+' if fav_ml > 0 else ''}{fav_ml})"

                output_data.append({
                    "isSpread": False,
                    "timeframe": "weekly",
                    "sport": get_sport_category(sport_key),
                    "matchFormatted": match_formatted,
                    "leadML": fav_ml,
                    "gap": gap
                })
        except Exception as e:
            print(f"Error fetching {sport_key}: {e}")

    with open("odds_data.json", "w") as f:
        json.dump(output_data, f, indent=2)

if __name__ == "__main__":
    fetch_and_process()
  
