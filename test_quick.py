"""Quick test to verify modules work"""
import sys

try:
    from data_generator import generate_data
    print("✓ data_generator imported")
    
    df = generate_data(5)
    print(f"✓ Generated {len(df)} days of data")
    print(df.head())
    
    from predictor_rulebased import predict_surge
    print("\n✓ predictor_rulebased imported")
    
    df_surge = predict_surge(df)
    print(f"✓ Surge prediction complete, surge days: {df_surge['surge_risk'].sum()}")
    
    print("\n✅ All core modules working!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
