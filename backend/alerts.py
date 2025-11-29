"""
Enhanced Alert Banner Module for HospitAI
Displays warnings and alerts based on hospital capacity and risk metrics.
"""

import streamlit as st


def show_alerts(df):
    """
    Display alert banners based on current hospital metrics.
    
    Checks multiple risk factors and displays appropriate alerts.
    """
    latest = df.iloc[-1]
    
    # Calculate ratios
    bed_ratio = latest['occupied_beds'] / latest['total_beds']
    icu_ratio = latest['occupied_icu'] / latest['total_icu_beds']
    vent_ratio = latest['ventilators_used'] / latest['total_ventilators']
    
    alerts_shown = False
    
    # Critical alerts (red)
    if bed_ratio > 0.90:
        st.error(f"🚨 **CRITICAL: Hospital at {bed_ratio*100:.0f}% capacity!** Immediate action required.")
        alerts_shown = True
    
    if icu_ratio > 0.90:
        st.error(f"🚨 **CRITICAL: ICU at {icu_ratio*100:.0f}% capacity!** Consider patient transfers.")
        alerts_shown = True
    
    # High alerts (orange/warning)
    if 0.75 < bed_ratio <= 0.90:
        st.warning(f"⚠️ **High bed occupancy: {bed_ratio*100:.0f}%** - Monitor closely")
        alerts_shown = True
    
    if 0.75 < icu_ratio <= 0.90:
        st.warning(f"⚠️ **High ICU occupancy: {icu_ratio*100:.0f}%** - Prepare contingency")
        alerts_shown = True
    
    if vent_ratio > 0.80:
        st.warning(f"💨 **Ventilator usage high: {vent_ratio*100:.0f}%**")
        alerts_shown = True
    
    if latest['flu_cases'] > 70:
        st.warning(f"🤒 **Flu surge: {int(latest['flu_cases'])} cases** (above threshold)")
        alerts_shown = True
    
    if latest['pollution'] > 150:
        st.warning(f"🌫️ **Poor air quality: AQI {latest['pollution']:.0f}**")
        alerts_shown = True
    
    if latest['medication_stock'] < 300:
        st.warning(f"💊 **Low medication stock: {int(latest['medication_stock'])} units**")
        alerts_shown = True
    
    # Staff alert
    staff_ratio = latest['staff_on_duty'] / latest['occupied_beds']
    if staff_ratio < 0.9:
        st.warning(f"👥 **Staff shortage: Ratio {staff_ratio:.2f}** (below 1.0)")
        alerts_shown = True
    
    # Surge risk alert
    if 'risk_score' in df.columns and latest['risk_score'] >= 3:
        st.error(f"⚠️ **HIGH SURGE RISK** - Score: {int(latest['risk_score'])}/6")
        alerts_shown = True
    
    # All clear
    if not alerts_shown:
        st.success("✅ **All systems normal** - No immediate concerns")


def show_capacity_gauge(df):
    """Display visual gauge of hospital capacity."""
    latest = df.iloc[-1]
    
    st.subheader("🏥 Capacity Overview")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        bed_ratio = latest['occupied_beds'] / latest['total_beds']
        st.progress(min(bed_ratio, 1.0))
    
    with col2:
        st.metric("Capacity", f"{bed_ratio*100:.1f}%")
    
    st.caption(f"Beds: {int(latest['occupied_beds'])}/{int(latest['total_beds'])} | "
               f"ICU: {int(latest['occupied_icu'])}/{int(latest['total_icu_beds'])} | "
               f"Ventilators: {int(latest['ventilators_used'])}/{int(latest['total_ventilators'])}")


if __name__ == "__main__":
    print("alerts.py loaded - run through Streamlit to see alerts")
