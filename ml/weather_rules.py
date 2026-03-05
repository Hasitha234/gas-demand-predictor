# ml/weather_rules.py
# Weather influence agent - rule-based multiplier

def get_season(month: int) -> str:
    """Returns Sri Lanka season for a given month number"""
    if month in [5, 6, 7, 8, 9]:
        return "SW_Monsoon"
    elif month in [10, 11, 12, 1]:
        return "NE_Monsoon"
    else:
        return "Dry"

def get_weather_multiplier(weather_influence: int, month: int) -> float:
    """
    Returns a usage multiplier based on user's weather sensitivity
    and current season.

    weather_influence: 0=None, 1=Low, 2=Medium, 3=High
    month: 1-12
    """
    season = get_season(month)

    # Base multiplier from user's weather sensitivity
    sensitivity_map = {0: 1.00, 1: 1.05, 2: 1.10, 3: 1.20}
    base = sensitivity_map.get(weather_influence, 1.0)

    # Season adjustment
    if season == "SW_Monsoon":
        season_factor = 1.10   # rainy = more indoor cooking
    elif season == "NE_Monsoon":
        season_factor = 1.07
    else:
        season_factor = 1.00   # dry season = normal

    # Only apply season factor if user is weather-sensitive
    if weather_influence == 0:
        return 1.0
    else:
        return round(base * season_factor, 3)

def adjust_depletion_days(predicted_days: float, weather_influence: int, month: int) -> int:
    """
    Adjusts predicted depletion days based on weather.
    More usage = fewer days remaining.
    """
    multiplier = get_weather_multiplier(weather_influence, month)
    adjusted = predicted_days / multiplier
    return max(1, int(round(adjusted)))

if __name__ == "__main__":
    # Test the rules
    print("Weather Rules Engine Test")
    print("-" * 40)
    from datetime import datetime
    current_month = datetime.now().month
    print(f"Current month: {current_month} ({get_season(current_month)})")
    print()
    for influence in [0, 1, 2, 3]:
        label = ["None", "Low", "Medium", "High"][influence]
        mult = get_weather_multiplier(influence, current_month)
        adjusted = adjust_depletion_days(30, influence, current_month)
        print(f"  Weather={label:<6} | Multiplier={mult} | 30 days → {adjusted} days")