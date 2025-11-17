#!/usr/bin/env python3

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Get AMD current price and options
amd = yf.Ticker('AMD')
price = amd.history(period='1d')['Close'][-1]
print(f'AMD Current Price: ${price:.2f}')

# Get nearest expiration dates
try:
    exp_dates = amd.options[:3]  # First 3 expiration dates
    print(f'Next expiration dates: {exp_dates}')

    for exp in exp_dates[:2]:  # Check first 2 expirations
        print(f'\n--- Options expiring {exp} ---')
        options = amd.option_chain(exp)
        
        # Filter calls near the money (within $10 of current price)
        calls = options.calls
        near_money = calls[(calls['strike'] >= price - 10) & (calls['strike'] <= price + 10)]
        
        if not near_money.empty:
            print('Affordable CALLS (within $43):')
            affordable = near_money[near_money['lastPrice'] <= 4.30]  # $4.30 max per contract
            if not affordable.empty:
                for _, row in affordable.head(5).iterrows():
                    cost = row['lastPrice'] * 100  # Contract cost
                    profit_breakeven = row['strike'] + row['lastPrice']
                    print(f'  Strike ${row["strike"]:.0f} - Premium: ${row["lastPrice"]:.2f} (${cost:.0f} total) - Breakeven: ${profit_breakeven:.2f}')
            else:
                print('  No calls under $4.30 premium')
                print('  Cheapest calls:')
                for _, row in near_money.head(3).iterrows():
                    cost = row['lastPrice'] * 100
                    print(f'    Strike ${row["strike"]:.0f} - Premium: ${row["lastPrice"]:.2f} (${cost:.0f} total)')
        
        # Also check some cheaper out-of-money options
        print('\nCheaper out-of-money calls:')
        otm_calls = calls[calls['strike'] > price + 5]  # $5+ out of money
        cheap_otm = otm_calls[otm_calls['lastPrice'] <= 1.00]  # Under $1 premium
        if not cheap_otm.empty:
            for _, row in cheap_otm.head(3).iterrows():
                cost = row['lastPrice'] * 100
                profit_breakeven = row['strike'] + row['lastPrice']
                print(f'  Strike ${row["strike"]:.0f} - Premium: ${row["lastPrice"]:.2f} (${cost:.0f} total) - Breakeven: ${profit_breakeven:.2f}')

except Exception as e:
    print(f"Error getting options data: {e}")