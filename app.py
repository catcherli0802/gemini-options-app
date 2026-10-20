import streamlit as st
from call import get_option_chain_data, analyze_with_gemini

st.set_page_config(page_title="Gemini Options Quant", layout="wide")
st.title("📊 Gemini Options Analysis Workbench")

st.sidebar.header("Configuration")
api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")

ticker = st.text_input("Enter Asset Ticker Symbol", value="AAPL").upper()

if st.button("Run Analytics Engine"):
    if not api_key:
        st.error("Please input your Gemini API Key in the left sidebar to proceed.")
    elif not ticker:
        st.error("Please enter a valid stock ticker symbol.")
    else:
        with st.spinner("Fetching market options matrix..."):
            calls, puts, spot = get_option_chain_data(ticker)

        if calls.empty and puts.empty:
            st.warning(f"Could not retrieve active option chains for ticker: {ticker}.")
        else:
            st.metric(label=f"Current {ticker} Spot Price", value=f"${spot:.2f}")

            tab1, tab2 = st.tabs(["🟢 Call Options (Nearest Expiry)", "🔴 Put Options (Nearest Expiry)"])
            with tab1:
                st.dataframe(calls, use_container_width=True)
            with tab2:
                st.dataframe(puts, use_container_width=True)

            st.markdown("---")
            st.subheader("🤖 Gemini Quant Market Assessment")
            with st.spinner("Generating AI structural market overview..."):
                try:
                    report = analyze_with_gemini(ticker, spot, calls, puts, api_key)
                    st.info(report)
                except Exception as e:
                    st.error(f"Gemini API Execution Error: {str(e)}")
