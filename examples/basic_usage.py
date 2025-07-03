# basic_usage.py - Simple example showing backward compatibility
"""
Basic example demonstrating streamlit-analytics2 usage
Shows that existing code works without any changes
"""

import streamlit as st
import streamlit_analytics2 as streamlit_analytics

# This is all you need - no setup code required!
with streamlit_analytics.track():
    st.title("📊 Streamlit Analytics2 Demo")
    
    st.markdown("""
    This demo shows the basic usage of streamlit-analytics2.
    
    - First run: You'll see a quick setup dialog
    - Subsequent runs: Works silently in the background
    - View analytics: Add `?analytics=on` to the URL
    """)
    
    # Create some widgets to track
    col1, col2 = st.columns(2)
    
    with col1:
        name = st.text_input("Enter your name", placeholder="John Doe")
        age = st.slider("Select your age", 0, 100, 25)
        color = st.color_picker("Pick a color", "#00f900")
    
    with col2:
        option = st.selectbox(
            "Choose your favorite",
            ["Python", "JavaScript", "Go", "Rust"]
        )
        
        agree = st.checkbox("I agree to the terms")
        
        if st.button("Submit", type="primary"):
            if name and agree:
                st.success(f"Thanks {name}! Your data has been recorded.")
                st.balloons()
            else:
                st.error("Please fill in your name and agree to the terms.")
    
    # Show some metrics
    st.divider()
    st.subheader("📈 Current Session Stats")
    
    # Access the analytics data (read-only)
    try:
        from streamlit_analytics2.state import data
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Pageviews", data.get('total_pageviews', 0))
        with col2:
            st.metric("Total Interactions", data.get('total_script_runs', 0))
        with col3:
            st.metric("Widgets Tracked", len(data.get('widgets', {})))
    except ImportError:
        st.info("Analytics data will appear here after interactions")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "View full analytics by adding `?analytics=on` to the URL | "
        "[Documentation](https://github.com/444B/streamlit-analytics2)"
    )