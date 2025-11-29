# HospitAI - Quick Start Guide

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
# Required for GPT features
OPENAI_API_KEY=your-openai-api-key

# Optional: Remote ML inference
REMOTE_MODE=false
REMOTE_URL=https://api.pipeshift.ai/hospitai
PIPESHIFT_TOKEN=your-token
```

## Running the Dashboard

```bash
python -m streamlit run app.py
```

Opens at `http://localhost:8501`

## Dashboard Tabs

| Tab | Description |
|-----|-------------|
| 📊 Summary | Current metrics, capacity gauges, risk score |
| 📈 Trends | Historical charts, environmental data |
| 🔮 Predictions | ML-based forecasts (local or Pipeshift) |
| 🎯 Scenarios | What-if simulator (flu, pollution, etc.) |
| 🏥 Compare | Multi-hospital comparison |
| 📥 Export | CSV, reports, GPT summaries |

## Features

### Core
- Seasonal data patterns (winter flu peaks, weekend effects)
- 6-factor risk scoring
- Resource tracking (ICU, ventilators, staff, meds)

### AI Integration
- **OpenAI GPT**: Admin reports, patient advisories
- **Pipeshift**: Remote ML inference endpoint

### Scenarios
- 🤒 Flu Outbreak
- 🌫️ Pollution Spike
- 🚨 Mass Casualty
- 👥 Staff Shortage
- 🔧 Equipment Failure
- 🌡️ Heatwave

## Optional Enhancements

| File | Requires |
|------|----------|
| `gpt_module.py` | `OPENAI_API_KEY` in `.env` |
| Remote inference | `REMOTE_URL` + `PIPESHIFT_TOKEN` in `.env` |

## Testing

```bash
python run_app.py      # Full test suite
python test_quick.py   # Quick verification
```

## Troubleshooting

- **Module errors**: Ensure all files in same directory
- **Streamlit not found**: `pip install streamlit`
- **GPT not working**: Check `OPENAI_API_KEY` in `.env`
- **Remote inference fails**: Falls back to local automatically
