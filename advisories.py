"""
Patient Advisory Module for HospitAI
Provides health guidance based on environmental and disease conditions.
"""

import streamlit as st


def show_advisory(df):
    """
    Display patient health advisories based on current conditions.
    
    Provides actionable guidance for:
    - Air quality concerns
    - Flu outbreak prevention
    - General health tips during high-risk periods
    
    Args:
        df (pd.DataFrame): Hospital and environmental data
    """
    # Get latest conditions
    latest = df.iloc[-1]
    
    st.subheader("💡 Health Advisories")
    
    advisories_shown = False
    
    # Air quality advisory
    if latest['pollution'] > 100:
        severity = "Unhealthy" if latest['pollution'] > 150 else "Moderate"
        st.info(f"""
        **🌫️ Air Quality Alert ({severity})**
        - Consider wearing a mask outdoors
        - Limit strenuous outdoor activities
        - Keep windows closed if possible
        - Use air purifiers indoors
        """)
        advisories_shown = True
    
    # Flu advisory
    if latest['flu_cases'] > 50:
        st.info("""
        **🤒 Flu Activity Elevated**
        - Practice frequent handwashing
        - Avoid close contact with sick individuals
        - Consider flu vaccination if not already vaccinated
        - Stay home if experiencing symptoms
        """)
        advisories_shown = True
    
    # Temperature advisory
    if latest['temperature'] < 10:
        st.info("""
        **🥶 Cold Weather Advisory**
        - Dress warmly in layers
        - Watch for signs of hypothermia
        - Check on elderly neighbors
        - Protect exposed skin
        """)
        advisories_shown = True
    elif latest['temperature'] > 30:
        st.info("""
        **🌡️ Heat Advisory**
        - Stay hydrated
        - Avoid prolonged sun exposure
        - Check on vulnerable individuals
        - Seek air-conditioned spaces
        """)
        advisories_shown = True
    
    # Hospital capacity advisory
    occupancy_ratio = latest['occupied_beds'] / latest['total_beds']
    if occupancy_ratio > 0.80:
        st.warning("""
        **🏥 Hospital Capacity Notice**
        - Emergency services may experience delays
        - Consider urgent care for non-critical issues
        - Have emergency contacts ready
        - Keep essential medications stocked
        """)
        advisories_shown = True
    
    # General wellness tip if no specific advisories
    if not advisories_shown:
        st.success("""
        **✅ General Wellness Tips**
        - Maintain regular exercise routine
        - Eat a balanced diet
        - Get adequate sleep (7-9 hours)
        - Stay up to date with preventive care
        """)


def show_risk_summary(df):
    """
    Display a summary of current risk factors.
    
    Args:
        df (pd.DataFrame): Hospital data with risk metrics
    """
    latest = df.iloc[-1]
    
    st.subheader("📊 Risk Factor Summary")
    
    # Create risk assessment
    risks = []
    
    # Pollution risk
    if latest['pollution'] > 150:
        risks.append(("High", "Air Quality", "🔴"))
    elif latest['pollution'] > 100:
        risks.append(("Moderate", "Air Quality", "🟡"))
    else:
        risks.append(("Low", "Air Quality", "🟢"))
    
    # Flu risk
    if latest['flu_cases'] > 70:
        risks.append(("High", "Flu Activity", "🔴"))
    elif latest['flu_cases'] > 50:
        risks.append(("Moderate", "Flu Activity", "🟡"))
    else:
        risks.append(("Low", "Flu Activity", "🟢"))
    
    # Capacity risk
    occupancy = latest['occupied_beds'] / latest['total_beds']
    if occupancy > 0.85:
        risks.append(("High", "Hospital Capacity", "🔴"))
    elif occupancy > 0.75:
        risks.append(("Moderate", "Hospital Capacity", "🟡"))
    else:
        risks.append(("Low", "Hospital Capacity", "🟢"))
    
    # Display in columns
    cols = st.columns(len(risks))
    for col, (level, factor, icon) in zip(cols, risks):
        with col:
            st.metric(label=f"{icon} {factor}", value=level)


# Test the advisory functions
if __name__ == "__main__":
    import pandas as pd
    
    print("Testing advisories.py:\n")
    
    # High-risk scenario
    print("Test: High-risk scenario")
    test_data = pd.DataFrame({
        'temperature': [8],
        'pollution': [160],
        'flu_cases': [75],
        'occupied_beds': [170],
        'total_beds': [200]
    })
    print("Temperature: 8°C, Pollution: 160, Flu: 75, Occupancy: 85%")
    print("Expected: Multiple advisories (cold, pollution, flu, capacity)\n")
    
    print("Run through Streamlit app to see formatted advisories.")
