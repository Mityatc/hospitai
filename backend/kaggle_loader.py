"""
Kaggle Dataset Loader for HospitAI
Downloads and processes hospital datasets from Kaggle.
"""

import os
import pandas as pd
import streamlit as st


def load_kaggle_dataset():
    """
    Load the Hospitals in India dataset from Kaggle.
    
    Returns:
        pd.DataFrame or None
    """
    try:
        import kagglehub
        
        with st.spinner("Downloading dataset from Kaggle..."):
            path = kagglehub.dataset_download("fringewidth/hospitals-in-india")
        
        # Find CSV files in the downloaded path
        csv_files = []
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith('.csv'):
                    csv_files.append(os.path.join(root, file))
        
        if csv_files:
            st.success(f"✅ Found {len(csv_files)} data files")
            return path, csv_files
        else:
            st.warning("No CSV files found in dataset")
            return path, []
            
    except ImportError:
        st.error("kagglehub not installed. Run: pip install kagglehub")
        return None, []
    except Exception as e:
        st.error(f"Error loading dataset: {str(e)}")
        return None, []


def render_kaggle_tab():
    """Render Kaggle dataset loader interface."""
    st.header("📊 Load Kaggle Hospital Dataset")
    
    st.markdown("""
    Load real hospital data from Kaggle's **Hospitals in India** dataset.
    
    This dataset contains information about hospitals across India including:
    - Hospital locations and types
    - Bed capacity
    - Specializations
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔽 Download from Kaggle", type="primary"):
            path, files = load_kaggle_dataset()
            
            if files:
                st.session_state['kaggle_path'] = path
                st.session_state['kaggle_files'] = files
    
    # Show loaded files
    if 'kaggle_files' in st.session_state and st.session_state['kaggle_files']:
        st.subheader("📁 Available Files")
        
        selected_file = st.selectbox(
            "Select a file to load",
            st.session_state['kaggle_files'],
            format_func=lambda x: os.path.basename(x)
        )
        
        if st.button("📂 Load Selected File"):
            try:
                df = pd.read_csv(selected_file)
                st.session_state['kaggle_data'] = df
                
                st.success(f"✅ Loaded {len(df)} rows")
                st.subheader("Data Preview")
                st.dataframe(df.head(20), use_container_width=True)
                
                st.subheader("Columns")
                st.write(list(df.columns))
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    with col2:
        st.info("""
        **First time setup:**
        1. Install: `pip install kagglehub`
        2. You may need Kaggle credentials
        3. Click Download button
        """)


def get_kaggle_data():
    """Get loaded Kaggle data from session."""
    return st.session_state.get('kaggle_data', None)
