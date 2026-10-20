import streamlit as st
import pandas as pd
# Import your calculations cleanly from call.py
from call import get_covered_call_recommendation

# Configure page visual width
st.set_page_config(page_title="Covered Call Engine", layout="wide")
st.title("📈 Covered Call Strategy Assistant")
st.write("Find Out-of-the-Money calls carrying an approximate user-defined chance of expiring In-The-Money (Delta) in your selected timeframe.")

# User entry layout - Defaults to NVDA
ticker = st.text_input("Enter Asset Ticker Symbol", value="NVDA").upper().strip()

# User Input Controls (Grid Layout)
col_input1, col_input2 = st.columns(2)
with col_input1:
    target_prob = st.slider("Target ITM Probability / Delta (%)", min_value=5, max_value=95, value=30, step=1, help="Probability that the option will expire in-the-money.")
with col_input2:
    target_weeks = st.number_input("Target Expiry Timeline (Weeks)", min_value=1, max_value=52, value=4, step=1, help="If the specified number of weeks does not have an exact expiration date, the closest available date is chosen automatically.")

# Add manual button trigger alongside the automatic state change conditions
button_clicked = st.button("Generate Strategy Recommendation")

# DUAL TRIGGER LOOP: Triggers if the button is explicitly pressed OR if any parameter values shift
if ticker:
    with st.spinner(f"Analyzing option matrix structures for {ticker}..."):
        # Pass parameters straight to backend calculation engine
        rec, status_msg, chain_df = get_covered_call_recommendation(ticker, target_prob=target_prob, target_weeks=target_weeks)
        
    if rec is None:
        st.error(f"Strategy Scan Failed: {status_msg}")
    else:
        # 1. Render Top Level Metric Dashboard Cards
        st.markdown("### 📊 Market Layout Overview")
        # 🌟 CHANGED: Expanded to 5 column slots to perfectly incorporate Premium metric
        m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
        
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
        with m_col5:
            # 🌟 NEW KPI: Upfront gross cash revenue generated per contract position 
            st.metric(label="Est. Premium Income", value=f"${rec['total_premium']:.2f}", help="Calculated as Option Bid Price * 100 shares per standard option contract position.")
            
        # 2. Highlighted Recommendation Breakdown Box
        st.markdown("---")
        st.subheader("🎯 Strategy Recommendation Summary")
        
        st.success(f"""
        **Covered Call Action Strategy Plan for {ticker}:**
        * Buy or hold 100 shares of underlying stock **{ticker}** at **${rec['spot_price']:.2f}**.
        * Sell the **{rec['expiry']}** expiration **${rec['strike']:.2f} Call Option**.
        * **Current Market Premium:** Bid: **${rec['bid']:.2f}** | Ask: **${rec['ask']:.2f}**
        * 💰 **Upfront Cash Collected:** You will make **${rec['total_premium']:.2f}** instantly in premium cash income per contract position.
        * **Mathematical Delta Verification:** **{rec['calculated_delta']:.3f}** *(Targeted probability setup: {rec['target_prob']:.1f}%)*.
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
else:
    st.error("Please enter a valid stock ticker symbol.")
