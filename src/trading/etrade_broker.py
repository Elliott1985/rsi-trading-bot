"""
E*TRADE Broker Integration
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
        
        # Get API credentials
        self.client_key = config.api.etrade_client_key
        self.client_secret = config.api.etrade_client_secret
        
        if not self.client_key or not self.client_secret:
            raise ValueError("E*TRADE API credentials not found in configuration")
            
        # Initialize E*TRADE clients  
        self.oauth = pyetrade.ETradeOAuth(
            self.client_key,
            self.client_secret
        )
        
        self.accounts = None
        self.market = None
        self.orders = None
        
        # Session state
        self.authenticated = False
        self.access_token = None
        self.access_secret = None
        self.account_key = None
        
        # Token file for persistence
        self.token_file = "etrade_tokens.json"
        
        logger.info(f"E*TRADE broker initialized (Sandbox: {sandbox})")
    
    async def authenticate(self) -> bool:
        """
        Authenticate with E*TRADE API using OAuth 1.0
        Returns True if successful, False otherwise
        """
        try:
            # Try to load existing tokens first
            if self._load_tokens():
                logger.info("Loaded existing E*TRADE tokens")
                return True
                
            logger.info("Starting E*TRADE OAuth authentication...")
            
            # Step 1: Get request token
            self.oauth.get_request_token()
            
            # Step 2: Get authorization URL
            auth_url = self.oauth.get_authorization_url()
            
            print("\n" + "="*60)
            print("E*TRADE AUTHENTICATION REQUIRED")
            print("="*60)
            print(f"1. Open this URL in your browser:")
            print(f"   {auth_url}")
            print(f"\n2. Log in to your E*TRADE account")
            print(f"3. Authorize the application")
            print(f"4. Copy the verification code from the webpage")
            print("="*60)
            
            # Step 3: Get verification code from user
            verification_code = input("\nEnter the verification code: ").strip()
            
            if not verification_code:
                logger.error("No verification code provided")
                return False
            
            # Step 4: Get access token
            self.oauth.get_access_token(verification_code)
            
            # Store tokens
            self.access_token = self.oauth.access_token
            self.access_secret = self.oauth.access_secret
            
            # Initialize API clients
            self._initialize_clients()
            
            # Save tokens for future use
            self._save_tokens()
            
            self.authenticated = True
            logger.info("E*TRADE authentication successful!")
            
            # Get account information
            await self._get_account_info()
            
            return True
            
        except Exception as e:
            logger.error(f"E*TRADE authentication failed: {e}")
            return False
    
    def _initialize_clients(self):
        """Initialize E*TRADE API clients with access tokens"""
        self.accounts = pyetrade.ETradeAccounts(
            client_key=self.client_key,
            client_secret=self.client_secret,
            resource_owner_key=self.access_token,
            resource_owner_secret=self.access_secret,
            sandbox=self.sandbox
        )
        
        self.market = pyetrade.ETradeMarket(
            client_key=self.client_key,
            client_secret=self.client_secret,
            resource_owner_key=self.access_token,
            resource_owner_secret=self.access_secret,
            sandbox=self.sandbox
        )
        
        self.orders = pyetrade.ETradeOrder(
            client_key=self.client_key,
            client_secret=self.client_secret,
            resource_owner_key=self.access_token,
            resource_owner_secret=self.access_secret,
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
            
            # Check token age (E*TRADE tokens expire after inactivity)
            token_time = datetime.fromisoformat(token_data['timestamp'])
            if datetime.now() - token_time > timedelta(hours=12):
                logger.info("Tokens are old, need re-authentication")
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
            accounts_response = self.accounts.get_accounts()
            
            if 'error' in accounts_response:
                raise Exception(f"Error getting accounts: {accounts_response['error']}")
            
            accounts_data = accounts_response['GetAccountsResponse']['Accounts']['Account']
            
            # Handle single account vs multiple accounts
            if isinstance(accounts_data, dict):
                accounts_data = [accounts_data]
            
            # Use first available account
            if accounts_data:
                self.account_key = accounts_data[0]['accountIdKey']
                account_name = accounts_data[0].get('accountDesc', 'N/A')
                logger.info(f"Using E*TRADE account: {account_name}")
                
                # Log account details
                for account in accounts_data:
                    logger.info(f"Available account: {account.get('accountDesc', 'N/A')} "
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
            
            if 'error' in balance_response:
                raise Exception(f"Error getting balance: {balance_response['error']}")
            
            balance_data = balance_response['GetAccountBalanceResponse']
            
            # Extract key balance information
            computed = balance_data.get('Computed', {})
            
            return {
                'total_value': float(computed.get('RealTimeValues', {}).get('totalAccountValue', 0)),
                'cash_available': float(computed.get('cashAvailableForInvestment', 0)),
                'buying_power': float(computed.get('buyingPower', 0)),
                'unrealized_pnl': float(computed.get('unrealizedPL', 0)),
                'margin_used': float(computed.get('marginBuyingPower', 0))
            }
            
        except Exception as e:
            logger.error(f"Failed to get account balance: {e}")
            raise
    
    async def get_positions(self) -> List[Dict[str, Any]]:
        """Get current positions"""
        try:
            if not self.authenticated or not self.account_key:
                raise Exception("Not authenticated or no account selected")
                
            # Get account positions
            positions_response = self.accounts.get_account_positions(self.account_key)
            
            if 'error' in positions_response:
                logger.warning(f"Error getting positions: {positions_response['error']}")
                return []
            
            positions_data = positions_response.get('GetAccountPositionsResponse', {})
            account_positions = positions_data.get('AccountPositions', {})
            
            if not account_positions:
                return []
            
            positions = account_positions.get('Position', [])
            
            # Handle single position vs multiple positions
            if isinstance(positions, dict):
                positions = [positions]
            
            formatted_positions = []
            for pos in positions:
                product_info = pos.get('ProductInfo', {})
                position_info = pos.get('Position', {})
                
                formatted_positions.append({
                    'symbol': product_info.get('symbol', ''),
                    'quantity': float(position_info.get('quantity', 0)),
                    'price_paid': float(position_info.get('pricePaid', 0)),
                    'current_price': float(position_info.get('currentPrice', 0)),
                    'market_value': float(position_info.get('marketValue', 0)),
                    'unrealized_pnl': float(position_info.get('unrealizedPL', 0)),
                    'product_type': product_info.get('securityType', ''),
                })
            
            return formatted_positions
            
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            return []
    
    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get real-time quote for a symbol"""
        try:
            if not self.authenticated:
                raise Exception("Not authenticated")
                
            quote_response = self.market.get_product_quote(symbol)
            
            if 'error' in quote_response:
                raise Exception(f"Error getting quote: {quote_response['error']}")
            
            quote_data = quote_response['GetProductQuoteResponse']['ProductQuoteData']
            
            return {
                'symbol': quote_data.get('symbol', symbol),
                'bid': float(quote_data.get('bid', 0)),
                'ask': float(quote_data.get('ask', 0)),
                'last': float(quote_data.get('lastTrade', 0)),
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
        Place a trade order
        
        Args:
            symbol: Stock symbol
            action: 'BUY' or 'SELL'
            quantity: Number of shares
            order_type: 'MARKET' or 'LIMIT'
            price: Limit price (required for LIMIT orders)
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
            
            logger.info(f"Placing {action} order for {quantity} shares of {symbol}")
            
            # Build order payload
            order_data = {
                'orderType': order_type,
                'clientOrderID': f"AI_{int(time.time())}",
                'priceType': order_type,
                'quantityType': 'QUANTITY',
                'instruments': [{
                    'symbol': symbol,
                    'quantity': quantity,
                    'action': action,
                    'quantityType': 'QUANTITY'
                }]
            }
            
            if order_type == 'LIMIT':
                order_data['limitPrice'] = price
            
            # Preview order first
            preview_response = self.orders.preview_equity_order(
                account_key=self.account_key,
                **order_data
            )
            
            if 'error' in preview_response:
                raise Exception(f"Order preview failed: {preview_response['error']}")
            
            # Check if we're in production mode and actually place the order
            if not self.sandbox:
                # In production, place the actual order
                order_response = self.orders.place_equity_order(
                    account_key=self.account_key,
                    **order_data
                )
                
                if 'error' in order_response:
                    raise Exception(f"Order placement failed: {order_response['error']}")
                
                order_id = order_response['PlaceEquityOrderResponse']['orderID']
                logger.info(f"Order placed successfully. Order ID: {order_id}")
                
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
                # In sandbox mode, just return the preview
                logger.info(f"SANDBOX MODE: Order preview successful for {symbol}")
                
                return {
                    'success': True,
                    'order_id': f"SANDBOX_{int(time.time())}",
                    'symbol': symbol,
                    'action': action,
                    'quantity': quantity,
                    'order_type': order_type,
                    'price': price,
                    'status': 'PREVIEW_ONLY'
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
    
    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Get status of an order"""
        try:
            if not self.authenticated or not self.account_key:
                raise Exception("Not authenticated or no account selected")
            
            # Get order details
            orders_response = self.orders.get_order_list(self.account_key)
            
            if 'error' in orders_response:
                raise Exception(f"Error getting orders: {orders_response['error']}")
            
            # Find the specific order
            orders_data = orders_response.get('GetOrderListResponse', {})
            orders_list = orders_data.get('OrderList', {}).get('Order', [])
            
            if isinstance(orders_list, dict):
                orders_list = [orders_list]
            
            for order in orders_list:
                if str(order.get('orderID')) == str(order_id):
                    return {
                        'order_id': order.get('orderID'),
                        'symbol': order.get('symbol'),
                        'status': order.get('orderStatus'),
                        'quantity': int(order.get('quantity', 0)),
                        'filled_quantity': int(order.get('quantityExecuted', 0)),
                        'price': float(order.get('limitPrice', 0)),
                        'order_type': order.get('orderType'),
                        'timestamp': order.get('orderPlacedTime')
                    }
            
            return {'error': f'Order {order_id} not found'}
            
        except Exception as e:
            logger.error(f"Failed to get order status: {e}")
            return {'error': str(e)}
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        try:
            if not self.authenticated or not self.account_key:
                raise Exception("Not authenticated or no account selected")
            
            cancel_response = self.orders.cancel_order(self.account_key, order_id)
            
            if 'error' in cancel_response:
                logger.error(f"Error canceling order {order_id}: {cancel_response['error']}")
                return False
            
            logger.info(f"Order {order_id} canceled successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            return False
    
    def is_market_open(self) -> bool:
        """Check if market is currently open"""
        now = datetime.now()
        
        # Simple market hours check (9:30 AM - 4:00 PM ET, weekdays)
        if now.weekday() >= 5:  # Weekend
            return False
        
        market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
        
        return market_open <= now <= market_close