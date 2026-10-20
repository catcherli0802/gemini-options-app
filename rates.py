import yfinance as yf

def get_current_risk_free_rate(target_weeks=4, fallback_rate=0.045):
    """
    Dynamically pulls the unique real-time market yield matching the exact 
    maturity length from the US sovereign treasury curve.
    """
    # 1. Route the target options timeline cleanly into the correct daily maturity bucket
    if target_weeks <= 2:
        ticker = "US1MT=X"   # 1-Month US Treasury Sovereign Yield
        label = "Live 1-Month Treasury Yield (US1MT=X)"
    elif target_weeks <= 8:
        ticker = "US3MT=X"   # 3-Month US Treasury Sovereign Yield
        label = "Live 3-Month Treasury Yield (US3MT=X)"
    elif target_weeks <= 18:
        ticker = "US6MT=X"   # 6-Month US Treasury Sovereign Yield
        label = "Live 6-Month Treasury Yield (US6MT=X)"
    elif target_weeks <= 36:
        ticker = "US1YT=X"   # 1-Year US Treasury Sovereign Yield
        label = "Live 1-Year Treasury Yield (US1YT=X)"
    elif target_weeks <= 78:
        ticker = "US2YT=X"   # 2-Year US Treasury Sovereign Yield
        label = "Live 2-Year Treasury Yield (US2YT=X)"
    elif target_weeks <= 200:
        ticker = "US5YT=X"   # 5-Year US Treasury Sovereign Yield
        label = "Live 5-Year Treasury Yield (US5YT=X)"
    else:
        ticker = "US10YT=X"  # 10-Year US Treasury Sovereign Yield
        label = "Live 10-Year Treasury Yield (US10YT=X)"

    # 2. Extract live market data using your exact pattern
    try:
        bond_asset = yf.Ticker(ticker)
        raw_yield = bond_asset.fast_info.get('lastPrice')
        
        # Secondary history fallback loop if fast_info encounters an empty response packet
        if raw_yield is None or raw_yield <= 0:
            hist = bond_asset.history(period="1d")
            if not hist.empty:
                raw_yield = hist['Close'].iloc[-1]
                
        if raw_yield and raw_yield > 0:
            # Note: These market quote streams return yields natively as a percentage (e.g., 4.51).
            # We divide by 100 to feed the proper math decimal (0.0451) into your Black-Scholes engine.
            return float(raw_yield / 100.0), label
            
    except Exception:
        pass # Gracefully transition to your network safety net profile if the API throttles
        
    return fallback_rate, f"Market Fallback Profile ({fallback_rate*100:.2f}%)"
