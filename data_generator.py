"""
Enhanced Data Generation Module for HospitAI
Simulates realistic hospital and environmental data with seasonal patterns.
"""

import pandas as pd
import numpy as np
from datetime import datetime


def generate_data(num_days=30, start_date="2025-01-01", hospital_id="H001", seed=42):
    """
    Generate simulated hospital and environmental data with seasonal patterns.
    
    Args:
        num_days (int): Number of days to simulate (default: 30)
        start_date (str): Starting date in YYYY-MM-DD format
        hospital_id (str): Hospital identifier
        seed (int): Random seed for reproducible data (default: 42)
    
    Returns:
        pd.DataFrame: DataFrame with daily hospital and environmental metrics
    """
    # Set seed for consistent data
    np.random.seed(seed)
    
    dates = pd.date_range(start_date, periods=num_days, freq='D')
    
    # Extract day of year for seasonal calculations
    day_of_year = dates.dayofyear
    
    # Seasonal temperature pattern (cold in winter, warm in summer)
    # Using sine wave: coldest around day 15 (Jan), warmest around day 196 (July)
    seasonal_temp = 20 + 10 * np.sin((day_of_year - 105) * 2 * np.pi / 365)
    temperature = seasonal_temp + np.random.normal(0, 3, num_days)
    
    # Humidity - higher in monsoon season (June-Sept)
    seasonal_humidity = 60 + 15 * np.sin((day_of_year - 80) * 2 * np.pi / 365)
    humidity = seasonal_humidity + np.random.normal(0, 8, num_days)
    humidity = np.clip(humidity, 30, 95)
    
    # Pollution - higher in winter (temperature inversion)
    seasonal_pollution = 80 - 30 * np.sin((day_of_year - 105) * 2 * np.pi / 365)
    pollution = seasonal_pollution + np.random.gamma(2, 10, num_days)
    pollution = np.clip(pollution, 20, 300)
    
    # Flu cases - peaks in winter months
    seasonal_flu = 40 + 30 * np.cos((day_of_year - 15) * 2 * np.pi / 365)
    flu_base = np.maximum(seasonal_flu, 10)
    flu_cases = np.random.poisson(flu_base)
    
    # Weekend effect - more accidents on weekends
    is_weekend = dates.dayofweek >= 5
    weekend_factor = np.where(is_weekend, 1.2, 1.0)
    
    # Hospital capacity
    total_beds = 200
    total_icu_beds = 30
    total_ventilators = 20
    total_staff = 150
    total_oxygen_units = 500

    # Occupied beds - correlated with flu, pollution, and weekends
    base_occupancy = 120
    flu_impact = (flu_cases - 40) * 0.4
    pollution_impact = (pollution - 80) * 0.08
    weekend_impact = np.where(is_weekend, 15, 0)
    noise = np.random.normal(0, 8, num_days)
    
    occupied_beds = base_occupancy + flu_impact + pollution_impact + weekend_impact + noise
    occupied_beds = np.clip(occupied_beds, 60, total_beds).astype(int)
    
    # ICU beds - subset of occupied, higher during severe cases
    icu_base = occupied_beds * 0.12
    icu_surge = np.where(flu_cases > 60, 5, 0)
    occupied_icu = np.clip(icu_base + icu_surge + np.random.normal(0, 2, num_days), 5, total_icu_beds).astype(int)
    
    # Ventilators in use - correlated with ICU
    ventilators_base = occupied_icu * 0.5
    ventilators_used = np.clip(ventilators_base + np.random.normal(0, 2, num_days), 0, total_ventilators).astype(int)
    
    # Staff on duty - varies by day, reduced on weekends
    staff_base = np.where(is_weekend, 100, 130)
    staff_on_duty = np.clip(staff_base + np.random.normal(0, 10, num_days), 80, total_staff).astype(int)
    
    # Oxygen units consumed daily
    oxygen_base = occupied_beds * 1.5 + occupied_icu * 5
    oxygen_consumed = np.clip(oxygen_base + np.random.normal(0, 20, num_days), 50, total_oxygen_units).astype(int)
    
    # Medication stock level (decreases over time, restocked weekly)
    med_stock = np.zeros(num_days)
    current_stock = 1000
    for i in range(num_days):
        daily_use = occupied_beds[i] * 2 + occupied_icu[i] * 5 + np.random.randint(10, 30)
        current_stock -= daily_use
        if dates[i].dayofweek == 0:  # Restock on Mondays
            current_stock = min(current_stock + 800, 1200)
        current_stock = max(current_stock, 100)
        med_stock[i] = current_stock
    
    # Emergency admissions
    emergency_base = 15 * weekend_factor
    emergency_admissions = np.random.poisson(emergency_base)
    
    df = pd.DataFrame({
        'date': dates,
        'hospital_id': hospital_id,
        'temperature': temperature.round(1),
        'humidity': humidity.round(1),
        'pollution': pollution.round(1),
        'flu_cases': flu_cases,
        'total_beds': total_beds,
        'occupied_beds': occupied_beds,
        'total_icu_beds': total_icu_beds,
        'occupied_icu': occupied_icu,
        'total_ventilators': total_ventilators,
        'ventilators_used': ventilators_used,
        'total_staff': total_staff,
        'staff_on_duty': staff_on_duty,
        'oxygen_consumed': oxygen_consumed,
        'medication_stock': med_stock.astype(int),
        'emergency_admissions': emergency_admissions,
        'is_weekend': is_weekend
    })
    
    df.set_index('date', inplace=True)
    return df


def generate_multi_hospital_data(num_days=30, start_date="2025-01-01"):
    """
    Generate data for multiple hospitals.
    
    Returns:
        dict: Dictionary with hospital_id as key and DataFrame as value
    """
    hospitals = {
        'H001': {'name': 'City General Hospital', 'size': 1.0},
        'H002': {'name': 'St. Mary Medical Center', 'size': 0.8},
        'H003': {'name': 'Regional Health Center', 'size': 1.2},
    }
    
    all_data = {}
    for h_id, info in hospitals.items():
        df = generate_data(num_days, start_date, h_id)
        # Scale by hospital size
        scale_cols = ['total_beds', 'occupied_beds', 'total_icu_beds', 'occupied_icu',
                      'total_ventilators', 'ventilators_used', 'total_staff', 'staff_on_duty']
        for col in scale_cols:
            df[col] = (df[col] * info['size']).astype(int)
        df['hospital_name'] = info['name']
        all_data[h_id] = df
    
    return all_data


# Test
if __name__ == "__main__":
    print("Testing enhanced data_generator.py:\n")
    df = generate_data(7)
    print(df[['temperature', 'flu_cases', 'occupied_beds', 'occupied_icu', 'ventilators_used']].to_string())
