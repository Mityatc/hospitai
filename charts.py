"""
Enhanced Chart Rendering Module for HospitAI
Functions to display metrics, charts, and visualizations in Streamlit.
"""

import streamlit as st
import pandas as pd
import altair as alt


def plot_time_series(df, predictions=None):
    """Display time-series line charts for key hospital metrics."""
    st.subheader("📈 Patient & Disease Trends")
    
    chart_data = df[['flu_cases', 'occupied_beds', 'emergency_admissions']].copy()
    st.line_chart(chart_data)
    
    st.subheader("🌡️ Environmental Factors")
    env_data = df[['temperature', 'humidity', 'pollution']]
    st.line_chart(env_data)


def show_metrics(df):
    """Display summary metrics in columns."""
    latest = df.iloc[-1]
    previous = df.iloc[-2] if len(df) > 1 else latest
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        delta = int(latest['flu_cases'] - previous['flu_cases'])
        st.metric("🤒 Flu Cases", int(latest['flu_cases']), delta)
    
    with col2:
        occ_pct = latest['occupied_beds'] / latest['total_beds'] * 100
        delta = int(latest['occupied_beds'] - previous['occupied_beds'])
        st.metric("🛏️ Bed Occupancy", f"{occ_pct:.1f}%", f"{delta} beds")
    
    with col3:
        st.metric("🌫️ Air Quality", int(latest['pollution']),
                  delta_color="inverse")
    
    with col4:
        st.metric("🌡️ Temperature", f"{latest['temperature']:.1f}°C")


def show_resource_metrics(df):
    """Display resource utilization metrics."""
    latest = df.iloc[-1]
    
    st.subheader("🏥 Resource Utilization")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        icu_pct = latest['occupied_icu'] / latest['total_icu_beds'] * 100
        st.metric("🚨 ICU Beds", 
                  f"{int(latest['occupied_icu'])}/{int(latest['total_icu_beds'])}",
                  f"{icu_pct:.0f}%")
    
    with col2:
        vent_pct = latest['ventilators_used'] / latest['total_ventilators'] * 100
        st.metric("💨 Ventilators",
                  f"{int(latest['ventilators_used'])}/{int(latest['total_ventilators'])}",
                  f"{vent_pct:.0f}%")
    
    with col3:
        staff_ratio = latest['staff_on_duty'] / latest['occupied_beds']
        st.metric("👥 Staff on Duty",
                  int(latest['staff_on_duty']),
                  f"Ratio: {staff_ratio:.2f}")
    
    with col4:
        med_status = "🟢" if latest['medication_stock'] > 500 else "🟡" if latest['medication_stock'] > 200 else "🔴"
        st.metric(f"{med_status} Med Stock",
                  int(latest['medication_stock']),
                  "units")


def plot_capacity_gauges(df):
    """Display capacity gauges for beds, ICU, and ventilators."""
    latest = df.iloc[-1]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        bed_pct = latest['occupied_beds'] / latest['total_beds']
        st.markdown("**🛏️ Bed Capacity**")
        st.progress(min(bed_pct, 1.0))
        st.caption(f"{int(latest['occupied_beds'])}/{int(latest['total_beds'])} ({bed_pct*100:.1f}%)")
    
    with col2:
        icu_pct = latest['occupied_icu'] / latest['total_icu_beds']
        st.markdown("**🚨 ICU Capacity**")
        st.progress(min(icu_pct, 1.0))
        st.caption(f"{int(latest['occupied_icu'])}/{int(latest['total_icu_beds'])} ({icu_pct*100:.1f}%)")
    
    with col3:
        vent_pct = latest['ventilators_used'] / latest['total_ventilators']
        st.markdown("**💨 Ventilator Usage**")
        st.progress(min(vent_pct, 1.0))
        st.caption(f"{int(latest['ventilators_used'])}/{int(latest['total_ventilators'])} ({vent_pct*100:.1f}%)")


def plot_risk_breakdown(breakdown):
    """Display risk factor breakdown."""
    st.subheader("⚠️ Risk Factor Analysis")
    
    factors = breakdown['factors']
    
    for factor_name, details in factors.items():
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            icon = "🔴" if details['at_risk'] else "🟢"
            st.write(f"{icon} **{factor_name}**")
        with col2:
            st.write(f"Value: {details['value']}")
        with col3:
            st.write(f"Threshold: {details['threshold']}")


def plot_surge_risk(df):
    """Display surge risk over time."""
    if 'risk_score' in df.columns:
        st.subheader("📊 Risk Score Timeline")
        
        chart_data = df[['risk_score']].copy()
        chart_data['threshold'] = 2  # Surge threshold
        
        st.area_chart(chart_data)
        
        surge_days = (df['risk_score'] >= 2).sum()
        st.caption(f"Days at elevated risk: {surge_days}/{len(df)} ({surge_days/len(df)*100:.1f}%)")


def plot_multi_hospital_comparison(hospital_data):
    """Compare metrics across multiple hospitals."""
    st.subheader("🏥 Multi-Hospital Comparison")
    
    comparison_data = []
    for h_id, df in hospital_data.items():
        latest = df.iloc[-1]
        comparison_data.append({
            'Hospital': latest.get('hospital_name', h_id),
            'Bed Occupancy (%)': latest['occupied_beds'] / latest['total_beds'] * 100,
            'ICU Occupancy (%)': latest['occupied_icu'] / latest['total_icu_beds'] * 100,
            'Flu Cases': latest['flu_cases'],
            'Staff Ratio': latest['staff_on_duty'] / latest['occupied_beds']
        })
    
    comp_df = pd.DataFrame(comparison_data)
    
    # Display as table
    st.dataframe(comp_df.style.format({
        'Bed Occupancy (%)': '{:.1f}',
        'ICU Occupancy (%)': '{:.1f}',
        'Staff Ratio': '{:.2f}'
    }), hide_index=True)
    
    # Bar chart comparison
    chart = alt.Chart(comp_df).mark_bar().encode(
        x='Hospital:N',
        y='Bed Occupancy (%):Q',
        color=alt.condition(
            alt.datum['Bed Occupancy (%)'] > 80,
            alt.value('#ff4b4b'),
            alt.value('#4CAF50')
        )
    ).properties(height=300)
    
    st.altair_chart(chart, use_container_width=True)


def plot_scenario_comparison(df_base, df_scenario, scenario_name):
    """Compare base data with scenario data."""
    st.subheader(f"📊 Scenario Impact: {scenario_name}")
    
    comparison = pd.DataFrame({
        'Baseline': df_base['occupied_beds'],
        'Scenario': df_scenario['occupied_beds']
    })
    
    st.line_chart(comparison)
    
    # Impact metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        change = df_scenario['occupied_beds'].mean() - df_base['occupied_beds'].mean()
        st.metric("Avg Bed Change", f"{change:+.1f}")
    with col2:
        peak_change = df_scenario['occupied_beds'].max() - df_base['occupied_beds'].max()
        st.metric("Peak Change", f"{peak_change:+.0f}")
    with col3:
        over_cap = (df_scenario['occupied_beds'] > df_scenario['total_beds'] * 0.9).sum()
        st.metric("Days Over 90%", over_cap)


if __name__ == "__main__":
    print("Charts module loaded. Functions available:")
    print("- plot_time_series(df)")
    print("- show_metrics(df)")
    print("- show_resource_metrics(df)")
    print("- plot_capacity_gauges(df)")
    print("- plot_risk_breakdown(breakdown)")
    print("- plot_surge_risk(df)")
    print("- plot_multi_hospital_comparison(hospital_data)")
    print("- plot_scenario_comparison(df_base, df_scenario, name)")
