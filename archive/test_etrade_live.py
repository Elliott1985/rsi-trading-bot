#!/usr/bin/env python3
"""
Test script for live E*TRADE authentication and API calls.
This will prompt you to authorize the app and enter a verification code.
"""

import os
import sys
import asyncio
sys.path.append('src')

from trading.etrade_real import ETradeBroker
from utils.config import Config

async def test_etrade_live():
    """Test E*TRADE live authentication flow"""
    print("=== E*TRADE Live Authentication Test ===")
    
    # Check if environment variables are set
    sandbox_key = os.getenv('ETRADE_SANDBOX_KEY')
    sandbox_secret = os.getenv('ETRADE_SANDBOX_SECRET')
    prod_key = os.getenv('ETRADE_PROD_KEY') 
    prod_secret = os.getenv('ETRADE_PROD_SECRET')
    
    print(f"ETRADE_SANDBOX_KEY: {'✓ Set' if sandbox_key else '✗ Not set'}")
    print(f"ETRADE_SANDBOX_SECRET: {'✓ Set' if sandbox_secret else '✗ Not set'}")
    print(f"ETRADE_PROD_KEY: {'✓ Set' if prod_key else '✗ Not set'}")
    print(f"ETRADE_PROD_SECRET: {'✓ Set' if prod_secret else '✗ Not set'}")
    print()
    
    # Load config
    config = Config()
    
    # Test sandbox mode first (safer)
    print("Testing SANDBOX mode...")
    try:
        broker = ETradeBroker(config, sandbox=True)
        
        # This will start OAuth flow
        success = await broker.authenticate()
        
        if success:
            print("✓ Sandbox authentication successful!")
            
            # Account info should be loaded during authentication
            if broker.account_key:
                print(f"✓ Account key: {broker.account_key}")
            else:
                print("✗ No account key found")
                
        else:
            print("✗ Sandbox authentication failed")
            
    except Exception as e:
        print(f"✗ Sandbox test failed: {e}")
    
    print("\n" + "="*50)
    
    # Ask if user wants to test production
    response = input("\nDo you want to test PRODUCTION mode? (y/N): ").strip().lower()
    if response in ['y', 'yes']:
        print("\n⚠️  WARNING: Testing PRODUCTION mode!")
        print("This will connect to your real E*TRADE account.")
        
        confirm = input("Are you sure? Type 'YES' to continue: ").strip()
        if confirm == 'YES':
            try:
                broker = ETradeBroker(config, sandbox=False)
                
                # This will start OAuth flow
                success = await broker.authenticate()
                
                if success:
                    print("✓ Production authentication successful!")
                    
                    # Account info should be loaded during authentication
                    if broker.account_key:
                        print(f"✓ Account key: {broker.account_key}")
                    else:
                        print("✗ No account key found")
                        
                else:
                    print("✗ Production authentication failed")
                    
            except Exception as e:
                print(f"✗ Production test failed: {e}")
        else:
            print("Production test cancelled.")
    else:
        print("Production test skipped.")

if __name__ == "__main__":
    asyncio.run(test_etrade_live())
