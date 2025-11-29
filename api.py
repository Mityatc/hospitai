"""
HospitAI FastAPI Backend
REST API for hospital surge prediction and capacity management.
"""

import io
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ai_agent import HospitAIAgent, get_agent_log
from data_generator import generate_data
from predictor_ml import predict_ml
from predictor_rulebased import get_risk_breakdown, predict_surge
from real_data_api import check_api_status, get_realtime_data

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
MAX_UPLOAD_SIZE_MB = 10
MAX_UPLOAD_ROWS = 10000
ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls"}
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]


def convert_numpy(obj: Any) -> Any:
    """Recursively convert numpy types to Python native types."""
    if isinstance(obj, dict):
        return {k: convert_numpy(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy(item) for item in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.bool_):
        return bool(obj)
    return obj


app = FastAPI(
    title="HospitAI API",
    description="AI-powered hospital surge prediction system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

# Application state
agent_instance: Optional[HospitAIAgent] = None
current_data: Optional[pd.DataFrame] = None
uploaded_data: Dict[str, pd.DataFrame] = {}


# Pydantic models
class HospitalMetrics(BaseModel):
    total_beds: int
    occupied_beds: int
    bed_occupancy: float
    total_icu: int
    occupied_icu: int
    icu_occupancy: float
    total_ventilators: int
    ventilators_used: int
    ventilator_usage: float
    staff_on_duty: int
    staff_ratio: float


class RiskFactor(BaseModel):
    name: str
    value: float
    threshold: float
    triggered: bool


class EnvironmentData(BaseModel):
    temperature: float
    humidity: int
    aqi: int
    flu_cases: int


# Helper functions
def get_or_generate_data(hospital_id: str = "H001", days: int = 30) -> pd.DataFrame:
    """Retrieve uploaded data if available, otherwise generate simulated data."""
    global current_data, uploaded_data

    if hospital_id in uploaded_data:
        df = uploaded_data[hospital_id].copy()
        if len(df) > days:
            df = df.tail(days)
        df = predict_surge(df)
        current_data = df
        return df

    if "UPLOADED" in uploaded_data and hospital_id == "UPLOADED":
        df = uploaded_data["UPLOADED"].copy()
        if len(df) > days:
            df = df.tail(days)
        df = predict_surge(df)
        current_data = df
        return df

    df = generate_data(num_days=days, hospital_id=hospital_id)
    df = predict_surge(df)
    current_data = df
    return df


def build_dashboard_response(df: pd.DataFrame, hospital_id: str = "H001") -> Dict:
    """Transform DataFrame into dashboard response format."""
    latest = df.iloc[-1]

    bed_change_1d = int(df["occupied_beds"].iloc[-1] - df["occupied_beds"].iloc[-2]) if len(df) >= 2 else 0
    bed_change_3d = int(df["occupied_beds"].iloc[-1] - df["occupied_beds"].iloc[-3]) if len(df) >= 3 else 0
    bed_change_7d = int(df["occupied_beds"].iloc[-1] - df["occupied_beds"].iloc[-7]) if len(df) >= 7 else 0
    icu_change_1d = int(df["occupied_icu"].iloc[-1] - df["occupied_icu"].iloc[-2]) if len(df) >= 2 else 0

    if bed_change_3d > 10:
        direction = "increasing"
        velocity = "rapid" if bed_change_3d > 20 else "moderate"
    elif bed_change_3d < -10:
        direction = "decreasing"
        velocity = "rapid" if bed_change_3d < -20 else "moderate"
    else:
        direction = "stable"
        velocity = "slow"

    breakdown = get_risk_breakdown(df)

    risk_factors = [
        {"name": "Flu Cases", "value": float(round(latest.get("flu_cases", 0), 1)), "threshold": 50, "triggered": bool(latest.get("flu_cases", 0) > 50)},
        {"name": "Air Quality", "value": float(round(latest.get("pollution", 0), 1)), "threshold": 100, "triggered": bool(latest.get("pollution", 0) > 100)},
        {"name": "Staff Ratio", "value": float(round(latest["staff_on_duty"] / max(latest["occupied_beds"], 1), 2)), "threshold": 1.0, "triggered": bool((latest["staff_on_duty"] / max(latest["occupied_beds"], 1)) < 1.0)},
        {"name": "Bed Occupancy", "value": float(round((latest["occupied_beds"] / latest["total_beds"]) * 100, 1)), "threshold": 80, "triggered": bool((latest["occupied_beds"] / latest["total_beds"]) > 0.8)},
        {"name": "ICU Occupancy", "value": float(round((latest["occupied_icu"] / latest["total_icu_beds"]) * 100, 1)), "threshold": 75, "triggered": bool((latest["occupied_icu"] / latest["total_icu_beds"]) > 0.75)},
        {"name": "Ventilator Usage", "value": float(round((latest["ventilators_used"] / latest["total_ventilators"]) * 100, 1)), "threshold": 70, "triggered": bool((latest["ventilators_used"] / latest["total_ventilators"]) > 0.7)},
    ]

    triggered_count = sum(1 for f in risk_factors if f["triggered"])

    result = {
        "hospital": {
            "id": hospital_id,
            "name": str(latest.get("hospital_name", "City General Hospital")),
            "location": "Delhi",
        },
        "metrics": {
            "total_beds": int(latest["total_beds"]),
            "occupied_beds": int(latest["occupied_beds"]),
            "bed_occupancy": float(round((latest["occupied_beds"] / latest["total_beds"]) * 100, 1)),
            "total_icu": int(latest["total_icu_beds"]),
            "occupied_icu": int(latest["occupied_icu"]),
            "icu_occupancy": float(round((latest["occupied_icu"] / latest["total_icu_beds"]) * 100, 1)),
            "total_ventilators": int(latest["total_ventilators"]),
            "ventilators_used": int(latest["ventilators_used"]),
            "ventilator_usage": float(round((latest["ventilators_used"] / latest["total_ventilators"]) * 100, 1)),
            "staff_on_duty": int(latest["staff_on_duty"]),
            "staff_ratio": float(round(latest["staff_on_duty"] / max(latest["occupied_beds"], 1), 2)),
        },
        "risk": {
            "score": int(triggered_count),
            "max_score": 6,
            "level": str(breakdown["risk_level"]),
            "factors": risk_factors,
        },
        "environment": {
            "temperature": float(round(latest.get("temperature", 20), 1)),
            "humidity": int(latest.get("humidity", 65)),
            "aqi": int(latest.get("pollution", 50)),
            "flu_cases": int(latest.get("flu_cases", 0)),
        },
        "trends": {
            "bed_change_1d": int(bed_change_1d),
            "bed_change_3d": int(bed_change_3d),
            "bed_change_7d": int(bed_change_7d),
            "icu_change_1d": int(icu_change_1d),
            "direction": direction,
            "velocity": velocity,
        },
        "timestamp": datetime.now().isoformat(),
    }

    return convert_numpy(result)


# API Endpoints

@app.get("/")
async def health_check():
    """API health check endpoint."""
    return {"status": "healthy", "service": "HospitAI API", "version": "1.0.0"}


@app.get("/api/dashboard/summary")
async def get_dashboard_summary(
    hospital_id: str = Query("H001", max_length=50),
    days: int = Query(30, ge=1, le=365),
):
    """Get complete dashboard summary for a hospital."""
    try:
        df = get_or_generate_data(hospital_id, days)
        return build_dashboard_response(df, hospital_id)
    except Exception as e:
        logger.error(f"Dashboard summary error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard data")


@app.get("/api/dashboard/metrics")
async def get_metrics(hospital_id: str = Query("H001", max_length=50)):
    """Get current hospital metrics."""
    try:
        df = get_or_generate_data(hospital_id)
        response = build_dashboard_response(df, hospital_id)
        return response["metrics"]
    except Exception as e:
        logger.error(f"Metrics error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")


@app.get("/api/dashboard/trends")
async def get_trends(
    hospital_id: str = Query("H001", max_length=50),
    days: int = Query(30, ge=1, le=365),
):
    """Get historical trend data for charts."""
    try:
        df = get_or_generate_data(hospital_id, days)

        trends = []
        for i, (idx, row) in enumerate(df.iterrows()):
            date_val = row.get("date", idx)
            date_str = date_val.strftime("%b %d") if hasattr(date_val, "strftime") else str(date_val)[:10]

            trends.append({
                "date": date_str,
                "beds": int(row["occupied_beds"]),
                "icu": int(row["occupied_icu"]),
                "admissions": int(row.get("admissions", 8 + (i % 5))),
                "discharges": int(row.get("discharges", 6 + (i % 4))),
            })

        return {"data": convert_numpy(trends), "days": days}
    except Exception as e:
        logger.error(f"Trends error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve trends")


@app.get("/api/predictions")
async def get_predictions(
    hospital_id: str = Query("H001", max_length=50),
    days: int = Query(7, ge=1, le=14),
):
    """Get ML predictions for future capacity."""
    try:
        df = get_or_generate_data(hospital_id, 30)
        predictions = predict_ml(df, days=days)

        result = []

        for idx, row in df.iterrows():
            date_val = row.get("date", idx)
            date_str = date_val.strftime("%b %d") if hasattr(date_val, "strftime") else str(date_val)[:10]

            result.append({
                "date": date_str,
                "actual": int(row["occupied_beds"]),
                "predicted": None,
                "upper_bound": None,
                "lower_bound": None,
                "risk_level": None,
            })

        if predictions is not None:
            total_beds = int(df["total_beds"].iloc[0])
            for i, (date, value) in enumerate(predictions.items()):
                pred_value = int(value)
                occupancy = (pred_value / total_beds) * 100

                if occupancy >= 90:
                    risk = "Critical"
                elif occupancy >= 80:
                    risk = "High"
                elif occupancy >= 70:
                    risk = "Medium"
                else:
                    risk = "Low"

                result.append({
                    "date": date.strftime("%b %d") if hasattr(date, "strftime") else str(date)[:10],
                    "actual": None,
                    "predicted": pred_value,
                    "upper_bound": pred_value + 10 + i * 2,
                    "lower_bound": max(0, pred_value - 8 - i),
                    "risk_level": risk,
                })

        insights = None
        if predictions is not None and len(predictions) > 0:
            peak_value = int(predictions.max())
            peak_date = predictions.idxmax()
            total_beds = int(df["total_beds"].iloc[0])
            threshold = int(total_beds * 0.9)

            days_until_threshold = None
            for i, val in enumerate(predictions):
                if val >= threshold:
                    days_until_threshold = i + 1
                    break

            insights = {
                "peak_occupancy": peak_value,
                "peak_date": peak_date.strftime("%b %d") if hasattr(peak_date, "strftime") else str(peak_date)[:10],
                "days_until_threshold": days_until_threshold,
                "threshold": threshold,
                "recommendation": "Prepare surge capacity" if peak_value > threshold * 0.9 else "Monitor closely",
            }

        return convert_numpy({"data": result, "insights": insights, "forecast_days": days})
    except Exception as e:
        logger.error(f"Predictions error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate predictions")


# AI Agent Endpoints

@app.get("/api/agent/status")
async def get_agent_status():
    """Get AI agent status."""
    global agent_instance
    return {
        "initialized": agent_instance is not None,
        "autonomous_mode": agent_instance.autonomous_mode if agent_instance else False,
        "pending_actions": len(agent_instance.pending_actions) if agent_instance else 0,
        "actions_taken": len(agent_instance.actions_taken) if agent_instance else 0,
    }


@app.post("/api/agent/run")
async def run_agent(
    hospital_id: str = Query("H001", max_length=50),
    autonomous_mode: bool = False,
):
    """Run AI agent analysis cycle."""
    global agent_instance, current_data

    try:
        df = get_or_generate_data(hospital_id)

        hospital_name = str(df["hospital_name"].iloc[0]) if "hospital_name" in df.columns else "City General Hospital"
        if agent_instance is None:
            agent_instance = HospitAIAgent(hospital_name=hospital_name, autonomous_mode=autonomous_mode)
        else:
            agent_instance.autonomous_mode = autonomous_mode

        results = agent_instance.run_cycle(df)

        actions_executed = []
        actions_pending = []

        for i, action in enumerate(results["actions"].get("executed", [])):
            actions_executed.append({
                "id": int(i),
                "action_type": str(action.action_type.value),
                "description": str(action.description),
                "priority": int(action.priority),
                "auto_executed": bool(action.auto_executed),
                "requires_approval": bool(action.requires_approval),
                "details": convert_numpy(action.details),
                "status": "executed",
            })

        for i, action in enumerate(results["actions"].get("pending", [])):
            actions_pending.append({
                "id": int(i),
                "action_type": str(action.action_type.value),
                "description": str(action.description),
                "priority": int(action.priority),
                "auto_executed": bool(action.auto_executed),
                "requires_approval": bool(action.requires_approval),
                "details": convert_numpy(action.details),
                "status": "pending",
            })

        issues = []
        for issue in results.get("issues", []):
            issues.append({
                "type": str(issue["type"]),
                "resource": str(issue["resource"]),
                "severity": str(issue["severity"].value) if hasattr(issue["severity"], "value") else str(issue["severity"]),
                "value": float(issue["value"]),
                "message": str(issue["message"]),
            })

        situation = convert_numpy(results["situation"])

        response = {
            "situation": situation,
            "issues": issues,
            "actions_executed": actions_executed,
            "actions_pending": actions_pending,
            "reasoning_trace": str(agent_instance.get_reasoning_trace()),
            "timestamp": datetime.now().isoformat(),
        }

        return convert_numpy(response)
    except Exception as e:
        logger.error(f"Agent run error: {e}")
        raise HTTPException(status_code=500, detail="Failed to run agent analysis")


@app.post("/api/agent/approve/{action_id}")
async def approve_action(action_id: int):
    """Approve a pending agent action."""
    global agent_instance

    if agent_instance is None:
        raise HTTPException(status_code=400, detail="Agent not initialized")

    success = agent_instance.approve_action(action_id)
    if success:
        return {"status": "approved", "action_id": action_id}
    raise HTTPException(status_code=404, detail="Action not found")


@app.post("/api/agent/reject/{action_id}")
async def reject_action(action_id: int):
    """Reject a pending agent action."""
    global agent_instance

    if agent_instance is None:
        raise HTTPException(status_code=400, detail="Agent not initialized")

    success = agent_instance.reject_action(action_id)
    if success:
        return {"status": "rejected", "action_id": action_id}
    raise HTTPException(status_code=404, detail="Action not found")


@app.get("/api/agent/analysis")
async def get_ai_analysis(hospital_id: str = Query("H001", max_length=50)):
    """Get detailed AI analysis."""
    global agent_instance

    try:
        df = get_or_generate_data(hospital_id)

        if agent_instance is None:
            agent_instance = HospitAIAgent()

        analysis = agent_instance.get_ai_analysis(df)
        return {"analysis": analysis, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"AI analysis error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate AI analysis")


@app.get("/api/agent/log")
async def get_action_log():
    """Get agent action log."""
    return {"log": get_agent_log()}


# External Data Endpoints

@app.get("/api/live-data")
async def get_live_data(city: str = Query("Delhi", max_length=100)):
    """Get live environmental data from external APIs."""
    try:
        data = get_realtime_data(city)
        return {
            "city": city,
            "weather": data["weather"],
            "air_quality": data["air_quality"],
            "combined": data["combined"],
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Live data error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch live data")


@app.get("/api/live-data/status")
async def get_external_api_status():
    """Check status of external APIs."""
    return check_api_status()


@app.get("/api/hospitals")
async def get_hospitals():
    """Get list of available hospitals."""
    global uploaded_data

    hospitals = [
        {"id": "H001", "name": "City General Hospital", "location": "Delhi"},
        {"id": "H002", "name": "St. Mary Medical Center", "location": "Mumbai"},
        {"id": "H003", "name": "Regional Health Center", "location": "Bangalore"},
    ]

    for hospital_id in uploaded_data.keys():
        if hospital_id not in [h["id"] for h in hospitals]:
            hospitals.insert(0, {
                "id": hospital_id,
                "name": "Uploaded Hospital Data" if hospital_id == "UPLOADED" else f"Uploaded: {hospital_id}",
                "location": "Custom Data",
                "is_uploaded": True,
            })

    return {"hospitals": hospitals}


@app.get("/api/alerts")
async def get_alerts(hospital_id: str = Query("H001", max_length=50)):
    """Get current alerts for a hospital."""
    try:
        df = get_or_generate_data(hospital_id)
        latest = df.iloc[-1]

        alerts = []

        bed_occ = (latest["occupied_beds"] / latest["total_beds"]) * 100
        icu_occ = (latest["occupied_icu"] / latest["total_icu_beds"]) * 100

        if icu_occ >= 85:
            alerts.append({
                "id": 1,
                "severity": "critical",
                "message": f"ICU at {icu_occ:.0f}% capacity - {int(latest['total_icu_beds'] - latest['occupied_icu'])} beds remaining",
                "timestamp": datetime.now().isoformat(),
            })
        elif icu_occ >= 75:
            alerts.append({
                "id": 1,
                "severity": "warning",
                "message": f"ICU at {icu_occ:.0f}% capacity - monitor closely",
                "timestamp": datetime.now().isoformat(),
            })

        if bed_occ >= 90:
            alerts.append({
                "id": 2,
                "severity": "critical",
                "message": f"Bed occupancy critical at {bed_occ:.0f}%",
                "timestamp": datetime.now().isoformat(),
            })
        elif bed_occ >= 80:
            alerts.append({
                "id": 2,
                "severity": "warning",
                "message": f"Bed occupancy elevated at {bed_occ:.0f}%",
                "timestamp": datetime.now().isoformat(),
            })

        if latest.get("pollution", 0) >= 150:
            alerts.append({
                "id": 3,
                "severity": "warning",
                "message": f"High AQI ({int(latest['pollution'])}) - expect respiratory admissions",
                "timestamp": datetime.now().isoformat(),
            })

        return {"alerts": alerts, "count": len(alerts)}
    except Exception as e:
        logger.error(f"Alerts error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve alerts")


# Data Upload Endpoints

def validate_file_extension(filename: str) -> str:
    """Validate and return file extension."""
    if not filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")
    return ext


def process_uploaded_file(df: pd.DataFrame) -> tuple:
    """Process and validate uploaded hospital data."""
    validation = {
        "valid": True,
        "error": None,
        "warnings": [],
        "columns_found": [],
        "columns_missing": [],
        "columns_generated": [],
    }

    if len(df) > MAX_UPLOAD_ROWS:
        validation["valid"] = False
        validation["error"] = f"File exceeds maximum row limit of {MAX_UPLOAD_ROWS}"
        return None, validation

    required_cols = ["date", "occupied_beds", "total_beds"]

    df.columns = df.columns.str.lower().str.strip().str.replace(" ", "_")

    processed = pd.DataFrame()

    for col in required_cols:
        if col in df.columns:
            validation["columns_found"].append(col)
        else:
            alternatives = {
                "date": ["datetime", "time", "day", "record_date"],
                "occupied_beds": ["beds_occupied", "current_beds", "beds_used", "occupied"],
                "total_beds": ["bed_capacity", "capacity", "max_beds", "beds_total"],
            }
            found = False
            for alt in alternatives.get(col, []):
                if alt in df.columns:
                    df = df.rename(columns={alt: col})
                    validation["columns_found"].append(f"{col} (from {alt})")
                    found = True
                    break
            if not found:
                validation["columns_missing"].append(col)

    if validation["columns_missing"]:
        validation["valid"] = False
        validation["error"] = f"Missing required columns: {', '.join(validation['columns_missing'])}"
        return None, validation

    try:
        processed["date"] = pd.to_datetime(df["date"])
    except Exception:
        validation["valid"] = False
        validation["error"] = "Could not parse date column. Use YYYY-MM-DD format."
        return None, validation

    processed["occupied_beds"] = pd.to_numeric(df["occupied_beds"], errors="coerce").fillna(100).astype(int)
    processed["total_beds"] = pd.to_numeric(df["total_beds"], errors="coerce").fillna(200).astype(int)

    # Validate data ranges
    if (processed["occupied_beds"] < 0).any() or (processed["total_beds"] <= 0).any():
        validation["valid"] = False
        validation["error"] = "Invalid values: beds must be positive numbers"
        return None, validation

    if (processed["occupied_beds"] > processed["total_beds"]).any():
        validation["warnings"].append("Some rows have occupied_beds > total_beds")

    # Process optional columns
    optional_mappings = [
        ("occupied_icu", 15, lambda p: (p["occupied_beds"] * 0.15).astype(int)),
        ("total_icu_beds", 30, lambda p: 30),
        ("ventilators_used", 10, lambda p: (p["occupied_icu"] * 0.5).astype(int)),
        ("total_ventilators", 20, lambda p: 20),
        ("staff_on_duty", 120, lambda p: np.random.randint(100, 140, len(p))),
        ("flu_cases", 30, lambda p: np.random.poisson(30, len(p))),
        ("temperature", 25, lambda p: np.random.normal(25, 5, len(p)).round(1)),
        ("humidity", 60, lambda p: np.random.normal(60, 10, len(p)).astype(int)),
    ]

    for col_name, default_val, generator in optional_mappings:
        if col_name in df.columns:
            processed[col_name] = pd.to_numeric(df[col_name], errors="coerce").fillna(default_val)
            if col_name in ["occupied_icu", "total_icu_beds", "ventilators_used", "total_ventilators", "staff_on_duty", "flu_cases", "humidity"]:
                processed[col_name] = processed[col_name].astype(int)
            validation["columns_found"].append(col_name)
        else:
            processed[col_name] = generator(processed)
            validation["columns_generated"].append(col_name)

    # Handle pollution/aqi column
    pollution_col = next((c for c in ["pollution", "aqi", "air_quality", "pollution_aqi"] if c in df.columns), None)
    if pollution_col:
        processed["pollution"] = pd.to_numeric(df[pollution_col], errors="coerce").fillna(75).astype(int)
        validation["columns_found"].append("pollution")
    else:
        processed["pollution"] = np.random.gamma(2, 30, len(df)).astype(int)
        validation["columns_generated"].append("pollution")

    # Add derived columns
    processed["total_staff"] = 150
    processed["oxygen_consumed"] = (processed["occupied_beds"] * 1.5).astype(int)
    processed["medication_stock"] = np.random.randint(500, 1000, len(df))
    processed["emergency_admissions"] = np.random.poisson(15, len(df))
    processed["is_weekend"] = processed["date"].dt.dayofweek >= 5
    processed["hospital_id"] = "UPLOADED"
    processed["hospital_name"] = "Uploaded Hospital Data"

    processed.set_index("date", inplace=True)
    processed.sort_index(inplace=True)

    if validation["columns_generated"]:
        validation["warnings"].append(f"Generated default values for: {', '.join(validation['columns_generated'])}")

    return processed, validation


@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    hospital_id: str = Query("UPLOADED", max_length=50),
):
    """Upload hospital data from CSV or Excel file."""
    global uploaded_data

    try:
        file_ext = validate_file_extension(file.filename)

        content = await file.read()
        
        # Check file size
        if len(content) > MAX_UPLOAD_SIZE_MB * 1024 * 1024:
            raise HTTPException(status_code=400, detail=f"File exceeds {MAX_UPLOAD_SIZE_MB}MB limit")

        if file_ext == "csv":
            df = pd.read_csv(io.BytesIO(content))
        else:
            df = pd.read_excel(io.BytesIO(content))

        processed_df, validation_result = process_uploaded_file(df)

        if not validation_result["valid"]:
            raise HTTPException(status_code=400, detail=validation_result["error"])

        uploaded_data[hospital_id] = processed_df

        logger.info(f"Data uploaded: {len(processed_df)} rows for hospital {hospital_id}")

        return {
            "success": True,
            "message": f"Successfully uploaded {len(processed_df)} rows of data",
            "hospital_id": hospital_id,
            "filename": file.filename,
            "rows": len(processed_df),
            "columns": list(processed_df.columns),
            "date_range": {
                "start": str(processed_df.index.min()),
                "end": str(processed_df.index.max()),
            },
            "validation": validation_result,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail="Error processing file")


@app.get("/api/upload/status")
async def get_upload_status():
    """Get status of uploaded data."""
    global uploaded_data

    uploads = []
    for hospital_id, df in uploaded_data.items():
        uploads.append({
            "hospital_id": hospital_id,
            "rows": len(df),
            "columns": list(df.columns),
            "date_range": {"start": str(df.index.min()), "end": str(df.index.max())},
        })

    return {"has_uploads": len(uploaded_data) > 0, "uploads": uploads}


@app.delete("/api/upload/{hospital_id}")
async def delete_uploaded_data(hospital_id: str):
    """Delete uploaded data for a hospital."""
    global uploaded_data

    if hospital_id in uploaded_data:
        del uploaded_data[hospital_id]
        logger.info(f"Deleted uploaded data for hospital {hospital_id}")
        return {"success": True, "message": f"Deleted uploaded data for {hospital_id}"}
    raise HTTPException(status_code=404, detail=f"No uploaded data found for {hospital_id}")


@app.get("/api/upload/template")
async def get_upload_template():
    """Get a sample CSV template for data upload."""
    dates = pd.date_range("2025-01-01", periods=30, freq="D")

    template_data = {
        "date": dates.strftime("%Y-%m-%d").tolist(),
        "occupied_beds": np.random.randint(100, 180, 30).tolist(),
        "total_beds": [200] * 30,
        "occupied_icu": np.random.randint(10, 25, 30).tolist(),
        "total_icu_beds": [30] * 30,
        "ventilators_used": np.random.randint(5, 15, 30).tolist(),
        "total_ventilators": [20] * 30,
        "staff_on_duty": np.random.randint(100, 140, 30).tolist(),
        "flu_cases": np.random.poisson(40, 30).tolist(),
        "temperature": np.random.normal(25, 5, 30).round(1).tolist(),
        "humidity": np.random.normal(60, 10, 30).round(0).astype(int).tolist(),
        "pollution": np.random.randint(50, 150, 30).tolist(),
    }

    return template_data


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
