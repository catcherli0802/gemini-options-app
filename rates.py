import yfinance as yf

def get_current_risk_free_rate(target_weeks=4, fallback_rate=0.045):
    """
    Selects a Treasury yield ticker based on the chosen options timeline 
    to properly reflect the term structure of interest rates (Yield Curve).
    """
    # Select index ticker matching the appropriate duration bucket
    if target_weeks <= 6:
        ticker = "^IRX"    # 13-Week / 3-Month T-Bill Index
    elif target_weeks <= 30:
        ticker = "^IRX"    # Fallback/standard loop; or use a 6-month tracking metric if available
    else:
        ticker = "^FVX"    # 5-Year Treasury Note Index (for long leaps positions)

    try:
        irx = yf.Ticker(ticker)
        raw_yield = irx.fast_info.get('lastPrice')
        
        if raw_yield is None or raw_yield <= 0:
            hist = irx.history(period="1d")
            if not hist.empty:
                raw_yield = hist['Close'].iloc[-1]
                
        if raw_yield and raw_yield > 0:
            # Most CBOE index values return as a percentage (e.g. 4.07). Convert to 0.0407
            return float(raw_yield / 100.0)
            
    except Exception:
        pass
        
    return fallback_rate
