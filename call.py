import yfinance as yf
import pandas as pd
import numpy as np
from scipy.stats import norm
from datetime import datetime, timedelta

def find_target_expiry(stock, target_days=28):
    """Finds the market expiration date closest to the target days (4 weeks)."""
    if not hasattr(stock, 'options') or not stock.options:
        return None, 0
        
    today = datetime.now()
    target_date = today + timedelta(days=target_days)
    
    # Parse available dates and find the closest match
    expiries = []
    for opt_date in stock.options:
        try:
            dt = datetime.strptime(opt_date, "%Y-%m-%d")
            expiries.append((dt, opt_date))
        except ValueError:
            continue
            
    if not expiries:
        return None, 0
        
    # Sort by absolute distance to our target date
    expiries.sort(key=lambda x: abs((x[0] - target_date).days))
    closest_dt, closest_str = expiries[0]
    
    # Calculate exact Days to Expiration (DTE)
    dte = (closest_dt - today).days
    return closest_str, max(dte, 1) # Ensure DTE is at least 1 to avoid division by zero

def calculate_approx_delta(spot, strike, iv, dte):
    """Approximates the option Delta using standard Black-Scholes d1 logic."""
    if spot <= 0 or strike <= 0 or iv <= 0 or dte <= 0:
        return 0.0
    
    t = dte / 365.0  # Time in years
    # Standard risk-free rate approximation (e.g., 4.5% or 0.045)
    r = 0.045 
    
    # Black-Scholes d1 formula component
    d1 = (np.log(spot / strike) + (r + (iv ** 2) / 2.0) * t) / (iv * np.sqrt(t))
    delta = norm.cdf(d1)
    return float(delta)

def get_covered_call_recommendation(ticker):
    """Scans the 4-week chain and finds the strike closest to a 30% probability (0.30 Delta)."""
    stock = yf.Ticker(ticker)
    
    # 1. Safely extract current spot price
    try:
        spot_price = stock.fast_info.get('lastPrice', 0.0)
    except Exception:
        try:
            spot_price = stock.history(period="1d")['Close'].iloc[-1]
        except Exception:
            return None, "Error retrieving spot price.", pd.DataFrame()
            
    if spot_price <= 0:
        return None, f"Invalid spot price retrieved for {ticker}.", pd.DataFrame()

    # 2. Locate expiration closest to 4 weeks (28 days)
    expiry_date, dte = find_target_expiry(stock, target_days=28)
    if not expiry_date:
        return None, "No valid options expiration dates found.", pd.DataFrame()
        
    try:
        # 3. Pull the exact call data matrix
        chain = stock.option_chain(expiry_date)
        calls = chain.calls.copy()
        
        if calls.empty:
            return None, f"Option chain matrix empty for expiry {expiry_date}.", pd.DataFrame()
            
        # Clean data columns
        cols = ['strike', 'bid', 'ask', 'volume', 'openInterest', 'impliedVolatility']
        calls = calls[cols].dropna()
        
        # Filter for Out-Of-The-Money (OTM) options only
        otm_calls = calls[calls['strike'] > spot_price].copy()
        if otm_calls.empty:
            otm_calls = calls.copy() # Fallback to all calls if none are strictly OTM
            
        # 4. Calculate approximate Delta for every option in the matrix
        deltas = []
        for _, row in otm_calls.iterrows():
            d = calculate_approx_delta(spot_price, row['strike'], row['impliedVolatility'], dte)
            deltas.append(d)
            
        otm_calls['calculated_delta'] = deltas
        
        # 5. Locate the contract closest to a 30% probability target (0.30 Delta)
        otm_calls['delta_distance'] = (otm_calls['calculated_delta'] - 0.30).abs()
        best_match_idx = otm_calls['delta_distance'].idxmin()
        recommendation = otm_calls.loc[best_match_idx].to_dict()
        
        # Add metadata variables to recommendation dictionary
        recommendation['expiry'] = expiry_date
        recommendation['dte'] = dte
        recommendation['spot_price'] = spot_price
        
        # Clean dataframe up for presentation sorting
        display_df = otm_calls.drop(columns=['delta_distance']).rename(
            columns={'calculated_delta': 'Estimated Delta'}
        ).head(15)
        
        return recommendation, "Success", display_df
        
    except Exception as e:
        return None, f"Calculation execution error: {str(e)}", pd.DataFrame()
