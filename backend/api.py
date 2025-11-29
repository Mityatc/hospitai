"""
HospitAI FastAPI Backend
REST API for the React frontend to connect with the Python backend.
"""

from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import numpy as np
import pandas as pd
import io

# Import existing modules
from data_generator import generate_data, generate_multi_hospital_data
from predictor_rulebased import predict_surge, get_risk_breakdown
from predictor_ml import predict_ml
from ai_agent import HospitAIAgent, get_agent_log, get_agent_memory, AlertLevel, ActionType
from real_data_api import get_realtime_data, check_api_status


# Custom JSON encoder for numpy types
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.bool_):
            return bool(obj)
        return super().default(obj)


def convert_numpy(obj):
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
    version="3.0.0"
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173", "http://localhost:8080", "http://127.0.0.1:8080", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
agent_instance: Optional[HospitAIAgent] = None
current_data = None
uploaded_data: Dict[str, pd.DataFrame] = {}  # Store uploaded data by hospital_id


# Pydantic models for request/response
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


class RiskAssessment(BaseModel):
    score: int
    max_score: int
    level: str
    factors: List[RiskFactor]


class EnvironmentData(BaseModel):
    temperature: float
    humidity: float
    aqi: int
    flu_cases: int


class TrendData(BaseModel):
    bed_change_1d: int
    bed_change_3d: int
    bed_change_7d: int
    icu_change_1d: int
    direction: str
    velocity: str


class DashboardResponse(BaseModel):
    hospital: Dict[str, str]
    metrics: HospitalMetrics
    risk: RiskAssessment
    environment: EnvironmentData
    trends: TrendData
    timestamp: str


class AgentIssue(BaseModel):
    type: str
    resource: str
    severity: str
    value: float
    message: str


class AgentAction(BaseModel):
    id: int
    action_type: str
    description: str
    priority: int
    auto_executed: bool
    requires_approval: bool
    details: Dict[str, Any]
    status: str


class AgentResponse(BaseModel):
    situation: Dict[str, Any]
    issues: List[AgentIssue]
    actions_executed: List[AgentAction]
    actions_pending: List[AgentAction]
    reasoning_trace: str


class PredictionPoint(BaseModel):
    date: str
    actual: Optional[int]
    predicted: Optional[int]
    upper_bound: Optional[int]
    lower_bound: Optional[int]
    risk_level: Optional[str]


# Helper functions
def get_or_generate_data(hospital_id: str = "H001", days: int = 30):
    """Get uploaded data if available, otherwise generate simulated data."""
    global current_data, uploaded_data
    
    # Check if we have uploaded data for this hospital
    if hospital_id in uploaded_data:
        df = uploaded_data[hospital_id].copy()
        # Limit to requested days if needed
        if len(df) > days:
            df = df.tail(days)
        df = predict_surge(df)
        current_data = df
        return df
    
    # Also check for generic "UPLOADED" data
    if "UPLOADED" in uploaded_data and hospital_id == "UPLOADED":
        df = uploaded_data["UPLOADED"].copy()
        if len(df) > days:
            df = df.tail(days)
        df = predict_surge(df)
        current_data = df
        return df
    
    # Fall back to generated data
    df = generate_data(num_days=days, hospital_id=hospital_id)
    df = predict_surge(df)
    current_data = df
    return df


