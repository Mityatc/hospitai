# HospitAI Dashboard

AI-powered hospital surge prediction system that forecasts patient influx based on environmental factors and disease trends.

## Overview

HospitAI helps hospitals anticipate patient surges by analyzing:
- Environmental data (pollution, temperature, humidity)
- Disease trends (flu cases)
- Hospital capacity metrics (bed occupancy)
- AI-powered autonomous agent for proactive decision-making

The system uses both rule-based and ML-based prediction models to provide early warnings and actionable insights.

## Architecture

HospitAI now has two interfaces:
1. **React Frontend** (Recommended) - Modern, responsive dashboard with real-time updates
2. **Streamlit Dashboard** (Legacy) - Original Python-based interface

## Project Structure

```
HospitAI/
├── api.py                  # FastAPI backend for React frontend
├── app.py                  # Streamlit dashboard (legacy)
├── ai_agent.py             # Autonomous AI agent system
├── data_generator.py       # Simulates hospital and environmental data
├── predictor_rulebased.py  # Rule-based surge prediction logic
├── predictor_ml.py         # ML-based prediction (linear regression)
├── real_data_api.py        # Live weather/AQI API integration
├── gpt_module.py           # Google Gemini AI integration
├── charts.py               # Chart rendering functions
├── alerts.py               # Alert banner logic
├── advisories.py           # Patient health advisories
├── requirements.txt        # Python dependencies
├── start_dev.bat           # Windows startup script
├── frontend/               # React frontend application
│   ├── src/
│   │   ├── pages/          # Dashboard, AIAgent, Predictions pages
│   │   ├── components/     # Reusable UI components
│   │   ├── hooks/          # React Query hooks for API
│   │   └── lib/            # API service & utilities
│   └── package.json
└── README.md
```

## Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm or yarn

### Backend Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Create .env file with API keys (optional)
cp .env.example .env
# Edit .env and add your API keys:
# - OPENWEATHER_API_KEY (for live weather data)
# - GEMINI_API_KEY (for AI analysis)
```

### Frontend Setup
```bash
cd frontend
npm install
```

## Usage

### Quick Start (Windows)
```bash
# Run both backend and frontend
start_dev.bat
```

### Manual Start

**Terminal 1 - Backend API:**
```bash
python -m uvicorn api:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Access the Application
- **Frontend Dashboard**: http://localhost:8080
- **API Documentation**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000

### Legacy Streamlit Dashboard
```bash
streamlit run app.py
```

## Features

### React Dashboard
- **Dashboard** - Real-time metrics, capacity gauges, trend charts
- **AI Agent** - Autonomous analysis with approve/reject workflow
- **Predictions** - ML-based forecasts with confidence intervals

### AI Agent Capabilities
The autonomous AI agent uses a ReAct architecture:
1. **PERCEIVE** - Gathers hospital metrics and environmental data
2. **REASON** - Analyzes patterns and identifies issues
3. **PLAN** - Generates prioritized action recommendations
4. **EXECUTE** - Auto-executes safe actions or queues for approval

### Monitored Thresholds
| Metric | Warning | Critical |
|--------|---------|----------|
| Bed Occupancy | 75% | 90% |
| ICU Occupancy | 70% | 85% |
| Ventilator Usage | 60% | 80% |
| Staff Ratio | - | < 0.15 |
| Air Quality (AQI) | 100 | 150 |

### API Endpoints
| Endpoint | Description |
|----------|-------------|
| `GET /api/dashboard/summary` | Complete dashboard data |
| `GET /api/dashboard/trends` | Historical trend data |
| `GET /api/predictions` | ML predictions |
| `POST /api/agent/run` | Run AI agent analysis |
| `POST /api/agent/approve/{id}` | Approve pending action |
| `GET /api/alerts` | Current alerts |
| `GET /api/live-data` | Live environmental data |

## Configuration

### Environment Variables
```env
# .env file
OPENWEATHER_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
```

### Frontend Configuration
```env
# frontend/.env
VITE_API_URL=http://localhost:8000
```

## Tech Stack

### Backend
- Python 3.10+
- FastAPI
- Pandas, NumPy, Scikit-learn
- Google Generative AI (Gemini)

### Frontend
- React 18 + TypeScript
- Vite
- Tailwind CSS
- Shadcn/ui components
- Recharts
- React Query

## License

MIT License - Feel free to use and modify for your needs.
