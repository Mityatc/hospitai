"""
Data Upload Module for HospitAI
Handles CSV/Excel file uploads and column mapping.
"""

import streamlit as st
import pandas as pd
from datetime import datetime


def render_upload_tab():
    """Render the data upload interface."""
    st.header("📤 Upload Hospital Data")
    
    st.markdown("""
    Upload your hospital's CSV or Excel file to use real data instead of simulated data.
    
    **Required columns** (or map your columns):
    - Date
    - Occupied Beds
    - Total Beds
    - Flu Cases (optional)
    - Temperature (optional)
    - Pollution/AQI (optional)
    """)
    
    uploaded_file = st.file_uploader(
        "Choose a CSV or Excel file",
        type=["csv", "xlsx", "xls"],
        help="Upload hospital admission data"
    )
    
    if uploaded_file is not None:
        try:
            # Read file
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            st.success(f"✅ Loaded {len(df)} rows from {uploaded_file.name}")
            
            # Show preview
            st.subheader("📋 Data Preview")
            st.dataframe(df.head(10), use_container_width=True)
            
            # Column mapping
            st.subheader("🔗 Map Your Columns")
            st.markdown("Match your columns to HospitAI's expected format:")
            
            columns = ["(None)"] + list(df.columns)
            
            col1, col2 = st.columns(2)
            
            with col1:
                date_col = st.selectbox("Date Column", columns, index=0)
                beds_col = st.selectbox("Occupied Beds", columns, index=0)
                total_beds_col = st.selectbox("Total Beds", columns, index=0)
                flu_col = st.selectbox("Flu Cases (optional)", columns, index=0)
            
            with col2:
                temp_col = st.selectbox("Temperature (optional)", columns, index=0)
                humidity_col = st.selectbox("Humidity (optional)", columns, index=0)
                pollution_col = st.selectbox("Pollution/AQI (optional)", columns, index=0)
                icu_col = st.selectbox("ICU Beds (optional)", columns, index=0)
            
            if st.button("🚀 Process Data", type="primary"):
                processed_df = process_uploaded_data(
                    df, date_col, beds_col, total_beds_col,
                    flu_col, temp_col, humidity_col, pollution_col, icu_col
                )
                
                if processed_df is not None:
                    st.session_state['uploaded_data'] = processed_df
                    st.success("✅ Data processed! Switch to Summary tab to view.")
                    return processed_df
                    
        except Exception as e:
            st.error(f"❌ Error reading file: {str(e)}")
    
    # Show sample data format
    with st.expander("📝 Sample Data Format"):
        st.markdown("""
        Your CSV should look something like this:
        
        | date | occupied_beds | total_beds | flu_cases | temperature | pollution |
        |------|---------------|------------|-----------|-------------|-----------|
        | 2025-01-01 | 150 | 200 | 45 | 22.5 | 85 |
        | 2025-01-02 | 155 | 200 | 48 | 21.0 | 92 |
        """)
        
        # Download sample template
        sample_df = create_sample_template()
        csv = sample_df.to_csv(index=False)
        st.download_button(
            "⬇️ Download Sample Template",
            csv,
            "hospitai_template.csv",
            "text/csv"
        )
    
    return None


def process_uploaded_data(df, date_col, beds_col, total_beds_col,
                          flu_col, temp_col, humidity_col, pollution_col, icu_col):
    """
    Process uploaded data into HospitAI format.
    """
    import numpy as np
    
    try:
        processed = pd.DataFrame()
        
        # Date column (required)
        if date_col != "(None)":
            processed['date'] = pd.to_datetime(df[date_col])
        else:
            processed['date'] = pd.date_range(start='2025-01-01', periods=len(df), freq='D')
        
        # Occupied beds (required)
        if beds_col != "(None)":
            processed['occupied_beds'] = pd.to_numeric(df[beds_col], errors='coerce').fillna(100)
        else:
            processed['occupied_beds'] = 100
        
        # Total beds
        if total_beds_col != "(None)":
            processed['total_beds'] = pd.to_numeric(df[total_beds_col], errors='coerce').fillna(200)
        else:
            processed['total_beds'] = 200
        
        # Optional columns with defaults
        if flu_col != "(None)":
            processed['flu_cases'] = pd.to_numeric(df[flu_col], errors='coerce').fillna(30)
        else:
            processed['flu_cases'] = np.random.poisson(30, len(df))
        
        if temp_col != "(None)":
            processed['temperature'] = pd.to_numeric(df[temp_col], errors='coerce').fillna(25)
        else:
            processed['temperature'] = np.random.normal(25, 5, len(df))
        
        if humidity_col != "(None)":
            processed['humidity'] = pd.to_numeric(df[humidity_col], errors='coerce').fillna(60)
        else:
            processed['humidity'] = np.random.normal(60, 10, len(df))
        
        if pollution_col != "(None)":
            processed['pollution'] = pd.to_numeric(df[pollution_col], errors='coerce').fillna(75)
        else:
            processed['pollution'] = np.random.gamma(2, 30, len(df))
        
        # ICU beds
        if icu_col != "(None)":
            processed['occupied_icu'] = pd.to_numeric(df[icu_col], errors='coerce').fillna(15)
        else:
            processed['occupied_icu'] = (processed['occupied_beds'] * 0.15).astype(int)
        
        # Add derived columns
        processed['total_icu_beds'] = 30
        processed['total_ventilators'] = 20
        processed['ventilators_used'] = (processed['occupied_icu'] * 0.5).astype(int)
        processed['total_staff'] = 150
        processed['staff_on_duty'] = np.random.randint(100, 140, len(df))
        processed['oxygen_consumed'] = (processed['occupied_beds'] * 1.5).astype(int)
        processed['medication_stock'] = np.random.randint(500, 1000, len(df))
        processed['emergency_admissions'] = np.random.poisson(15, len(df))
        processed['is_weekend'] = processed['date'].dt.dayofweek >= 5
        processed['hospital_id'] = 'UPLOADED'
        
        # Set date as index
        processed.set_index('date', inplace=True)
        
        return processed
        
    except Exception as e:
        st.error(f"Error processing data: {str(e)}")
        return None


def create_sample_template():
    """Create a sample CSV template for download."""
    import numpy as np
    
    dates = pd.date_range('2025-01-01', periods=30, freq='D')
    
    return pd.DataFrame({
        'date': dates.strftime('%Y-%m-%d'),
        'occupied_beds': np.random.randint(100, 180, 30),
        'total_beds': 200,
        'icu_occupied': np.random.randint(10, 25, 30),
        'flu_cases': np.random.poisson(40, 30),
        'temperature': np.random.normal(25, 5, 30).round(1),
        'humidity': np.random.normal(60, 10, 30).round(1),
        'pollution_aqi': np.random.randint(50, 150, 30)
    })


def get_uploaded_data():
    """Get uploaded data from session state if available."""
    return st.session_state.get('uploaded_data', None)
