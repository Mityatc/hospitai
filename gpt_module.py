"""
AI Integration Module for HospitAI
Uses Google Gemini API for generating summaries and advisories.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Gemini API configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

# Try to import and configure Gemini
GEMINI_AVAILABLE = False
genai = None

try:
    import google.generativeai as genai
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        GEMINI_AVAILABLE = True
except ImportError:
    pass


def call_gemini(prompt: str) -> str:
    """Call Gemini API with a prompt."""
    if not GEMINI_AVAILABLE:
        return None
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"⚠️ Gemini Error: {str(e)}"


def generate_mock_summary(df):
    """Generate mock summary for demo/fallback."""
    latest = df.iloc[-1]
    occupancy = latest['occupied_beds'] / latest['total_beds'] * 100
    icu_occ = latest['occupied_icu'] / latest['total_icu_beds'] * 100
    
    if occupancy > 85:
        status, action = "critical", "Immediate capacity expansion recommended."
    elif occupancy > 70:
        status, action = "elevated", "Monitor closely and prepare contingency."
    else:
        status, action = "stable", "Continue standard operations."
    
    return f"""📊 **Executive Summary**

Hospital capacity is {status} at {occupancy:.1f}% occupancy, {icu_occ:.1f}% ICU.
Flu cases averaged {df['flu_cases'].mean():.0f}/day, AQI at {df['pollution'].mean():.0f}.
Peak occupancy: {df['occupied_beds'].max()} beds.

**Action:** {action}"""


def generate_summary(forecast_csv: str) -> str:
    """Generate summary using Gemini or fallback to mock."""
    if DEMO_MODE or not GEMINI_AVAILABLE:
        import pandas as pd
        import io
        df = pd.read_csv(io.StringIO(forecast_csv), index_col=0)
        return generate_mock_summary(df)
    
    prompt = f"""You are a hospital administrator AI. Analyze this hospital data and provide a brief 4-line executive summary with key insights and one recommendation:

{forecast_csv[:3000]}

Keep it concise and actionable."""
    
    result = call_gemini(prompt)
    return result if result else "⚠️ Unable to generate summary"


def generate_advisory(conditions: dict) -> str:
    """Generate health advisory using Gemini."""
    if DEMO_MODE or not GEMINI_AVAILABLE:
        advisories = []
        if conditions.get('pollution', 0) > 100:
            advisories.append("🌫️ Poor air quality. Limit outdoor activities.")
        if conditions.get('flu_cases', 0) > 50:
            advisories.append("🤒 Elevated flu activity. Practice hand hygiene.")
        if conditions.get('temperature', 20) > 30:
            advisories.append("🌡️ Heat alert. Stay hydrated.")
        if not advisories:
            advisories.append("✅ Conditions normal. Maintain regular health practices.")
        return "\n".join(advisories)
    
    prompt = f"""As a health advisor, provide 3 brief patient advisories based on:
- Temperature: {conditions.get('temperature')}°C
- Air Quality (AQI): {conditions.get('pollution')}
- Flu Cases: {conditions.get('flu_cases')}
- Hospital Occupancy: {conditions.get('occupancy')}%

Use emojis and keep each advisory to one sentence."""
    
    result = call_gemini(prompt)
    return result if result else "✅ General: Maintain healthy habits."


def generate_admin_report(df) -> str:
    """Generate comprehensive admin report using Gemini."""
    if DEMO_MODE or not GEMINI_AVAILABLE:
        return generate_mock_summary(df)
    
    latest = df.iloc[-1]
    risk_days = (df['risk_score'] >= 2).sum() if 'risk_score' in df.columns else 0
    
    stats = f"""Hospital Performance Data:
- Period: {df.index[0].strftime('%Y-%m-%d')} to {df.index[-1].strftime('%Y-%m-%d')} ({len(df)} days)
- Average Bed Occupancy: {df['occupied_beds'].mean():.1f}/{latest['total_beds']} ({df['occupied_beds'].mean()/latest['total_beds']*100:.1f}%)
- Average ICU Occupancy: {df['occupied_icu'].mean():.1f}/{latest['total_icu_beds']}
- Peak Occupancy: {df['occupied_beds'].max()} beds
- Average Flu Cases: {df['flu_cases'].mean():.1f}/day
- Average Air Quality: {df['pollution'].mean():.1f} AQI
- Days at High Risk: {risk_days}/{len(df)}
- Current Staff Ratio: {latest['staff_on_duty']/latest['occupied_beds']:.2f}
- Medication Stock: {latest['medication_stock']} units"""

    prompt = f"""As a hospital administrator AI, provide a professional executive summary (5-6 sentences) based on this data. Include:
1. Overall status assessment
2. Key concerns if any
3. Resource utilization insight
4. One specific recommendation

{stats}"""
    
    result = call_gemini(prompt)
    return result if result else generate_mock_summary(df)


def get_ai_mode():
    """Return current AI mode for display."""
    if DEMO_MODE:
        return "🎭 Demo Mode"
    elif GEMINI_AVAILABLE:
        return "🤖 Google Gemini"
    else:
        return "⚠️ AI Not Configured"


if __name__ == "__main__":
    print(f"AI Mode: {get_ai_mode()}")
    print(f"Gemini Available: {GEMINI_AVAILABLE}")
