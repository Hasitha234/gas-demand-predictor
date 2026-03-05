# backend/models.py
# Pydantic data models (shapes of data going in and out of API)

from pydantic import BaseModel, EmailStr
from typing   import Optional, List
from datetime import datetime

# ── Auth models ─────────────────────────────────────
class UserRegister(BaseModel):
    name:     str
    email:    str
    password: str
    role:     str = "user"  # user / operator / admin

class UserLogin(BaseModel):
    email:    str
    password: str

class UserOut(BaseModel):
    id:    str
    name:  str
    email: str
    role:  str

# ── Household models ────────────────────────────────
class HouseholdInput(BaseModel):
    user_id:           str
    purchase_date:     str        # "YYYY-MM-DD"
    cylinder_size_kg:  float      # 5, 12.5, or 37.5
    household_size:    int        # 1-6
    avg_daily_hours:   float      # hours cooking per day
    cooking_frequency: int        # 1=Once, 2=Twice, 3=Three, 4=More
    area_type:         int        # 0=Urban, 1=Semi-urban, 2=Rural
    residence_type:    int        # 0=House, 1=Apartment, 2=Shared
    primary_usage:     int        # 0-4
    weather_influence: int        # 0=None, 1=Low, 2=Medium, 3=High
    weather_impact_type: int      # 0=No change, 1=Rainy, 2=Cold
    guest_impact:      int        # 0=Never, 1=Rarely, 2=Sometimes, 3=Often

class HouseholdPrediction(BaseModel):
    user_id:                  str
    predicted_days:           int
    weather_adjusted_days:    int
    depletion_date:           str
    purchase_date:            str
    cylinder_size_kg:         float
    weather_multiplier:       float
    alert_message:            str

# ── Station models ──────────────────────────────────
class StationForecastRequest(BaseModel):
    station_id: str

class DayForecast(BaseModel):
    date:           str
    predicted_sales: int
    day_label:      str

class StationForecast(BaseModel):
    station_id:    str
    station_type:  str
    forecast:      List[DayForecast]
    avg_daily:     float
    total_7_day:   int
    alert_message: str