def df_to_dashboard_response(df, hospital_id: str = "H001") -> Dict:
    """Convert DataFrame to dashboard response format."""
    latest = df.iloc[-1]
    
    # Calculate trends
    bed_change_1d = int(df['occupied_beds'].iloc[-1] - df['occupied_beds'].iloc[-2]) if len(df) >= 2 else 0
    bed_change_3d = int(df['occupied_beds'].iloc[-1] - df['occupied_beds'].iloc[-3]) if len(df) >= 3 else 0
    bed_change_7d = int(df['occupied_beds'].iloc[-1] - df['occupied_beds'].iloc[-7]) if len(df) >= 7 else 0
    icu_change_1d = int(df['occupied_icu'].iloc[-1] - df['occupied_icu'].iloc[-2]) if len(df) >= 2 else 0
    
    # Determine trend direction
    if bed_change_3d > 10:
        direction = "increasing"
        velocity = "rapid" if bed_change_3d > 20 else "moderate"
    elif bed_change_3d < -10:
        direction = "decreasing"
        velocity = "rapid" if bed_change_3d < -20 else "moderate"
    else:
        direction = "stable"
        velocity = "slow"
    
    # Get risk breakdown
    breakdown = get_risk_breakdown(df)
    
    # Build risk factors
    risk_factors = [
        {"name": "Flu Cases", "value": float(round(latest.get('flu_cases', 0), 1)), "threshold": 50, "triggered": bool(latest.get('flu_cases', 0) > 50)},
        {"name": "Air Quality", "value": float(round(latest.get('pollution', 0), 1)), "threshold": 100, "triggered": bool(latest.get('pollution', 0) > 100)},
        {"name": "Staff Ratio", "value": float(round(latest['staff_on_duty'] / max(latest['occupied_beds'], 1), 2)), "threshold": 1.0, "triggered": bool((latest['staff_on_duty'] / max(latest['occupied_beds'], 1)) < 1.0)},
        {"name": "Bed Occupancy", "value": float(round((latest['occupied_beds'] / latest['total_beds']) * 100, 1)), "threshold": 80, "triggered": bool((latest['occupied_beds'] / latest['total_beds']) > 0.8)},
        {"name": "ICU Occupancy", "value": float(round((latest['occupied_icu'] / latest['total_icu_beds']) * 100, 1)), "threshold": 75, "triggered": bool((latest['occupied_icu'] / latest['total_icu_beds']) > 0.75)},
        {"name": "Ventilator Usage", "value": float(round((latest['ventilators_used'] / latest['total_ventilators']) * 100, 1)), "threshold": 70, "triggered": bool((latest['ventilators_used'] / latest['total_ventilators']) > 0.7)}
    ]
    
    triggered_count = sum(1 for f in risk_factors if f['triggered'])
    
    result = {
        "hospital": {
            "id": hospital_id,
            "name": str(latest.get('hospital_name', 'City General Hospital')),
            "location": "Delhi"
        },
        "metrics": {
            "total_beds": int(latest['total_beds']),
            "occupied_beds": int(latest['occupied_beds']),
            "bed_occupancy": float(round((latest['occupied_beds'] / latest['total_beds']) * 100, 1)),
            "total_icu": int(latest['total_icu_beds']),
            "occupied_icu": int(latest['occupied_icu']),
            "icu_occupancy": float(round((latest['occupied_icu'] / latest['total_icu_beds']) * 100, 1)),
            "total_ventilators": int(latest['total_ventilators']),
            "ventilators_used": int(latest['ventilators_used']),
            "ventilator_usage": float(round((latest['ventilators_used'] / latest['total_ventilators']) * 100, 1)),
            "staff_on_duty": int(latest['staff_on_duty']),
            "staff_ratio": float(round(latest['staff_on_duty'] / max(latest['occupied_beds'], 1), 2))
        },
        "risk": {
            "score": int(triggered_count),
            "max_score": 6,
            "level": str(breakdown['risk_level']),
            "factors": risk_factors
        },
        "environment": {
            "temperature": float(round(latest.get('temperature', 20), 1)),
            "humidity": int(latest.get('humidity', 65)),
            "aqi": int(latest.get('pollution', 50)),
            "flu_cases": int(latest.get('flu_cases', 0))
        },
        "trends": {
            "bed_change_1d": int(bed_change_1d),
            "bed_change_3d": int(bed_change_3d),
            "bed_change_7d": int(bed_change_7d),
            "icu_change_1d": int(icu_change_1d),
            "direction": direction,
            "velocity": velocity
        },
        "timestamp": datetime.now().isoformat()
    }
    
    # Convert all numpy types to native Python types
    return convert_numpy(result)


# API Endpoints

@app.get("/")
async def root():
    """API health check."""
    return {"status": "healthy", "service": "HospitAI API", "version": "3.0.0"}


