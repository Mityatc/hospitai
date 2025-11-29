"""
Enhanced Rule-Based Surge Predictor for HospitAI
Includes resource-aware predictions and multi-factor analysis.
"""

import pandas as pd
import numpy as np


def predict_surge(df):
    """
    Predict hospital surge risk using enhanced rule-based thresholds.
    
    Rules:
    - High flu cases (7-day average > 50)
    - High pollution (7-day average > 100 AQI)
    - High bed occupancy (> 80%)
    - High ICU occupancy (> 75%)
    - Low staff ratio (staff/occupied_beds < 1.0)
    - High ventilator usage (> 70%)
    
    Args:
        df (pd.DataFrame): Hospital data
    
    Returns:
        pd.DataFrame: DataFrame with surge risk columns added
    """
    df = df.copy()
    
    # Rolling averages
    df['flu_avg_7d'] = df['flu_cases'].rolling(window=7, min_periods=1).mean().round(1)
    df['pollution_avg_7d'] = df['pollution'].rolling(window=7, min_periods=1).mean().round(1)
    
    # Occupancy ratios
    df['bed_occupancy_ratio'] = (df['occupied_beds'] / df['total_beds']).round(3)
    df['icu_occupancy_ratio'] = (df['occupied_icu'] / df['total_icu_beds']).round(3)
    df['ventilator_usage_ratio'] = (df['ventilators_used'] / df['total_ventilators']).round(3)
    df['staff_ratio'] = (df['staff_on_duty'] / df['occupied_beds']).round(3)
    
    # Thresholds
    FLU_THRESHOLD = 50
    POLLUTION_THRESHOLD = 100
    BED_OCCUPANCY_THRESHOLD = 0.80
    ICU_OCCUPANCY_THRESHOLD = 0.75
    VENTILATOR_THRESHOLD = 0.70
    STAFF_RATIO_MIN = 1.0

    # Individual risk factors
    df['risk_flu'] = (df['flu_avg_7d'] > FLU_THRESHOLD).astype(int)
    df['risk_pollution'] = (df['pollution_avg_7d'] > POLLUTION_THRESHOLD).astype(int)
    df['risk_beds'] = (df['bed_occupancy_ratio'] > BED_OCCUPANCY_THRESHOLD).astype(int)
    df['risk_icu'] = (df['icu_occupancy_ratio'] > ICU_OCCUPANCY_THRESHOLD).astype(int)
    df['risk_ventilators'] = (df['ventilator_usage_ratio'] > VENTILATOR_THRESHOLD).astype(int)
    df['risk_staff'] = (df['staff_ratio'] < STAFF_RATIO_MIN).astype(int)
    
    # Calculate risk score (0-6)
    risk_columns = ['risk_flu', 'risk_pollution', 'risk_beds', 'risk_icu', 'risk_ventilators', 'risk_staff']
    df['risk_score'] = df[risk_columns].sum(axis=1)
    
    # Surge risk: any 2+ factors present
    df['surge_risk'] = (df['risk_score'] >= 2).astype(int)
    
    # Risk level categorization
    df['risk_level'] = pd.cut(
        df['risk_score'],
        bins=[-1, 0, 1, 2, 4, 6],
        labels=['Normal', 'Low', 'Moderate', 'High', 'Critical']
    )
    
    return df


def get_risk_breakdown(df):
    """
    Get detailed breakdown of current risk factors.
    
    Returns:
        dict: Risk factor details
    """
    latest = df.iloc[-1]
    
    breakdown = {
        'overall_score': int(latest['risk_score']),
        'risk_level': str(latest['risk_level']),
        'factors': {
            'Flu Cases': {
                'value': f"{latest['flu_avg_7d']:.1f}",
                'threshold': '> 50',
                'at_risk': bool(latest['risk_flu'])
            },
            'Air Quality': {
                'value': f"{latest['pollution_avg_7d']:.1f}",
                'threshold': '> 100 AQI',
                'at_risk': bool(latest['risk_pollution'])
            },
            'Bed Occupancy': {
                'value': f"{latest['bed_occupancy_ratio']*100:.1f}%",
                'threshold': '> 80%',
                'at_risk': bool(latest['risk_beds'])
            },
            'ICU Occupancy': {
                'value': f"{latest['icu_occupancy_ratio']*100:.1f}%",
                'threshold': '> 75%',
                'at_risk': bool(latest['risk_icu'])
            },
            'Ventilator Usage': {
                'value': f"{latest['ventilator_usage_ratio']*100:.1f}%",
                'threshold': '> 70%',
                'at_risk': bool(latest['risk_ventilators'])
            },
            'Staff Ratio': {
                'value': f"{latest['staff_ratio']:.2f}",
                'threshold': '< 1.0',
                'at_risk': bool(latest['risk_staff'])
            }
        }
    }
    return breakdown


if __name__ == "__main__":
    from data_generator import generate_data
    
    print("Testing enhanced predictor_rulebased.py:\n")
    df = generate_data(14)
    df_surge = predict_surge(df)
    
    print("Risk Analysis:")
    print(df_surge[['flu_cases', 'occupied_beds', 'risk_score', 'risk_level']].tail(5))
    
    print("\nRisk Breakdown:")
    breakdown = get_risk_breakdown(df_surge)
    print(f"Overall: {breakdown['risk_level']} (Score: {breakdown['overall_score']}/6)")
