"""
Export Utilities for HospitAI
Functions to export data and reports with optional GPT integration.
"""

import pandas as pd
import io
from datetime import datetime


def export_to_csv(df, filename_prefix="hospitai_report"):
    """Export DataFrame to CSV format."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{filename_prefix}_{timestamp}.csv"
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer)
    return csv_buffer.getvalue(), filename


def generate_summary_report(df, predictions=None):
    """Generate a text summary report of hospital status."""
    latest = df.iloc[-1]
    
    report = f"""
================================================================================
                        HOSPITAI SURGE PREDICTION REPORT
                        Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
================================================================================

CURRENT STATUS SUMMARY
----------------------
Date Range: {df.index[0].strftime("%Y-%m-%d")} to {df.index[-1].strftime("%Y-%m-%d")}
Total Days Analyzed: {len(df)}

HOSPITAL CAPACITY
-----------------
Total Beds: {int(latest['total_beds'])}
Occupied Beds: {int(latest['occupied_beds'])} ({latest['occupied_beds']/latest['total_beds']*100:.1f}%)
Available Beds: {int(latest['total_beds'] - latest['occupied_beds'])}

ICU Status:
  Total ICU Beds: {int(latest['total_icu_beds'])}
  Occupied ICU: {int(latest['occupied_icu'])} ({latest['occupied_icu']/latest['total_icu_beds']*100:.1f}%)

RESOURCE UTILIZATION
--------------------
Ventilators: {int(latest['ventilators_used'])}/{int(latest['total_ventilators'])} in use
Staff on Duty: {int(latest['staff_on_duty'])}/{int(latest['total_staff'])}
Oxygen Consumed: {int(latest['oxygen_consumed'])} units
Medication Stock: {int(latest['medication_stock'])} units

ENVIRONMENTAL CONDITIONS
------------------------
Temperature: {latest['temperature']:.1f}°C
Humidity: {latest['humidity']:.1f}%
Air Quality (AQI): {latest['pollution']:.0f}

DISEASE METRICS
---------------
Flu Cases: {int(latest['flu_cases'])}
Emergency Admissions: {int(latest['emergency_admissions'])}
"""
    
    if 'risk_score' in df.columns:
        surge_days = (df['risk_score'] >= 2).sum()
        report += f"""
SURGE RISK ANALYSIS
-------------------
Days with Surge Risk: {surge_days}/{len(df)} ({surge_days/len(df)*100:.1f}%)
Current Risk Score: {int(latest['risk_score'])}/6
Risk Level: {latest['risk_level']}
"""
    
    if predictions is not None:
        report += f"""
PREDICTIONS ({len(predictions)}-DAY FORECAST)
---------------------------
Average Predicted: {predictions.mean():.0f} beds
Peak Predicted: {predictions.max():.0f} beds
"""
    
    report += f"""
================================================================================
                              END OF REPORT
================================================================================
"""
    return report


def render_export_tab(df, predictions=None):
    """Render the export tab with GPT integration."""
    import streamlit as st
    from gpt_module import generate_admin_report, GEMINI_AVAILABLE
    from predictor_ml import get_inference_mode
    
    st.header("📥 Export Data & Reports")
    
    # Show inference mode
    st.caption(f"Inference Mode: {get_inference_mode()}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Export Raw Data")
        csv_data, csv_filename = export_to_csv(df)
        st.download_button(
            label="⬇️ Download CSV",
            data=csv_data,
            file_name=csv_filename,
            mime="text/csv"
        )
        st.caption(f"{len(df)} days of data")
    
    with col2:
        st.subheader("📝 Export Report")
        report_text = generate_summary_report(df, predictions)
        st.download_button(
            label="⬇️ Download Report (TXT)",
            data=report_text,
            file_name=f"hospitai_report_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain"
        )
    
    st.markdown("---")
    
    # GPT Summary Section
    st.subheader("🧠 AI-Generated Summary")
    
    if not GEMINI_AVAILABLE:
        st.warning("OpenAI API key not configured. Add OPENAI_API_KEY to .env file.")
    
    if st.button("🧠 Generate Admin Report", type="primary"):
        with st.spinner("Generating AI summary..."):
            summary = generate_admin_report(df)
            st.text_area("📄 Executive Summary", summary, height=150)
    
    # Preview report
    with st.expander("👁️ Preview Standard Report"):
        st.text(report_text)


if __name__ == "__main__":
    print("export_utils.py loaded")
