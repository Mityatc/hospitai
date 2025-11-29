# HospitAI Backend

FastAPI backend for hospital surge prediction system.

## Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your API keys

# Run server
uvicorn main:app --reload --port 8000
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/api/dashboard/summary` | GET | Dashboard data |
| `/api/predictions` | GET | ML predictions |
| `/api/agent/run` | POST | Run AI agent |
| `/api/upload` | POST | Upload hospital data |
| `/api/live-data` | GET | Live weather/AQI |

## Deploy to Render

1. Push to GitHub
2. Connect repo on render.com
3. Set environment variables
4. Deploy

## Environment Variables

- `GEMINI_API_KEY` - Google Gemini API key
- `OPENWEATHER_API_KEY` - OpenWeatherMap API key
- `ALLOWED_ORIGINS` - CORS origins (comma-separated)
