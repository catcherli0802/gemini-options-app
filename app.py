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

# 🌟 CHANGED: Reconfigured input rows to fit 3 side-by-side controls
col_input1, col_input2, col_input3 = st.columns(3)
with col_input1:
    target_prob = st.slider("Target ITM Probability / Delta (%)", min_value=5, max_value=95, value=30, step=1, help="Probability that the option will expire in-the-money.")
with col_input2:
    target_weeks = st.number_input("Target Expiry Timeline (Weeks)", min_value=1, max_value=52, value=4, step=1, help="If the specified number of weeks does not have an exact expiration date, the closest available date is chosen automatically.")
with col_input3:
    # 🌟 NEW USER CONTROL: Input for sizing standard contract entries
    num_contracts = st.number_input("Number of Contracts to Sell", min_value=1, max_value=1000, value=1, step=1, help="Scales your total premium metrics. 1 contract = 100 shares.")

# Add manual button trigger alongside the automatic state change conditions
button_clicked = st.button("Generate Strategy Recommendation")

# DUAL TRIGGER LOOP: Triggers if the button is explicitly pressed OR if any parameter values shift
if ticker:
    with st.spinner(f"Analyzing option matrix structures for {ticker}..."):
        # Pass the number of contracts forward to the calculation pipeline
        rec, status_msg, chain_df = get_covered_call_recommendation(ticker, target_prob=target_prob, target_weeks=target_weeks, num_contracts=num_contracts)
        
    if rec is None:
        st.error(f"Strategy Scan Failed: {status_msg}")
    else:
        # 1. Render Top Level Metric Dashboard Cards
        st.markdown("### 📊 Market Layout Overview")
        m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
        
        with m_col1:
            st.metric(label=f"Current {ticker} Spot Price", value=f"${rec['spot_price']:.2f}")
        with m_col2:
            st.metric(label="Target Expiry Date", value=rec['expiry'], delta=f"{rec['dte']} Days Away")
        with m_col3:
            st.metric(label="Recommended Strike Price", value=f"${rec['strike']:.2f}")
        with m_col4:
            iv_percentage = rec['impliedVolatility'] * 100
            st.metric(label="Target Implied Volatility (IV)", value=f"{iv_percentage:.1f}%")
        with m_col5:
            # 🌟 SCALED KPI CARD: Updates cash calculation based on your contracts sizing input
            st.metric(label="Est. Premium Income", value=f"${rec['total_premium']:.2f}", help="Calculated as (Option Bid Price * 100) * Number of Contracts.")
            
        # 2. Highlighted Recommendation Breakdown Box
        st.markdown("---")
        st.subheader("🎯 Strategy Recommendation Summary")
        
        # Calculate shares required for transparency brief
        required_shares = rec['num_contracts'] * 100
        
        st.success(f"""
        **Covered Call Action Strategy Plan for {ticker}:**
        * Buy or hold **{required_shares:,}** shares of underlying stock **{ticker}** at **${rec['spot_price']:.2f}** (covers your position).
        * Sell **{rec['num_contracts']}** of the **{rec['expiry']}** expiration **${rec['strike']:.2f} Call Option** contracts.
        * **Current Market Premium:** Bid: **${rec['bid']:.2f}** | Ask: **${rec['ask']:.2f}**
        * 💰 **Upfront Cash Collected:** You will make **${rec['total_premium']:.2f}** instantly in premium cash income from this block position.
        * **Mathematical Delta Verification:** **{rec['calculated_delta']:.3f}** *(Targeted probability setup: {rec['target_prob']:.1f}%)*.
        """)
        
        # 3. Comprehensive Data Context Grid Table
        st.markdown("### 🔍 Scanned Options Chain Context Table")
        st.write("This table shows the available options contracts surrounding your recommendation target, sorted by strike price.")
        
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
            st.dataframe(chain_df.style.format(format_dict), use_container_width=True)
else:
    st.error("Please enter a valid stock ticker symbol.")
