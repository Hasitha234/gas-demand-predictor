# ⛽ Gas Demand Predictor

AI-powered LPG gas demand prediction and auto-refill suggestion system for Sri Lanka.

## Features

- 🏠 **Household Prediction** — Predicts exact gas depletion date based on usage habits
- 📊 **Station Forecasting** — 7-day demand forecast for gas station operators
- 🤖 **Agentic Architecture** — 3 AI agents (Usage, Weather, Demand) + Orchestrator
- 🔊 **Voice Alerts** — Browser-based voice notifications
- 📧 **Email Alerts** — Automatic email when gas is running low
- 📱 **Web Dashboard** — React frontend with charts and analytics

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite + Recharts |
| Backend | FastAPI (Python) |
| Database | MongoDB Atlas |
| ML Models | Random Forest + Gradient Boosting |
| Notifications | Gmail SMTP + Web Speech API |

## Project Structure
```
gas-demand-predictor/
├── backend/          # FastAPI backend
│   ├── main.py       # App entry point
│   ├── agents.py     # AI agents + orchestrator
│   ├── routes.py     # API endpoints
│   ├── models.py     # Data models
│   ├── database.py   # MongoDB connection
│   └── notifications.py  # Email system
├── frontend/         # React web app
│   └── src/
│       ├── pages/    # Home, Login, Register, Household, Station
│       └── components/
├── ml/               # Machine learning
│   ├── scripts/      # Data prep + training scripts
│   ├── weather_rules.py
│   └── *.json        # Model info files
├── data/
│   ├── raw/          # Original datasets
│   └── processed/    # Cleaned + synthetic datasets
└── .env.example      # Environment variable template
```

## Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/gas-demand-predictor.git
cd gas-demand-predictor
```

### 2. Set up Python environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
```

### 3. Configure environment variables
```bash
cp .env.example .env
# Edit .env with your MongoDB URL and Gmail credentials
```

### 4. Prepare data and train models
```bash
python ml/scripts/household_data_merger.py
python ml/scripts/synthetic_station_data_generator.py
python ml/scripts/train_household_model.py
python ml/scripts/train_station_model.py
```

### 5. Start the backend
```bash
python -m uvicorn backend.main:app --reload --port 8000
```

### 6. Start the frontend
```bash
cd frontend
npm install
npm run dev
```

### 7. Open in browser
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs

## ML Models

| Model | Algorithm | Purpose | MAE |
|---|---|---|---|
| Household Depletion | Random Forest | Predict days until gas runs out | ~15 days |
| Station Demand | Gradient Boosting | 7-day cylinder sales forecast | ~20 cylinders |
| Weather Agent | Rule Engine | Adjust predictions by season | N/A |

## Dataset Sources

- `household_filtered.csv` — 877 household usage records (real survey data)
- `household_gas_data.csv` — 877 enriched household survey responses (real)
- `gas_station_survey.csv` — 55 gas station operator survey responses (real)
- `station_sales_synthetic.csv` — 5,475 daily sales records (synthetically generated from survey statistics)

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | /api/auth/register | Register new user |
| POST | /api/auth/login | Login |
| POST | /api/household/predict | Get depletion prediction |
| GET | /api/station/forecast/{id} | Get 7-day forecast |
| GET | /api/station/list | List all stations |
| GET | /api/stats | System statistics |

## Research Prototype

This is a research prototype demonstrating predictive modeling and modular agent-based architecture for LPG management in Sri Lanka.