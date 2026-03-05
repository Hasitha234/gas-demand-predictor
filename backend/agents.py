# backend/agents.py
# The three agents + orchestrator

import pickle
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add project root to path so we can import weather_rules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ml.weather_rules import get_weather_multiplier, adjust_depletion_days

# ── Load models once when server starts ────────────
print("📦 Loading ML models...")

with open("ml/household_model.pkl", "rb") as f:
    HOUSEHOLD_MODEL = pickle.load(f)

with open("ml/household_model_info.json") as f:
    HOUSEHOLD_INFO = json.load(f)

with open("ml/station_models.pkl", "rb") as f:
    STATION_MODELS = pickle.load(f)

with open("ml/station_model_info.json") as f:
    STATION_INFO = json.load(f)

print("✅ Models loaded successfully")

# ════════════════════════════════════════════════════
# AGENT 1: Usage Behavior Agent
# Predicts how many days until gas runs out
# ════════════════════════════════════════════════════
def usage_behavior_agent(input_data: dict) -> int:
    """
    Takes household input and returns predicted depletion days.
    """
    features = HOUSEHOLD_INFO["features"]

    row = pd.DataFrame([{
        "area_type":          input_data["area_type"],
        "num_people":         input_data["household_size"],
        "avg_daily_hours":    input_data["avg_daily_hours"],
        "cylinder_size_kg":   input_data["cylinder_size_kg"],
        "weather_influence":  input_data["weather_influence"],
        "residence_type":     input_data["residence_type"],
        "cooking_frequency":  input_data["cooking_frequency"],
        "primary_usage":      input_data["primary_usage"],
        "weather_impact_type":input_data["weather_impact_type"],
        "guest_impact":       input_data["guest_impact"],
    }])

    predicted_days = HOUSEHOLD_MODEL.predict(row)[0]
    return max(1, int(round(predicted_days)))


# ════════════════════════════════════════════════════
# AGENT 2: Weather Influence Agent
# Adjusts depletion days based on season + sensitivity
# ════════════════════════════════════════════════════
def weather_influence_agent(predicted_days: int, weather_influence: int) -> dict:
    """
    Adjusts predicted days using current season weather multiplier.
    """
    current_month = datetime.now().month
    multiplier    = get_weather_multiplier(weather_influence, current_month)
    adjusted_days = adjust_depletion_days(predicted_days, weather_influence, current_month)

    return {
        "original_days":  predicted_days,
        "adjusted_days":  adjusted_days,
        "multiplier":     multiplier,
        "month":          current_month,
    }


