import yfinance as yf
import pandas as pd
from google import genai

def get_option_chain_data(ticker):
    stock = yf.Ticker(ticker)
    try:
        spot_price = stock.fast_info.get('lastPrice', 0.0)
    except:
        spot_price = 0.0

    if not stock.options:
        return pd.DataFrame(), pd.DataFrame(), spot_price

    nearest_expiry = stock.options[0]
    chain = stock.option_chain(nearest_expiry)

    cols = ['strike', 'bid', 'ask', 'volume', 'openInterest', 'impliedVolatility']
    calls = chain.calls[cols].dropna().head(10)
    puts = chain.puts[cols].dropna().head(10)

    return calls, puts, spot_price

def analyze_with_gemini(ticker, spot_price, calls_df, puts_df, api_key):
    client = genai.Client(api_key=api_key)

    prompt = f"""
    You are a professional quantitative derivative analyst. Analyze this options chain dataset for {ticker}.
    Current Stock Spot Price: ${spot_price:.2f}

    Top Calls Matrix:
    {calls_df.to_string()}

    Top Puts Matrix:
    {puts_df.to_string()}

    Provide a professional, concise summary assessing market structure:
    1. Identify key near-term support or resistance walls based on open interest/volume nodes.
    2. Note any notable implied volatility (IV) anomalies between out-of-the-money calls vs puts.
    """

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
    )
    return response.text
