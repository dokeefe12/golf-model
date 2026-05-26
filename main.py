import pandas as pd
import requests
from datetime import datetime

EXCEL_FILE = "golf_model.xlsx"

PLAYERS = [
    ["Scottie Scheffler", 1, 98, 96, 95, 94],
    ["Rory McIlroy", 2, 96, 95, 93, 91],
    ["Xander Schauffele", 3, 95, 94, 92, 90],
    ["Collin Morikawa", 4, 93, 91, 96, 88],
    ["Ludvig Aberg", 5, 92, 94, 90, 87],
    ["Viktor Hovland", 6, 91, 90, 88, 86],
    ["Patrick Cantlay", 7, 90, 88, 91, 89],
    ["Wyndham Clark", 8, 89, 92, 84, 86],
    ["Hideki Matsuyama", 9, 88, 87, 90, 85],
    ["Tommy Fleetwood", 10, 88, 86, 91, 84],
    ["Max Homa", 11, 87, 85, 88, 86],
    ["Justin Thomas", 12, 86, 87, 84, 83],
    ["Jordan Spieth", 13, 85, 83, 82, 90],
    ["Sam Burns", 14, 84, 86, 80, 85],
    ["Tony Finau", 15, 84, 88, 82, 81],
    ["Cameron Young", 16, 83, 90, 78, 79],
    ["Sahith Theegala", 17, 83, 84, 80, 86],
    ["Russell Henley", 18, 82, 78, 88, 83],
    ["Matt Fitzpatrick", 19, 82, 79, 86, 84],
    ["Keegan Bradley", 20, 81, 82, 84, 80],
    ["Brian Harman", 21, 81, 76, 87, 83],
    ["Jason Day", 22, 80, 78, 82, 86],
    ["Sepp Straka", 23, 80, 81, 83, 79],
    ["Min Woo Lee", 24, 79, 86, 77, 81],
    ["Akshay Bhatia", 25, 79, 80, 82, 80],
    ["Corey Conners", 26, 78, 79, 86, 76],
    ["Adam Scott", 27, 78, 81, 80, 82],
    ["Si Woo Kim", 28, 77, 79, 81, 80],
    ["Shane Lowry", 29, 77, 75, 84, 86],
    ["Rickie Fowler", 30, 76, 78, 80, 82],
    ["Will Zalatoris", 31, 76, 83, 79, 74],
    ["Denny McCarthy", 32, 75, 72, 78, 92],
    ["Tom Kim", 33, 75, 74, 83, 81],
    ["Eric Cole", 34, 74, 73, 79, 84],
    ["J.T. Poston", 35, 74, 72, 81, 86],
    ["Chris Kirk", 36, 73, 74, 80, 82],
    ["Byeong Hun An", 37, 73, 82, 75, 76],
    ["Harris English", 38, 72, 75, 79, 81],
    ["Lucas Glover", 39, 72, 76, 82, 75],
    ["Maverick McNealy", 40, 71, 73, 78, 84],
    ["Taylor Moore", 41, 71, 75, 76, 82],
    ["Kurt Kitayama", 42, 70, 79, 74, 78],
    ["Nicolai Hojgaard", 43, 70, 82, 73, 76],
    ["Cam Davis", 44, 69, 78, 74, 80],
    ["Adam Hadwin", 45, 69, 72, 80, 82],
    ["Nick Taylor", 46, 68, 71, 79, 83],
    ["Keith Mitchell", 47, 68, 83, 72, 74],
    ["Beau Hossler", 48, 67, 73, 76, 84],
    ["Andrew Putnam", 49, 67, 68, 81, 86],
    ["Davis Thompson", 50, 66, 76, 75, 79],
    ["Austin Eckroat", 51, 66, 74, 77, 80],
    ["Jake Knapp", 52, 65, 81, 70, 75],
    ["Ben Griffin", 53, 65, 72, 78, 82],
    ["Taylor Pendrith", 54, 64, 82, 71, 74],
    ["Alex Noren", 55, 64, 70, 82, 83],
    ["Emiliano Grillo", 56, 63, 72, 79, 80],
    ["Brendon Todd", 57, 63, 65, 78, 90],
    ["Gary Woodland", 58, 62, 78, 70, 77],
    ["Billy Horschel", 59, 62, 71, 77, 84],
    ["Christiaan Bezuidenhout", 60, 61, 68, 80, 86],
]

COURSE = {
    "tournament": "Current PGA Event",
    "course": "Course updates weekly/manual",
    "latitude": 33.5020,
    "longitude": -82.0228,
    "course_style": "Major-style test",
    "driving_importance": 0.25,
    "iron_importance": 0.35,
    "short_game_importance": 0.20,
    "putting_importance": 0.20,
}


