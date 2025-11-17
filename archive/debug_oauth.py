#!/usr/bin/env python3
"""
Debug E*TRADE OAuth - Step by step with detailed logging
"""

import os
from dotenv import load_dotenv
from requests_oauthlib import OAuth1Session
import json

# Load environment variables
load_dotenv('config/api_keys.env')

def main():
    print("🔐 E*TRADE OAuth Debug")
    print("="*50)
    
    # Get credentials
    client_key = os.getenv('ETRADE_PROD_KEY')
    client_secret = os.getenv('ETRADE_PROD_SECRET')
    
    print(f"API Key: {client_key}")
    print(f"API Secret: {client_secret[:10]}...")
    print()
    
    if not client_key or not client_secret:
        print("❌ Missing credentials!")
        return
    
    try:
        # Step 1: Request token
        print("🔄 Step 1: Getting request token...")
        oauth = OAuth1Session(
            client_key,
            client_secret=client_secret,
            callback_uri="oob"
        )
        
        request_token_url = "https://api.etrade.com/oauth/request_token"
        print(f"Request URL: {request_token_url}")
        
        fetch_response = oauth.fetch_request_token(request_token_url)
        print(f"✅ Request token response: {fetch_response}")
        
        resource_owner_key = fetch_response.get('oauth_token')
        resource_owner_secret = fetch_response.get('oauth_token_secret')
        
        print(f"Request token: {resource_owner_key}")
        print(f"Request secret: {resource_owner_secret[:10]}...")
        print()
        
        # Step 2: Authorization URL
        print("🔄 Step 2: Authorization URL")
        auth_url = f"https://us.etrade.com/e/t/etws/authorize?key={client_key}&token={resource_owner_key}"
        print(f"Authorization URL: {auth_url}")
        print()
        print("👉 Open this URL in your browser and get the verification code:")
        print(auth_url)
        print()
        
        # Step 3: Get verification code
        verifier = input("🔑 Enter verification code: ").strip()
        print(f"Verification code: {verifier}")
        print()
        
        # Step 4: Access token
        print("🔄 Step 3: Getting access token...")
        oauth = OAuth1Session(
            client_key,
            client_secret=client_secret,
            resource_owner_key=resource_owner_key,
            resource_owner_secret=resource_owner_secret,
            verifier=verifier
        )
        
        access_token_url = "https://api.etrade.com/oauth/access_token"
        print(f"Access token URL: {access_token_url}")
        
        oauth_tokens = oauth.fetch_access_token(access_token_url)
        print(f"✅ Access token response: {oauth_tokens}")
        
        access_token = oauth_tokens.get('oauth_token')
        access_secret = oauth_tokens.get('oauth_token_secret')
        
        print(f"Access token: {access_token}")
        print(f"Access secret: {access_secret[:10]}...")
        print()
        
        # Step 5: Test API call
        print("🔄 Step 4: Testing API call...")
        oauth = OAuth1Session(
            client_key,
            client_secret=client_secret,
            resource_owner_key=access_token,
            resource_owner_secret=access_secret
        )
        
        # Test account list
        test_url = "https://api.etrade.com/v1/user/api/account/list"
        print(f"Test URL: {test_url}")
        
        response = oauth.get(test_url)
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ API call successful!")
            try:
                data = response.json()
                print(f"Response data: {json.dumps(data, indent=2)[:500]}...")
            except:
                print(f"Response text: {response.text[:200]}...")
        else:
            print(f"❌ API call failed: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
        # Save tokens for testing
        token_data = {
            'resource_owner_key': access_token,
            'resource_owner_secret': access_secret,
            'timestamp': '2025-10-15T08:05:00.000000',
            'sandbox': False
        }
        
        with open('etrade_tokens_prod.json', 'w') as f:
            json.dump(token_data, f)
        print("💾 Saved tokens to etrade_tokens_prod.json")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()