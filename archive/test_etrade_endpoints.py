#!/usr/bin/env python3
"""
Test E*TRADE API endpoints to find the correct ones
"""

import os
import asyncio
import sys
sys.path.append('src')

from trading.etrade_real import ETradeBroker
from utils.config import Config

async def test_endpoints():
    """Test various E*TRADE API endpoints"""
    
    print("🔍 Testing E*TRADE API Endpoints")
    print("=" * 50)
    
    config = Config()
    broker = ETradeBroker(config, sandbox=True)
    
    # Authenticate first
    print("🔐 Authenticating...")
    if not await broker.authenticate():
        print("❌ Authentication failed")
        return
        
    print("✅ Authenticated successfully")
    print(f"Base URL: {broker.base_url}")
    print()
    
    # Test different account endpoints
    account_endpoints = [
        "/v1/account/list",
        "/v1/accounts/list", 
        "/v1/user/api/account/list",
        "/account/list",
        "/accounts/list"
    ]
    
    print("📋 Testing Account List Endpoints:")
    print("-" * 40)
    
    for endpoint in account_endpoints:
        try:
            url = f"{broker.base_url}{endpoint}"
            print(f"Testing: {endpoint}")
            
            response = broker.oauth.get(url, timeout=10)
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"  ✅ SUCCESS - Content length: {len(response.text)}")
                try:
                    data = response.json()
                    print(f"  📄 JSON keys: {list(data.keys()) if isinstance(data, dict) else 'Not dict'}")
                except:
                    print(f"  📄 Response text (first 200 chars): {response.text[:200]}")
            elif response.status_code == 404:
                print(f"  ❌ Not found")
            elif response.status_code == 401:
                print(f"  🔒 Unauthorized")
            elif response.status_code == 403:
                print(f"  🚫 Forbidden")
            else:
                print(f"  ⚠️  Other error")
                
        except Exception as e:
            print(f"  💥 Exception: {e}")
        
        print()
    
    # Test market data endpoints
    print("📈 Testing Market Data Endpoints:")
    print("-" * 40)
    
    market_endpoints = [
        "/v1/market/productlookup",
        "/v1/market/product/lookup",
        "/v1/market/optionslist",
        "/market/productlookup"
    ]
    
    for endpoint in market_endpoints:
        try:
            url = f"{broker.base_url}{endpoint}"
            params = {'company': 'AAPL', 'type': 'eq'}
            print(f"Testing: {endpoint}")
            
            response = broker.oauth.get(url, params=params, timeout=10)
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"  ✅ SUCCESS")
            elif response.status_code == 404:
                print(f"  ❌ Not found")
            else:
                print(f"  ⚠️  Status {response.status_code}")
                
        except Exception as e:
            print(f"  💥 Exception: {e}")
        
        print()

if __name__ == "__main__":
    asyncio.run(test_endpoints())