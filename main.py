import pandas as pd
import requests
from datetime import datetime

EXCEL_FILE = "golf_model.xlsx"


def get_weather(lat, lon):
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&daily=temperature_2m_max,precipitation_probability_max,windspeed_10m_max"
        f"&forecast_days=5&timezone=auto"
    )

    response = requests.get(url)
    data = response.json()

    return pd.DataFrame({
        "date": data["daily"]["time"],
        "max_temp": data["daily"]["temperature_2m_max"],
        "precipitation": data["daily"]["precipitation_probability_max"],
        "wind_speed": data["daily"]["windspeed_10m_max"]
    })


def get_players():
    players = [
        ["Scottie Scheffler", 1, 98],
        ["Rory McIlroy", 2, 95],
        ["Xander Schauffele", 3, 93],
        ["Collin Morikawa", 4, 91],
        ["Ludvig Aberg", 5, 90],
        ["Justin Thomas", 6, 89],
    ]

    df = pd.DataFrame(players, columns=[
        "player",
        "world_rank",
        "rating"
    ])

    return df


def build_model(players):
    players["projected_score"] = (
        players["rating"] * 0.7 +
        (100 - players["world_rank"]) * 0.3
    )

    players = players.sort_values(
        "projected_score",
        ascending=False
    )

    return players


def write_excel(weather, model):
    with pd.ExcelWriter(EXCEL_FILE, engine="openpyxl") as writer:
        weather.to_excel(writer, sheet_name="Weather", index=False)
        model.to_excel(writer, sheet_name="Model", index=False)

        dashboard = pd.DataFrame({
            "Item": [
                "Last Updated",
                "Tournament",
                "Course"
            ],
            "Value": [
                datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Current PGA Event",
                "Current Course"
            ]
        })

        dashboard.to_excel(writer, sheet_name="Dashboard", index=False)


def main():
    weather = get_weather(33.5020, -82.0228)

    players = get_players()

    model = build_model(players)

    write_excel(weather, model)

    print("Spreadsheet updated.")


if __name__ == "__main__":
    main()
