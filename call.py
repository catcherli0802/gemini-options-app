import yfinance as yf
import pandas as pd
import numpy as np
from scipy.stats import norm
from datetime import datetime, timedelta

# Import your live yield retrieval microservice
from rates import get_current_risk_free_rate

def find_target_expiry(stock, target_days=28):
    """Finds the market expiration date closest to the target days."""
    if not hasattr(stock, 'options') or not stock.options:
        return None, 0
        
    today = datetime.now()
    target_date = today + timedelta(days=target_days)
    
    expiries = []
    for opt_date in stock.options:
        try:
            dt = datetime.strptime(opt_date, "%Y-%m-%d")
            expiries.append((dt, opt_date))
        except ValueError:
            continue
            
    if not expiries:
        return None, 0
        
    # Extract the datetime object from the first index of the tuple (x[0])
    expiries.sort(key=lambda x: abs((x[0] - target_date).days))
    closest_dt, closest_str = expiries[0]
    
    dte = (closest_dt - today).days
    return closest_str, max(dte, 1)

def calculate_approx_delta(spot, strike, iv, dte, r):
    """Approximates the option Delta using standard Black-Scholes d1 logic with live rates."""
    if spot <= 0 or strike <= 0 or iv <= 0 or dte <= 0:
        return 0.0
    
    t = dte / 365.0  # Time in years
    
    d1 = (np.log(spot / strike) + (r + (iv ** 2) / 2.0) * t) / (iv * np.sqrt(t))
    delta = norm.cdf(d1)
    return float(delta)

def black_scholes_call_price(spot, strike, iv, dte, r):
    """Calculates the theoretical Black-Scholes price of a Call Option using live rates."""
    if spot <= 0 or strike <= 0 or iv <= 0:
        return 0.0
    if dte <= 0:
        return max(0.0, spot - strike) # Intrinsic value at expiration
        
    t = dte / 365.0
    
    d1 = (np.log(spot / strike) + (r + (iv ** 2) / 2.0) * t) / (iv * np.sqrt(t))
    d2 = d1 - iv * np.sqrt(t)
    
    call_price = spot * norm.cdf(d1) - strike * np.exp(-r * t) * norm.cdf(d2)
    return float(call_price)

def get_time_decay_curve(spot, strike, iv, max_dte):
    """Generates a data matrix tracking call price progression using the dynamic market rate."""
    today = datetime.now()
    r = get_current_risk_free_rate() # Fetch current rate once for graph compilation
    
    days_to_expiration = list(range(int(max_dte), -1, -1))
    calendar_dates = []
    prices = []
    
    for dte in days_to_expiration:
        days_passed = int(max_dte) - dte
        future_date = today + timedelta(days=days_passed)
        calendar_dates.append(future_date.strftime("%Y-%m-%d"))
        
        p = black_scholes_call_price(spot, strike, iv, dte, r)
        prices.append(p)
        
    df = pd.DataFrame({
        "Timeline Date": calendar_dates,
        "Theoretical Option Value": prices
    })
    return df.set_index("Timeline Date")

def get_covered_call_recommendation(ticker, target_prob=30.0, target_weeks=4, num_contracts=1):
    """Scans the chain and finds the strike closest to a user probability (Delta) target."""
    stock = yf.Ticker(ticker)
    target_delta = target_prob / 100.0
    target_days = target_weeks * 7
    
    # Extract live macro yield benchmark from our new module
    r = get_current_risk_free_rate()
    
    try:
        spot_price = stock.fast_info.get('lastPrice', 0.0)
    except Exception:
        try:
            spot_price = stock.history(period="1d")['Close'].iloc[-1]
        except Exception:
            return None, "Error retrieving spot price.", pd.DataFrame()
            
    if spot_price <= 0:
        return None, f"Invalid spot price retrieved for {ticker}.", pd.DataFrame()

    expiry_date, dte = find_target_expiry(stock, target_days=target_days)
    if not expiry_date:
        return None, "No valid options expiration dates found.", pd.DataFrame()
        
    try:
        chain = stock.option_chain(expiry_date)
        calls = chain.calls.copy()
        
        if calls.empty:
            return None, f"Option chain matrix empty for expiry {expiry_date}.", pd.DataFrame()
            
        cols = ['strike', 'bid', 'ask', 'volume', 'openInterest', 'impliedVolatility']
        calls = calls[cols].dropna()
        
        otm_calls = calls[calls['strike'] > spot_price].copy()
        if otm_calls.empty:
            otm_calls = calls.copy()
            
        deltas = []
        for _, row in otm_calls.iterrows():
            d = calculate_approx_delta(spot_price, row['strike'], row['impliedVolatility'], dte, r)
            deltas.append(d)
            
        otm_calls['calculated_delta'] = deltas
        
        otm_calls['delta_distance'] = (otm_calls['calculated_delta'] - target_delta).abs()
        best_match_idx = otm_calls['delta_distance'].idxmin()
        recommendation = otm_calls.loc[best_match_idx].to_dict()
        
        recommendation['total_premium'] = recommendation['bid'] * 100.0 * num_contracts
        recommendation['expiry'] = expiry_date
        recommendation['dte'] = dte
        recommendation['spot_price'] = spot_price
        recommendation['target_prob'] = target_prob
        recommendation['num_contracts'] = num_contracts
        recommendation['risk_free_rate'] = r  # <-- Passed to dictionary
        
        display_df = otm_calls.drop(columns=['delta_distance']).rename(
            columns={'calculated_delta': 'Estimated Delta'}
        ).head(15)
        
        return recommendation, "Success", display_df
        
    except Exception as e:
        return None, f"Calculation execution error: {str(e)}", pd.DataFrame()
