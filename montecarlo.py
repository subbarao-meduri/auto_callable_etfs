#!/usr/bin/env python3
"""
Monte Carlo simulation of a representative autocallable note (CAIE-style).
Simulates price paths using geometric Brownian motion and evaluates note payoffs.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Simulation Parameters
S0 = 100.0            # Starting index level (normalized to 100)
mu = 0.07             # Annual drift (expected return). Default: 7% (typical equity market)
sigma = 0.18          # Annual volatility. Default: 18% (S&P 500 historical volatility)
T = 5.0               # Maturity in years. Default: 5 years (CAIE typical maturity)
dt = 1/252.0          # Time step size (years). Default: daily (252 trading days/year)

# Note Structure Parameters
coupon_annual = 0.147 # Gross annual coupon rate. Default: 14.7% (CAIE current yield)
fee_annual = 0.0074   # Annual expense ratio. Default: 0.74% (CAIE expense ratio)
monthly_barrier = 0.60   # Coupon barrier as fraction of start. Default: 60% (coupon paid if index >= 60%)
autocall_trigger = 1.00  # Autocall trigger as fraction of start. Default: 100% (early call if index >= 100%)
call_interval_years = 1  # Autocall check frequency (years). Default: 1 year (annual checks)

# Simulation Settings
n_sims = 200000       # Number of Monte Carlo simulations. Default: 200k (higher = smoother tails, slower)
seed = 42             # Random seed for reproducibility
np.random.seed(seed)

# Derived calculations
steps = int(T / dt)
monthly_indices = set((np.round(np.arange(1, int(T*12)+1) * (1/12) / dt)).astype(int))
annual_indices = set((np.round(np.arange(1, int(T/call_interval_years)+1) * call_interval_years / dt)).astype(int))
monthly_coupon = coupon_annual / 12.0

# Results arrays
total_returns = np.zeros(n_sims)
annualized_returns = np.zeros(n_sims)

# Monte Carlo simulation
for sim in range(n_sims):
    # Generate geometric Brownian motion path
    z = np.random.randn(steps)
    log_returns = (mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * z
    log_prices = np.concatenate([[0.0], np.cumsum(log_returns)])
    prices = S0 * np.exp(log_prices)
    
    accrued_coupons = 0.0
    called = False
    call_time = None
    
    # Evaluate note over time
    for idx in range(1, steps + 1):
        price = prices[idx]
        
        # Monthly coupon check
        if idx in monthly_indices:
            if price >= monthly_barrier * S0:
                accrued_coupons += monthly_coupon
        
        # Annual autocall check
        if idx in annual_indices:
            if price >= autocall_trigger * S0:
                called = True
                call_time = idx * dt
                break
    
    # Calculate final payoff
    if called:
        gross_total = 1.0 + accrued_coupons
    else:
        final_price = prices[-1]
        if final_price >= monthly_barrier * S0:
            gross_total = 1.0 + accrued_coupons
        else:
            gross_total = (final_price / S0) + accrued_coupons
    
    # Apply fee drag (continuous compounding)
    duration = call_time if called else T
    net_total = gross_total * np.exp(-fee_annual * duration)
    
    total_returns[sim] = net_total - 1.0
    annualized_returns[sim] = ((net_total) ** (1.0 / (duration if duration > 0 else T))) - 1.0

# Aggregate results
df = pd.DataFrame({
    "total_return": total_returns,
    "annualized_return": annualized_returns
})

# Print statistics
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

# Generate histogram
plt.figure(figsize=(9, 5))
plt.hist(df.total_return, bins=200, density=True, edgecolor='none')
plt.title("Monte Carlo distribution of representative CAIE note total return (net of fees)")
plt.xlabel("Total return over investment period (fraction)")
plt.ylabel("Density")
plt.grid(alpha=0.2)
plt.savefig('montecarlo_results.png', dpi=150, bbox_inches='tight')
print(f"\nPlot saved to montecarlo_results.png")
