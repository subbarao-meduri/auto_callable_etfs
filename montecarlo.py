#!/usr/bin/env python3
"""
Monte Carlo simulation of a representative autocallable note like those in CAIE.
Assumptions described in the message. Change parameters below as needed.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# -----------------------------
# Parameters (change as desired)
S0 = 100.0            # starting index level (normalized)
mu = 0.07             # annual drift (expected return)
sigma = 0.18          # annual volatility
T = 5.0               # maturity in years (CAIE uses laddered notes; 5y assumed)
dt = 1/252.0          # daily steps (for path granularity)
coupon_annual = 0.147 # gross annual coupon (14.7%)
fee_annual = 0.0074   # expense ratio (0.74%)
monthly_barrier = 0.60   # coupon barrier (60% of start)
autocall_trigger = 1.00  # autocall trigger (100% of start) at annual observations
call_interval_years = 1  # autocall check every 1 year
n_sims = 200000       # number of Monte Carlo runs (increase for smoother tails)
seed = 42
np.random.seed(seed)

# Derived
steps = int(T / dt)
time_grid = np.linspace(0, T, steps + 1)
monthly_indices = set((np.round(np.arange(1, int(T*12)+1) * (1/12) / dt)).astype(int))  # monthly check indices
annual_indices = set((np.round(np.arange(1, int(T/call_interval_years)+1) * call_interval_years / dt)).astype(int))

monthly_coupon = coupon_annual / 12.0

# Arrays to collect results
total_returns = np.zeros(n_sims)   # total return (including coupons, principal, net of fee)
annualized_returns = np.zeros(n_sims)

for sim in range(n_sims):
    # simulate lognormal GBM daily path
    z = np.random.randn(steps)
    log_returns = (mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * z
    log_prices = np.concatenate([[0.0], np.cumsum(log_returns)])  # log S/S0
    prices = S0 * np.exp(log_prices)
    
    accrued_coupons = 0.0
    called = False
    call_time = None
    cashflow = 0.0
    
    # iterate through time steps and check monthly/annual events
    for idx in range(1, steps + 1):
        price = prices[idx]
        
        # monthly coupon observation
        if idx in monthly_indices:
            if price >= monthly_barrier * S0:
                accrued_coupons += monthly_coupon  # coupon for one month (fraction of principal)
        
        # annual autocall observation
        if idx in annual_indices:
            if price >= autocall_trigger * S0:
                # early call: pay principal + accrued coupons (pro-rated)
                called = True
                call_time = idx * dt
                break
    
    if called:
        # cashflow: principal (1.0 per unit) + accrued coupons until call_time
        gross_total = 1.0 + accrued_coupons
    else:
        final_price = prices[-1]
        # If final price >= monthly_barrier (60%), principal returned, else principal * (final/start)
        if final_price >= monthly_barrier * S0:
            gross_total = 1.0 + accrued_coupons
        else:
            # principal loss proportionate to index return
            gross_total = (final_price / S0) + accrued_coupons
    
    # model fees roughly: apply fee_annual continuously -> multiply by exp(-fee_annual * duration)
    # duration: call_time if called else T
    duration = call_time if called else T
    net_total = gross_total * np.exp(-fee_annual * duration)
    
    total_returns[sim] = net_total - 1.0  # net total return over principal (as fraction of principal)
    annualized_returns[sim] = ( (net_total) ** (1.0 / (duration if duration>0 else T)) ) - 1.0

# Summaries
df = pd.DataFrame({
    "total_return": total_returns,
    "annualized_return": annualized_returns
})

print("Simulations:", n_sims)
print("\n=== TOTAL RETURNS (over investment period) ===")
print("Mean total return (net): {:.2%}".format(df.total_return.mean()))
print("Median total return (net): {:.2%}".format(df.total_return.median()))
print("5th percentile total return (net): {:.2%}".format(np.percentile(df.total_return, 5)))
print("95th percentile total return (net): {:.2%}".format(np.percentile(df.total_return, 95)))
print("Max total return (net): {:.2%}".format(df.total_return.max()))
print("Min total return (net): {:.2%}".format(df.total_return.min()))

print("\n=== CAGR / ANNUALIZED RETURNS ===")
print("Mean annualized return (CAGR): {:.2%}".format(df.annualized_return.mean()))
print("Median annualized return (CAGR): {:.2%}".format(df.annualized_return.median()))
print("5th percentile annualized return (CAGR): {:.2%}".format(np.percentile(df.annualized_return, 5)))
print("95th percentile annualized return (CAGR): {:.2%}".format(np.percentile(df.annualized_return, 95)))
print("Max annualized return (CAGR): {:.2%}".format(df.annualized_return.max()))
print("Min annualized return (CAGR): {:.2%}".format(df.annualized_return.min()))

# Histogram of total returns
plt.figure(figsize=(9,5))
plt.hist(df.total_return, bins=200, density=True, edgecolor='none')
plt.title("Monte Carlo distribution of representative CAIE note total return (net of fees)")
plt.xlabel("Total return over investment period (fraction)")
plt.ylabel("Density")
plt.grid(alpha=0.2)
plt.savefig('montecarlo_results.png', dpi=150, bbox_inches='tight')
print(f"\nPlot saved to montecarlo_results.png")
