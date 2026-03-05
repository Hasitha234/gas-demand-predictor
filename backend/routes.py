# backend/routes.py
# All API endpoints

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timedelta
from typing import List
import os
from jose import jwt
from passlib.context import CryptContext
from bson import ObjectId

from backend.models import (
    UserRegister, UserLogin, UserOut,
    HouseholdInput, HouseholdPrediction,
    StationForecastRequest, StationForecast,
)
from backend.database import get_db
from backend.agents import (
    orchestrate_household_prediction,
    orchestrate_station_forecast,
)

router   = APIRouter()
pwd_ctx  = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET   = os.getenv("SECRET_KEY", "secret")
ALGO     = os.getenv("ALGORITHM", "HS256")

# ── Helpers ──────────────────────────────────────────
def hash_password(password: str) -> str:
    return pwd_ctx.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)

def create_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(minutes=10080)
    return jwt.encode(payload, SECRET, algorithm=ALGO)

def obj_id(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    return doc

# ── Health check ─────────────────────────────────────
@router.get("/")
async def root():
    return {"message": "Gas Demand Predictor API is running ✅", "version": "1.0"}

@router.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

# ── Auth routes ──────────────────────────────────────
@router.post("/auth/register")
async def register(user: UserRegister):
    db = get_db()
    existing = await db.users.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = {
        "name":       user.name,
        "email":      user.email,
        "password":   hash_password(user.password),
        "role":       user.role,
        "created_at": datetime.now().isoformat(),
    }
    result = await db.users.insert_one(new_user)
    token  = create_token({"sub": str(result.inserted_id), "role": user.role})
    return {"token": token, "user": {"id": str(result.inserted_id),
            "name": user.name, "email": user.email, "role": user.role}}

@router.post("/auth/login")
async def login(creds: UserLogin):
    db   = get_db()
    user = await db.users.find_one({"email": creds.email})
    if not user or not verify_password(creds.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_token({"sub": str(user["_id"]), "role": user["role"]})
    return {"token": token, "user": {"id": str(user["_id"]),
            "name": user["name"], "email": user["email"], "role": user["role"]}}

# ── Household routes ─────────────────────────────────
@router.post("/household/predict")
async def predict_household(data: HouseholdInput):
    db = get_db()

    # Run orchestrator
    result = orchestrate_household_prediction(data.dict())

    # Save to database
    record = {**data.dict(), **result, "created_at": datetime.now().isoformat()}
    await db.gas_usage.insert_one(record)

    return result

@router.get("/household/history/{user_id}")
async def household_history(user_id: str):
    db   = get_db()
    docs = await db.gas_usage.find(
        {"user_id": user_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(10).to_list(length=10)
    return {"history": docs}

# ── Station routes ───────────────────────────────────
@router.get("/station/forecast/{station_id}")
async def station_forecast(station_id: str):
    db     = get_db()
    result = orchestrate_station_forecast(station_id)

    # Save prediction to database
    record = {**result, "generated_at": datetime.now().isoformat()}
    await db.predictions.insert_one(record)

    return result

@router.get("/station/list")
async def list_stations():
    import json
    with open("ml/station_model_info.json") as f:
        info = json.load(f)
    stations = [{"station_id": s["station_id"],
                 "station_type": s["type"],
                 "mae": s["mae"]} for s in info["stations"]]
    return {"stations": stations}

# ── Dashboard stats ──────────────────────────────────
@router.get("/stats")
async def get_stats():
    db = get_db()
    total_users       = await db.users.count_documents({})
    total_predictions = await db.gas_usage.count_documents({})
    total_station_preds = await db.predictions.count_documents({})
    return {
        "total_users":           total_users,
        "total_predictions":     total_predictions,
        "station_predictions":   total_station_preds,
        "last_updated":          datetime.now().isoformat(),
    }