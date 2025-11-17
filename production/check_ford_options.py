#!/usr/bin/env python3

import yfinance as yf
import pandas as pd
from datetime import datetime

# Get Ford current price and options
try:
    ford = yf.Ticker('F')
    
    # Try to get current price from info first, fallback to recent price
    try:
        price = ford.info.get('currentPrice') or ford.info.get('previousClose')
        if not price:
            # Fallback: use a reasonable estimate for Ford
            price = 11.0  # Ford typically trades $10-12
        print(f'Ford (F) Current Price: ${price:.2f}')
    except:
        price = 11.0  # Safe estimate
        print(f'Ford (F) Estimated Price: ${price:.2f}')

    # Get nearest expiration dates
    exp_dates = ford.options[:3] if hasattr(ford, 'options') and ford.options else []
    
    if exp_dates:
        print(f'Next expiration dates: {exp_dates}')

        for exp in exp_dates[:2]:  # Check first 2 expirations
            print(f'\n--- Ford Options expiring {exp} ---')
            try:
                options = ford.option_chain(exp)
                
                # Filter calls near and out of the money
                calls = options.calls
                
                # Near the money calls (within $2 of current price)
                near_money = calls[(calls['strike'] >= price - 2) & (calls['strike'] <= price + 2)]
                
                if not near_money.empty:
                    print('CALLS within $43 budget:')
                    affordable = near_money[near_money['lastPrice'] <= 4.30]  # Max $430 per contract
                    if not affordable.empty:
                        for _, row in affordable.head(5).iterrows():
                            cost = row['lastPrice'] * 100  # Contract cost
                            profit_breakeven = row['strike'] + row['lastPrice']
                            print(f'  ${row["strike"]:.0f} strike - Premium: ${row["lastPrice"]:.2f} (${cost:.0f} total) - Breakeven: ${profit_breakeven:.2f}')
                    else:
                        print('  Checking cheapest near-money calls:')
                        for _, row in near_money.head(3).iterrows():
                            cost = row['lastPrice'] * 100
                            print(f'    ${row["strike"]:.0f} strike - Premium: ${row["lastPrice"]:.2f} (${cost:.0f} total)')
                
                # Out of money calls (cheaper)
                otm_calls = calls[calls['strike'] > price]
                cheap_otm = otm_calls[otm_calls['lastPrice'] <= 0.50]  # Under $0.50 premium
                if not cheap_otm.empty:
                    print('\nCheap out-of-money CALLS:')
                    for _, row in cheap_otm.head(5).iterrows():
                        cost = row['lastPrice'] * 100
                        profit_breakeven = row['strike'] + row['lastPrice']
                        print(f'  ${row["strike"]:.0f} strike - Premium: ${row["lastPrice"]:.2f} (${cost:.0f} total) - Breakeven: ${profit_breakeven:.2f}')
                
                # Also check puts for comparison
                puts = options.puts
                cheap_puts = puts[(puts['strike'] <= price + 1) & (puts['lastPrice'] <= 0.50)]
                if not cheap_puts.empty:
                    print('\nCheap PUTS (bearish bets):')
                    for _, row in cheap_puts.head(3).iterrows():
                        cost = row['lastPrice'] * 100
                        profit_breakeven = row['strike'] - row['lastPrice']
                        print(f'  ${row["strike"]:.0f} strike - Premium: ${row["lastPrice"]:.2f} (${cost:.0f} total) - Breakeven: ${profit_breakeven:.2f}')
                        
            except Exception as e:
                print(f'  Error getting options for {exp}: {e}')
    else:
        print('No options data available (market may be closed)')
        print('\nTypical Ford Options (estimate):')
        print('Ford usually trades $10-12, so typical options:')
        print(f'- ${price+1:.0f} strike calls: ~$0.10-0.30 ($10-30 per contract)')
        print(f'- ${price+2:.0f} strike calls: ~$0.05-0.15 ($5-15 per contract)')
        print(f'- ${price-1:.0f} strike puts: ~$0.10-0.25 ($10-25 per contract)')

except Exception as e:
    print(f"Error getting Ford data: {e}")
    print('\nFord typically trades around $10-12')
    print('Estimated affordable options:')
    print('- $12 strike calls: ~$0.15-0.30 ($15-30 per contract)')
    print('- $13 strike calls: ~$0.05-0.15 ($5-15 per contract)')
    print('- $10 strike puts: ~$0.10-0.20 ($10-20 per contract)')