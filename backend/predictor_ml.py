"""
ML-Based Predictor for HospitAI
Supports both local and remote (Pipeshift) inference.
"""

import os
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from dotenv import load_dotenv

load_dotenv()

# Remote inference configuration
REMOTE_MODE = os.getenv("REMOTE_MODE", "false").lower() == "true"
REMOTE_URL = os.getenv("REMOTE_URL", "")
PIPESHIFT_TOKEN = os.getenv("PIPESHIFT_TOKEN", "")


def fetch_remote_prediction(df, days):
    """
    Fetch predictions from Pipeshift remote endpoint.
    
    Args:
        df: DataFrame with historical data
        days: Number of days to predict
    
    Returns:
        pd.Series: Predicted values
    """
    try:
        import requests
        
        headers = {"Authorization": f"Bearer {PIPESHIFT_TOKEN}"}
        payload = {
            "data": df.reset_index().to_dict(orient="records"),
            "days": days
        }
        
        response = requests.post(REMOTE_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        predictions = result.get("predictions", [])
        
        # Convert to Series
        future_dates = pd.date_range(
            start=df.index[-1] + pd.Timedelta(days=1),
            periods=days,
            freq='D'
        )
        return pd.Series(predictions, index=future_dates, name='predicted_occupied_beds')
    
    except Exception as e:
        print(f"Remote prediction failed: {e}. Falling back to local.")
        return local_model_predict(df, days)


def local_model_predict(df, days=7):
    """
    Local prediction using Linear Regression.
    
    Args:
        df: DataFrame with historical data
        days: Number of days to predict
    
    Returns:
        pd.Series: Predicted occupied beds
    """
    df_train = df.copy().reset_index(drop=True)
    
    # Features - only numeric columns
    feature_cols = ['temperature', 'humidity', 'pollution', 'flu_cases']
    X = df_train[feature_cols].values.astype(float)
    day_indices = np.arange(len(df_train)).reshape(-1, 1)
    X = np.hstack([day_indices, X])
    
    # Target
    y = df_train['occupied_beds'].values.astype(float)
    
    # Train
    model = LinearRegression()
    model.fit(X, y)
    
    # Prepare future features - only use numeric columns for mean
    numeric_cols = ['temperature', 'humidity', 'pollution', 'flu_cases']
    recent_data = df_train[numeric_cols].tail(7)
    recent_avg = recent_data.mean()
    
    future_indices = np.arange(len(df_train), len(df_train) + days).reshape(-1, 1)
    future_features = np.tile([
        float(recent_avg['temperature']),
        float(recent_avg['humidity']),
        float(recent_avg['pollution']),
        float(recent_avg['flu_cases'])
    ], (days, 1))
    
    X_future = np.hstack([future_indices, future_features])
    
    # Predict
    predictions = model.predict(X_future)
    predictions = np.clip(predictions, 0, float(df['total_beds'].iloc[0]))
    
    # Handle date index
    if 'date' in df.columns:
        last_date = pd.to_datetime(df['date'].iloc[-1])
    else:
        last_date = df.index[-1] if isinstance(df.index[-1], pd.Timestamp) else pd.Timestamp.now()
    
    future_dates = pd.date_range(
        start=last_date + pd.Timedelta(days=1),
        periods=days,
        freq='D'
    )
    
    return pd.Series(predictions, index=future_dates, name='predicted_occupied_beds')


def predict_ml(df, days=7):
    """
    Main prediction function - routes to local or remote based on config.
    
    Args:
        df: DataFrame with historical data
        days: Number of days to predict
    
    Returns:
        pd.Series: Predicted occupied beds
    """
    if REMOTE_MODE and REMOTE_URL and PIPESHIFT_TOKEN:
        return fetch_remote_prediction(df, days)
    else:
        return local_model_predict(df, days)


def get_inference_mode():
    """Return current inference mode for display."""
    if REMOTE_MODE and REMOTE_URL:
        return "🌐 Remote (Pipeshift)"
    return "💻 Local"


if __name__ == "__main__":
    from data_generator import generate_data
    
    print(f"Inference Mode: {get_inference_mode()}")
    print(f"Remote Mode: {REMOTE_MODE}")
    
    df = generate_data(10)
    predictions = predict_ml(df, days=3)
    print("\nPredictions:")
    print(predictions.round(1))
