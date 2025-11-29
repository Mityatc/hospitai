# HospitAI - Quick Start Guide

## Installation

```bash
cd backend
pip install -r requirements.txt
```

## Configuration

Copy `.env.example` to `.env` in the backend folder and configure:

```bash
cd backend
cp .env.example .env
```

Edit `.env`:
```env
# Required for AI features
GEMINI_API_KEY=your-gemini-api-key

# Optional: Live weather data
OPENWEATHER_API_KEY=your-openweather-key
```

## Running the Application

### Option 1: Full Stack (Recommended)

**Terminal 1 - Backend API:**
```bash
cd backend
python -m uvicorn api:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Access at:
- Frontend: http://localhost:8080
- API Docs: http://localhost:8000/docs

### Option 2: Streamlit Dashboard (Legacy)

```bash
cd backend
python -m streamlit run app.py
```

Opens at `http://localhost:8501`

## Dashboard Features

| Feature | Description |
|---------|-------------|
| 📊 Dashboard | Current metrics, capacity gauges, risk score |
| 📈 Trends | Historical charts, environmental data |
| 🔮 Predictions | ML-based forecasts |
| 🤖 AI Agent | Autonomous analysis & recommendations |
| 📤 Data Upload | Import real hospital CSV/Excel data |
| 🎯 Scenarios | What-if simulator (flu, pollution, etc.) |

## Data Upload

Upload your hospital's real data:
- **Required**: `date`, `occupied_beds`, `total_beds`
- **Optional**: `occupied_icu`, `flu_cases`, `temperature`, `pollution`

Missing columns are auto-generated with realistic defaults.

## Testing

```bash
cd backend
python run_app.py      # Full test suite
python test_quick.py   # Quick verification
```

## Troubleshooting

- **Module errors**: Run commands from `backend/` directory
- **Streamlit not found**: `pip install streamlit`
- **AI not working**: Check `GEMINI_API_KEY` in `backend/.env`
- **Frontend errors**: Run `npm install` in `frontend/`
