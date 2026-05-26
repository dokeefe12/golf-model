import os
import requests
import pandas as pd
from datetime import datetime
from openpyxl import Workbook, load_workbook

DATA_GOLF_KEY = os.getenv("DATA_GOLF_API_KEY")
EXCEL_FILE = "golf_model.xlsx"

if not DATA_GOLF_KEY:
    raise ValueError("Missing DATA_GOLF_API_KEY GitHub secret.")


def get_json(url):
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def datagolf(endpoint, params=None):
    if params is None:
        params = {}

    params["key"] = DATA_GOLF_KEY
    params["file_format"] = "json"

    url = f"https://feeds.datagolf.com/{endpoint}"
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def flatten_to_df(data):
    if isinstance(data, list):
        return pd.json_normalize(data)

    if isinstance(data, dict):
        for value in data.values():
            if isinstance(value, list):
                return pd.json_normalize(value)

    return pd.DataFrame()


def get_current_tournament():
    year = datetime.now().year

    schedule = datagolf(
        "get-schedule",
        {
            "tour": "pga",
            "season": year,
            "upcoming_only": "yes"
        }
    )

    df = flatten_to_df(schedule)

    if df.empty:
        return {
            "event_name": "Unknown Tournament",
            "course": "Unknown Course",
            "date": datetime.now().strftime("%Y-%m-%d")
        }

    row = df.iloc[0]

    return {
        "event_name": row.get("event_name", row.get("name", "Unknown Tournament")),
        "course": row.get("course", row.get("course_name", "Unknown Course")),
        "date": row.get("start_date", datetime.now().strftime("%Y-%m-%d"))
    }


def get_field():
    data = datagolf(
        "field-updates",
        {
            "tour": "pga"
        }
    )
    return flatten_to_df(data)


def get_rankings():
    data = datagolf("preds/get-dg-rankings")
    return flatten_to_df(data)


def get_skill_ratings():
    data = datagolf(
        "preds/skill-ratings",
        {
            "display": "value"
        }
    )
    return flatten_to_df(data)


def get_player_decompositions():
    data = datagolf(
        "preds/player-decompositions",
        {
            "tour": "pga"
        }
    )
    return flatten_to_df(data)


def find_course_weather(course_name):
    courses = pd.read_csv("data/courses.csv")

    match = courses[courses["course"].str.lower() == course_name.lower()]

    if match.empty:
        return pd.DataFrame([{
            "course": course_name,
            "weather_note": "Course not found in courses.csv. Add latitude and longitude."
        }])

    lat = match.iloc[0]["latitude"]
    lon = match.iloc[0]["longitude"]

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,windspeed_10m_max",
        "forecast_days": 7,
        "timezone": "auto",
        "temperature_unit": "fahrenheit",
        "windspeed_unit": "mph"
    }

    data = get_json(url + "?" + requests.compat.urlencode(params))

    daily = data.get("daily", {})

    return pd.DataFrame({
        "date": daily.get("time", []),
        "high_temp": daily.get("temperature_2m_max", []),
        "low_temp": daily.get("temperature_2m_min", []),
        "precip_probability": daily.get("precipitation_probability_max", []),
        "max_wind_mph": daily.get("windspeed_10m_max", [])
    })


def clean_name(df):
    for col in df.columns:
        if col.lower() in ["player_name", "name", "player"]:
            return df.rename(columns={col: "player_name"})
    return df


def build_model(field, rankings, skills, decomps):
    field = clean_name(field)
    rankings = clean_name(rankings)
    skills = clean_name(skills)
    decomps = clean_name(decomps)

    model = field.copy()

    if "player_name" not in model.columns:
        model["player_name"] = "Unknown Player"

    for df in [rankings, skills, decomps]:
        if not df.empty and "player_name" in df.columns:
            model = model.merge(df, on="player_name", how="left", suffixes=("", "_extra"))

    numeric_cols = model.select_dtypes(include="number").columns.tolist()

    if numeric_cols:
        model["raw_score"] = model[numeric_cols].mean(axis=1, skipna=True)
    else:
        model["raw_score"] = 0

    model["model_rank"] = model["raw_score"].rank(ascending=False, method="min")
    model = model.sort_values("model_rank")

    return model


def write_excel(tournament, field, rankings, skills, decomps, weather, model):
    with pd.ExcelWriter(EXCEL_FILE, engine="openpyxl") as writer:
        pd.DataFrame([tournament]).to_excel(writer, sheet_name="Tournament", index=False)
        field.to_excel(writer, sheet_name="Field", index=False)
        rankings.to_excel(writer, sheet_name="Rankings", index=False)
        skills.to_excel(writer, sheet_name="Skill_Ratings", index=False)
        decomps.to_excel(writer, sheet_name="Player_Decomp", index=False)
        weather.to_excel(writer, sheet_name="Weather", index=False)
        model.to_excel(writer, sheet_name="Model", index=False)

        summary = pd.DataFrame({
            "Item": [
                "Last Updated",
                "Tournament",
                "Course",
                "Start Date",
                "Players Pulled",
                "Model Note"
            ],
            "Value": [
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                tournament["event_name"],
                tournament["course"],
                tournament["date"],
                len(field),
                "Higher raw_score = better projected fit. Customize weights later."
            ]
        })

        summary.to_excel(writer, sheet_name="Dashboard", index=False)


def main():
    tournament = get_current_tournament()

    print(f"Updating model for: {tournament['event_name']}")

    field = get_field()
    rankings = get_rankings()
    skills = get_skill_ratings()
    decomps = get_player_decompositions()
    weather = find_course_weather(tournament["course"])

    model = build_model(field, rankings, skills, decomps)

    write_excel(
        tournament,
        field,
        rankings,
        skills,
        decomps,
        weather,
        model
    )

    print("Excel file updated successfully.")


if __name__ == "__main__":
    main()