@app.get("/api/dashboard/summary")
async def get_dashboard_summary(
    hospital_id: str = Query("H001", description="Hospital ID"),
    days: int = Query(30, description="Number of days of data")
):
    """Get complete dashboard summary."""
    try:
        df = get_or_generate_data(hospital_id, days)
        return df_to_dashboard_response(df, hospital_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard/metrics")
async def get_metrics(hospital_id: str = "H001"):
    """Get current hospital metrics."""
    try:
        df = get_or_generate_data(hospital_id)
        response = df_to_dashboard_response(df, hospital_id)
        return response["metrics"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard/trends")
async def get_trends(hospital_id: str = "H001", days: int = 30):
    """Get historical trend data for charts."""
    try:
        df = get_or_generate_data(hospital_id, days)
        
        trends = []
        for i, (idx, row) in enumerate(df.iterrows()):
            # Handle date formatting
            date_val = row.get('date', idx)
            if hasattr(date_val, 'strftime'):
                date_str = date_val.strftime('%b %d')
            else:
                date_str = str(date_val)[:10]
            
            trends.append({
                "date": date_str,
                "beds": int(row['occupied_beds']),
                "icu": int(row['occupied_icu']),
                "admissions": int(row.get('admissions', 8 + (i % 5))),
                "discharges": int(row.get('discharges', 6 + (i % 4)))
            })
        
        return {"data": convert_numpy(trends), "days": days}
    except Exception as e:
        import traceback
        print(f"Trends error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/predictions")
async def get_predictions(
    hospital_id: str = "H001",
    days: int = Query(7, ge=1, le=14, description="Days to predict")
):
    """Get ML predictions for future capacity."""
    try:
        df = get_or_generate_data(hospital_id, 30)
        predictions = predict_ml(df, days=days)
        
        # Build response with historical + predicted
        result = []
        
        # Historical data (last 30 days)
        for idx, row in df.iterrows():
            # Handle date formatting
            date_val = row.get('date', idx)
            if hasattr(date_val, 'strftime'):
                date_str = date_val.strftime('%b %d')
            else:
                date_str = str(date_val)[:10]
                
            result.append({
                "date": date_str,
                "actual": int(row['occupied_beds']),
                "predicted": None,
                "upper_bound": None,
                "lower_bound": None,
                "risk_level": None
            })
        
        # Predicted data
        if predictions is not None:
            total_beds = int(df['total_beds'].iloc[0])
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
                    "date": date.strftime('%b %d') if hasattr(date, 'strftime') else str(date)[:10],
                    "actual": None,
                    "predicted": pred_value,
                    "upper_bound": pred_value + 10 + i * 2,
                    "lower_bound": max(0, pred_value - 8 - i),
                    "risk_level": risk
                })
        
        # Calculate insights
        if predictions is not None and len(predictions) > 0:
            peak_value = int(predictions.max())
            peak_date = predictions.idxmax()
            total_beds = int(df['total_beds'].iloc[0])
            threshold = int(total_beds * 0.9)
            
            days_until_threshold = None
            for i, val in enumerate(predictions):
                if val >= threshold:
                    days_until_threshold = i + 1
                    break
            
            insights = {
                "peak_occupancy": peak_value,
                "peak_date": peak_date.strftime('%b %d') if hasattr(peak_date, 'strftime') else str(peak_date)[:10],
                "days_until_threshold": days_until_threshold,
                "threshold": threshold,
                "recommendation": "Prepare surge capacity" if peak_value > threshold * 0.9 else "Monitor closely"
            }
        else:
            insights = None
        
        return convert_numpy({
            "data": result,
            "insights": insights,
            "forecast_days": days
        })
    except Exception as e:
        import traceback
        print(f"Predictions error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agent/status")
async def get_agent_status():
    """Get AI agent status."""
    global agent_instance
    return {
        "initialized": agent_instance is not None,
        "autonomous_mode": agent_instance.autonomous_mode if agent_instance else False,
        "pending_actions": len(agent_instance.pending_actions) if agent_instance else 0,
        "actions_taken": len(agent_instance.actions_taken) if agent_instance else 0
    }


