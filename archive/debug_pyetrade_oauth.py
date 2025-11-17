#!/usr/bin/env python3
"""
Debug pyetrade OAuth to understand token structure
"""

import pyetrade
import os

# Load credentials
client_key = os.getenv('ETRADE_SANDBOX_KEY', 'your_key')
client_secret = os.getenv('ETRADE_SANDBOX_SECRET', 'your_secret')

print("🔍 Debugging PyETrade OAuth")
print("=" * 40)

try:
    oauth = pyetrade.ETradeOAuth(client_key, client_secret)
    
    print("🔧 Before get_request_token:")
    print(f"  Available attributes: {[attr for attr in dir(oauth) if not attr.startswith('_')]}")
    
    oauth.get_request_token()
    
    print("\n🔧 After get_request_token:")
    print(f"  resource_owner_key: {getattr(oauth, 'resource_owner_key', 'NOT_FOUND')}")
    print(f"  access_token: {getattr(oauth, 'access_token', 'NOT_FOUND')}")
    
    auth_url = f"{oauth.auth_token_url}?key={client_key}&token={oauth.resource_owner_key}"
    print(f"\n🔗 Authorization URL: {auth_url}")
    
    verifier = input("\n🔑 Enter verification code (or 'skip' to skip): ").strip()
    
    if verifier and verifier != 'skip':
        oauth.get_access_token(verifier)
        
        print("\n🔧 After get_access_token:")
        print(f"  All attributes: {[attr for attr in dir(oauth) if not attr.startswith('_')]}")
        print(f"  access_token: {getattr(oauth, 'access_token', 'NOT_FOUND')}")
        print(f"  resource_owner_key: {getattr(oauth, 'resource_owner_key', 'NOT_FOUND')}")
        
        # Print all non-private attributes
        for attr in dir(oauth):
            if not attr.startswith('_') and not callable(getattr(oauth, attr)):
                value = getattr(oauth, attr)
                if value and isinstance(value, str) and len(value) < 100:
                    print(f"  {attr}: {value}")
                elif value:
                    print(f"  {attr}: {type(value)} (length: {len(str(value))})")
    else:
        print("Skipping access token test")
    
except Exception as e:
    print(f"❌ Error: {e}")

print("\n✅ Debug complete")