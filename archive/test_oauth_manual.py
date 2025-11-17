#!/usr/bin/env python3
"""
Manual E*TRADE OAuth Test
Run this interactively to complete OAuth authentication
"""

import asyncio
import sys
sys.path.append('src')

from trading.etrade_real import ETradeBroker
from utils.config import Config

async def test_oauth():
    """Test OAuth authentication manually"""
    print("🔐 Manual E*TRADE OAuth Test")
    print("="*50)
    
    config = Config()
    broker = ETradeBroker(config, sandbox=False)
    
    print(f"Using API Key: {broker.client_key}")
    print(f"Using API Secret: {broker.client_secret[:10]}...")
    print()
    
    # Attempt authentication
    success = await broker.authenticate()
    
    if success:
        print("✅ Authentication successful!")
        
        # Test a simple API call
        try:
            balance = await broker.get_account_balance()
            print(f"💰 Account Balance: ${balance.get('total_value', 0):,.2f}")
            print(f"💵 Available Cash: ${balance.get('cash_available', 0):,.2f}")
        except Exception as e:
            print(f"⚠️  Could not fetch balance: {e}")
    else:
        print("❌ Authentication failed!")
    
    return success

if __name__ == "__main__":
    asyncio.run(test_oauth())