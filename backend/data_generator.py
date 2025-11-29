"""
Data Generation Module for HospitAI
Simulates realistic hospital and environmental data.
"""

import pandas as pd
import numpy as np
from datetime import datetime


def generate_data(num_days=30, start_date="2025-01-01", hospital_id="H001", seed=42):
    np.random.seed(seed)
    dates = pd.date_range(start_date, periods=num_days, freq='D')
    day_of_year = dates.dayofyear
    
    # Seasonal patterns
    seasonal_temp = 20 + 10 * np.sin((day_of_year - 105) * 2 * np.pi / 365)
    temperature = seasonal_temp + np.random.normal(0, 3, num_days)
    
    seasonal_humidity = 60 + 15 * np.sin((day_of_year - 80) * 2 * np.pi / 365)
    humidity = np.clip(seasonal_humidity + np.random.normal(0, 8, num_days), 30, 95)
    
    seasonal_pollution = 80 - 30 * np.sin((day_of_year - 105) * 2 * np.pi / 365)
    pollution = np.clip(seasonal_pollution + np.random.gamma(2, 10, num_days), 20, 300)
    
    seasonal_flu = 40 + 30 * np.cos((day_of_year - 15) * 2 * np.pi / 365)
    flu_cases = np.random.poisson(np.maximum(seasonal_flu, 10))
    
    is_weekend = dates.dayofweek >= 5
    weekend_factor = np.where(is_weekend, 1.2, 1.0)
    
    total_beds, total_icu_beds, total_ventilators = 200, 30, 20
    
    base_occupancy = 120
    flu_impact = (flu_cases - 40) * 0.4
    pollution_impact = (pollution - 80) * 0.08
    weekend_impact = np.where(is_weekend, 15, 0)
    noise = np.random.normal(0, 8, num_days)
    
    occupied_beds = np.clip(base_occupancy + flu_impact + pollution_impact + weekend_impact + noise, 60, total_beds).astype(int)
    occupied_icu = np.clip(occupied_beds * 0.12 + np.where(flu_cases > 60, 5, 0) + np.random.normal(0, 2, num_days), 5, total_icu_beds).astype(int)
    ventilators_used = np.clip(occupied_icu * 0.5 + np.random.normal(0, 2, num_days), 0, total_ventilators).astype(int)
    staff_on_duty = np.clip(np.where(is_weekend, 100, 130) + np.random.normal(0, 10, num_days), 80, 150).astype(int)
    
    df = pd.DataFrame({
        'date': dates, 'hospital_id': hospital_id,
        'temperature': temperature.round(1), 'humidity': humidity.round(1),
        'pollution': pollution.round(1), 'flu_cases': flu_cases,
        'total_beds': total_beds, 'occupied_beds': occupied_beds,
        'total_icu_beds': total_icu_beds, 'occupied_icu': occupied_icu,
        'total_ventilators': total_ventilators, 'ventilators_used': ventilators_used,
        'total_staff': 150, 'staff_on_duty': staff_on_duty,
        'oxygen_consumed': (occupied_beds * 1.5).astype(int),
        'medication_stock': np.random.randint(500, 1000, num_days),
        'emergency_admissions': np.random.poisson(15 * weekend_factor),
        'is_weekend': is_weekend, 'hospital_name': 'City General Hospital'
    })
    df.set_index('date', inplace=True)
    return df


def generate_multi_hospital_data(num_days=30, start_date="2025-01-01"):
    hospitals = {'H001': ('City General Hospital', 1.0), 'H002': ('St. Mary Medical Center', 0.8), 'H003': ('Regional Health Center', 1.2)}
    all_data = {}
    for h_id, (name, size) in hospitals.items():
        df = generate_data(num_days, start_date, h_id)
        for col in ['total_beds', 'occupied_beds', 'total_icu_beds', 'occupied_icu', 'total_ventilators', 'ventilators_used', 'total_staff', 'staff_on_duty']:
            df[col] = (df[col] * size).astype(int)
        df['hospital_name'] = name
        all_data[h_id] = df
    return all_data
