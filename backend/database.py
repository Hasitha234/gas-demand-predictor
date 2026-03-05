# backend/database.py
# MongoDB Atlas connection

import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL   = os.getenv("MONGODB_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME", "gas_predictor")

client = None
db     = None

async def connect_db():
    global client, db
    client = AsyncIOMotorClient(MONGODB_URL)
    db     = client[DATABASE_NAME]
    print(f"✅ Connected to MongoDB Atlas: {DATABASE_NAME}")

async def close_db():
    global client
    if client:
        client.close()
        print("🔌 MongoDB connection closed")

def get_db():
    return db