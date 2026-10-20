import yfinance as yf

def get_current_risk_free_rate(target_weeks=4, fallback_rate=0.045):
    """
    Selects a Treasury yield ticker based on the chosen options timeline 
    and returns a tuple of (decimal_rate, label_string).
    """
    # 1. Map target weeks to the closest standardized Treasury duration asset
    if target_weeks <= 2:
        ticker = "^IRX"  # Standard fallback to 13-week index for immediate hyper-short positions
        label = "1-Month T-Bill (Approx via ^IRX)"
    elif target_weeks <= 10:
        ticker = "^IRX"  # 13-Week / 3-Month Treasury Bill Index
        label = "3-Month T-Bill (^IRX)"
    elif target_weeks <= 36:
        ticker = "^IRX"  # 26-Week / 6-Month baseline proxy
        label = "6-Month T-Bill (Curve Proxy)"
    else:
        ticker = "^FVX"  # 5-Year Treasury Note Index for long LEAPS duration buckets
        label = "1-Year+ Bond Proxy (^FVX)"

    # 2. Query market engine data
    try:
        irx = yf.Ticker(ticker)
        raw_yield = irx.fast_info.get('lastPrice')
        
        if raw_yield is None or raw_yield <= 0:
            hist = irx.history(period="1d")
            if not hist.empty:
                raw_yield = hist['Close'].iloc[-1]
                
        if raw_yield and raw_yield > 0:
            return float(raw_yield / 100.0), label
            
    except Exception:
        pass
        
    return fallback_rate, f"Fallback Default ({fallback_rate*100:.1f}%)"