def get_weather(lat, lon):
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&daily=temperature_2m_max,temperature_2m_min,"
        "precipitation_probability_max,windspeed_10m_max"
        "&forecast_days=7"
        "&timezone=auto"
        "&temperature_unit=fahrenheit"
        "&windspeed_unit=mph"
    )

    response = requests.get(url, timeout=30)
    response.raise_for_status()
    data = response.json()

    daily = data["daily"]

    return pd.DataFrame({
        "Date": daily["time"],
        "High Temp": daily["temperature_2m_max"],
        "Low Temp": daily["temperature_2m_min"],
        "Rain Chance %": daily["precipitation_probability_max"],
        "Max Wind MPH": daily["windspeed_10m_max"],
    })


def get_players():
    return pd.DataFrame(
        PLAYERS,
        columns=[
            "Player",
            "World Rank",
            "Base Rating",
            "Driving Rating",
            "Iron Rating",
            "Putting Rating",
        ]
    )


def build_course_fit(players):
    df = players.copy()

    df["Course Fit Score"] = (
        df["Driving Rating"] * COURSE["driving_importance"] +
        df["Iron Rating"] * COURSE["iron_importance"] +
        df["Putting Rating"] * COURSE["putting_importance"] +
        df["Base Rating"] * COURSE["short_game_importance"]
    )

    return df.sort_values("Course Fit Score", ascending=False)


def build_model(players, course_fit, weather):
    model = course_fit.copy()

    avg_wind = weather["Max Wind MPH"].mean()
    avg_rain = weather["Rain Chance %"].mean()

    weather_penalty = 0

    if avg_wind >= 15:
        weather_penalty += 2

    if avg_rain >= 40:
        weather_penalty += 1.5

    model["Weather Difficulty Adjustment"] = weather_penalty

    model["Final Projection Score"] = (
        model["Base Rating"] * 0.40 +
        model["Course Fit Score"] * 0.45 +
        (100 - model["World Rank"]) * 0.15 -
        model["Weather Difficulty Adjustment"]
    )

    model["Projected Rank"] = model["Final Projection Score"].rank(
        ascending=False,
        method="min"
    )

    model = model.sort_values("Projected Rank")

    model["Prediction Tier"] = pd.cut(
        model["Projected Rank"],
        bins=[0, 10, 25, 60],
        labels=["Top Pick", "Strong Play", "Longshot"]
    )

    return model


def write_excel(players, course_fit, weather, model):
    with pd.ExcelWriter(EXCEL_FILE, engine="openpyxl") as writer:
        dashboard = pd.DataFrame({
            "Item": [
                "Last Updated",
                "Tournament",
                "Course",
                "Course Style",
                "Players in Model",
                "Top Projected Player",
                "Average Wind MPH",
                "Average Rain Chance",
                "Model Note",
            ],
            "Value": [
                datetime.now().strftime("%Y-%m-%d %H:%M"),
                COURSE["tournament"],
                COURSE["course"],
                COURSE["course_style"],
                len(players),
                model.iloc[0]["Player"],
                round(weather["Max Wind MPH"].mean(), 1),
                round(weather["Rain Chance %"].mean(), 1),
                "Free starter model using manual player ratings, course fit, and weather.",
            ]
        })

        tournament = pd.DataFrame([COURSE])

        sources = pd.DataFrame({
            "Source": [
                "Open-Meteo Weather",
                "Manual Player Ratings",
                "Manual Course Fit",
                "GitHub Actions"
            ],
            "Purpose": [
                "Free weather forecast",
                "Starter golfer ratings",
                "Course-style weighting",
                "Weekly spreadsheet update"
            ]
        })

        github_setup = pd.DataFrame({
            "Step": [
                "1",
                "2",
                "3",
                "4"
            ],
            "Instruction": [
                "Edit player list in main.py when needed.",
                "Edit course latitude/longitude in main.py for each tournament.",
                "GitHub Actions runs weekly.",
                "Download golf_model.xlsx after workflow finishes."
            ]
        })

        dashboard.to_excel(writer, sheet_name="Dashboard", index=False)
        tournament.to_excel(writer, sheet_name="Tournament", index=False)
        players.to_excel(writer, sheet_name="Players", index=False)
        course_fit.to_excel(writer, sheet_name="CourseFit", index=False)
        weather.to_excel(writer, sheet_name="Weather", index=False)
        model.to_excel(writer, sheet_name="Model", index=False)
        sources.to_excel(writer, sheet_name="Sources", index=False)
        github_setup.to_excel(writer, sheet_name="GitHub_Setup", index=False)


def main():
    players = get_players()
    weather = get_weather(COURSE["latitude"], COURSE["longitude"])
    course_fit = build_course_fit(players)
    model = build_model(players, course_fit, weather)

    write_excel(players, course_fit, weather, model)

    print("Upgraded golf spreadsheet updated successfully.")


if __name__ == "__main__":
    main()
