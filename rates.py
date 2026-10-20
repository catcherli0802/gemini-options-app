import yfinance as yf

def get_current_risk_free_rate(fallback_rate=0.045):
    """
    Fetches the live yield of the 13-Week Treasury Bill (^IRX) via yfinance.
    Converts percent values (e.g. 4.75) down into standard calculation decimals (0.0475).
    """
    try:
        irx = yf.Ticker("^IRX")
        
        # Pull current price using fast_info layer
        raw_yield = irx.fast_info.get('lastPrice')
        
        # Fallback loop to historical close dataframe if data layer is throttled
        if raw_yield is None or raw_yield <= 0:
            hist = irx.history(period="1d")
            if not hist.empty:
                raw_yield = hist['Close'].iloc[-1]
                
        if raw_yield and raw_yield > 0:
            return float(raw_yield / 100.0)
            
    except Exception:
        pass # Silently drop into safety net configuration
        
    return fallback_rate
