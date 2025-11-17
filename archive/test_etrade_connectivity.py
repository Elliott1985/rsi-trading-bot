#!/usr/bin/env python3
"""
Test E*TRADE API connectivity and OAuth URLs
"""

import os
import requests
from requests_oauthlib import OAuth1Session

def test_etrade_connectivity():
    """Test basic connectivity to E*TRADE API endpoints"""
    
    print("=== E*TRADE Connectivity Test ===")
    
    # Test endpoints
    endpoints = {
        "Production API": "https://api.etrade.com",
        "Sandbox API": "https://etwssandbox.etrade.com", 
        "Authorization": "https://us.etrade.com"
    }
    
    for name, url in endpoints.items():
        try:
            print(f"\nTesting {name}: {url}")
            response = requests.get(url, timeout=10)
            print(f"✓ Status: {response.status_code}")
            if response.status_code == 200:
                print("  - Endpoint is reachable")
            else:
                print(f"  - Got response but status {response.status_code}")
        except requests.exceptions.ConnectTimeout:
            print("✗ Connection timeout")
        except requests.exceptions.ConnectionError as e:
            print(f"✗ Connection error: {e}")
        except Exception as e:
            print(f"✗ Error: {e}")

def test_oauth_request():
    """Test OAuth request token generation"""
    
    print("\n=== OAuth Request Token Test ===")
    
    # Load credentials
    sandbox_key = os.getenv('ETRADE_SANDBOX_KEY')
    sandbox_secret = os.getenv('ETRADE_SANDBOX_SECRET')
    
    if not sandbox_key or not sandbox_secret:
        print("✗ E*TRADE credentials not found in environment")
        return False
        
    print(f"Using key: {sandbox_key[:10]}...")
    
    try:
        # Try sandbox first
        oauth = OAuth1Session(
            sandbox_key,
            client_secret=sandbox_secret,
            callback_uri="oob"
        )
        
        # Test both API endpoints
        endpoints = [
            "https://etwssandbox.etrade.com/oauth/request_token",
            "https://api.etrade.com/oauth/request_token"
        ]
        
        for endpoint in endpoints:
            print(f"\nTrying endpoint: {endpoint}")
            try:
                response = oauth.fetch_request_token(endpoint)
                print("✓ OAuth request token successful!")
                print(f"  Token: {response.get('oauth_token', 'N/A')[:20]}...")
                
                # Generate auth URL
                token = response.get('oauth_token')
                auth_url = f"https://us.etrade.com/e/t/etws/authorize?key={sandbox_key}&token={token}"
                print(f"✓ Authorization URL: {auth_url}")
                return True
                
            except Exception as e:
                print(f"✗ Failed: {e}")
                
    except Exception as e:
        print(f"✗ OAuth setup failed: {e}")
    
    return False

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv('config/api_keys.env')
    
    test_etrade_connectivity()
    test_oauth_request()