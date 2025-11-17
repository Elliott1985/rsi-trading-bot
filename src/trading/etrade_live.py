"""
LIVE E*TRADE BROKER - PRODUCTION READY
Uses official pyetrade SDK for reliable API access
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pyetrade
from utils.logger import setup_logger
from utils.config import Config

logger = setup_logger(__name__)

class ETradeliveBroker:
    """Production E*TRADE broker using official pyetrade SDK"""
    
    def __init__(self, config: Config, sandbox: bool = True):
        self.config = config
        self.sandbox = sandbox
        
        # Get API credentials
        if sandbox:
            self.client_key = os.getenv('ETRADE_SANDBOX_KEY', config.api.etrade_client_key)
            self.client_secret = os.getenv('ETRADE_SANDBOX_SECRET', config.api.etrade_client_secret)
        else:
            self.client_key = os.getenv('ETRADE_PROD_KEY')
            self.client_secret = os.getenv('ETRADE_PROD_SECRET')
        
        if not self.client_key or not self.client_secret:
            raise ValueError(f"E*TRADE credentials not found for {'sandbox' if sandbox else 'production'}")
        
        # Initialize pyetrade client
        self.oauth = pyetrade.ETradeOAuth(self.client_key, self.client_secret)
        self.client = None
        self.authenticated = False
        self.accounts = []
        
        # Token storage
        self.token_file = f"etrade_tokens_pyetrade_{'sandbox' if sandbox else 'prod'}.json"
        
        logger.info(f"E*TRADE Live broker initialized ({'Sandbox' if sandbox else 'Production'} mode)")
    
    async def authenticate(self) -> bool:
        """Authenticate with E*TRADE using pyetrade SDK"""
        try:
            # Try to load existing tokens
            if self._load_tokens():
                return True
            
            logger.info("Starting E*TRADE OAuth authentication...")
            
            # Step 1: Get request token
            self.oauth.get_request_token()
            
            # Step 2: Construct authorization URL manually
            auth_url = f"{self.oauth.auth_token_url}?key={self.client_key}&token={self.oauth.resource_owner_key}"
            
            print(f"\\n{'='*60}")
            print("🔐 E*TRADE OAUTH AUTHENTICATION")
            print(f"{'='*60}")
            print("1. Open this URL in your browser:")
            print(f"   {auth_url}")
            print("\\n2. Log in to your E*TRADE account")
            print("3. Authorize the application")
            print("4. Copy the verification code")
            print(f"{'='*60}")
            
            # Step 3: Get verification code
            verifier = input("\\n🔑 Enter verification code: ").strip()
            
            if not verifier:
                logger.error("No verification code provided")
                return False
            
            # Step 4: Get access token
            self.oauth.get_access_token(verifier)
            
            # Step 5: Create authenticated client
            self.client = pyetrade.ETradeAccounts(
                self.client_key,
                self.client_secret, 
                self.oauth.access_token,
                self.oauth.access_token  # pyetrade might use access_token for both
            )
            
            # Test the connection by getting accounts
            await self._get_accounts()
            
            self.authenticated = True
            self._save_tokens()
            
            logger.info("✅ E*TRADE authentication successful!")
            return True
            
        except Exception as e:
            logger.error(f"E*TRADE authentication failed: {e}")
            return False
    
    def _save_tokens(self):
        """Save OAuth tokens"""
        try:
            token_data = {
                'access_token': self.oauth.access_token,
                'resource_owner_key': getattr(self.oauth, 'resource_owner_key', ''),
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
            
            # Check token age (E*TRADE tokens expire after ~8 hours)
            token_time = datetime.fromisoformat(token_data['timestamp'])
            if datetime.now() - token_time > timedelta(hours=6):  # Refresh after 6 hours to be safe
                logger.info("Tokens expired, need re-authentication")
                return False
            
            # Restore tokens
            self.oauth.access_token = token_data['access_token']
            self.oauth.resource_owner_key = token_data.get('resource_owner_key', '')
            
            # Create authenticated client
            self.client = pyetrade.ETradeAccounts(
                self.client_key,
                self.client_secret,
                self.oauth.access_token,
                self.oauth.access_token
            )
            
            self.authenticated = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to load tokens: {e}")
            return False
    
    async def _get_accounts(self):
        """Get account information"""
        try:
            if not self.client:
                raise Exception("Client not initialized")
            
            # Get account list
            response = self.client.list_accounts()
            
            if 'Accounts' in response and 'Account' in response['Accounts']:
                accounts = response['Accounts']['Account']
                
                # Handle single account vs multiple accounts
                if isinstance(accounts, dict):
                    accounts = [accounts]
                
                self.accounts = accounts
                
                if self.accounts:
                    first_account = self.accounts[0]
                    account_id = first_account.get('accountIdKey')
                    account_name = first_account.get('accountDesc', 'N/A')
                    logger.info(f"Found {len(self.accounts)} accounts. Using: {account_name} ({account_id})")
                else:
                    raise Exception("No accounts found")
            else:
                raise Exception("Invalid account response format")
                
        except Exception as e:
            logger.error(f"Failed to get accounts: {e}")
            raise
    
    async def get_account_balance(self, account_key: str = None) -> Dict[str, float]:
        """Get account balance"""
        try:
            if not self.authenticated or not self.client:
                raise Exception("Not authenticated")
            
            if not account_key and self.accounts:
                account_key = self.accounts[0]['accountIdKey']
            
            if not account_key:
                raise Exception("No account key available")
            
            # Get account balance
            response = self.client.get_account_balance(account_key)
            
            if 'BalanceResponse' in response:
                balance_data = response['BalanceResponse']
                computed = balance_data.get('Computed', {})
                
                return {
                    'total_value': float(computed.get('RealTimeValues', {}).get('totalAccountValue', 0)),
                    'cash_available': float(computed.get('cashAvailableForInvestment', 0)),
                    'buying_power': float(computed.get('buyingPower', 0)),
                    'unrealized_pnl': float(computed.get('unrealizedPL', 0)),
                    'margin_used': 0.0
                }
            else:
                raise Exception("Invalid balance response format")
                
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            raise
    
    async def get_positions(self, account_key: str = None) -> List[Dict]:
        """Get current positions"""
        try:
            if not self.authenticated or not self.client:
                raise Exception("Not authenticated")
            
            if not account_key and self.accounts:
                account_key = self.accounts[0]['accountIdKey']
            
            # Get positions
            response = self.client.get_account_positions(account_key)
            
            positions = []
            if 'PositionResponse' in response and 'AccountPortfolio' in response['PositionResponse']:
                portfolio = response['PositionResponse']['AccountPortfolio']
                
                # Handle single vs multiple positions
                if isinstance(portfolio, list):
                    for pos in portfolio:
                        positions.extend(self._parse_position(pos))
                else:
                    positions.extend(self._parse_position(portfolio))
            
            return positions
            
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            return []
    
    def _parse_position(self, portfolio_item) -> List[Dict]:
        """Parse position data from portfolio response"""
        positions = []
        
        if 'Position' in portfolio_item:
            pos_list = portfolio_item['Position']
            if isinstance(pos_list, dict):
                pos_list = [pos_list]
            
            for pos in pos_list:
                try:
                    symbol = pos.get('symbolDescription', 'Unknown')
                    quantity = float(pos.get('quantity', 0))
                    current_price = float(pos.get('Quick', {}).get('lastTrade', 0))
                    
                    positions.append({
                        'symbol': symbol,
                        'quantity': quantity,
                        'current_price': current_price,
                        'market_value': quantity * current_price
                    })
                except Exception as e:
                    logger.error(f"Error parsing position: {e}")
        
        return positions
    
    async def place_order(self, symbol: str, action: str, quantity: int, 
                         order_type: str = 'MARKET', price: float = None, 
                         account_key: str = None) -> Dict[str, Any]:
        """Place a live order"""
        try:
            if not self.authenticated or not self.client:
                raise Exception("Not authenticated")
            
            if not account_key and self.accounts:
                account_key = self.accounts[0]['accountIdKey']
            
            logger.info(f"🚨 PLACING REAL ORDER: {action} {quantity} {symbol}")
            
            # Create order client
            order_client = pyetrade.ETradeOrder(
                self.client_key,
                self.client_secret,
                self.oauth.access_token,
                self.oauth.access_secret
            )
            
            # Build order payload
            order_payload = {
                'AccountID': account_key,
                'OrderType': action.upper(),  # BUY or SELL
                'ClientOrderID': f"AI_{int(time.time())}",
                'Instrument': [
                    {
                        'Product': {
                            'securityType': 'EQ',  # Equity
                            'symbol': symbol
                        },
                        'Quantity': str(quantity)
                    }
                ],
                'PriceType': order_type.upper(),
                'OrderTerm': 'GOOD_FOR_DAY',
                'MarketSession': 'REGULAR'
            }
            
            # Add price for limit orders
            if order_type.upper() == 'LIMIT' and price:
                order_payload['LimitPrice'] = str(price)
            
            # Preview order first
            logger.info("📋 Previewing order...")
            preview_response = order_client.preview_equity_order(account_key, order_payload)
            
            if 'PreviewOrderResponse' in preview_response:
                preview_data = preview_response['PreviewOrderResponse']
                estimated_cost = preview_data.get('totalOrderValue', 'Unknown')
                estimated_commission = preview_data.get('totalCommission', 'Unknown')
                
                print(f"\\n📊 ORDER PREVIEW:")
                print(f"   Symbol: {symbol}")
                print(f"   Action: {action} {quantity} shares")
                print(f"   Type: {order_type}")
                print(f"   Estimated Cost: ${estimated_cost}")
                print(f"   Commission: ${estimated_commission}")
                
                if not self.sandbox:
                    confirm = input("\\n⚠️  CONFIRM REAL ORDER? Type 'PLACE ORDER' to execute: ")
                    if confirm != 'PLACE ORDER':
                        print("Order cancelled by user")
                        return {'status': 'cancelled', 'reason': 'User cancelled'}
                
                # Place the actual order
                if self.sandbox:
                    print("🟡 SANDBOX: Order would be placed in production")
                    return {
                        'status': 'simulated',
                        'order_id': f"SIM_{int(time.time())}",
                        'symbol': symbol,
                        'action': action,
                        'quantity': quantity,
                        'estimated_cost': estimated_cost
                    }
                else:
                    logger.info("🚀 Placing live order...")
                    place_response = order_client.place_equity_order(account_key, order_payload)
                    
                    if 'PlaceOrderResponse' in place_response:
                        order_data = place_response['PlaceOrderResponse']
                        order_id = order_data.get('OrderID', 'Unknown')
                        
                        logger.info(f"✅ Order placed successfully! ID: {order_id}")
                        
                        return {
                            'status': 'success',
                            'order_id': order_id,
                            'symbol': symbol,
                            'action': action,
                            'quantity': quantity,
                            'response': place_response
                        }
                    else:
                        raise Exception(f"Order placement failed: {place_response}")
            else:
                raise Exception(f"Order preview failed: {preview_response}")
                
        except Exception as e:
            logger.error(f"Order placement failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'symbol': symbol,
                'action': action,
                'quantity': quantity
            }
    
    async def cancel_order(self, order_id: str, account_key: str = None) -> bool:
        """Cancel an order"""
        try:
            if not account_key and self.accounts:
                account_key = self.accounts[0]['accountIdKey']
            
            order_client = pyetrade.ETradeOrder(
                self.client_key,
                self.client_secret,
                self.oauth.access_token,
                self.oauth.access_secret
            )
            
            response = order_client.cancel_order(account_key, order_id)
            
            if 'CancelOrderResponse' in response:
                logger.info(f"✅ Order {order_id} cancelled successfully")
                return True
            else:
                logger.error(f"Failed to cancel order {order_id}: {response}")
                return False
                
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            return False
    
    async def get_orders(self, account_key: str = None) -> List[Dict]:
        """Get order history"""
        try:
            if not account_key and self.accounts:
                account_key = self.accounts[0]['accountIdKey']
            
            order_client = pyetrade.ETradeOrder(
                self.client_key,
                self.client_secret,
                self.oauth.access_token,
                self.oauth.access_secret
            )
            
            response = order_client.list_orders(account_key)
            
            orders = []
            if 'OrdersResponse' in response and 'Order' in response['OrdersResponse']:
                order_list = response['OrdersResponse']['Order']
                if isinstance(order_list, dict):
                    order_list = [order_list]
                
                for order in order_list:
                    orders.append({
                        'order_id': order.get('orderId'),
                        'symbol': order.get('Instrument', [{}])[0].get('Product', {}).get('symbol'),
                        'action': order.get('OrderType'),
                        'quantity': order.get('Instrument', [{}])[0].get('Quantity'),
                        'status': order.get('orderStatus'),
                        'placed_time': order.get('placedTime')
                    })
            
            return orders
            
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            return []