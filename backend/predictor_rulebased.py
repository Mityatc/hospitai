"""
Rule-Based Surge Predictor for HospitAI
"""

import pandas as pd
import numpy as np


def predict_surge(df):
    df = df.copy()
    df['flu_avg_7d'] = df['flu_cases'].rolling(window=7, min_periods=1).mean().round(1)
    df['pollution_avg_7d'] = df['pollution'].rolling(window=7, min_periods=1).mean().round(1)
    df['bed_occupancy_ratio'] = (df['occupied_beds'] / df['total_beds']).round(3)
    df['icu_occupancy_ratio'] = (df['occupied_icu'] / df['total_icu_beds']).round(3)
    df['ventilator_usage_ratio'] = (df['ventilators_used'] / df['total_ventilators']).round(3)
    df['staff_ratio'] = (df['staff_on_duty'] / df['occupied_beds']).round(3)
    
    df['risk_flu'] = (df['flu_avg_7d'] > 50).astype(int)
    df['risk_pollution'] = (df['pollution_avg_7d'] > 100).astype(int)
    df['risk_beds'] = (df['bed_occupancy_ratio'] > 0.80).astype(int)
    df['risk_icu'] = (df['icu_occupancy_ratio'] > 0.75).astype(int)
    df['risk_ventilators'] = (df['ventilator_usage_ratio'] > 0.70).astype(int)
    df['risk_staff'] = (df['staff_ratio'] < 1.0).astype(int)
    
    risk_columns = ['risk_flu', 'risk_pollution', 'risk_beds', 'risk_icu', 'risk_ventilators', 'risk_staff']
    df['risk_score'] = df[risk_columns].sum(axis=1)
    df['surge_risk'] = (df['risk_score'] >= 2).astype(int)
    df['risk_level'] = pd.cut(df['risk_score'], bins=[-1, 0, 1, 2, 4, 6],
                              labels=['Normal', 'Low', 'Moderate', 'High', 'Critical'])
    return df


def get_risk_breakdown(df):
    latest = df.iloc[-1]
    return {
        'overall_score': int(latest['risk_score']),
        'risk_level': str(latest['risk_level']),
        'factors': {
            'Flu Cases': {'value': f"{latest['flu_avg_7d']:.1f}", 'at_risk': bool(latest['risk_flu'])},
            'Air Quality': {'value': f"{latest['pollution_avg_7d']:.1f}", 'at_risk': bool(latest['risk_pollution'])},
            'Bed Occupancy': {'value': f"{latest['bed_occupancy_ratio']*100:.1f}%", 'at_risk': bool(latest['risk_beds'])},
            'ICU Occupancy': {'value': f"{latest['icu_occupancy_ratio']*100:.1f}%", 'at_risk': bool(latest['risk_icu'])},
            'Ventilator Usage': {'value': f"{latest['ventilator_usage_ratio']*100:.1f}%", 'at_risk': bool(latest['risk_ventilators'])},
            'Staff Ratio': {'value': f"{latest['staff_ratio']:.2f}", 'at_risk': bool(latest['risk_staff'])}
        }
    }
