#!/usr/bin/env python3
"""Test crypto data access"""

import sys
import os
sys.path.append('src')

from api.alpaca_client import AlpacaClient
from utils.config_manager import get_config

def test_crypto():
    config = get_config()
    client = AlpacaClient(config)
    
    # Check account and crypto status
    try:
        # Get raw account data to check crypto_status
        account_data = client.api.get_account()
        print(f'Account status: {account_data.status}')
        print(f'Portfolio value: ${float(account_data.portfolio_value):.2f}')
        
        # Check crypto status
        crypto_status = getattr(account_data, 'crypto_status', 'NOT_AVAILABLE')
        print(f'Crypto status: {crypto_status}')
        
        if crypto_status != 'ACTIVE':
            print('\n🪙 Crypto trading is not enabled on your account.')
            print('   You need to sign the crypto agreement in your Alpaca dashboard.')
            return
            
    except Exception as e:
        print(f'Error checking account: {e}')
        return
    
    # Test crypto data access with correct format (BTC/USD not BTCUSD)
    print('\nTesting crypto data access...')
    crypto_symbols = ['BTC/USD', 'ETH/USD', 'LTC/USD']
    
    for symbol in crypto_symbols:
        try:
            data = client.get_bars(symbol, timeframe='1Day', limit=5)
            if data is not None and not data.empty:
                print(f'✅ {symbol}: Got {len(data)} bars')
                print(f'   Latest close: ${data["close"].iloc[-1]:.2f}')
            else:
                print(f'❌ {symbol}: No data returned')
        except Exception as e:
            print(f'❌ {symbol}: Error - {e}')

if __name__ == "__main__":
    test_crypto()