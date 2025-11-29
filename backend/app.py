"""
HospitAI Dashboard v3.0 - Production-Ready Application
AI-based hospital surge prediction with real-time data integration.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Import custom modules
from data_generator import generate_data, generate_multi_hospital_data
from predictor_rulebased import predict_surge, get_risk_breakdown
from predictor_ml import predict_ml
from charts import (plot_time_series, show_metrics, show_resource_metrics,
                    plot_capacity_gauges, plot_risk_breakdown, plot_surge_risk,
                    plot_multi_hospital_comparison, plot_scenario_comparison)
from alerts import show_alerts, show_capacity_gauge
from advisories import show_advisory, show_risk_summary
from scenarios import apply_scenario, compare_scenarios, SCENARIO_DESCRIPTIONS
from export_utils import export_to_csv, generate_summary_report

# Page configuration
st.set_page_config(
    page_title="HospitAI Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {font-size: 2.5rem; font-weight: bold; color: #1E88E5;}
    .sub-header {font-size: 1.2rem; color: #666;}
    .live-badge {background: #4CAF50; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem;}
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<p class="main-header">🏥 HospitAI Dashboard</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">AI-Powered Hospital Surge Prediction System v3.0</p>', unsafe_allow_html=True)
st.markdown("---")

# Sidebar
st.sidebar.header("⚙️ Dashboard Controls")

# Data Source Selection
st.sidebar.subheader("📊 Data Source")
data_source = st.sidebar.radio(
    "Select Data Source",
    ["Simulated Data", "Upload CSV", "Live API Data"],
    help="Choose where to get hospital data from"
)

# City selection for live data
if data_source == "Live API Data":
    city = st.sidebar.selectbox(
        "Select City",
        ["Delhi", "Mumbai", "Bangalore", "Chennai", "Kolkata", "Hyderabad"]
    )
else:
    city = "Delhi"

# Date range selection
st.sidebar.subheader("📅 Date Range")
col1, col2 = st.sidebar.columns(2)
with col1:
    start_date = st.date_input("Start Date", datetime(2025, 1, 1))
with col2:
    end_date = st.date_input("End Date", datetime(2025, 1, 31))

num_days = (end_date - start_date).days + 1
if num_days < 7:
    st.sidebar.warning("Select at least 7 days")
    num_days = 7

# Hospital selection
st.sidebar.subheader("🏥 Hospital Selection")
view_mode = st.sidebar.radio("View Mode", ["Single Hospital", "Multi-Hospital Comparison"])

if view_mode == "Single Hospital":
    hospital_options = {
        "H001": "City General Hospital",
        "H002": "St. Mary Medical Center", 
        "H003": "Regional Health Center"
    }
    selected_hospital = st.sidebar.selectbox(
        "Select Hospital",
        options=list(hospital_options.keys()),
        format_func=lambda x: hospital_options[x]
    )

# Prediction settings
st.sidebar.subheader("🔮 Prediction Settings")
predict_days = st.sidebar.slider("Days to Predict", 1, 14, 7)

# Load data based on source
df_with_surge = None
hospital_data = None

if data_source == "Upload CSV":
    from data_upload import get_uploaded_data
    uploaded = get_uploaded_data()
    if uploaded is not None:
        df_with_surge = predict_surge(uploaded)
        st.sidebar.success("✅ Using uploaded data")
    else:
        st.sidebar.info("📤 Go to Upload tab to load data")

elif data_source == "Live API Data":
    from real_data_api import get_realtime_data, check_api_status
    api_status = check_api_status()
    
    if api_status["openweather_configured"]:
        st.sidebar.success(f"🌐 Live: {city}")
        live_data = get_realtime_data(city)
        # Show live environmental data in sidebar
        st.sidebar.metric("🌡️ Temperature", f"{live_data['combined']['temperature']}°C")
        st.sidebar.metric("🌫️ AQI", live_data['combined']['pollution'])
    else:
        st.sidebar.warning("⚠️ API key not configured")

# Generate simulated data if no other source
if df_with_surge is None:
    with st.spinner("Loading hospital data..."):
        if view_mode == "Single Hospital":
            df = generate_data(num_days=num_days, start_date=str(start_date), hospital_id=selected_hospital if view_mode == "Single Hospital" else "H001")
            
            # Inject live environmental data if available
            if data_source == "Live API Data":
                try:
                    from real_data_api import get_realtime_data
                    live = get_realtime_data(city)
                    df['temperature'] = live['combined']['temperature']
                    df['pollution'] = live['combined']['pollution']
                    df['humidity'] = live['combined']['humidity']
                except:
                    pass
            
            df_with_surge = predict_surge(df)
        else:
            hospital_data = generate_multi_hospital_data(num_days=num_days, start_date=str(start_date))
            for h_id in hospital_data:
                hospital_data[h_id] = predict_surge(hospital_data[h_id])
            df_with_surge = hospital_data['H001']

# Generate predictions
try:
    predictions = predict_ml(df_with_surge, days=predict_days)
except Exception as e:
    predictions = None

# Display alerts
show_alerts(df_with_surge)
st.markdown("---")

# Main tabs - now with 9 tabs including Agentic AI
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "📊 Summary",
    "📈 Trends", 
    "🔮 Predictions",
    "🎯 Scenarios",
    "🏥 Compare",
    "🌐 Live Data",
    "🤖 AI Agent",
    "📤 Upload",
    "📥 Export"
])

# Tab 1: Summary
with tab1:
    st.header("Current Status Overview")
    
    # Show data source badge
    if data_source == "Live API Data":
        st.markdown(f'<span class="live-badge">🔴 LIVE - {city}</span>', unsafe_allow_html=True)
    
    show_metrics(df_with_surge)
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        plot_capacity_gauges(df_with_surge)
        st.markdown("---")
        show_resource_metrics(df_with_surge)
    
    with col2:
        breakdown = get_risk_breakdown(df_with_surge)
        st.subheader(f"Risk Level: {breakdown['risk_level']}")
        st.metric("Risk Score", f"{breakdown['overall_score']}/6")
        plot_risk_breakdown(breakdown)

# Tab 2: Trends
with tab2:
    st.header("Historical Trends")
    plot_time_series(df_with_surge)
    st.markdown("---")
    plot_surge_risk(df_with_surge)
    
    with st.expander("📋 View Raw Data"):
        st.dataframe(df_with_surge, use_container_width=True)

# Tab 3: Predictions
with tab3:
    st.header("Future Predictions")
    
    if predictions is not None:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader(f"📊 {predict_days}-Day Bed Occupancy Forecast")
            combined = pd.DataFrame({
                'Historical': df_with_surge['occupied_beds'],
                'Predicted': predictions
            })
            st.line_chart(combined)
        
        with col2:
            st.subheader("Forecast Details")
            pred_df = pd.DataFrame({
                'Date': predictions.index.strftime('%Y-%m-%d'),
                'Predicted Beds': predictions.values.round(0).astype(int)
            })
            st.dataframe(pred_df, hide_index=True)
            
            avg_pred = predictions.mean()
            current = df_with_surge['occupied_beds'].iloc[-1]
            trend = "📈 Increasing" if avg_pred > current else "📉 Decreasing"
            
            st.info(f"""
            **Trend:** {trend}  
            **Current:** {int(current)} beds  
            **Avg Predicted:** {int(avg_pred)} beds  
            **Peak Predicted:** {int(predictions.max())} beds
            """)
            
            total_beds = df_with_surge['total_beds'].iloc[0]
            if (predictions > total_beds * 0.85).any():
                st.warning("⚠️ Capacity may exceed 85% during forecast period!")
    else:
        st.error("Unable to generate predictions.")
    
    st.markdown("---")
    show_advisory(df_with_surge)

# Tab 4: What-If Scenarios
with tab4:
    st.header("🎯 What-If Scenario Simulator")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        scenario_type = st.selectbox(
            "Select Scenario",
            options=list(SCENARIO_DESCRIPTIONS.keys()),
            format_func=lambda x: SCENARIO_DESCRIPTIONS[x]['name']
        )
        
        intensity = st.slider("Scenario Intensity", 0.5, 2.0, 1.0, 0.1)
        
        scenario_info = SCENARIO_DESCRIPTIONS[scenario_type]
        st.info(f"**{scenario_info['name']}**\n\n{scenario_info['description']}")
    
    with col2:
        if st.button("🚀 Run Scenario", type="primary"):
            with st.spinner("Simulating..."):
                df_scenario = apply_scenario(df_with_surge, scenario_type, intensity)
                impact = compare_scenarios(df_with_surge, df_scenario)
                plot_scenario_comparison(df_with_surge, df_scenario, scenario_info['name'])
                
                col_a, col_b, col_c = st.columns(3)
                col_a.metric("Avg Bed Change", f"{impact['bed_occupancy_change']:+.1f}")
                col_b.metric("Avg ICU Change", f"{impact['icu_occupancy_change']:+.1f}")
                col_c.metric("Days Over 90%", impact['days_over_capacity'])

# Tab 5: Multi-Hospital Comparison
with tab5:
    st.header("🏥 Multi-Hospital Comparison")
    
    if view_mode == "Multi-Hospital Comparison" and hospital_data:
        plot_multi_hospital_comparison(hospital_data)
        
        st.markdown("---")
        comparison_trends = pd.DataFrame()
        for h_id, h_df in hospital_data.items():
            h_name = h_df['hospital_name'].iloc[0]
            comparison_trends[h_name] = h_df['occupied_beds']
        st.line_chart(comparison_trends)
        
        st.subheader("⚠️ Risk Level Comparison")
        risk_data = []
        for h_id, h_df in hospital_data.items():
            latest = h_df.iloc[-1]
            risk_data.append({
                'Hospital': latest['hospital_name'],
                'Risk Score': int(latest['risk_score']),
                'Risk Level': str(latest['risk_level']),
                'Surge Days': int((h_df['risk_score'] >= 2).sum())
            })
        st.dataframe(pd.DataFrame(risk_data), hide_index=True)
    else:
        st.info("Switch to 'Multi-Hospital Comparison' mode in the sidebar.")

# Tab 6: Live Data
with tab6:
    st.header("🌐 Real-Time Environmental Data")
    
    from real_data_api import get_realtime_data, check_api_status
    
    api_status = check_api_status()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("API Status")
        if api_status["openweather_configured"]:
            st.success(f"✅ OpenWeatherMap: Connected")
            st.caption(f"Key: {api_status['api_key_preview']}")
        else:
            st.warning("⚠️ OpenWeatherMap: Not configured")
            st.caption("Add OPENWEATHER_API_KEY to .env file")
    
    with col2:
        selected_city = st.selectbox(
            "Select City for Live Data",
            ["Delhi", "Mumbai", "Bangalore", "Chennai", "Kolkata", "Hyderabad"],
            key="live_city"
        )
    
    if st.button("🔄 Fetch Live Data", type="primary"):
        with st.spinner(f"Fetching data for {selected_city}..."):
            live_data = get_realtime_data(selected_city)
            
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🌡️ Weather Data")
                weather = live_data['weather']
                st.metric("Temperature", f"{weather['temperature']}°C")
                st.metric("Humidity", f"{weather['humidity']}%")
                st.metric("Pressure", f"{weather['pressure']} hPa")
                st.caption(f"Source: {weather['source']}")
            
            with col2:
                st.subheader("🌫️ Air Quality")
                aqi = live_data['air_quality']
                
                aqi_color = "🟢" if aqi['aqi'] < 50 else "🟡" if aqi['aqi'] < 100 else "🟠" if aqi['aqi'] < 150 else "🔴"
                st.metric(f"{aqi_color} AQI", aqi['aqi'])
                st.metric("PM2.5", f"{aqi['pm25']} µg/m³")
                st.metric("PM10", f"{aqi['pm10']} µg/m³")
                st.caption(f"Source: {aqi['source']}")
            
            st.success(f"✅ Data fetched at {live_data['combined']['timestamp']}")

# Tab 7: Agentic AI
with tab7:
    st.header("🤖 Autonomous AI Agent")
    st.markdown("*Intelligent agent that monitors, reasons, and takes action*")
    
    from ai_agent import HospitAIAgent, get_agent_log, AlertLevel
    
    # Initialize agent in session state
    if 'ai_agent' not in st.session_state:
        st.session_state.ai_agent = HospitAIAgent(
            hospital_name=df_with_surge['hospital_name'].iloc[0] if 'hospital_name' in df_with_surge.columns else "City General Hospital"
        )
    
    agent = st.session_state.ai_agent
    
    # Agent controls
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        autonomous_mode = st.toggle("🔄 Autonomous Mode", value=agent.autonomous_mode,
                                    help="When enabled, agent can auto-execute low-risk actions")
        agent.autonomous_mode = autonomous_mode
    
    with col2:
        if st.button("🧠 Run Agent Cycle", type="primary"):
            with st.spinner("Agent thinking..."):
                st.session_state.agent_results = agent.run_cycle(df_with_surge)
    
    with col3:
        if autonomous_mode:
            st.info("🤖 Agent will auto-execute alerts and low-risk actions")
        else:
            st.info("👤 All actions require manual approval")
    
    st.markdown("---")
    
    # Display agent results
    if 'agent_results' in st.session_state:
        results = st.session_state.agent_results
        
        # Situation Overview
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📊 Current Situation Assessment")
            situation = results['situation']
            metrics = situation['metrics']
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Bed Occupancy", f"{metrics['bed_occupancy']}%", 
                     delta=f"{situation['trends']['bed_change_3d']:+d} (3d)")
            m2.metric("ICU Occupancy", f"{metrics['icu_occupancy']}%")
            m3.metric("Ventilator Usage", f"{metrics['ventilator_usage']}%")
            m4.metric("Staff Ratio", f"{metrics['staff_ratio']:.2f}")
            
            # Trend indicator
            trend = situation['trends']
            if trend['direction'] == 'increasing':
                st.warning(f"📈 Trend: {trend['direction'].title()} ({trend['velocity']})")
            elif trend['direction'] == 'decreasing':
                st.success(f"📉 Trend: {trend['direction'].title()} ({trend['velocity']})")
            else:
                st.info(f"➡️ Trend: Stable")
        
        with col2:
            st.subheader("⚠️ Issues Detected")
            issues = results['issues']
            if issues:
                for issue in issues:
                    severity = issue['severity']
                    if severity == AlertLevel.EMERGENCY:
                        st.error(f"🚨 {issue['message']}")
                    elif severity == AlertLevel.CRITICAL:
                        st.error(f"🔴 {issue['message']}")
                    elif severity == AlertLevel.WARNING:
                        st.warning(f"🟡 {issue['message']}")
                    else:
                        st.info(f"🔵 {issue['message']}")
            else:
                st.success("✅ No critical issues detected")
        
        st.markdown("---")
        
        # Actions Section
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("⚡ Actions Taken")
            actions = results['actions']
            if actions['executed']:
                for action in actions['executed']:
                    st.success(f"✅ {action.description}")
                    with st.expander("Details"):
                        st.json(action.details)
            else:
                st.info("No actions auto-executed")
        
        with col2:
            st.subheader("⏳ Pending Approval")
            pending = agent.get_pending_actions_summary()
            if pending:
                for i, action in enumerate(pending):
                    with st.container():
                        st.markdown(f"**{action['action']}**")
                        st.caption(f"Type: {action['type']} | Priority: {'⭐' * action['priority']}")
                        c1, c2 = st.columns(2)
                        if c1.button("✅ Approve", key=f"approve_{i}"):
                            agent.approve_action(i)
                            st.rerun()
                        if c2.button("❌ Reject", key=f"reject_{i}"):
                            agent.reject_action(i)
                            st.rerun()
            else:
                st.info("No actions pending")
        
        st.markdown("---")
        
        # Reasoning Trace
        with st.expander("🧠 Agent Reasoning Trace", expanded=False):
            st.markdown(agent.get_reasoning_trace())
        
        # AI Analysis
        st.subheader("🤖 AI Analysis & Recommendations")
        if st.button("Generate AI Analysis"):
            with st.spinner("AI analyzing situation..."):
                analysis = agent.get_ai_analysis(df_with_surge)
                st.markdown(analysis)
    
    else:
        st.info("👆 Click 'Run Agent Cycle' to start the AI agent analysis")
        
        # Show agent capabilities
        st.markdown("""
        ### Agent Capabilities
        
        The HospitAI Agent uses a **ReAct** (Reasoning + Acting) architecture:
        
        1. **🔍 PERCEIVE** - Gathers current hospital metrics and environmental data
        2. **🧠 REASON** - Analyzes patterns, identifies issues, assesses risks
        3. **📋 PLAN** - Generates prioritized action recommendations
        4. **⚡ EXECUTE** - Takes autonomous actions or queues for approval
        5. **📚 LEARN** - Tracks outcomes to improve future decisions
        
        **Monitored Thresholds:**
        - Bed Occupancy: Warning at 75%, Critical at 90%
        - ICU Occupancy: Warning at 70%, Critical at 85%
        - Ventilator Usage: Warning at 60%, Critical at 80%
        - Staff Ratio: Minimum 0.15 staff per patient
        - Air Quality: Warning at AQI 100, Critical at 150
        """)
    
    # Agent Log
    st.markdown("---")
    with st.expander("📜 Agent Action Log"):
        log = get_agent_log()
        if log:
            log_df = pd.DataFrame(log)
            st.dataframe(log_df, use_container_width=True)
        else:
            st.info("No actions logged yet")

# Tab 8: Upload Data
with tab8:
    from data_upload import render_upload_tab
    render_upload_tab()

# Tab 9: Export
with tab9:
    from export_utils import render_export_tab
    render_export_tab(df_with_surge, predictions)

# Footer
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.caption(f"📅 {start_date} to {end_date}")
with col2:
    st.caption(f"📊 Source: {data_source}")
with col3:
    st.caption(f"🔄 {datetime.now().strftime('%H:%M:%S')}")
with col4:
    st.caption("🏥 HospitAI v3.0")