# ════════════════════════════════════════════════════
# AGENT 3: Historical Demand Agent
# Forecasts next 7 days of sales for a station
# ════════════════════════════════════════════════════
def historical_demand_agent(station_id: str) -> dict:
    """
    Generates a 7-day sales forecast for a given station.
    """
    if station_id not in STATION_MODELS:
        # Return a default forecast for unknown stations
        today = datetime.now()
        forecast = []
        for i in range(1, 8):
            day = today + timedelta(days=i)
            forecast.append({
                "date":            day.strftime("%Y-%m-%d"),
                "predicted_sales": 100,
                "day_label":       day.strftime("%A"),
            })
        return {"station_id": station_id, "station_type": "Unknown",
                "forecast": forecast, "avg_daily": 100, "total_7_day": 700}

    station_data = STATION_MODELS[station_id]
    model        = station_data["model"]
    features     = station_data["features"]
    station_type = station_data["type"]

    # Get last known data to build lag features
    last_records = station_data["last_data"]
    last_sales   = [r["cylinders_sold"] for r in last_records]

    today    = datetime.now()
    forecast = []

    def get_season_encoded(month):
        if month in [5,6,7,8,9]: return 2   # SW_Monsoon
        if month in [10,11,12,1]: return 1   # NE_Monsoon
        return 0                             # Dry

    type_map = {"Urban": 0, "Semi-urban": 1, "Rural": 2}

    festival_dates = [
        "2025-01-15","2025-02-04","2025-04-12","2025-04-13","2025-04-14",
        "2025-05-12","2025-06-11","2025-10-20","2025-12-25","2025-12-31",
        "2026-01-15","2026-02-04","2026-04-13","2026-04-14","2026-04-15",
    ]
    festival_dates_dt = pd.to_datetime(festival_dates)

    rolling_sales = list(last_sales)  # grows as we predict forward

    for i in range(1, 8):
        future_date  = today + timedelta(days=i)
        is_weekend   = int(future_date.weekday() >= 5)
        is_festival  = int(any(abs((future_date - fd).days) <= 2 for fd in festival_dates_dt))

        lag1  = rolling_sales[-1]  if len(rolling_sales) >= 1  else 100
        lag7  = rolling_sales[-7]  if len(rolling_sales) >= 7  else 100
        lag14 = rolling_sales[-14] if len(rolling_sales) >= 14 else 100
        roll7 = np.mean(rolling_sales[-7:]) if len(rolling_sales) >= 7 else 100

        row = pd.DataFrame([{
            "station_type_encoded": type_map.get(station_type, 0),
            "day_of_week":          future_date.weekday(),
            "is_weekend":           is_weekend,
            "is_festival_week":     is_festival,
            "season_encoded":       get_season_encoded(future_date.month),
            "month":                future_date.month,
            "quarter":              (future_date.month - 1) // 3 + 1,
            "day_of_year":          future_date.timetuple().tm_yday,
            "week_number":          future_date.isocalendar()[1],
            "supplier_lead_days":   last_records[-1].get("supplier_lead_days", 5),
            "lag_1":                lag1,
            "lag_7":                lag7,
            "lag_14":               lag14,
            "rolling_mean_7":       roll7,
        }])

        predicted = max(0, int(round(model.predict(row)[0])))
        rolling_sales.append(predicted)

        forecast.append({
            "date":             future_date.strftime("%Y-%m-%d"),
            "predicted_sales":  predicted,
            "day_label":        future_date.strftime("%A"),
        })

    avg_daily  = round(sum(f["predicted_sales"] for f in forecast) / 7, 1)
    total_7day = sum(f["predicted_sales"] for f in forecast)

    return {
        "station_id":   station_id,
        "station_type": station_type,
        "forecast":     forecast,
        "avg_daily":    avg_daily,
        "total_7_day":  total_7day,
    }


# ════════════════════════════════════════════════════
# ORCHESTRATOR — combines all 3 agents
# ════════════════════════════════════════════════════
def orchestrate_household_prediction(input_data: dict) -> dict:
    """
    Runs all 3 agents and returns final combined prediction.
    """
    # Agent 1: base prediction
    base_days = usage_behavior_agent(input_data)

    # Agent 2: weather adjustment
    weather_result = weather_influence_agent(base_days, input_data["weather_influence"])
    final_days     = weather_result["adjusted_days"]

    # Calculate depletion date
    purchase_date  = datetime.strptime(input_data["purchase_date"], "%Y-%m-%d")
    depletion_date = purchase_date + timedelta(days=final_days)
    days_left      = (depletion_date - datetime.now()).days

    # Build alert message
    if days_left <= 3:
        alert = f"🚨 URGENT: Your gas cylinder is expected to run out in {days_left} days! Order now."
    elif days_left <= 7:
        alert = f"⚠️ WARNING: Your gas cylinder will run out in {days_left} days. Plan your refill soon."
    else:
        alert = f"✅ Your gas cylinder is expected to last {days_left} more days (until {depletion_date.strftime('%B %d, %Y')})."

    return {
        "user_id":               input_data["user_id"],
        "predicted_days":        base_days,
        "weather_adjusted_days": final_days,
        "depletion_date":        depletion_date.strftime("%Y-%m-%d"),
        "purchase_date":         input_data["purchase_date"],
        "cylinder_size_kg":      input_data["cylinder_size_kg"],
        "weather_multiplier":    weather_result["multiplier"],
        "days_left":             days_left,
        "alert_message":         alert,
    }


def orchestrate_station_forecast(station_id: str) -> dict:
    """
    Runs Historical Demand Agent and adds alert message.
    """
    result = historical_demand_agent(station_id)

    # Build alert
    total = result["total_7_day"]
    avg   = result["avg_daily"]
    if avg > 300:
        alert = f"🚨 HIGH DEMAND: Expect ~{int(avg)} cylinders/day. Consider emergency restocking."
    elif avg > 150:
        alert = f"⚠️ MODERATE DEMAND: ~{int(avg)} cylinders/day expected. Monitor stock closely."
    else:
        alert = f"✅ NORMAL DEMAND: ~{int(avg)} cylinders/day expected over next 7 days."

    result["alert_message"] = alert
    return result