@app.post("/api/agent/run")
async def run_agent(
    hospital_id: str = "H001",
    autonomous_mode: bool = False
):
    """Run AI agent analysis cycle."""
    global agent_instance, current_data
    
    try:
        # Get or generate data
        df = get_or_generate_data(hospital_id)
        
        # Initialize or update agent
        hospital_name = str(df['hospital_name'].iloc[0]) if 'hospital_name' in df.columns else "City General Hospital"
        if agent_instance is None:
            agent_instance = HospitAIAgent(
                hospital_name=hospital_name,
                autonomous_mode=autonomous_mode
            )
        else:
            agent_instance.autonomous_mode = autonomous_mode
        
        # Run agent cycle
        results = agent_instance.run_cycle(df)
        
        # Format response - convert all values to native Python types
        actions_executed = []
        actions_pending = []
        
        for i, action in enumerate(results['actions'].get('executed', [])):
            actions_executed.append({
                "id": int(i),
                "action_type": str(action.action_type.value),
                "description": str(action.description),
                "priority": int(action.priority),
                "auto_executed": bool(action.auto_executed),
                "requires_approval": bool(action.requires_approval),
                "details": convert_numpy(action.details),
                "status": "executed"
            })
        
        for i, action in enumerate(results['actions'].get('pending', [])):
            actions_pending.append({
                "id": int(i),
                "action_type": str(action.action_type.value),
                "description": str(action.description),
                "priority": int(action.priority),
                "auto_executed": bool(action.auto_executed),
                "requires_approval": bool(action.requires_approval),
                "details": convert_numpy(action.details),
                "status": "pending"
            })
        
        issues = []
        for issue in results.get('issues', []):
            issues.append({
                "type": str(issue['type']),
                "resource": str(issue['resource']),
                "severity": str(issue['severity'].value) if hasattr(issue['severity'], 'value') else str(issue['severity']),
                "value": float(issue['value']),
                "message": str(issue['message'])
            })
        
        # Convert situation to native types
        situation = convert_numpy(results['situation'])
        
        response = {
            "situation": situation,
            "issues": issues,
            "actions_executed": actions_executed,
            "actions_pending": actions_pending,
            "reasoning_trace": str(agent_instance.get_reasoning_trace()),
            "timestamp": datetime.now().isoformat()
        }
        
        return convert_numpy(response)
    except Exception as e:
        import traceback
        print(f"Agent run error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agent/approve/{action_id}")
async def approve_action(action_id: int):
    """Approve a pending agent action."""
    global agent_instance
    
    if agent_instance is None:
        raise HTTPException(status_code=400, detail="Agent not initialized")
    
    success = agent_instance.approve_action(action_id)
    if success:
        return {"status": "approved", "action_id": action_id}
    else:
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
    else:
        raise HTTPException(status_code=404, detail="Action not found")


