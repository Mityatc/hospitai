"""
HospitAI FastAPI Backend
REST API for hospital surge prediction and capacity management.
"""

import io
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ai_agent import HospitAIAgent, get_agent_log
from data_generator import generate_data
from predictor_ml import predict_ml
from predictor_rulebased import get_risk_breakdown, predict_surge
from real_data_api import check_api_status, get_realtime_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_UPLOAD_SIZE_MB = 10
MAX_UPLOAD_ROWS = 10000
ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls"}

# Get allowed origins from environment or use defaults
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",") if os.getenv("ALLOWED_ORIGINS") else [
    "http://localhost:5173", "http://localhost:3000", "http://localhost:8080",
    "http://127.0.0.1:5173", "http://127.0.0.1:8080"
]


def convert_numpy(obj: Any) -> Any:
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


app = FastAPI(title="HospitAI API", description="Hospital surge prediction system", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

agent_instance: Optional[HospitAIAgent] = None
current_data: Optional[pd.DataFrame] = None
uploaded_data: Dict[str, pd.DataFrame] = {}


def get_or_generate_data(hospital_id: str = "H001", days: int = 30) -> pd.DataFrame:
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
    latest = df.iloc[-1]
    bed_change_1d = int(df["occupied_beds"].iloc[-1] - df["occupied_beds"].iloc[-2]) if len(df) >= 2 else 0
    bed_change_3d = int(df["occupied_beds"].iloc[-1] - df["occupied_beds"].iloc[-3]) if len(df) >= 3 else 0
    bed_change_7d = int(df["occupied_beds"].iloc[-1] - df["occupied_beds"].iloc[-7]) if len(df) >= 7 else 0
    icu_change_1d = int(df["occupied_icu"].iloc[-1] - df["occupied_icu"].iloc[-2]) if len(df) >= 2 else 0
    
    direction = "stable"
    velocity = "slow"
    if bed_change_3d > 10:
        direction = "increasing"
        velocity = "rapid" if bed_change_3d > 20 else "moderate"
    elif bed_change_3d < -10:
        direction = "decreasing"
        velocity = "rapid" if bed_change_3d < -20 else "moderate"
    
    breakdown = get_risk_breakdown(df)
    risk_factors = [
        {"name": "Flu Cases", "value": float(round(latest.get("flu_cases", 0), 1)), "threshold": 50, "triggered": bool(latest.get("flu_cases", 0) > 50)},
        {"name": "Air Quality", "value": float(round(latest.get("pollution", 0), 1)), "threshold": 100, "triggered": bool(latest.get("pollution", 0) > 100)},
        {"name": "Staff Ratio", "value": float(round(latest["staff_on_duty"] / max(latest["occupied_beds"], 1), 2)), "threshold": 1.0, "triggered": bool((latest["staff_on_duty"] / max(latest["occupied_beds"], 1)) < 1.0)},
        {"name": "Bed Occupancy", "value": float(round((latest["occupied_beds"] / latest["total_beds"]) * 100, 1)), "threshold": 80, "triggered": bool((latest["occupied_beds"] / latest["total_beds"]) > 0.8)},
        {"name": "ICU Occupancy", "value": float(round((latest["occupied_icu"] / latest["total_icu_beds"]) * 100, 1)), "threshold": 75, "triggered": bool((latest["occupied_icu"] / latest["total_icu_beds"]) > 0.75)},
        {"name": "Ventilator Usage", "value": float(round((latest["ventilators_used"] / latest["total_ventilators"]) * 100, 1)), "threshold": 70, "triggered": bool((latest["ventilators_used"] / latest["total_ventilators"]) > 0.7)},
    ]
    
    return convert_numpy({
        "hospital": {"id": hospital_id, "name": str(latest.get("hospital_name", "City General Hospital")), "location": "Delhi"},
        "metrics": {
            "total_beds": int(latest["total_beds"]), "occupied_beds": int(latest["occupied_beds"]),
            "bed_occupancy": float(round((latest["occupied_beds"] / latest["total_beds"]) * 100, 1)),
            "total_icu": int(latest["total_icu_beds"]), "occupied_icu": int(latest["occupied_icu"]),
            "icu_occupancy": float(round((latest["occupied_icu"] / latest["total_icu_beds"]) * 100, 1)),
            "total_ventilators": int(latest["total_ventilators"]), "ventilators_used": int(latest["ventilators_used"]),
            "ventilator_usage": float(round((latest["ventilators_used"] / latest["total_ventilators"]) * 100, 1)),
            "staff_on_duty": int(latest["staff_on_duty"]),
            "staff_ratio": float(round(latest["staff_on_duty"] / max(latest["occupied_beds"], 1), 2)),
        },
        "risk": {"score": sum(1 for f in risk_factors if f["triggered"]), "max_score": 6, "level": str(breakdown["risk_level"]), "factors": risk_factors},
        "environment": {"temperature": float(round(latest.get("temperature", 20), 1)), "humidity": int(latest.get("humidity", 65)),
                       "aqi": int(latest.get("pollution", 50)), "flu_cases": int(latest.get("flu_cases", 0))},
        "trends": {"bed_change_1d": bed_change_1d, "bed_change_3d": bed_change_3d, "bed_change_7d": bed_change_7d,
                  "icu_change_1d": icu_change_1d, "direction": direction, "velocity": velocity},
        "timestamp": datetime.now().isoformat(),
    })


@app.get("/")
async def health_check():
    return {"status": "healthy", "service": "HospitAI API", "version": "1.0.0"}


@app.get("/api/dashboard/summary")
async def get_dashboard_summary(hospital_id: str = Query("H001", max_length=50), days: int = Query(30, ge=1, le=365)):
    try:
        df = get_or_generate_data(hospital_id, days)
        return build_dashboard_response(df, hospital_id)
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard data")


@app.get("/api/dashboard/metrics")
async def get_metrics(hospital_id: str = Query("H001", max_length=50)):
    try:
        df = get_or_generate_data(hospital_id)
        return build_dashboard_response(df, hospital_id)["metrics"]
    except Exception as e:
        logger.error(f"Metrics error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")


@app.get("/api/dashboard/trends")
async def get_trends(hospital_id: str = Query("H001", max_length=50), days: int = Query(30, ge=1, le=365)):
    try:
        df = get_or_generate_data(hospital_id, days)
        trends = []
        for i, (idx, row) in enumerate(df.iterrows()):
            date_val = row.get("date", idx)
            date_str = date_val.strftime("%b %d") if hasattr(date_val, "strftime") else str(date_val)[:10]
            trends.append({"date": date_str, "beds": int(row["occupied_beds"]), "icu": int(row["occupied_icu"]),
                          "admissions": int(row.get("admissions", 8 + (i % 5))), "discharges": int(row.get("discharges", 6 + (i % 4)))})
        return {"data": convert_numpy(trends), "days": days}
    except Exception as e:
        logger.error(f"Trends error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve trends")


@app.get("/api/predictions")
async def get_predictions(hospital_id: str = Query("H001", max_length=50), days: int = Query(7, ge=1, le=14)):
    try:
        df = get_or_generate_data(hospital_id, 30)
        predictions = predict_ml(df, days=days)
        result = []
        for idx, row in df.iterrows():
            date_val = row.get("date", idx)
            date_str = date_val.strftime("%b %d") if hasattr(date_val, "strftime") else str(date_val)[:10]
            result.append({"date": date_str, "actual": int(row["occupied_beds"]), "predicted": None, "upper_bound": None, "lower_bound": None, "risk_level": None})
        
        if predictions is not None:
            total_beds = int(df["total_beds"].iloc[0])
            for i, (date, value) in enumerate(predictions.items()):
                pred_value = int(value)
                occupancy = (pred_value / total_beds) * 100
                risk = "Critical" if occupancy >= 90 else "High" if occupancy >= 80 else "Medium" if occupancy >= 70 else "Low"
                result.append({"date": date.strftime("%b %d") if hasattr(date, "strftime") else str(date)[:10],
                              "actual": None, "predicted": pred_value, "upper_bound": pred_value + 10 + i * 2,
                              "lower_bound": max(0, pred_value - 8 - i), "risk_level": risk})
        
        insights = None
        if predictions is not None and len(predictions) > 0:
            peak_value = int(predictions.max())
            peak_date = predictions.idxmax()
            total_beds = int(df["total_beds"].iloc[0])
            threshold = int(total_beds * 0.9)
            days_until = next((i + 1 for i, val in enumerate(predictions) if val >= threshold), None)
            insights = {"peak_occupancy": peak_value, "peak_date": peak_date.strftime("%b %d") if hasattr(peak_date, "strftime") else str(peak_date)[:10],
                       "days_until_threshold": days_until, "threshold": threshold,
                       "recommendation": "Prepare surge capacity" if peak_value > threshold * 0.9 else "Monitor closely"}
        return convert_numpy({"data": result, "insights": insights, "forecast_days": days})
    except Exception as e:
        logger.error(f"Predictions error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate predictions")


@app.get("/api/agent/status")
async def get_agent_status():
    global agent_instance
    return {"initialized": agent_instance is not None, "autonomous_mode": agent_instance.autonomous_mode if agent_instance else False,
            "pending_actions": len(agent_instance.pending_actions) if agent_instance else 0,
            "actions_taken": len(agent_instance.actions_taken) if agent_instance else 0}


@app.post("/api/agent/run")
async def run_agent(hospital_id: str = Query("H001", max_length=50), autonomous_mode: bool = False):
    global agent_instance, current_data
    try:
        df = get_or_generate_data(hospital_id)
        hospital_name = str(df["hospital_name"].iloc[0]) if "hospital_name" in df.columns else "City General Hospital"
        if agent_instance is None:
            agent_instance = HospitAIAgent(hospital_name=hospital_name, autonomous_mode=autonomous_mode)
        else:
            agent_instance.autonomous_mode = autonomous_mode
        results = agent_instance.run_cycle(df)
        
        actions_executed = [{"id": i, "action_type": str(a.action_type.value), "description": str(a.description),
                            "priority": int(a.priority), "auto_executed": bool(a.auto_executed),
                            "requires_approval": bool(a.requires_approval), "details": convert_numpy(a.details), "status": "executed"}
                           for i, a in enumerate(results["actions"].get("executed", []))]
        actions_pending = [{"id": i, "action_type": str(a.action_type.value), "description": str(a.description),
                           "priority": int(a.priority), "auto_executed": bool(a.auto_executed),
                           "requires_approval": bool(a.requires_approval), "details": convert_numpy(a.details), "status": "pending"}
                          for i, a in enumerate(results["actions"].get("pending", []))]
        issues = [{"type": str(i["type"]), "resource": str(i["resource"]),
                  "severity": str(i["severity"].value) if hasattr(i["severity"], "value") else str(i["severity"]),
                  "value": float(i["value"]), "message": str(i["message"])} for i in results.get("issues", [])]
        
        return convert_numpy({"situation": results["situation"], "issues": issues, "actions_executed": actions_executed,
                             "actions_pending": actions_pending, "reasoning_trace": str(agent_instance.get_reasoning_trace()),
                             "timestamp": datetime.now().isoformat()})
    except Exception as e:
        logger.error(f"Agent error: {e}")
        raise HTTPException(status_code=500, detail="Failed to run agent")


@app.post("/api/agent/approve/{action_id}")
async def approve_action(action_id: int):
    global agent_instance
    if agent_instance is None:
        raise HTTPException(status_code=400, detail="Agent not initialized")
    if agent_instance.approve_action(action_id):
        return {"status": "approved", "action_id": action_id}
    raise HTTPException(status_code=404, detail="Action not found")


@app.post("/api/agent/reject/{action_id}")
async def reject_action(action_id: int):
    global agent_instance
    if agent_instance is None:
        raise HTTPException(status_code=400, detail="Agent not initialized")
    if agent_instance.reject_action(action_id):
        return {"status": "rejected", "action_id": action_id}
    raise HTTPException(status_code=404, detail="Action not found")


@app.get("/api/agent/analysis")
async def get_ai_analysis(hospital_id: str = Query("H001", max_length=50)):
    global agent_instance
    try:
        df = get_or_generate_data(hospital_id)
        if agent_instance is None:
            agent_instance = HospitAIAgent()
        return {"analysis": agent_instance.get_ai_analysis(df), "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate analysis")


@app.get("/api/agent/log")
async def get_action_log():
    return {"log": get_agent_log()}


@app.get("/api/live-data")
async def get_live_data(city: str = Query("Delhi", max_length=100)):
    try:
        data = get_realtime_data(city)
        return {"city": city, "weather": data["weather"], "air_quality": data["air_quality"],
                "combined": data["combined"], "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Live data error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch live data")


@app.get("/api/live-data/status")
async def get_external_api_status():
    return check_api_status()


@app.get("/api/hospitals")
async def get_hospitals():
    global uploaded_data
    hospitals = [{"id": "H001", "name": "City General Hospital", "location": "Delhi"},
                {"id": "H002", "name": "St. Mary Medical Center", "location": "Mumbai"},
                {"id": "H003", "name": "Regional Health Center", "location": "Bangalore"}]
    for hid in uploaded_data.keys():
        if hid not in [h["id"] for h in hospitals]:
            hospitals.insert(0, {"id": hid, "name": "Uploaded Data" if hid == "UPLOADED" else f"Uploaded: {hid}",
                                "location": "Custom", "is_uploaded": True})
    return {"hospitals": hospitals}


@app.get("/api/alerts")
async def get_alerts(hospital_id: str = Query("H001", max_length=50)):
    try:
        df = get_or_generate_data(hospital_id)
        latest = df.iloc[-1]
        alerts = []
        bed_occ = (latest["occupied_beds"] / latest["total_beds"]) * 100
        icu_occ = (latest["occupied_icu"] / latest["total_icu_beds"]) * 100
        
        if icu_occ >= 85:
            alerts.append({"id": 1, "severity": "critical", "message": f"ICU at {icu_occ:.0f}%", "timestamp": datetime.now().isoformat()})
        elif icu_occ >= 75:
            alerts.append({"id": 1, "severity": "warning", "message": f"ICU at {icu_occ:.0f}%", "timestamp": datetime.now().isoformat()})
        if bed_occ >= 90:
            alerts.append({"id": 2, "severity": "critical", "message": f"Beds at {bed_occ:.0f}%", "timestamp": datetime.now().isoformat()})
        elif bed_occ >= 80:
            alerts.append({"id": 2, "severity": "warning", "message": f"Beds at {bed_occ:.0f}%", "timestamp": datetime.now().isoformat()})
        if latest.get("pollution", 0) >= 150:
            alerts.append({"id": 3, "severity": "warning", "message": f"High AQI ({int(latest['pollution'])})", "timestamp": datetime.now().isoformat()})
        return {"alerts": alerts, "count": len(alerts)}
    except Exception as e:
        logger.error(f"Alerts error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve alerts")


# Data Upload Endpoints

def process_uploaded_file(df: pd.DataFrame) -> tuple:
    validation = {"valid": True, "error": None, "warnings": [], "columns_found": [], "columns_missing": [], "columns_generated": []}
    if len(df) > MAX_UPLOAD_ROWS:
        validation["valid"] = False
        validation["error"] = f"File exceeds {MAX_UPLOAD_ROWS} rows"
        return None, validation
    
    required_cols = ["date", "occupied_beds", "total_beds"]
    df.columns = df.columns.str.lower().str.strip().str.replace(" ", "_")
    processed = pd.DataFrame()
    
    for col in required_cols:
        if col in df.columns:
            validation["columns_found"].append(col)
        else:
            alternatives = {"date": ["datetime", "time", "day"], "occupied_beds": ["beds_occupied", "current_beds"], "total_beds": ["bed_capacity", "capacity"]}
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
        validation["error"] = f"Missing: {', '.join(validation['columns_missing'])}"
        return None, validation
    
    try:
        processed["date"] = pd.to_datetime(df["date"])
    except:
        validation["valid"] = False
        validation["error"] = "Invalid date format"
        return None, validation
    
    processed["occupied_beds"] = pd.to_numeric(df["occupied_beds"], errors="coerce").fillna(100).astype(int)
    processed["total_beds"] = pd.to_numeric(df["total_beds"], errors="coerce").fillna(200).astype(int)
    
    optional = [("occupied_icu", 15), ("total_icu_beds", 30), ("ventilators_used", 10), ("total_ventilators", 20),
                ("staff_on_duty", 120), ("flu_cases", 30), ("temperature", 25), ("humidity", 60)]
    for col, default in optional:
        if col in df.columns:
            processed[col] = pd.to_numeric(df[col], errors="coerce").fillna(default)
            validation["columns_found"].append(col)
        else:
            if col == "occupied_icu":
                processed[col] = (processed["occupied_beds"] * 0.15).astype(int)
            elif col == "ventilators_used":
                processed[col] = (processed.get("occupied_icu", 15) * 0.5).astype(int)
            elif col in ["flu_cases", "humidity"]:
                processed[col] = np.random.poisson(default, len(df)) if col == "flu_cases" else np.random.normal(default, 10, len(df)).astype(int)
            elif col == "temperature":
                processed[col] = np.random.normal(default, 5, len(df)).round(1)
            else:
                processed[col] = default
            validation["columns_generated"].append(col)
    
    pollution_col = next((c for c in ["pollution", "aqi", "air_quality"] if c in df.columns), None)
    if pollution_col:
        processed["pollution"] = pd.to_numeric(df[pollution_col], errors="coerce").fillna(75).astype(int)
        validation["columns_found"].append("pollution")
    else:
        processed["pollution"] = np.random.gamma(2, 30, len(df)).astype(int)
        validation["columns_generated"].append("pollution")
    
    processed["total_staff"] = 150
    processed["hospital_id"] = "UPLOADED"
    processed["hospital_name"] = "Uploaded Data"
    processed.set_index("date", inplace=True)
    processed.sort_index(inplace=True)
    
    if validation["columns_generated"]:
        validation["warnings"].append(f"Generated: {', '.join(validation['columns_generated'])}")
    return processed, validation


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), hospital_id: str = Query("UPLOADED", max_length=50)):
    global uploaded_data
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file")
        ext = file.filename.lower().rsplit(".", 1)[-1] if "." in file.filename else ""
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"Invalid type. Allowed: {ALLOWED_EXTENSIONS}")
        
        content = await file.read()
        if len(content) > MAX_UPLOAD_SIZE_MB * 1024 * 1024:
            raise HTTPException(status_code=400, detail=f"File exceeds {MAX_UPLOAD_SIZE_MB}MB")
        
        df = pd.read_csv(io.BytesIO(content)) if ext == "csv" else pd.read_excel(io.BytesIO(content))
        processed_df, validation = process_uploaded_file(df)
        
        if not validation["valid"]:
            raise HTTPException(status_code=400, detail=validation["error"])
        
        uploaded_data[hospital_id] = processed_df
        logger.info(f"Uploaded {len(processed_df)} rows for {hospital_id}")
        
        return {"success": True, "message": f"Uploaded {len(processed_df)} rows", "hospital_id": hospital_id,
                "filename": file.filename, "rows": len(processed_df), "columns": list(processed_df.columns),
                "date_range": {"start": str(processed_df.index.min()), "end": str(processed_df.index.max())},
                "validation": validation}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail="Upload failed")


@app.get("/api/upload/status")
async def get_upload_status():
    global uploaded_data
    uploads = [{"hospital_id": hid, "rows": len(df), "columns": list(df.columns),
               "date_range": {"start": str(df.index.min()), "end": str(df.index.max())}}
              for hid, df in uploaded_data.items()]
    return {"has_uploads": len(uploaded_data) > 0, "uploads": uploads}


@app.delete("/api/upload/{hospital_id}")
async def delete_uploaded_data(hospital_id: str):
    global uploaded_data
    if hospital_id in uploaded_data:
        del uploaded_data[hospital_id]
        return {"success": True, "message": f"Deleted {hospital_id}"}
    raise HTTPException(status_code=404, detail="Not found")


@app.get("/api/upload/template")
async def get_upload_template():
    dates = pd.date_range("2025-01-01", periods=30, freq="D")
    return {"date": dates.strftime("%Y-%m-%d").tolist(), "occupied_beds": np.random.randint(100, 180, 30).tolist(),
            "total_beds": [200] * 30, "occupied_icu": np.random.randint(10, 25, 30).tolist(), "total_icu_beds": [30] * 30,
            "flu_cases": np.random.poisson(40, 30).tolist(), "pollution": np.random.randint(50, 150, 30).tolist()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
