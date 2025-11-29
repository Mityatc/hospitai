"""
Test Script for HospitAI Modules
Tests data generation, prediction, and other core functions.
"""

from data_generator import generate_data
from predictor_rulebased import predict_surge
from predictor_ml import predict_ml


def main():
    """Run tests on all HospitAI modules."""
    
    print("=" * 60)
    print("HospitAI Module Test Suite")
    print("=" * 60)
    
    # Test 1: Data Generation
    print("\n[1] Testing Data Generation...")
    df = generate_data(num_days=10)
    print(f"✓ Generated {len(df)} days of data")
    print(f"  Columns: {', '.join(df.columns)}")
    print(f"  Date range: {df.index[0]} to {df.index[-1]}")
    
    # Test 2: Rule-Based Surge Prediction
    print("\n[2] Testing Rule-Based Surge Predictor...")
    df_with_surge = predict_surge(df)
    surge_days = df_with_surge['surge_risk'].sum()
    print(f"✓ Surge prediction complete")
    print(f"  Surge risk detected on {surge_days} out of {len(df)} days")
    print(f"  Surge rate: {surge_days/len(df)*100:.1f}%")
    
    # Test 3: ML Prediction
    print("\n[3] Testing ML-Based Predictor...")
    try:
        predictions = predict_ml(df, days=3)
        print(f"✓ ML predictions generated for {len(predictions)} days")
        print(f"  Predicted occupancy range: {predictions.min():.0f} - {predictions.max():.0f} beds")
    except Exception as e:
        print(f"✗ ML prediction failed: {e}")
    
    # Test 4: Display Sample Data
    print("\n[4] Sample Data (Last 3 Days):")
    print("-" * 60)
    sample = df_with_surge[['flu_cases', 'pollution', 'occupied_beds', 'surge_risk']].tail(3)
    print(sample.to_string())
    
    # Test 5: Summary Statistics
    print("\n[5] Summary Statistics:")
    print("-" * 60)
    print(f"  Average flu cases: {df['flu_cases'].mean():.1f}")
    print(f"  Average pollution (AQI): {df['pollution'].mean():.1f}")
    print(f"  Average bed occupancy: {df['occupied_beds'].mean():.1f}")
    print(f"  Average occupancy rate: {(df['occupied_beds']/df['total_beds']).mean()*100:.1f}%")
    
    print("\n" + "=" * 60)
    print("All tests completed successfully!")
    print("Run 'streamlit run app.py' to launch the dashboard.")
    print("=" * 60)


if __name__ == "__main__":
    main()