@app.get("/api/agent/analysis")
async def get_ai_analysis(hospital_id: str = "H001"):
    """Get detailed AI analysis using Gemini."""
    global agent_instance, current_data
    
    try:
        df = get_or_generate_data(hospital_id)
        
        if agent_instance is None:
            agent_instance = HospitAIAgent()
        
        analysis = agent_instance.get_ai_analysis(df)
        return {"analysis": analysis, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agent/log")
async def get_action_log():
    """Get agent action log."""
    return {"log": get_agent_log()}


@app.get("/api/live-data")
async def get_live_data(city: str = "Delhi"):
    """Get live environmental data from OpenWeatherMap APIs."""
    try:
        data = get_realtime_data(city)
        return {
            "city": city,
            "weather": data['weather'],
            "air_quality": data['air_quality'],
            "combined": data['combined'],
            "timestamp": datetime.now().isoformat()
        }
    except ValueError as e:
        # API key not configured
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch live data: {str(e)}")


@app.get("/api/live-data/status")
async def get_api_status():
    """Check status of external APIs."""
    status = check_api_status()
    return status


@app.get("/api/hospitals")
async def get_hospitals():
    """Get list of available hospitals."""
    global uploaded_data
    
    hospitals = [
        {"id": "H001", "name": "City General Hospital", "location": "Delhi"},
        {"id": "H002", "name": "St. Mary Medical Center", "location": "Mumbai"},
        {"id": "H003", "name": "Regional Health Center", "location": "Bangalore"}
    ]
    
    # Add uploaded data hospitals
    for hospital_id in uploaded_data.keys():
        if hospital_id not in [h["id"] for h in hospitals]:
            hospitals.insert(0, {
                "id": hospital_id,
                "name": "Uploaded Hospital Data" if hospital_id == "UPLOADED" else f"Uploaded: {hospital_id}",
                "location": "Custom Data",
                "is_uploaded": True
            })
    
    return {"hospitals": hospitals}


@app.get("/api/alerts")
async def get_alerts(hospital_id: str = "H001"):
    """Get current alerts for a hospital."""
    try:
        df = get_or_generate_data(hospital_id)
        latest = df.iloc[-1]
        
        alerts = []
        
        # Check various conditions
        bed_occ = (latest['occupied_beds'] / latest['total_beds']) * 100
        icu_occ = (latest['occupied_icu'] / latest['total_icu_beds']) * 100
        
        if icu_occ >= 85:
            alerts.append({
                "id": 1,
                "severity": "critical",
                "message": f"ICU at {icu_occ:.0f}% capacity - {int(latest['total_icu_beds'] - latest['occupied_icu'])} beds remaining",
                "timestamp": datetime.now().isoformat()
            })
        elif icu_occ >= 75:
            alerts.append({
                "id": 1,
                "severity": "warning",
                "message": f"ICU at {icu_occ:.0f}% capacity - monitor closely",
                "timestamp": datetime.now().isoformat()
            })
        
        if bed_occ >= 90:
            alerts.append({
                "id": 2,
                "severity": "critical",
                "message": f"Bed occupancy critical at {bed_occ:.0f}%",
                "timestamp": datetime.now().isoformat()
            })
        elif bed_occ >= 80:
            alerts.append({
                "id": 2,
                "severity": "warning",
                "message": f"Bed occupancy elevated at {bed_occ:.0f}%",
                "timestamp": datetime.now().isoformat()
            })
        
        if latest.get('pollution', 0) >= 150:
            alerts.append({
                "id": 3,
                "severity": "warning",
                "message": f"High AQI ({int(latest['pollution'])}) - expect respiratory admissions",
                "timestamp": datetime.now().isoformat()
            })
        
        return {"alerts": alerts, "count": len(alerts)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== DATA UPLOAD ENDPOINTS ==============

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), hospital_id: str = Query("UPLOADED", description="Hospital ID for uploaded data")):
    """
    Upload hospital data from CSV or Excel file.
    The uploaded data will be used instead of simulated data.
    """
    global uploaded_data
    
    try:
        # Validate file type
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        file_ext = file.filename.lower().split('.')[-1]
        if file_ext not in ['csv', 'xlsx', 'xls']:
            raise HTTPException(status_code=400, detail="Only CSV and Excel files are supported")
        
        # Read file content
        content = await file.read()
        
        # Parse file based on type
        if file_ext == 'csv':
            df = pd.read_csv(io.BytesIO(content))
        else:
            df = pd.read_excel(io.BytesIO(content))
        
        # Validate and process the data
        processed_df, validation_result = process_uploaded_file(df)
        
        if not validation_result['valid']:
            raise HTTPException(status_code=400, detail=validation_result['error'])
        
        # Store the processed data
        uploaded_data[hospital_id] = processed_df
        
        return {
            "success": True,
            "message": f"Successfully uploaded {len(processed_df)} rows of data",
            "hospital_id": hospital_id,
            "filename": file.filename,
            "rows": len(processed_df),
            "columns": list(processed_df.columns),
            "date_range": {
                "start": str(processed_df.index.min()) if hasattr(processed_df.index, 'min') else str(processed_df['date'].min()),
                "end": str(processed_df.index.max()) if hasattr(processed_df.index, 'max') else str(processed_df['date'].max())
            },
            "validation": validation_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Upload error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


def process_uploaded_file(df: pd.DataFrame) -> tuple:
    """
    Process and validate uploaded hospital data.
    Returns (processed_df, validation_result)
    """
    validation = {
        'valid': True,
        'error': None,
        'warnings': [],
        'columns_found': [],
        'columns_missing': [],
        'columns_generated': []
    }
    
    # Required columns mapping (user column -> our column)
    required_cols = ['date', 'occupied_beds', 'total_beds']
    optional_cols = ['occupied_icu', 'total_icu_beds', 'ventilators_used', 'total_ventilators', 
                     'staff_on_duty', 'flu_cases', 'temperature', 'humidity', 'pollution']
    
    # Normalize column names (lowercase, strip whitespace)
    df.columns = df.columns.str.lower().str.strip().str.replace(' ', '_')
    
    processed = pd.DataFrame()
    
    # Check for required columns
    for col in required_cols:
        if col in df.columns:
            validation['columns_found'].append(col)
        else:
            # Try common alternatives
            alternatives = {
                'date': ['datetime', 'time', 'day', 'record_date'],
                'occupied_beds': ['beds_occupied', 'current_beds', 'beds_used', 'occupied'],
                'total_beds': ['bed_capacity', 'capacity', 'max_beds', 'beds_total']
            }
            found = False
            for alt in alternatives.get(col, []):
                if alt in df.columns:
                    df = df.rename(columns={alt: col})
                    validation['columns_found'].append(f"{col} (from {alt})")
                    found = True
                    break
            if not found:
                validation['columns_missing'].append(col)
    
    # If missing required columns, return error
    if validation['columns_missing']:
        validation['valid'] = False
        validation['error'] = f"Missing required columns: {', '.join(validation['columns_missing'])}"
        return None, validation
    
    # Process date column
    try:
        processed['date'] = pd.to_datetime(df['date'])
    except:
        validation['valid'] = False
        validation['error'] = "Could not parse date column. Please use YYYY-MM-DD format."
        return None, validation
    
    # Process required numeric columns
    processed['occupied_beds'] = pd.to_numeric(df['occupied_beds'], errors='coerce').fillna(100).astype(int)
    processed['total_beds'] = pd.to_numeric(df['total_beds'], errors='coerce').fillna(200).astype(int)
    
    # Process optional columns or generate defaults
    if 'occupied_icu' in df.columns:
        processed['occupied_icu'] = pd.to_numeric(df['occupied_icu'], errors='coerce').fillna(15).astype(int)
        validation['columns_found'].append('occupied_icu')
    else:
        processed['occupied_icu'] = (processed['occupied_beds'] * 0.15).astype(int)
        validation['columns_generated'].append('occupied_icu')
    
    if 'total_icu_beds' in df.columns:
        processed['total_icu_beds'] = pd.to_numeric(df['total_icu_beds'], errors='coerce').fillna(30).astype(int)
        validation['columns_found'].append('total_icu_beds')
    else:
        processed['total_icu_beds'] = 30
        validation['columns_generated'].append('total_icu_beds')
    
    if 'ventilators_used' in df.columns:
        processed['ventilators_used'] = pd.to_numeric(df['ventilators_used'], errors='coerce').fillna(10).astype(int)
        validation['columns_found'].append('ventilators_used')
    else:
        processed['ventilators_used'] = (processed['occupied_icu'] * 0.5).astype(int)
        validation['columns_generated'].append('ventilators_used')
    
    if 'total_ventilators' in df.columns:
        processed['total_ventilators'] = pd.to_numeric(df['total_ventilators'], errors='coerce').fillna(20).astype(int)
        validation['columns_found'].append('total_ventilators')
    else:
        processed['total_ventilators'] = 20
        validation['columns_generated'].append('total_ventilators')
    
    if 'staff_on_duty' in df.columns:
        processed['staff_on_duty'] = pd.to_numeric(df['staff_on_duty'], errors='coerce').fillna(120).astype(int)
        validation['columns_found'].append('staff_on_duty')
    else:
        processed['staff_on_duty'] = np.random.randint(100, 140, len(df))
        validation['columns_generated'].append('staff_on_duty')
    
    if 'flu_cases' in df.columns:
        processed['flu_cases'] = pd.to_numeric(df['flu_cases'], errors='coerce').fillna(30).astype(int)
        validation['columns_found'].append('flu_cases')
    else:
        processed['flu_cases'] = np.random.poisson(30, len(df))
        validation['columns_generated'].append('flu_cases')
    
    if 'temperature' in df.columns:
        processed['temperature'] = pd.to_numeric(df['temperature'], errors='coerce').fillna(25).round(1)
        validation['columns_found'].append('temperature')
    else:
        processed['temperature'] = np.random.normal(25, 5, len(df)).round(1)
        validation['columns_generated'].append('temperature')
    
    if 'humidity' in df.columns:
        processed['humidity'] = pd.to_numeric(df['humidity'], errors='coerce').fillna(60).astype(int)
        validation['columns_found'].append('humidity')
    else:
        processed['humidity'] = np.random.normal(60, 10, len(df)).astype(int)
        validation['columns_generated'].append('humidity')
    
    # Check for pollution/aqi column
    pollution_col = None
    for col in ['pollution', 'aqi', 'air_quality', 'pollution_aqi']:
        if col in df.columns:
            pollution_col = col
            break
    
    if pollution_col:
        processed['pollution'] = pd.to_numeric(df[pollution_col], errors='coerce').fillna(75).astype(int)
        validation['columns_found'].append('pollution')
    else:
        processed['pollution'] = np.random.gamma(2, 30, len(df)).astype(int)
        validation['columns_generated'].append('pollution')
    
    # Add derived columns
    processed['total_staff'] = 150
    processed['oxygen_consumed'] = (processed['occupied_beds'] * 1.5).astype(int)
    processed['medication_stock'] = np.random.randint(500, 1000, len(df))
    processed['emergency_admissions'] = np.random.poisson(15, len(df))
    processed['is_weekend'] = processed['date'].dt.dayofweek >= 5
    processed['hospital_id'] = 'UPLOADED'
    processed['hospital_name'] = 'Uploaded Hospital Data'
    
    # Set date as index
    processed.set_index('date', inplace=True)
    processed.sort_index(inplace=True)
    
    # Add warnings
    if validation['columns_generated']:
        validation['warnings'].append(f"Generated default values for: {', '.join(validation['columns_generated'])}")
    
    return processed, validation


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
            "date_range": {
                "start": str(df.index.min()),
                "end": str(df.index.max())
            }
        })
    
    return {
        "has_uploads": len(uploaded_data) > 0,
        "uploads": uploads
    }


