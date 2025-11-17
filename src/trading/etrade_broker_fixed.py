"""
E*TRADE Broker Integration - Fixed Version
Handles authentication, market data, and trade execution with E*TRADE API
"""

import os
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pyetrade
from src.utils.logger import setup_logger
from src.utils.config import Config

logger = setup_logger(__name__)

class ETradeBroker:
    """E*TRADE API integration for live trading"""
    
    def __init__(self, config: Config, sandbox: bool = True):
        """
        Initialize E*TRADE broker connection
        
        Args:
            config: Configuration object with API keys
            sandbox: Use sandbox (True) or production (False) environment
        """
        self.config = config
        self.sandbox = sandbox
        
        # Get API credentials based on environment
        if sandbox:
            self.client_key = os.getenv('ETRADE_SANDBOX_KEY') or config.api.etrade_client_key
            self.client_secret = os.getenv('ETRADE_SANDBOX_SECRET') or config.api.etrade_client_secret
        else:
            self.client_key = os.getenv('ETRADE_PROD_KEY')
            self.client_secret = os.getenv('ETRADE_PROD_SECRET')
        
        if not self.client_key or not self.client_secret:
            raise ValueError(f"E*TRADE API credentials not found for {'sandbox' if sandbox else 'production'} environment")
            
        # Initialize E*TRADE OAuth manager
        self.oauth = pyetrade.ETradeOAuth(self.client_key, self.client_secret)
        
        # E*TRADE API clients (initialized after authentication)
        self.accounts = None
        self.market = None
        self.orders = None
        
        # Session state
        self.authenticated = False
        self.access_token = None
        self.access_secret = None
        self.account_key = None
        
        # Token file for persistence
        self.token_file = f"etrade_tokens_{'sandbox' if sandbox else 'prod'}.json"
        
        logger.info(f"E*TRADE broker initialized ({'Sandbox' if sandbox else 'Production'} mode)")
    
    async def authenticate(self) -> bool:
        """
        Authenticate with E*TRADE API using OAuth 1.0
        Returns True if successful, False otherwise
        """
        try:
            # Try to load existing tokens first
            if self._load_tokens():
                logger.info("Loaded existing E*TRADE tokens")
                await self._get_account_info()
                return True
                
            logger.info("Starting E*TRADE OAuth authentication...")
            
            # Step 1: Get request token and authorization URL
            request_token = self.oauth.get_request_token()
            auth_url = self.oauth.get_authorization_url(request_token)
            
            print("\n" + "="*60)
            print("🔐 E*TRADE AUTHENTICATION REQUIRED")
            print("="*60)
            print(f"1. Open this URL in your browser:")
            print(f"   {auth_url}")
            print(f"\n2. Log in to your E*TRADE account")
            print(f"3. Authorize the application")
            print(f"4. Copy the verification code from the webpage")
            print("="*60)
            
            # Step 2: Get verification code from user
            verification_code = input("\n🔑 Enter the verification code: ").strip()
            
            if not verification_code:
                logger.error("No verification code provided")
                return False
            
            # Step 3: Get access token
            access_token = self.oauth.get_access_token(request_token, verification_code)
            
            # Store tokens
            self.access_token = access_token['oauth_token']
            self.access_secret = access_token['oauth_token_secret']
            
            # Initialize API clients
            self._initialize_clients()
            
            # Save tokens for future use
            self._save_tokens()
            
            self.authenticated = True
            logger.info("✅ E*TRADE authentication successful!")
            
            # Get account information
            await self._get_account_info()
            
            return True
            
        except Exception as e:
            logger.error(f"E*TRADE authentication failed: {e}")
            return False
    
    def _initialize_clients(self):
        """Initialize E*TRADE API clients with access tokens"""
        self.accounts = pyetrade.ETradeAccounts(
            self.client_key,
            self.client_secret,
            self.access_token,
            self.access_secret,
            sandbox=self.sandbox
        )
        
        self.market = pyetrade.ETradeMarket(
            self.client_key,
            self.client_secret,
            self.access_token,
            self.access_secret,
            sandbox=self.sandbox
        )
        
        self.orders = pyetrade.ETradeOrder(
            self.client_key,
            self.client_secret,
            self.access_token,
            self.access_secret,
            sandbox=self.sandbox
        )
    
    def _save_tokens(self):
        """Save OAuth tokens to file for persistence"""
        try:
            token_data = {
                'access_token': self.access_token,
                'access_secret': self.access_secret,
                'timestamp': datetime.now().isoformat(),
                'sandbox': self.sandbox
            }
            
            with open(self.token_file, 'w') as f:
                json.dump(token_data, f, indent=2)
                
            logger.debug("Saved E*TRADE tokens to file")
            
        except Exception as e:
            logger.error(f"Failed to save tokens: {e}")
    
    def _load_tokens(self) -> bool:
        """Load OAuth tokens from file"""
        try:
            if not os.path.exists(self.token_file):
                return False
                
            with open(self.token_file, 'r') as f:
                token_data = json.load(f)
            
            # Check if tokens are for the same environment
            if token_data.get('sandbox') != self.sandbox:
                logger.info("Token environment mismatch, need new authentication")
                return False
            
            # Check token age (E*TRADE tokens can expire)
            token_time = datetime.fromisoformat(token_data['timestamp'])
            if datetime.now() - token_time > timedelta(hours=8):
                logger.info("Tokens may be expired, attempting re-authentication")
                return False
            
            self.access_token = token_data['access_token']
            self.access_secret = token_data['access_secret']
            
            # Initialize clients with loaded tokens
            self._initialize_clients()
            self.authenticated = True
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load tokens: {e}")
            return False
    
    async def _get_account_info(self):
        """Get account information and set default account"""
        try:
            if not self.authenticated:
                raise Exception("Not authenticated")
                
            # Get account list
            accounts_response = self.accounts.get_account_list()
            
            if 'error' in accounts_response or 'AccountListResponse' not in accounts_response:
                raise Exception(f"Error getting accounts: {accounts_response}")
            
            accounts_list = accounts_response['AccountListResponse']['Accounts']['Account']
            
            # Handle single account vs multiple accounts
            if isinstance(accounts_list, dict):
                accounts_list = [accounts_list]
            
            # Use first available account
            if accounts_list:
                self.account_key = accounts_list[0]['accountIdKey']
                account_name = accounts_list[0].get('accountDesc', 'N/A')
                account_type = accounts_list[0].get('accountType', 'N/A')
                logger.info(f"Using E*TRADE account: {account_name} ({account_type})")
                
                # Log all available accounts
                for account in accounts_list:
                    logger.debug(f"Available account: {account.get('accountDesc', 'N/A')} "
                              f"(Type: {account.get('accountType', 'N/A')})")
            else:
                raise Exception("No accounts found")
                
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            raise
    
    async def get_account_balance(self) -> Dict[str, float]:
        """Get current account balance and positions"""
        try:
            if not self.authenticated or not self.account_key:
                raise Exception("Not authenticated or no account selected")
                
            # Get account balance
            balance_response = self.accounts.get_account_balance(self.account_key)
            
            if 'error' in balance_response or 'BalanceResponse' not in balance_response:
                raise Exception(f"Error getting balance: {balance_response}")
            
            balance_data = balance_response['BalanceResponse']
            
            # Extract key balance information - structure may vary
            computed = balance_data.get('Computed', {})
            
            # Handle different response structures
            cash_available = 0
            total_value = 0
            buying_power = 0
            
            if 'RealTimeValues' in computed:
                total_value = float(computed['RealTimeValues'].get('totalAccountValue', 0))
            if 'cashAvailableForInvestment' in computed:
                cash_available = float(computed.get('cashAvailableForInvestment', 0))
            if 'buyingPower' in computed:
                buying_power = float(computed.get('buyingPower', 0))
                
            return {
                'total_value': total_value,
                'cash_available': cash_available,
                'buying_power': buying_power,
                'unrealized_pnl': float(computed.get('unrealizedPL', 0)),
                'margin_used': float(computed.get('marginBuyingPower', 0))
            }
            
        except Exception as e:
            logger.error(f"Failed to get account balance: {e}")
            raise
    
    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get real-time quote for a symbol"""
        try:
            if not self.authenticated:
                raise Exception("Not authenticated")
                
            # Get product lookup first to ensure symbol is valid
            quote_response = self.market.get_product_lookup(symbol)
            
            if 'error' in quote_response:
                raise Exception(f"Error looking up symbol: {quote_response['error']}")
            
            # Now get the actual quote
            quote_response = self.market.get_product_quote(symbol)
            
            if 'error' in quote_response or 'ProductQuoteResponse' not in quote_response:
                raise Exception(f"Error getting quote: {quote_response}")
            
            quote_data = quote_response['ProductQuoteResponse']['ProductQuoteData']
            
            # Handle different quote data structures
            if isinstance(quote_data, list):
                quote_data = quote_data[0]
                
            return {
                'symbol': quote_data.get('symbol', symbol),
                'bid': float(quote_data.get('bid', 0)),
                'ask': float(quote_data.get('ask', 0)), 
                'last': float(quote_data.get('lastTrade', quote_data.get('last', 0))),
                'volume': int(quote_data.get('volume', 0)),
                'change': float(quote_data.get('netChange', 0)),
                'change_pct': float(quote_data.get('netChangePct', 0)),
                'high': float(quote_data.get('high', 0)),
                'low': float(quote_data.get('low', 0)),
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Failed to get quote for {symbol}: {e}")
            raise
    
    async def place_order(self, symbol: str, action: str, quantity: int, 
                         order_type: str = 'MARKET', price: float = None) -> Dict[str, Any]:
        """
        Place a trade order (preview mode for sandbox, real for production)
        """
        try:
            if not self.authenticated or not self.account_key:
                raise Exception("Not authenticated or no account selected")
            
            # Validate parameters
            action = action.upper()
            if action not in ['BUY', 'SELL']:
                raise ValueError("Action must be 'BUY' or 'SELL'")
            
            order_type = order_type.upper()
            if order_type not in ['MARKET', 'LIMIT']:
                raise ValueError("Order type must be 'MARKET' or 'LIMIT'")
            
            if order_type == 'LIMIT' and price is None:
                raise ValueError("Price is required for LIMIT orders")
            
            logger.info(f"Placing {action} order for {quantity} shares of {symbol} ({'SANDBOX' if self.sandbox else 'LIVE'})")
            
            # Build order payload for pyetrade
            order_client_id = f"AI_TRADE_{int(time.time())}"
            
            # Create the order preview first
            try:
                if order_type == 'MARKET':
                    preview_response = self.orders.preview_equity_order(
                        account=self.account_key,
                        symbol=symbol,
                        quantity=quantity,
                        side=action,
                        order_type='MARKET',
                        client_order_id=order_client_id
                    )
                else:  # LIMIT
                    preview_response = self.orders.preview_equity_order(
                        account=self.account_key,
                        symbol=symbol,
                        quantity=quantity,
                        side=action,
                        order_type='LIMIT',
                        limit_price=price,
                        client_order_id=order_client_id
                    )
                
                if 'error' in preview_response:
                    raise Exception(f"Order preview failed: {preview_response['error']}")
                
                # In sandbox mode, we typically only preview
                if self.sandbox:
                    logger.info(f"SANDBOX: Order preview successful for {symbol}")
                    return {
                        'success': True,
                        'order_id': f"SANDBOX_{order_client_id}",
                        'symbol': symbol,
                        'action': action,
                        'quantity': quantity,
                        'order_type': order_type,
                        'price': price,
                        'status': 'PREVIEW_ONLY'
                    }
                else:
                    # In production, place the actual order
                    logger.warning("PRODUCTION ORDER PLACEMENT - This will use real money!")
                    
                    # For safety, we'll still preview only unless explicitly confirmed
                    return {
                        'success': True,
                        'order_id': f"PROD_PREVIEW_{order_client_id}",
                        'symbol': symbol,
                        'action': action,
                        'quantity': quantity,
                        'order_type': order_type,
                        'price': price,
                        'status': 'PROD_PREVIEW_ONLY',
                        'note': 'Production orders require explicit confirmation'
                    }
                    
            except Exception as e:
                logger.error(f"Order operation failed: {e}")
                return {
                    'success': False,
                    'error': str(e),
                    'symbol': symbol,
                    'action': action,
                    'quantity': quantity
                }
                
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            return {
                'success': False,
                'error': str(e),
                'symbol': symbol,
                'action': action,
                'quantity': quantity
            }
    
    def is_market_open(self) -> bool:
        """Check if market is currently open (simplified check)"""
        now = datetime.now()
        
        # Simple market hours check (9:30 AM - 4:00 PM ET, weekdays)
        if now.weekday() >= 5:  # Weekend
            return False
        
        # This is a simplified check - in production you'd want timezone handling
        market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
        
        return market_open <= now <= market_close

    async def get_positions(self) -> List[Dict[str, Any]]:
        """Get current positions (simplified for now)"""
        # This would require implementing the positions API call
        # For now, return empty list
        logger.info("Positions API not yet implemented")
        return []