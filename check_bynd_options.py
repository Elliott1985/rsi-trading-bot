#!/usr/bin/env python3
import yfinance as yf
import requests
import sys

bynd = yf.Ticker("BYND")
current_price = bynd.info.get('currentPrice')
if current_price:
    print(f"BYND Current Price: ~${current_price:.2f}\n")
else:
    print("Could not fetch current price for BYND.\n")

try:
    exp = bynd.options[0]
    chain = bynd.option_chain(exp)

    calls = chain.calls[chain.calls['lastPrice'] * 100 <= 43]
    puts = chain.puts[chain.puts['lastPrice'] * 100 <= 43]

    print(f"Expiration: {exp}")
    print(f"\nCALLS under $43: {len(calls)}")
    for _, row in calls.head(5).iterrows():
        print(f"  ${row['strike']:.1f} strike = ${row['lastPrice']*100:.2f}/contract")

    print(f"\nPUTS under $43: {len(puts)}")
    for _, row in puts.head(5).iterrows():
        print(f"  ${row['strike']:.1f} strike = ${row['lastPrice']*100:.2f}/contract")

except requests.exceptions.JSONDecodeError as e:
    print(f"Error decoding JSON from yfinance: {e}")
    print("This might be due to rate-limiting or an issue with the Yahoo Finance API.")
    sys.exit(1)
except IndexError:
    print("No option expiration dates found for BYND. Exiting.")
    sys.exit(1)
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    sys.exit(1)
