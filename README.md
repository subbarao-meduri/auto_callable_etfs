# Autocallable ETF Monte Carlo Simulation

A Monte Carlo simulation tool for analyzing autocallable structured notes/ETFs, specifically modeled after the **Calamos Autocallable Income ETF (ticker CAIE)**. This simulation models the distribution of outcomes (best/worst real yields) under market randomness to help understand the risk-return profile of autocallable structured products.

## Overview

This project simulates a representative autocallable note similar to those held in CAIE's portfolio. CAIE holds a laddered portfolio of autocallable notes tied to an S&P-500-linked autocall index and targets high monthly income. The fund's coupon stream is driven by those notes ([Calamos Investments](https://www.calamos.com/)).

The simulation uses geometric Brownian motion (GBM) to model underlying index movements over a 5-year period and accounts for:

- **Monthly coupon payments** (14.7% annual gross, subject to barrier conditions)
- **Annual autocall triggers** (early redemption at 100% of starting level)
- **Principal protection barriers** (60% barrier for coupon eligibility and principal protection)
- **Management fees** (0.74% annual expense ratio)

While CAIE uses laddering (many notes) and swaps/treasury collateral to produce exposure, this model uses a representative single-note payoff as a first-order approximation that captures the essential autocall/barrier dynamics.

## Key Product Features (What's Being Modeled)

Based on CAIE public materials and financial reporting:

1. **Monthly Coupon Payments**: The notes pay a coupon for each month the reference index is above 60% of its starting level (the "coupon barrier") ([Financial Times](https://www.ft.com/)).

2. **Annual Autocall Trigger**: Each note is typically callable after one year if the reference index is at or above 100% of its starting level. If called, you receive principal + accrued coupons to date ([Financial Times](https://www.ft.com/)).

3. **Coupon Rate**: CAIE's current quoted annualized coupon (weighted average across the ladder) is around ~14.7% (this is an income target/current yield figure reported) ([Financial Times](https://www.ft.com/)).

4. **Expense Ratio**: The ETF expense ratio is ~0.74% ([Financial Times](https://www.ft.com/)).

5. **Maturity Structure**: The fund uses laddered notes, typically with 5-year maturities ([Calamos Investments](https://www.calamos.com/)). This simulation models a representative 5-year note.

6. **Principal Protection**: If at maturity the index is ≥ 60% of start, you get full principal back (and any coupons). If final index < 60%, principal is reduced proportionally (i.e., you lose (1 − final/start)) ([Financial Times](https://www.ft.com/)).

## Modeling Assumptions

**Important — read before running:**

### What's Included:

- **Underlying Index**: S&P-500 style index simulated using geometric Brownian motion
  - Default assumptions: `mu = 0.07` (7% expected annual drift) and `sigma = 0.18` (18% annual volatility)
  - These can be changed to match actual historical drift/volatility if desired

- **Observation Cadence**:
  - **Coupon observation**: Monthly (every 1/12 year). If monthly index ≥ 60% of start, that month's coupon is paid
  - **Autocall test**: Every 12 months (annually). If index ≥ 100% at that annual check, the note is called

- **Coupon Rate**: Product-level annualized coupon set to 14.7% in the example; monthly coupon = 14.7% / 12. This is the gross coupon before fees. (The real ETF's weighted coupon varies; 14.7% is the reported current yield) ([Financial Times](https://www.ft.com/))

- **Maturity**: Models a 5-year note (Calamos materials mention 5-year maturities in some products) ([Calamos Investments](https://www.calamos.com/)). Can be changed to 3-year or other durations by modifying `T` parameter

- **Final Protection/Barrier**: If at maturity the index is ≥ 60% of start, you get full principal back (and any coupons). If final index < 60%, principal is reduced proportionally

- **Fees**: 0.74% annual expense ratio — modeled as a continuous drag on the total return (practical approximation) subtracted from gross coupon/cash flows ([Financial Times](https://www.ft.com/))

### What's NOT Included:

- **Counterparty/default risk**: Not modeled. These can materially affect realized returns but are harder to simulate without note-specific data
- **Liquidity spreads**: Not modeled
- **Issuer behavior**: Not modeled (e.g., discretionary call decisions beyond contractual triggers)
- **Multiple heterogeneous notes**: Models a representative single note rather than aggregating multiple heterogeneous notes (though this captures essential autocall/barrier dynamics)

## Features

- 200,000 Monte Carlo simulations for robust statistical analysis
- Calculation of both total returns and CAGR (annualized returns)
- Statistical summaries including mean, median, and percentiles
- Visualization of return distribution via histogram
- Easily adaptable parameters for different market assumptions or product structures

## Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

## Installation

1. Clone this repository:
```bash
git clone <your-repo-url>
cd auto_call_etf
```

2. Install required Python packages:
```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install numpy pandas matplotlib
```

## Usage

Run the simulation:
```bash
python3 montecarlo.py
```

The script will:
1. Run 200,000 Monte Carlo simulations
2. Print statistical summaries for both total returns and CAGR
3. Generate a histogram plot saved as `montecarlo_results.png`

## Output

The simulation outputs:

### Total Returns (over investment period)
- Mean, median, and percentile statistics
- Represents returns over varying time periods (1-5 years depending on autocall)

### CAGR / Annualized Returns
- Annualized return statistics for easier comparison
- Normalized to per-year basis regardless of holding period

### Visualization
- Histogram showing the distribution of total returns
- Saved as `montecarlo_results.png`

## Parameters

You can modify the simulation parameters in `montecarlo.py`:

```python
S0 = 100.0            # Starting index level (normalized)
mu = 0.07             # Annual drift (expected return) - can use historical S&P 500 data
sigma = 0.18          # Annual volatility - can use historical S&P 500 data
T = 5.0               # Maturity in years (change to 3.0 for 3-year product)
coupon_annual = 0.147 # Gross annual coupon (14.7%)
fee_annual = 0.0074   # Expense ratio (0.74%)
monthly_barrier = 0.60   # Coupon barrier (60% of start)
autocall_trigger = 1.00  # Autocall trigger (100% of start)
call_interval_years = 1  # Autocall check every 1 year
n_sims = 200000       # Number of Monte Carlo runs (increase for smoother tails)
```

## How It Works

1. **Path Simulation**: For each simulation, generates a daily price path using geometric Brownian motion
2. **Monthly Coupon Checks**: At each month, checks if index is above 60% barrier to accrue coupon
3. **Annual Autocall Checks**: At each year, checks if index reaches 100% trigger for early redemption
4. **Final Settlement**: If not called early, calculates final payout based on:
   - Principal protection if index ≥ 60% at maturity
   - Principal loss proportional to index decline if index < 60% at maturity
5. **Fee Application**: Applies management fees continuously over the holding period
6. **Return Calculation**: Computes both total return and annualized return (CAGR)

## Interpreting Results

The simulation helps answer questions like:
- What's the distribution of possible outcomes?
- What's the probability of achieving the target coupon yield?
- What are the tail risks (best/worst case scenarios)?
- How does early autocall affect returns?

**Example interpretation:**
- **Median CAGR of 13.85%**: Half of simulations achieve this or better
- **5th percentile CAGR of 10.83%**: 95% of outcomes are better than this (5% chance of worse)
- **95th percentile CAGR of 13.85%**: Most outcomes cluster around this level (many autocall early)
- **Minimum CAGR of -19.25%**: Worst-case scenario (very rare, <0.001% probability)

## Adapting the Model

### Using Historical Statistics

To use actual S&P 500 historical drift and volatility:
1. Calculate historical annual returns and volatility from S&P 500 data
2. Update `mu` and `sigma` parameters accordingly
3. Re-run the simulation

### Modeling Different Products

- **3-year notes**: Change `T = 3.0`
- **Different coupon rates**: Modify `coupon_annual`
- **Different barriers**: Adjust `monthly_barrier` and `autocall_trigger`
- **Different market assumptions**: Update `mu` and `sigma` for different market regimes

### Extending the Model

Potential enhancements (not currently implemented):
- Multiple heterogeneous notes aggregated into fund-level returns
- Counterparty risk modeling
- Liquidity spread adjustments
- Discretionary call behavior by issuers

## Example Output

```
Simulations: 200000

=== TOTAL RETURNS (over investment period) ===
Mean total return (net): 24.75%
Median total return (net): 13.85%
5th percentile total return (net): 13.85%
95th percentile total return (net): 67.20%
Max total return (net): 67.20%
Min total return (net): -65.67%

=== CAGR / ANNUALIZED RETURNS ===
Mean annualized return (CAGR): 12.83%
Median annualized return (CAGR): 13.85%
5th percentile annualized return (CAGR): 10.83%
95th percentile annualized return (CAGR): 13.85%
Max annualized return (CAGR): 13.85%
Min annualized return (CAGR): -19.25%

Plot saved to montecarlo_results.png
```

## References

- [Calamos Investments](https://www.calamos.com/) - CAIE product information
- [Financial Times](https://www.ft.com/) - CAIE reporting and analysis
- [SEC](https://www.sec.gov/) - Regulatory filings and fund structure

## License

MIT License

Copyright (c) 2024

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
