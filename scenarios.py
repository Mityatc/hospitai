"""
What-If Scenario Simulator for HospitAI
Allows users to simulate different conditions and see predicted outcomes.
"""

import pandas as pd
import numpy as np


def apply_scenario(df, scenario_type, intensity=1.0):
    """
    Apply a what-if scenario to the data and predict outcomes.
    
    Args:
        df (pd.DataFrame): Base hospital data
        scenario_type (str): Type of scenario to simulate
        intensity (float): Severity multiplier (0.5 = mild, 1.0 = moderate, 2.0 = severe)
    
    Returns:
        pd.DataFrame: Modified data with scenario applied
    """
    df_scenario = df.copy()
    
    if scenario_type == "flu_outbreak":
        # Simulate flu outbreak - cases increase significantly
        flu_increase = np.random.poisson(30 * intensity, len(df))
        df_scenario['flu_cases'] = df['flu_cases'] + flu_increase
        # More beds occupied due to flu
        df_scenario['occupied_beds'] = np.clip(
            df['occupied_beds'] + (flu_increase * 0.5).astype(int),
            0, df['total_beds'].iloc[0]
        )
        df_scenario['occupied_icu'] = np.clip(
            df['occupied_icu'] + (flu_increase * 0.1).astype(int),
            0, df['total_icu_beds'].iloc[0]
        )
        
    elif scenario_type == "pollution_spike":
        # Simulate severe pollution event
        df_scenario['pollution'] = np.clip(df['pollution'] * (1 + 0.5 * intensity), 0, 400)
        # Respiratory cases increase
        resp_increase = (df_scenario['pollution'] - df['pollution']) * 0.1
        df_scenario['occupied_beds'] = np.clip(
            df['occupied_beds'] + resp_increase.astype(int),
            0, df['total_beds'].iloc[0]
        )
        
    elif scenario_type == "mass_casualty":
        # Simulate accident or disaster
        casualty_days = np.random.choice(len(df), size=max(1, int(len(df) * 0.1)), replace=False)
        casualties = np.zeros(len(df))
        casualties[casualty_days] = np.random.poisson(20 * intensity, len(casualty_days))
        df_scenario['emergency_admissions'] = df['emergency_admissions'] + casualties.astype(int)
        df_scenario['occupied_beds'] = np.clip(
            df['occupied_beds'] + (casualties * 0.8).astype(int),
            0, df['total_beds'].iloc[0]
        )
        df_scenario['occupied_icu'] = np.clip(
            df['occupied_icu'] + (casualties * 0.3).astype(int),
            0, df['total_icu_beds'].iloc[0]
        )

    elif scenario_type == "staff_shortage":
        # Simulate staff shortage (illness, strike, etc.)
        df_scenario['staff_on_duty'] = (df['staff_on_duty'] * (1 - 0.3 * intensity)).astype(int)
        # Reduced capacity means some patients may need transfer
        capacity_reduction = (df['staff_on_duty'] - df_scenario['staff_on_duty']) * 0.5
        df_scenario['occupied_beds'] = np.clip(
            df['occupied_beds'] - capacity_reduction.astype(int),
            0, df['total_beds'].iloc[0]
        )
        
    elif scenario_type == "equipment_failure":
        # Simulate ventilator or equipment shortage
        df_scenario['total_ventilators'] = (df['total_ventilators'] * (1 - 0.4 * intensity)).astype(int)
        df_scenario['ventilators_used'] = np.minimum(
            df['ventilators_used'],
            df_scenario['total_ventilators']
        )
        
    elif scenario_type == "heatwave":
        # Simulate extreme heat event
        df_scenario['temperature'] = df['temperature'] + (10 * intensity)
        # Heat-related admissions
        heat_cases = np.where(df_scenario['temperature'] > 35, 
                              np.random.poisson(15 * intensity, len(df)), 0)
        df_scenario['emergency_admissions'] = df['emergency_admissions'] + heat_cases
        df_scenario['occupied_beds'] = np.clip(
            df['occupied_beds'] + (heat_cases * 0.6).astype(int),
            0, df['total_beds'].iloc[0]
        )
    
    # Recalculate resource usage
    df_scenario['ventilators_used'] = np.clip(
        (df_scenario['occupied_icu'] * 0.6).astype(int),
        0, df_scenario['total_ventilators']
    )
    df_scenario['oxygen_consumed'] = (
        df_scenario['occupied_beds'] * 1.5 + df_scenario['occupied_icu'] * 5
    ).astype(int)
    
    return df_scenario


def compare_scenarios(df_base, df_scenario):
    """
    Compare base data with scenario data and return impact summary.
    
    Returns:
        dict: Impact metrics comparing base vs scenario
    """
    impact = {
        'bed_occupancy_change': (
            df_scenario['occupied_beds'].mean() - df_base['occupied_beds'].mean()
        ),
        'icu_occupancy_change': (
            df_scenario['occupied_icu'].mean() - df_base['occupied_icu'].mean()
        ),
        'peak_occupancy_base': df_base['occupied_beds'].max(),
        'peak_occupancy_scenario': df_scenario['occupied_beds'].max(),
        'days_over_capacity': (
            df_scenario['occupied_beds'] > df_scenario['total_beds'] * 0.9
        ).sum(),
        'resource_strain_index': (
            (df_scenario['occupied_beds'] / df_scenario['total_beds']).mean() * 100
        )
    }
    return impact


SCENARIO_DESCRIPTIONS = {
    'flu_outbreak': {
        'name': '🤒 Flu Outbreak',
        'description': 'Simulates a sudden increase in influenza cases',
        'impacts': ['Increased bed occupancy', 'Higher ICU demand', 'More staff needed']
    },
    'pollution_spike': {
        'name': '🌫️ Pollution Spike',
        'description': 'Simulates severe air quality deterioration',
        'impacts': ['Respiratory admissions increase', 'Oxygen demand rises']
    },
    'mass_casualty': {
        'name': '🚨 Mass Casualty Event',
        'description': 'Simulates accident or disaster scenario',
        'impacts': ['Emergency surge', 'ICU overflow risk', 'Staff overtime']
    },
    'staff_shortage': {
        'name': '👥 Staff Shortage',
        'description': 'Simulates reduced staffing levels',
        'impacts': ['Reduced capacity', 'Longer wait times', 'Transfer needs']
    },
    'equipment_failure': {
        'name': '🔧 Equipment Failure',
        'description': 'Simulates ventilator or equipment shortage',
        'impacts': ['Critical care limitations', 'Transfer requirements']
    },
    'heatwave': {
        'name': '🌡️ Heatwave',
        'description': 'Simulates extreme heat event',
        'impacts': ['Heat-related admissions', 'Elderly at risk', 'Dehydration cases']
    }
}


if __name__ == "__main__":
    from data_generator import generate_data
    
    print("Testing scenarios.py:\n")
    df = generate_data(14)
    
    for scenario in ['flu_outbreak', 'pollution_spike', 'mass_casualty']:
        df_scenario = apply_scenario(df, scenario, intensity=1.5)
        impact = compare_scenarios(df, df_scenario)
        print(f"\n{scenario.upper()}:")
        print(f"  Bed change: {impact['bed_occupancy_change']:+.1f}")
        print(f"  ICU change: {impact['icu_occupancy_change']:+.1f}")
        print(f"  Days over 90%: {impact['days_over_capacity']}")
