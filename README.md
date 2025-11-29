# HospitAI

AI-powered hospital surge prediction and capacity management system.

## Project Structure

```
hospitai/
├── backend/          # FastAPI Python backend
│   ├── main.py       # API endpoints
│   ├── ai_agent.py   # AI agent system
│   └── ...
├── frontend/         # React TypeScript frontend
│   ├── src/
│   └── ...
└── README.md
```

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env
# Add your API keys to .env
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
# Set VITE_API_URL to your backend URL
npm run dev
```

## Deployment

### Backend → Render.com

1. Create new Web Service on Render
2. Connect GitHub repo
3. Root Directory: `backend`
4. Build: `pip install -r requirements.txt`
5. Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Add environment variables

### Frontend → Vercel

1. Import project on Vercel
2. Root Directory: `frontend`
3. Framework: Vite
4. Add `VITE_API_URL` environment variable

## Features

- Real-time hospital capacity monitoring
- ML-based surge predictions
- AI agent for automated recommendations
- Live weather and air quality data
- CSV/Excel data upload
- Interactive dashboards

## Tech Stack

- **Backend**: FastAPI, Python, scikit-learn, Google Gemini
- **Frontend**: React, TypeScript, Vite, Tailwind CSS, shadcn/ui
