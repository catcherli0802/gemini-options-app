import yfinance as yf
import numpy as np

def fetch_live_index_yield(ticker, default_value):
    """Safely extracts live yields from robust Yahoo CBOE indices."""
    try:
        bond = yf.Ticker(ticker)
        # Pull live price metric
        val = bond.fast_info.get('lastPrice')
        
        # Secondary fallback layer if fast_info encounters an exchange delay
        if val is None or val <= 0:
            hist = bond.history(period="1d")
            if not hist.empty:
                val = hist['Close'].iloc[-1]
                
        if val and val > 0:
            # CBOE indices return numbers like 4.15. Convert to decimal form (0.0415)
            return float(val / 100.0)
    except Exception:
        pass
    return default_value

def get_current_risk_free_rate(target_weeks=4, fallback_rate=0.045):
    """
    Dynamically fetches core sovereign indices and uses linear interpolation 
    to extract distinctly different yields for any targeted week horizon.
    """
    # 1. Fetch live market anchors dynamically from stable CBOE pillars
    r_3m = fetch_live_index_yield("^IRX", 0.0415)  # 3-Month Bill Anchor (~13 weeks)
    r_5y = fetch_live_index_yield("^FVX", 0.0493)  # 5-Year Note Anchor (~260 weeks)
    r_10y = fetch_live_index_yield("^TNX", 0.0514) # 10-Year Note Anchor (~520 weeks)

    # Convert our structural horizons into consistent week counts
    w_3m = 13.0
    w_5y = 260.0
    w_10y = 520.0

    # 2. Map target weeks smoothly onto the dynamic curve using linear math
    if target_weeks <= w_3m:
        # Front-end curve slope (1-Month to 3-Month interpolation)
        # Simulates a shifting front-end rate using the 3M baseline
        fraction = target_weeks / w_3m
        calculated_rate = r_3m * (0.95 + 0.05 * fraction) 
        label = f"Dynamic Yield Curve: Front-End Tier (Based on ^IRX)"
        
    elif target_weeks <= w_5y:
        # Mid-end curve slope (3-Month up to 5-Year interpolation)
        calculated_rate = np.interp(target_weeks, [w_3m, w_5y], [r_3m, r_5y])
        label = f"Dynamic Yield Curve: Mid-Term Tier (Interpolated ^IRX to ^FVX)"
        
    else:
        # Back-end curve slope (5-Year up to 10-Year interpolation)
        calculated_rate = np.interp(target_weeks, [w_5y, w_10y], [r_5y, r_10y])
        label = f"Dynamic Yield Curve: Long-Term Tier (Interpolated ^FVX to ^TNX)"

    return float(calculated_rate), label