@app.delete("/api/upload/{hospital_id}")
async def delete_uploaded_data(hospital_id: str):
    """Delete uploaded data for a hospital."""
    global uploaded_data
    
    if hospital_id in uploaded_data:
        del uploaded_data[hospital_id]
        return {"success": True, "message": f"Deleted uploaded data for {hospital_id}"}
    else:
        raise HTTPException(status_code=404, detail=f"No uploaded data found for {hospital_id}")


@app.get("/api/upload/template")
async def get_upload_template():
    """Get a sample CSV template for data upload."""
    dates = pd.date_range('2025-01-01', periods=30, freq='D')
    
    template_data = {
        'date': dates.strftime('%Y-%m-%d'),
        'occupied_beds': np.random.randint(100, 180, 30),
        'total_beds': [200] * 30,
        'occupied_icu': np.random.randint(10, 25, 30),
        'total_icu_beds': [30] * 30,
        'ventilators_used': np.random.randint(5, 15, 30),
        'total_ventilators': [20] * 30,
        'staff_on_duty': np.random.randint(100, 140, 30),
        'flu_cases': np.random.poisson(40, 30),
        'temperature': np.random.normal(25, 5, 30).round(1),
        'humidity': np.random.normal(60, 10, 30).round(0).astype(int),
        'pollution': np.random.randint(50, 150, 30)
    }
    
    return convert_numpy(template_data)


# Run with: uvicorn api:app --reload --port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
