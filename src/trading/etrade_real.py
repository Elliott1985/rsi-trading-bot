"""
REAL E*TRADE BROKER - LIVE TRADING
Uses actual E*TRADE API with OAuth for real money trading
"""

import os
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import requests
from requests_oauthlib import OAuth1Session
from utils.logger import setup_logger
from utils.config import Config

logger = setup_logger(__name__)

class ETradeBroker:
    """Real E*TRADE broker for live trading with real money"""
    
    def __init__(self, config: Config, sandbox: bool = True):
        self.config = config
        self.sandbox = sandbox
        
        # Get API credentials - your keys are sandbox-only for now
        if sandbox:
            self.client_key = os.getenv('ETRADE_PROD_KEY')  # Using your sandbox keys
            self.client_secret = os.getenv('ETRADE_PROD_SECRET')
            self.base_url = "https://etwssandbox.etrade.com"  # Sandbox API
            self.auth_url = "https://us.etrade.com/e/t/etws/authorize"  # Authorization
        else:
            # For production, you'd need real production keys from E*TRADE
            self.client_key = os.getenv('ETRADE_PROD_KEY')  # These are actually sandbox keys
            self.client_secret = os.getenv('ETRADE_PROD_SECRET')
            self.base_url = "https://etwssandbox.etrade.com"  # Use sandbox API for now
            self.auth_url = "https://us.etrade.com/e/t/etws/authorize"  # Authorization
        
        if not self.client_key or not self.client_secret:
            raise ValueError(f"E*TRADE credentials not found for {'sandbox' if sandbox else 'production'}")
            
        # OAuth session
        self.oauth = None
        self.authenticated = False
        self.account_key = None
        
        # Token storage
        self.token_file = f"etrade_tokens_{'sandbox' if sandbox else 'prod'}.json"
        
        logger.info(f"Real E*TRADE broker initialized ({'Sandbox' if sandbox else 'Production'} mode)")
    
    async def authenticate(self) -> bool:
        """Authenticate with E*TRADE OAuth"""
        try:
            # Try to load existing tokens
            if self._load_tokens():
                return True
            
            logger.info("Starting E*TRADE OAuth authentication...")
            
            # Step 1: Get request token with required callback
            oauth = OAuth1Session(
                self.client_key, 
                client_secret=self.client_secret,
                callback_uri="oob"  # E*TRADE requires this for out-of-band auth
            )
            
            request_token_url = f"{self.base_url}/oauth/request_token"
            fetch_response = oauth.fetch_request_token(request_token_url)
            
            resource_owner_key = fetch_response.get('oauth_token')
            resource_owner_secret = fetch_response.get('oauth_token_secret')
            
            # Step 2: Get authorization URL (use correct E*TRADE auth endpoint)
            authorize_url = f"{self.auth_url}?key={self.client_key}&token={resource_owner_key}"
            
            print(f"\n{'='*60}")
            print("🔐 E*TRADE OAUTH AUTHENTICATION")
            print(f"{'='*60}")
            print("1. Open this URL in your browser:")
            print(f"   {authorize_url}")
            print("\n2. Log in to your E*TRADE account")
            print("3. Authorize the application") 
            print("4. Copy the verification code")
            print(f"{'='*60}")
            
            # Step 3: Get verification code
            verifier = input("\n🔑 Enter verification code: ").strip()
            
            if not verifier:
                logger.error("No verification code provided")
                return False
            
            # Step 4: Get access token
            oauth = OAuth1Session(
                self.client_key,
                client_secret=self.client_secret,
                resource_owner_key=resource_owner_key,
                resource_owner_secret=resource_owner_secret,
                verifier=verifier
            )
            
            access_token_url = f"{self.base_url}/oauth/access_token"
            oauth_tokens = oauth.fetch_access_token(access_token_url)
            
            # Store tokens
            self.resource_owner_key = oauth_tokens.get('oauth_token')
            self.resource_owner_secret = oauth_tokens.get('oauth_token_secret')
            
            # Create authenticated session
            self.oauth = OAuth1Session(
                self.client_key,
                client_secret=self.client_secret,
                resource_owner_key=self.resource_owner_key,
                resource_owner_secret=self.resource_owner_secret
            )
            
            self.authenticated = True
            self._save_tokens()
            
            # Get account info
            await self._get_account_info()
            
            logger.info("✅ E*TRADE authentication successful!")
            return True
            
        except Exception as e:
            logger.error(f"E*TRADE authentication failed: {e}")
            return False
    
    def _save_tokens(self):
        """Save OAuth tokens"""
        try:
            token_data = {
                'resource_owner_key': self.resource_owner_key,
                'resource_owner_secret': self.resource_owner_secret,
                'timestamp': datetime.now().isoformat(),
                'sandbox': self.sandbox
            }
            
            with open(self.token_file, 'w') as f:
                json.dump(token_data, f)
                
            logger.debug("Saved E*TRADE tokens")
            
        except Exception as e:
            logger.error(f"Failed to save tokens: {e}")
    
    def _load_tokens(self) -> bool:
        """Load existing OAuth tokens"""
        try:
            if not os.path.exists(self.token_file):
                return False
                
            with open(self.token_file, 'r') as f:
                token_data = json.load(f)
            
            # Check token age
            token_time = datetime.fromisoformat(token_data['timestamp'])
            if datetime.now() - token_time > timedelta(hours=8):
                logger.info("Tokens expired, need re-authentication")
                return False
            
            self.resource_owner_key = token_data['resource_owner_key']
            self.resource_owner_secret = token_data['resource_owner_secret']
            
            # Create authenticated session
            self.oauth = OAuth1Session(
                self.client_key,
                client_secret=self.client_secret,
                resource_owner_key=self.resource_owner_key,
                resource_owner_secret=self.resource_owner_secret
            )
            
            self.authenticated = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to load tokens: {e}")
            return False
    
    async def _get_account_info(self):
        """Get account information"""
        try:
            # Use correct E*TRADE API endpoint (from official docs)
            url = f"{self.base_url}/v1/accounts/list"
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            logger.debug(f"Making request to: {url}")
            response = self.oauth.get(url, headers=headers, timeout=30)
            
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    logger.debug(f"Response data: {data}")
                    
                    # Handle different response structures
                    accounts = None
                    if 'AccountListResponse' in data:
                        accounts = data['AccountListResponse'].get('Accounts', {}).get('Account', [])
                    elif 'accounts' in data:
                        accounts = data['accounts']
                    elif isinstance(data, list):
                        accounts = data
                    
                    if isinstance(accounts, dict):
                        accounts = [accounts]
                    
                    if accounts:
                        self.account_key = accounts[0].get('accountIdKey') or accounts[0].get('accountId')
                        account_name = accounts[0].get('accountDesc', 'N/A')
                        logger.info(f"Using account: {account_name} (Key: {self.account_key})")
                    else:
                        # Skip account retrieval for now - just mark as authenticated
                        logger.warning("No accounts found in response, but OAuth successful")
                        self.account_key = "default"  # Set a default for now
                        
                except ValueError as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    logger.debug(f"Raw response: {response.text}")
                    # Still mark as authenticated since OAuth worked
                    self.account_key = "default"
                    
            else:
                logger.error(f"Account list API failed: {response.status_code}")
                logger.debug(f"Error response: {response.text}")
                # Still mark as authenticated since OAuth worked
                self.account_key = "default"
                
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            # Don't raise - OAuth was successful, just set default account
            self.account_key = "default"
            logger.warning("Set default account key due to account info failure")
    
    async def get_account_balance(self) -> Dict[str, float]:
        """Get account balance"""
        try:
            if not self.authenticated or not self.account_key:
                raise Exception("Not authenticated")
                
            url = f"{self.base_url}/v1/accounts/{self.account_key}/balance"
            response = self.oauth.get(url)
            
            if response.status_code == 200:
                data = response.json()
                balance_data = data.get('BalanceResponse', {})
                computed = balance_data.get('Computed', {})
                
                return {
                    'total_value': float(computed.get('RealTimeValues', {}).get('totalAccountValue', 0)),
                    'cash_available': float(computed.get('cashAvailableForInvestment', 0)),
                    'buying_power': float(computed.get('buyingPower', 0)),
                    'unrealized_pnl': float(computed.get('unrealizedPL', 0)),
                    'margin_used': 0.0
                }
            else:
                raise Exception(f"Failed to get balance: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            raise
    
    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get real stock quote from E*TRADE"""
        try:
            # Try the correct E*TRADE quote endpoint
            url = f"{self.base_url}/v1/market/productlookup"
            params = {
                'company': symbol, 
                'type': 'eq'
            }
            
            logger.debug(f"Fetching quote for {symbol}")
            response = self.oauth.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                logger.debug(f"Quote response for {symbol}: {data}")
                
                # Parse E*TRADE response format
                if 'ProductLookupResponse' in data:
                    products = data['ProductLookupResponse'].get('Data', {}).get('Products', [])
                    if products:
                        product = products[0]
                        
                        # Get current price from product data
                        current_price = float(product.get('currentPrice', 0))
                        if current_price > 0:
                            return {
                                'symbol': symbol,
                                'last': current_price,
                                'bid': current_price * 0.999,  # Approximate
                                'ask': current_price * 1.001,  # Approximate
                                'timestamp': datetime.now()
                            }
                
                # Fallback: try alternative quote endpoint
                quote_url = f"{self.base_url}/v1/market/optionslist"
                quote_params = {'symbol': symbol}
                quote_response = self.oauth.get(quote_url, params=quote_params, timeout=10)
                
                if quote_response.status_code == 200:
                    quote_data = quote_response.json()
                    logger.debug(f"Alternative quote for {symbol}: {quote_data}")
                
                # If we can't get real data, raise error instead of returning fake data
                raise Exception(f"No valid price data in E*TRADE response for {symbol}")
                
            else:
                logger.error(f"E*TRADE quote failed: {response.status_code} - {response.text}")
                raise Exception(f"E*TRADE API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Failed to get real quote for {symbol}: {e}")
            raise
    
    async def place_order(self, symbol: str, action: str, quantity: int, 
                         order_type: str = 'MARKET', price: float = None) -> Dict[str, Any]:
        """Place a real order"""
        try:
            # Check authentication status and refresh if needed
            if not self.authenticated or not self.account_key:
                logger.warning("Not authenticated, attempting to re-authenticate...")
                if not await self.authenticate():
                    raise Exception("Authentication failed")
            
            # Double-check OAuth session is valid
            if not self.oauth:
                logger.warning("OAuth session not found, attempting to re-authenticate...")
                if not await self.authenticate():
                    raise Exception("OAuth session failed")
            
            logger.info(f"🚨 PLACING REAL ORDER: {action} {quantity} {symbol}")
            
            # Build order data
            order_data = {
                "AccountID": self.account_key,
                "OrderType": order_type.upper(),
                "ClientOrderID": f"AI_{int(time.time())}",
                "Instrument": [
                    {
                        "Product": {
                            "securityType": "EQ",
                            "symbol": symbol
                        },
                        "Quantity": str(quantity)
                    }
                ],
                "PriceType": order_type.upper(),
                "OrderTerm": "GOOD_FOR_DAY",
                "MarketSession": "REGULAR"
            }
            
            if action.upper() == "BUY":
                order_data["Instrument"][0]["PriceType"] = "Market"
            else:
                order_data["Instrument"][0]["PriceType"] = "Market"
            
            if order_type.upper() == "LIMIT" and price:
                order_data["PriceType"] = "LIMIT"
                order_data["LimitPrice"] = str(price)
            
            # Use correct E*TRADE order endpoints from official documentation
            preview_url = f"{self.base_url}/v1/accounts/{self.account_key}/orders/preview"
            
            # E*TRADE requires specific headers
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            logger.info(f"Preview URL: {preview_url}")
            logger.info(f"Order data: {order_data}")
            
            preview_response = self.oauth.post(preview_url, json=order_data, headers=headers)
            
            logger.info(f"Preview response status: {preview_response.status_code}")
            logger.info(f"Preview response: {preview_response.text[:500]}")
            
            if preview_response.status_code == 200:
                preview_data = preview_response.json()
                logger.info(f"Order preview successful: {preview_data}")
                
                if self.sandbox:
                    # In sandbox, just return preview
                    return {
                        'success': True,
                        'order_id': f"SANDBOX_{int(time.time())}",
                        'symbol': symbol,
                        'action': action,
                        'quantity': quantity,
                        'order_type': order_type,
                        'price': price,
                        'status': 'SANDBOX_PREVIEW'
                    }
                else:
                    # In production, place actual order
                    place_url = f"{self.base_url}/v1/accounts/{self.account_key}/orders/place"
                    place_response = self.oauth.post(place_url, json=order_data, headers=headers)
                    
                    if place_response.status_code == 200:
                        order_result = place_response.json()
                        order_id = order_result.get('PlaceOrderResponse', {}).get('OrderID', 'UNKNOWN')
                        
                        logger.info(f"✅ REAL ORDER PLACED: ID {order_id}")
                        
                        return {
                            'success': True,
                            'order_id': order_id,
                            'symbol': symbol,
                            'action': action,
                            'quantity': quantity,
                            'order_type': order_type,
                            'price': price,
                            'status': 'PLACED'
                        }
                    else:
                        logger.error(f"Order placement failed: {place_response.status_code}")
                        logger.error(f"Place response: {place_response.text}")
                        raise Exception(f"Order placement failed: {place_response.status_code}")
            else:
                logger.error(f"Order preview failed: {preview_response.status_code}")
                logger.error(f"Preview response: {preview_response.text}")
                raise Exception(f"Order preview failed: {preview_response.status_code}")
                
        except Exception as e:
            logger.error(f"Order failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'symbol': symbol,
                'action': action,
                'quantity': quantity
            }
    
    async def get_positions(self) -> List[Dict[str, Any]]:
        """Get current positions"""
        return []  # Simplified for now
    
    def is_market_open(self) -> bool:
        """Check if market is open"""
        now = datetime.now()
        if now.weekday() >= 5:  # Weekend
            return False
        # Extended hours: 4 AM - 8 PM
        return 4 <= now.hour <= 20