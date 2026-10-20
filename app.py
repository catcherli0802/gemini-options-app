import streamlit as st
import pandas as pd
# Import your calculations cleanly from call.py
from call import get_covered_call_recommendation

# Configure page visual width
st.set_page_config(page_title="Covered Call Engine", layout="wide")
st.title("📈 Covered Call Strategy Assistant")
st.write("Find Out-of-the-Money calls carrying an approximate **30% chance** of expiring In-The-Money (~0.30 Delta) in roughly 4 weeks.")

# User entry layout
ticker = st.text_input("Enter Asset Ticker Symbol", value="AAPL").upper().strip()

if st.button("Generate Strategy Recommendation"):
    if not ticker:
        st.error("Please enter a valid stock ticker symbol.")
    else:
        with st.spinner(f"Analyzing option matrix structures for {ticker}..."):
            rec, status_msg, chain_df = get_covered_call_recommendation(ticker)
            
        if rec is None:
            st.error(f"Strategy Scan Failed: {status_msg}")
        else:
            # 1. Render Top Level Metric Dashboard Cards
            st.markdown("### 📊 Market Layout Overview")
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            
            with m_col1:
                st.metric(label=f"Current {ticker} Spot Price", value=f"${rec['spot_price']:.2f}")
            with m_col2:
                st.metric(label="Target Expiry Date", value=rec['expiry'], delta=f"{rec['dte']} Days Away")
            with m_col3:
                st.metric(label="Recommended Strike Price", value=f"${rec['strike']:.2f}")
            with m_col4:
                # Format IV into a human-readable percentage scale
                iv_percentage = rec['impliedVolatility'] * 100
                st.metric(label="Target Implied Volatility (IV)", value=f"{iv_percentage:.1f}%")
                
            # 2. Highlighted Recommendation Breakdown Box
            st.markdown("---")
            st.subheader("🎯 Strategy Recommendation Summary")
            
            st.success(f"""
            **Covered Call Action Strategy Plan for {ticker}:**
            * Buy or hold 100 shares of underlying stock **{ticker}** at **${rec['spot_price']:.2f}**.
            * Sell the **{rec['expiry']}** expiration **${rec['strike']:.2f} Call Option**.
            * **Current Market Premium:** Bid: **${rec['bid']:.2f}** | Ask: **${rec['ask']:.2f}**
            * **Mathematical Delta Verification:** **{rec['calculated_delta']:.3f}** *(Extremely close to your target 0.300 layout probability)*.
            """)
            
            # 3. Comprehensive Data Context Grid Table
            st.markdown("### 🔍 Scanned Options Chain Context Table")
            st.write("This table shows the available options contracts surrounding your recommendation target, sorted by strike price.")
            
            # Format dataframe columns cleanly for user interface viewing
            if not chain_df.empty:
                format_dict = {
                    'strike': '${:.2f}',
                    'bid': '${:.2f}',
                    'ask': '${:.2f}',
                    'volume': '{:,.0f}',
                    'openInterest': '{:,.0f}',
                    'impliedVolatility': '{:.2%}',
                    'Estimated Delta': '{:.3f}'
                }
                
                # Apply format properties to dataframe display render
                st.dataframe(chain_df.style.format(format_dict), use_container_width=True)
