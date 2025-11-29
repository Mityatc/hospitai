"""
ML-Based Predictor for HospitAI
"""

import os
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from dotenv import load_dotenv

load_dotenv()

REMOTE_MODE = os.getenv("REMOTE_MODE", "false").lower() == "true"
REMOTE_URL = os.getenv("REMOTE_URL", "")
PIPESHIFT_TOKEN = os.getenv("PIPESHIFT_TOKEN", "")


def local_model_predict(df, days=7):
    df_train = df.copy().reset_index(drop=True)
    feature_cols = ['temperature', 'humidity', 'pollution', 'flu_cases']
    X = df_train[feature_cols].values.astype(float)
    day_indices = np.arange(len(df_train)).reshape(-1, 1)
    X = np.hstack([day_indices, X])
    y = df_train['occupied_beds'].values.astype(float)
    
    model = LinearRegression()
    model.fit(X, y)
    
    recent_avg = df_train[feature_cols].tail(7).mean()
    future_indices = np.arange(len(df_train), len(df_train) + days).reshape(-1, 1)
    future_features = np.tile([float(recent_avg[c]) for c in feature_cols], (days, 1))
    X_future = np.hstack([future_indices, future_features])
    
    predictions = np.clip(model.predict(X_future), 0, float(df['total_beds'].iloc[0]))
    
    if 'date' in df.columns:
        last_date = pd.to_datetime(df['date'].iloc[-1])
    else:
        last_date = df.index[-1] if isinstance(df.index[-1], pd.Timestamp) else pd.Timestamp.now()
    
    future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=days, freq='D')
    return pd.Series(predictions, index=future_dates, name='predicted_occupied_beds')


def predict_ml(df, days=7):
    return local_model_predict(df, days)
