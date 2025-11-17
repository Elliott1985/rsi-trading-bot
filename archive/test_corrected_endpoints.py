#!/usr/bin/env python3
"""
Test corrected E*TRADE API endpoints based on official documentation
"""

import json
from requests_oauthlib import OAuth1Session
from dotenv import load_dotenv
import os

load_dotenv('config/api_keys.env')

def test_corrected_endpoints():
    print("🧪 Testing Corrected E*TRADE API Endpoints")
    print("="*60)
    
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
    
    print(f"Using tokens: {token_data['resource_owner_key'][:20]}...")
    print()
    
    # Test the corrected account list endpoint from official docs
    print("🔍 Testing corrected account list endpoint...")
    url = "https://api.etrade.com/v1/accounts/list"
    
    headers = {
        'Accept': 'application/json'
    }
    
    try:
        response = oauth.get(url, headers=headers, timeout=10)
        print(f"   URL: {url}")
        print(f"   Status: {response.status_code}")
        print(f"   Headers sent: {headers}")
        print(f"   Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("   ✅ SUCCESS! Account list retrieved!")
            try:
                data = response.json()
                print(f"   📊 Response data:")
                print(json.dumps(data, indent=4)[:1000])
                
                # Extract account keys for future use
                if 'AccountListResponse' in data:
                    accounts = data['AccountListResponse'].get('Accounts', {}).get('Account', [])
                    if accounts:
                        print(f"\n   📋 Found {len(accounts)} account(s):")
                        for i, account in enumerate(accounts):
                            account_id = account.get('accountId', 'Unknown')
                            account_key = account.get('accountIdKey', 'Unknown')  
                            account_mode = account.get('accountMode', 'Unknown')
                            print(f"      Account {i+1}: ID={account_id}, Key={account_key}, Mode={account_mode}")
                            
            except Exception as e:
                print(f"   ⚠️  JSON parse error: {e}")
                print(f"   Raw response: {response.text[:300]}...")
                
        elif response.status_code == 401:
            print("   ❌ Unauthorized - OAuth token may be invalid")
        elif response.status_code == 403:
            print("   ❌ Forbidden - Account may lack API permissions")
        else:
            print(f"   ❌ Error: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")

    # Test market data endpoint
    print(f"\n🔍 Testing market data endpoint...")
    market_url = "https://api.etrade.com/v1/market/productlookup"
    params = {
        'company': 'AAPL',
        'type': 'EQ'
    }
    
    try:
        response = oauth.get(market_url, params=params, headers=headers, timeout=10)
        print(f"   URL: {market_url}")
        print(f"   Params: {params}")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ SUCCESS! Market data retrieved!")
            try:
                data = response.json()
                print(f"   📊 Market data sample:")
                print(json.dumps(data, indent=2)[:500] + "...")
            except:
                print(f"   Raw response: {response.text[:200]}...")
        else:
            print(f"   Response: {response.text[:200]}...")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")

if __name__ == "__main__":
    test_corrected_endpoints()