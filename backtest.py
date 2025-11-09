#!/usr/bin/env python3
"""
Historical backtest for CAIE-style autocallable notes using real S&P 500 data.
Evaluates rolling 5-year windows across historical periods and applies note logic.
"""

import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from tqdm import tqdm
import datetime as dt

# Note Structure Parameters
T_years = 5                   # Maturity in years. Default: 5 years (CAIE typical maturity)
coupon_annual = 0.147         # Gross annual coupon rate. Default: 14.7% (CAIE current yield)
monthly_barrier = 0.60        # Coupon barrier as fraction of start. Default: 60% (coupon paid if index >= 60%)
autocall_trigger = 1.00      # Autocall trigger as fraction of start. Default: 100% (early call if index >= 100%)
fee_annual = 0.0074           # Annual expense ratio. Default: 0.74% (CAIE expense ratio)

# Data Parameters
start_symbol = '^GSPC'        # Index symbol. Default: S&P 500
start_date = '1928-01-01'     # Earliest date to fetch. Default: 1928 (start of S&P 500 data)
end_date = dt.date.today().isoformat()  # Latest date (today)

print("Downloading S&P500 history...")
df = yf.download(start_symbol, start=start_date, end=end_date, progress=False)
if df.empty:
    raise RuntimeError("Failed to download data. Run locally with internet access or provide CSV.")

# Handle MultiIndex columns from yfinance
if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.droplevel(1)

price_col = 'Adj Close' if 'Adj Close' in df.columns else 'Close'
prices = df[price_col].copy()
prices.name = 'price'
prices = prices.dropna()
prices = prices.asfreq('B', method='pad')  # Resample to business daily

# Generate rolling window start dates
min_date = prices.index[0]
max_date = prices.index[-1] - pd.DateOffset(years=T_years)
start_dates = prices.loc[:max_date].index

print(f"Total historical start dates to evaluate: {len(start_dates)}")


def evaluate_window(prices_series, start_ts, T_years,
                    monthly_barrier, autocall_trigger, coupon_annual, fee_annual):
    """
    Evaluate one historical window for note performance.
    
    Returns dict with: 'called', 'call_time_years', 'total_return', 
                       'principal_loss', 'missed_coupon_months', 'duration'
    """
    S0 = float(prices_series.loc[start_ts])
    end_ts = start_ts + pd.DateOffset(years=T_years)
    window = prices_series.loc[start_ts:end_ts]
    
    if window.index[-1] < end_ts:
        return None  # Incomplete window
    
    # Generate observation dates
    monthly_obs = pd.date_range(start=start_ts + pd.offsets.MonthEnd(0),
                                end=end_ts, freq='ME')
    annual_obs = [start_ts + pd.DateOffset(years=k) for k in range(1, T_years+1)]
    
    accrued_coupons = 0.0
    monthly_coupon = coupon_annual / 12.0
    called = False
    call_time_years = None
    missed_coupon_months = 0
    
    # Evaluate note over time
    for mo in monthly_obs:
        # Get price at month-end (use last available if market closed)
        if mo not in window.index:
            mo_price = window[:mo].iloc[-1]
        else:
            mo_price = window.loc[mo]
        
        # Monthly coupon check
        if mo_price >= monthly_barrier * S0:
            accrued_coupons += monthly_coupon
        else:
            missed_coupon_months += 1
        
        # Annual autocall check
        if mo in annual_obs:
            chkdate = mo
            pr = window[:chkdate].iloc[-1]
            if pr >= autocall_trigger * S0:
                called = True
                call_time_years = (chkdate - start_ts).days / 365.25
                break
    
    # Calculate final payoff
    if called:
        gross_total = 1.0 + accrued_coupons
        duration = call_time_years
    else:
        final_price = window.iloc[-1]
        if final_price >= monthly_barrier * S0:
            gross_total = 1.0 + accrued_coupons
        else:
            gross_total = (final_price / S0) + accrued_coupons
        duration = T_years
    
    # Apply fee drag
    net_total = gross_total * np.exp(-fee_annual * (duration if duration > 0 else T_years))
    total_return = net_total - 1.0
    
    return {
        'called': called,
        'call_time_years': call_time_years,
        'total_return': total_return,
        'principal_loss': (not called and window.iloc[-1] < monthly_barrier * S0),
        'missed_coupon_months': missed_coupon_months,
        'duration': duration
    }


# Evaluate all rolling windows
results = []
print("Evaluating rolling windows (this may take a few minutes)...")
for sd in tqdm(start_dates):
    res = evaluate_window(prices, sd, T_years, monthly_barrier,
                          autocall_trigger, coupon_annual, fee_annual)
    if res is not None:
        results.append((sd, res))

if len(results) == 0:
    raise RuntimeError("No complete windows found for given T_years.")

# Aggregate results
res_df = pd.DataFrame([{
    'start': r[0],
    'called': r[1]['called'],
    'total_return': r[1]['total_return'],
    'principal_loss': r[1]['principal_loss'],
    'missed_coupon_months': r[1]['missed_coupon_months'],
    'duration': r[1]['duration']
} for r in results])

# Print statistics
print(f"Number of windows evaluated: {len(res_df)}")
print("Principal loss (final < 60%) fraction:", res_df.principal_loss.mean())
print("Called early fraction:", res_df.called.mean())
print("Ever missed coupon (>=1 month missed) fraction:", (res_df.missed_coupon_months > 0).mean())
print()
print("Total return percentiles (net):")
for p in [1, 5, 10, 25, 50, 75, 90, 95, 99]:
    print(f"  {p}th pct: {np.percentile(res_df.total_return, p):+.2%}")

# Generate histogram
plt.figure(figsize=(10, 6))
plt.hist(res_df.total_return, bins=200, density=False)
plt.xlabel("Total return (net fraction of principal)")
plt.ylabel("Number of historical windows")
plt.title(f"Distribution of historical total returns for {T_years}-yr autocallable note (S&P500)")
plt.grid(alpha=0.2)
plt.axvline(np.percentile(res_df.total_return, 5), color='r', linestyle='--', label='5th pct')
plt.legend()
plt.tight_layout()
plt.savefig('historical_autocall_total_return_hist.png', dpi=150)
print("Histogram saved to historical_autocall_total_return_hist.png")

# Show worst 10 windows
worst = res_df.sort_values('total_return').head(10)
print("\nWorst 10 windows (start date and net total return):")
print(worst[['start', 'total_return', 'principal_loss', 'called', 'missed_coupon_months']].to_string(index=False))
