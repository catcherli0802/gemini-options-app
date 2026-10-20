import yfinance as yf
import pandas as pd
from google import genai

def get_option_chain_data(ticker):
    """Fetches stock spot price and clean option tables using yfinance with safety fallbacks."""
    stock = yf.Ticker(ticker)
    
    # Safely extract the current spot price
    try:
        spot_price = stock.fast_info.get('lastPrice', 0.0)
    except Exception:
        try:
            # Secondary fallback for stock price
            spot_price = stock.history(period="1d")['Close'].iloc[-1]
        except Exception:
            spot_price = 0.0
        
    # Check if options are returned by the scraper
    if not hasattr(stock, 'options') or not stock.options:
        return pd.DataFrame(), pd.DataFrame(), spot_price
        
    try:
        # Pick the absolute nearest available expiration date string safely
        available_expiries = list(stock.options)
        if len(available_expiries) == 0:
            return pd.DataFrame(), pd.DataFrame(), spot_price
            
        nearest_expiry = available_expiries[0]
        chain = stock.option_chain(nearest_expiry)
        
        # Filter for the most critical metrics
        cols = ['strike', 'bid', 'ask', 'volume', 'openInterest', 'impliedVolatility']
        
        # Process Calls safely
        calls = chain.calls[cols].dropna().head(10) if not chain.calls.empty else pd.DataFrame()
        # Process Puts safely
        puts = chain.puts[cols].dropna().head(10) if not chain.puts.empty else pd.DataFrame()
        
        return calls, puts, spot_price
        
    except Exception as e:
        # Prevent the whole web app from crashing on a scraper KeyError/ValueError
        print(f"Data scraping handling error: {str(e)}")
        return pd.DataFrame(), pd.DataFrame(), spot_price

def analyze_with_gemini(ticker, spot_price, calls_df, puts_df, api_key):
    """Packages data into a strict financial prompt and executes a Gemini query."""
    # Initialize the modern official Google GenAI client
    client = genai.Client(api_key=api_key)
    
    # Provide context if data tables are currently empty due to scrape failure
    calls_str = calls_df.to_string() if not calls_df.empty else "No current Call data retrieved from source."
    puts_str = puts_df.to_string() if not puts_df.empty else "No current Put data retrieved from source."
    
    prompt = f"""
    You are a professional quantitative derivative analyst. Analyze this options market environment for {ticker}.
    Current Stock Spot Price: ${spot_price:.2f}
    
    Top Calls Matrix:
    {calls_str}
    
    Top Puts Matrix:
    {puts_str}
    
    Provide a professional summary:
    1. If data is present, evaluate key near-term support/resistance walls and implied volatility nodes.
    2. If the data blocks are empty, briefly explain to the user the risks of relying on unofficial web scrapers for real-time market pipelines and what alternatives exist.
    """
    
    # 🌟 Fixed: Updated to the live, supported gemini-3.8-flash model
    response = client.models.generate_content(
        model='gemini-3.8-flash',
        contents=prompt,
    )
    return response.text
