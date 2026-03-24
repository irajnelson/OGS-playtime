import json
import sys
import time
from datetime import datetime

import pandas as pd
import requests


def get_player_id(username: str) -> int:
    """Find the user's numeric id on OGS."""
    url = f"https://online-go.com/api/v1/players?username={username}"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    if "results" in data and len(data["results"]) > 0:
        return data["results"][0]["id"]
    else:
        raise ValueError(f"User '{username}' not found.")


def calculate_ogs_playtime(username: str) -> pd.DataFrame:
    """Calculate the total hours spent playing live/blitz games and return a DataFrame."""
    player_id = get_player_id(username)
    print(f"Found user '{username}' with ID {player_id}.")
    print("Fetching game history...")

    url = f"https://online-go.com/api/v1/players/{player_id}/games/"

    # Make sure games have finished, order by most recent, get 100 games at a time
    params = {"ended__isnull": "false", "ordering": "-id", "page_size": 100}

    games_data = []

    while url:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        for game in data.get("results", []):
            speed = None

            # Formatting is inconsistent in OGS API
            tc_params = game.get("time_control_parameters")
            if isinstance(tc_params, str):
                try:
                    tc_params = json.loads(tc_params.replace("'", '"'))
                except Exception:
                    tc_params = {}
            if isinstance(tc_params, dict):
                speed = tc_params.get("speed")

            if not speed:
                tc = game.get("time_control")
                if isinstance(tc, str):
                    try:
                        tc = json.loads(tc.replace("'", '"'))
                    except Exception:
                        tc = {}
                if isinstance(tc, dict):
                    speed = tc.get("speed")

            if not speed:
                speed = game.get("speed")

            # Only process live or blitz games, not correspondance
            if speed in ["live", "blitz"]:
                # Skip annulled or cancelled games
                if game.get("annulled") or game.get("cancelled"):
                    continue

                started_str = game.get("started")
                ended_str = game.get("ended")

                if started_str and ended_str:
                    try:
                        started = datetime.fromisoformat(started_str)
                        ended = datetime.fromisoformat(ended_str)

                        duration_seconds = (ended - started).total_seconds()
                        if duration_seconds > 0:
                            games_data.append(
                                {
                                    "game_id": game.get("id"),
                                    "speed": speed,
                                    "started": started,
                                    "ended": ended,
                                    "duration_minutes": duration_seconds / 60,
                                    "duration_hours": duration_seconds / 3600,
                                }
                            )
                    except ValueError as e:
                        print(
                            f"Warning: Error with game {game.get('id')}: {e}",
                            file=sys.stderr,
                        )

        # get next URL
        url = data.get("next")
        # No need to have params in the next request
        params = None

        # Be nice to the API, otherwise you'll get 429 errors
        if url:
            time.sleep(0.5)

    df = pd.DataFrame(games_data)

    # Remove duplicates
    if not df.empty:
        df = df.drop_duplicates(subset=["game_id"])

    print(f"\nProcessed {len(df)} games")
    return df