# ml/scripts/train_household_model.py
# Trains a Random Forest model to predict household gas depletion days

import pandas as pd
import numpy as np
import pickle
import os
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler

print("=" * 50)
print("HOUSEHOLD DEPLETION MODEL TRAINER")
print("=" * 50)

# ── Load data ───────────────────────────────────────
print("\n📂 Loading cleaned household data...")
df = pd.read_csv("data/processed/household_merged_clean.csv")
print(f"   Rows: {len(df)}, Columns: {len(df.columns)}")

# ── Define features and target ──────────────────────
FEATURES = [
    "area_type",
    "num_people",
    "avg_daily_hours",
    "cylinder_size_kg",
    "weather_influence",
    "residence_type",
    "cooking_frequency",
    "primary_usage",
    "weather_impact_type",
    "guest_impact",
]
TARGET = "usual_duration_days"

X = df[FEATURES]
y = df[TARGET]

print(f"\n   Features: {FEATURES}")
print(f"   Target: {TARGET}")
print(f"   Target range: {y.min()} - {y.max()} days")

# ── Split data ──────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
print(f"\n   Train size: {len(X_train)} rows")
print(f"   Test size:  {len(X_test)} rows")

# ── Train Random Forest ─────────────────────────────
print("\n⚙️  Training Random Forest model...")
rf_model = RandomForestRegressor(
    n_estimators=200,
    max_depth=10,
    min_samples_split=5,
    random_state=42
)
rf_model.fit(X_train, y_train)
rf_predictions = rf_model.predict(X_test)

rf_mae  = mean_absolute_error(y_test, rf_predictions)
rf_rmse = np.sqrt(mean_squared_error(y_test, rf_predictions))
rf_r2   = r2_score(y_test, rf_predictions)

print(f"   ✅ Random Forest trained")
print(f"   MAE  : {rf_mae:.2f} days  (avg prediction error)")
print(f"   RMSE : {rf_rmse:.2f} days")
print(f"   R²   : {rf_r2:.3f}  (1.0 = perfect)")

# ── Train Linear Regression (baseline) ─────────────
print("\n⚙️  Training Linear Regression (baseline)...")
lr_model = LinearRegression()
lr_model.fit(X_train, y_train)
lr_predictions = lr_model.predict(X_test)

lr_mae  = mean_absolute_error(y_test, lr_predictions)
lr_rmse = np.sqrt(mean_squared_error(y_test, lr_predictions))
lr_r2   = r2_score(y_test, lr_predictions)

print(f"   ✅ Linear Regression trained")
print(f"   MAE  : {lr_mae:.2f} days")
print(f"   RMSE : {lr_rmse:.2f} days")
print(f"   R²   : {lr_r2:.3f}")

# ── Feature importance ──────────────────────────────
print("\n📊 Feature Importance (Random Forest):")
importances = pd.Series(rf_model.feature_importances_, index=FEATURES)
importances = importances.sort_values(ascending=False)
for feat, score in importances.items():
    bar = "█" * int(score * 50)
    print(f"   {feat:<25} {bar} {score:.3f}")

# ── Save models ─────────────────────────────────────
os.makedirs("ml", exist_ok=True)

with open("ml/household_model.pkl", "wb") as f:
    pickle.dump(rf_model, f)
print("\n✅ Saved ml/household_model.pkl")

with open("ml/household_model_lr.pkl", "wb") as f:
    pickle.dump(lr_model, f)
print("✅ Saved ml/household_model_lr.pkl")

# Save feature list so backend knows what columns to send
import json
model_info = {
    "features": FEATURES,
    "target": TARGET,
    "rf_mae": round(rf_mae, 2),
    "rf_r2": round(rf_r2, 3),
    "lr_mae": round(lr_mae, 2),
}
with open("ml/household_model_info.json", "w") as f:
    json.dump(model_info, f, indent=2)
print("✅ Saved ml/household_model_info.json")

print("\n🎉 Household model training complete!")