# ml/scripts/train_station_model.py
# Trains Linear Regression models for 7-day station demand forecasting
# (Prophet fallback - works perfectly on Windows)

import pandas as pd
import numpy as np
import pickle
import json
import os
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import LabelEncoder

print("=" * 50)
print("STATION DEMAND FORECAST MODEL TRAINER")
print("(Using Gradient Boosting - Windows compatible)")
print("=" * 50)

# ── Load synthetic station data ─────────────────────
print("\n📂 Loading synthetic station data...")
df = pd.read_csv("data/processed/station_sales_synthetic.csv")
df["date"] = pd.to_datetime(df["date"])
print(f"   Rows: {len(df)}")
print(f"   Stations: {df['station_id'].nunique()}")

# ── Engineer time features ──────────────────────────
print("\n⚙️  Engineering features...")
df["day_of_year"]  = df["date"].dt.dayofyear
df["month"]        = df["date"].dt.month
df["quarter"]      = df["date"].dt.quarter

# Encode season
season_map = {"Dry": 0, "NE_Monsoon": 1, "SW_Monsoon": 2}
df["season_encoded"] = df["season"].map(season_map)

# Encode station type
type_map = {"Urban": 0, "Semi-urban": 1, "Rural": 2}
df["station_type_encoded"] = df["station_type"].map(type_map)

# Lag features — yesterday's and last week's sales
df = df.sort_values(["station_id", "date"])
df["lag_1"]  = df.groupby("station_id")["cylinders_sold"].shift(1)
df["lag_7"]  = df.groupby("station_id")["cylinders_sold"].shift(7)
df["lag_14"] = df.groupby("station_id")["cylinders_sold"].shift(14)

# Rolling average (last 7 days)
df["rolling_mean_7"] = (
    df.groupby("station_id")["cylinders_sold"]
    .transform(lambda x: x.shift(1).rolling(7).mean())
)

# Drop rows where lag features are NaN (first 14 days per station)
df = df.dropna()
print(f"   Rows after feature engineering: {len(df)}")

# ── Define features ─────────────────────────────────
FEATURES = [
    "station_type_encoded",
    "day_of_week",
    "is_weekend",
    "is_festival_week",
    "season_encoded",
    "month",
    "quarter",
    "day_of_year",
    "week_number",
    "supplier_lead_days",
    "lag_1",
    "lag_7",
    "lag_14",
    "rolling_mean_7",
]
TARGET = "cylinders_sold"

# ── Train one model per station ─────────────────────
print("\n⚙️  Training models for each station...\n")

station_models  = {}
station_metrics = []
stations = df["station_id"].unique()

for i, station_id in enumerate(stations):
    station_df = df[df["station_id"] == station_id].copy()

    X = station_df[FEATURES]
    y = station_df[TARGET]

    # 80/20 split — keep time order
    split_idx = int(len(station_df) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    # Train Gradient Boosting model
    model = GradientBoostingRegressor(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        random_state=42
    )
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)

    mae  = mean_absolute_error(y_test, predictions)
    rmse = np.sqrt(mean_squared_error(y_test, predictions))
    mape = np.mean(np.abs((y_test.values - predictions) / (y_test.values + 1))) * 100

    station_models[station_id] = {
        "model":    model,
        "features": FEATURES,
        "type":     station_df["station_type"].iloc[0],
        # Store last 14 days for making future predictions
        "last_data": station_df.tail(14)[["date","cylinders_sold"] + FEATURES].to_dict("records"),
    }

    station_metrics.append({
        "station_id": station_id,
        "type":       station_df["station_type"].iloc[0],
        "mae":        round(mae, 1),
        "rmse":       round(rmse, 1),
        "mape":       round(mape, 1),
    })

    station_type = station_df["station_type"].iloc[0]
    print(f"   [{i+1:02d}/15] {station_id} ({station_type:<10}) | MAE: {mae:.1f} | MAPE: {mape:.1f}%")

# ── Summary ─────────────────────────────────────────
metrics_df = pd.DataFrame(station_metrics)
print(f"\n📊 Model Performance Summary:")
print(f"   Average MAE  : {metrics_df['mae'].mean():.1f} cylinders")
print(f"   Average MAPE : {metrics_df['mape'].mean():.1f}%")
print(f"   Best station : {metrics_df.loc[metrics_df['mape'].idxmin(), 'station_id']}")
print(f"   Worst station: {metrics_df.loc[metrics_df['mape'].idxmax(), 'station_id']}")

# ── Save ────────────────────────────────────────────
os.makedirs("ml", exist_ok=True)

with open("ml/station_models.pkl", "wb") as f:
    pickle.dump(station_models, f)
print("\n✅ Saved ml/station_models.pkl")

with open("ml/station_model_info.json", "w") as f:
    json.dump({
        "stations":  station_metrics,
        "features":  FEATURES,
        "avg_mae":   round(metrics_df["mae"].mean(), 1),
        "avg_mape":  round(metrics_df["mape"].mean(), 1),
    }, f, indent=2)
print("✅ Saved ml/station_model_info.json")

print("\n🎉 Station model training complete!")