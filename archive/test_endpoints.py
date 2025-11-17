#!/usr/bin/env python3
"""
Test E*TRADE API endpoints with authenticated session
"""

import json
from requests_oauthlib import OAuth1Session
from dotenv import load_dotenv
import os

load_dotenv('config/api_keys.env')

def test_endpoints():
    print("🧪 Testing E*TRADE API Endpoints")
    print("="*50)
    
    # Load saved tokens
    try:
        with open('etrade_tokens_prod.json', 'r') as f:
            token_data = json.load(f)
    except:
        print("❌ No saved tokens found. Run debug_oauth.py first.")
        return
        
    # Create authenticated session
    client_key = os.getenv('ETRADE_PROD_KEY')
    client_secret = os.getenv('ETRADE_PROD_SECRET')
    
    oauth = OAuth1Session(
        client_key,
        client_secret=client_secret,
        resource_owner_key=token_data['resource_owner_key'],
        resource_owner_secret=token_data['resource_owner_secret']
    )
    
    # Test different endpoints
    endpoints = [
        "https://api.etrade.com/v1/user/api/account/list",
        "https://api.etrade.com/user/api/account/list", 
        "https://api.etrade.com/accounts",
        "https://api.etrade.com/v1/accounts",
        "https://api.etrade.com/v1/user/api/accounts",
        "https://api.etrade.com/v1/account/list",
    ]
    
    for endpoint in endpoints:
        print(f"\n🔍 Testing: {endpoint}")
        try:
            response = oauth.get(endpoint, timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ SUCCESS!")
                try:
                    data = response.json()
                    print(f"   Data: {json.dumps(data, indent=2)[:300]}...")
                except:
                    print(f"   Text: {response.text[:200]}...")
                break
            elif response.status_code == 404:
                print("   ❌ Not Found")
            elif response.status_code == 401:
                print("   ❌ Unauthorized")
            elif response.status_code == 403:
                print("   ❌ Forbidden")
            else:
                print(f"   ❌ Error: {response.status_code}")
                print(f"   Response: {response.text[:100]}...")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")

    print("\n🧪 Testing market data endpoints...")
    market_endpoints = [
        "https://api.etrade.com/v1/market/productlookup?company=AAPL&type=EQ",
        "https://api.etrade.com/market/productlookup?company=AAPL&type=EQ",
    ]
    
    for endpoint in market_endpoints:
        print(f"\n🔍 Testing: {endpoint}")
        try:
            response = oauth.get(endpoint, timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ SUCCESS!")
                try:
                    data = response.json()
                    print(f"   Data: {json.dumps(data, indent=2)[:300]}...")
                except:
                    print(f"   Text: {response.text[:200]}...")
            else:
                print(f"   Response: {response.text[:100]}...")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")

if __name__ == "__main__":
    test_endpoints()