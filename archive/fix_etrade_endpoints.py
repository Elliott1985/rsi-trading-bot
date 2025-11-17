#!/usr/bin/env python3
"""
Fix E*TRADE API endpoints by testing all possible variations
Based on official E*TRADE API documentation
"""

import asyncio
import sys
import json
sys.path.append('src')

from trading.etrade_real import ETradeBroker
from utils.config import Config

async def test_all_endpoints():
    """Test all possible E*TRADE API endpoint variations"""
    
    print("🔧 Fixing E*TRADE API Endpoints")
    print("=" * 50)
    
    config = Config()
    broker = ETradeBroker(config, sandbox=True)
    
    # Authenticate first
    print("🔐 Authenticating...")
    if not await broker.authenticate():
        print("❌ Authentication failed")
        return
        
    print("✅ Authenticated - testing endpoints...")
    
    # Test account endpoints based on official E*TRADE API docs
    account_endpoints = [
        # Official E*TRADE API v1 endpoints
        "/v1/user/api/account/list",
        "/v1/user/api/accounts/list",
        "/v1/accounts/list.json",
        "/v1/account/list.json",
        "/account/list",
        "/accounts/list",
        
        # Alternative formats
        "/v1/user/api/account",
        "/v1/user/api/accounts",
        "/user/api/account/list",
        "/api/account/list",
    ]
    
    print("\n📋 Testing Account Endpoints:")
    print("-" * 40)
    
    working_endpoints = []
    
    for endpoint in account_endpoints:
        try:
            url = f"{broker.base_url}{endpoint}"
            print(f"Testing: {endpoint}")
            
            # Try with different headers
            headers_sets = [
                {'Accept': 'application/json'},
                {'Accept': 'application/xml'},
                {'Content-Type': 'application/json', 'Accept': 'application/json'},
                {}  # No special headers
            ]
            
            for i, headers in enumerate(headers_sets):
                try:
                    response = broker.oauth.get(url, headers=headers, timeout=10)
                    print(f"  Headers {i+1}: Status {response.status_code}")
                    
                    if response.status_code == 200:
                        print(f"  ✅ SUCCESS with headers {i+1}!")
                        working_endpoints.append({
                            'endpoint': endpoint,
                            'headers': headers,
                            'response_length': len(response.text)
                        })
                        
                        # Try to parse response
                        try:
                            data = response.json()
                            print(f"  📄 JSON keys: {list(data.keys())}")
                        except:
                            print(f"  📄 Response preview: {response.text[:200]}...")
                        break
                    elif response.status_code == 404:
                        continue  # Try next header set
                    else:
                        print(f"    Status: {response.status_code}")
                        
                except Exception as e:
                    if "IncompleteRead" in str(e):
                        print(f"    Connection issue (may still work)")
                    else:
                        print(f"    Error: {str(e)[:50]}...")
                    
        except Exception as e:
            print(f"  💥 Failed: {e}")
        
        print()
    
    # Test market data endpoints
    print("📈 Testing Market Data Endpoints:")
    print("-" * 40)
    
    market_endpoints = [
        "/v1/market/productlookup",
        "/v1/market/product/lookup", 
        "/v1/market/lookup",
        "/market/productlookup",
        "/productlookup",
    ]
    
    for endpoint in market_endpoints:
        try:
            url = f"{broker.base_url}{endpoint}"
            params = {'company': 'AAPL', 'type': 'eq'}
            print(f"Testing: {endpoint}")
            
            response = broker.oauth.get(url, params=params, timeout=10)
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"  ✅ Market data endpoint works!")
                working_endpoints.append({
                    'endpoint': endpoint,
                    'type': 'market',
                    'params': params
                })
                
        except Exception as e:
            print(f"  Error: {e}")
        
        print()
    
    # Test order endpoints
    print("📋 Testing Order Endpoints:")
    print("-" * 40)
    
    if broker.account_key:
        order_endpoints = [
            f"/v1/user/api/account/{broker.account_key}/orders/preview",
            f"/v1/user/api/account/{broker.account_key}/orders/place",
            f"/v1/account/{broker.account_key}/orders/preview",
            f"/v1/account/{broker.account_key}/orders/place",
        ]
        
        for endpoint in order_endpoints:
            try:
                url = f"{broker.base_url}{endpoint}"
                print(f"Testing: {endpoint}")
                
                # Don't actually place orders, just test endpoint existence
                response = broker.oauth.get(url, timeout=5)
                print(f"  Status: {response.status_code}")
                
                if response.status_code in [200, 400, 405]:  # 405 = Method not allowed (expects POST)
                    print(f"  ✅ Order endpoint exists!")
                    working_endpoints.append({
                        'endpoint': endpoint,
                        'type': 'orders'
                    })
                    
            except Exception as e:
                print(f"  Error: {e}")
            
            print()
    
    # Summary
    print("🎯 WORKING ENDPOINTS FOUND:")
    print("=" * 40)
    
    if working_endpoints:
        for ep in working_endpoints:
            print(f"✅ {ep['endpoint']}")
            if 'headers' in ep:
                print(f"   Headers: {ep['headers']}")
    else:
        print("❌ No working endpoints found")
        
        print("\n🔍 Let's try alternative approaches...")
        await try_alternative_approaches(broker)
    
    return working_endpoints

async def try_alternative_approaches(broker):
    """Try alternative approaches to access E*TRADE API"""
    
    print("\n🔄 Trying Alternative Approaches:")
    print("-" * 40)
    
    # Try different base URLs
    alternative_urls = [
        "https://etgacb2.etrade.com",  # Production gateway
        "https://api.etrade.com/v1",  # With version in URL
        "https://etwssandbox.etrade.com",  # Original sandbox
        "https://api.etrade.com/sandbox",  # Sandbox path
    ]
    
    for base_url in alternative_urls:
        print(f"\nTrying base URL: {base_url}")
        
        try:
            # Test basic connectivity
            response = broker.oauth.get(f"{base_url}/v1/user/api/account/list", timeout=10)
            print(f"  Status: {response.status_code}")
            
            if response.status_code in [200, 401, 403]:  # Any response is good
                print(f"  ✅ This base URL responds!")
                
        except Exception as e:
            print(f"  ❌ Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_all_endpoints())