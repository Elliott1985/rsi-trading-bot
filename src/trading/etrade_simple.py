"""
Simple E*TRADE Broker Integration 
Basic functionality for testing and simulation
"""

import os
from typing import Dict, List, Any
from datetime import datetime
from src.utils.logger import setup_logger
from src.utils.config import Config

logger = setup_logger(__name__)

class ETradeBroker:
    """Simplified E*TRADE integration for testing"""
    
    def __init__(self, config: Config, sandbox: bool = True):
        self.config = config
        self.sandbox = sandbox
        self.authenticated = False
        self.account_key = "DEMO_ACCOUNT"
        
        # Get API credentials
        if sandbox:
            self.client_key = os.getenv('ETRADE_SANDBOX_KEY', config.api.etrade_client_key)
            self.client_secret = os.getenv('ETRADE_SANDBOX_SECRET', config.api.etrade_client_secret)
        else:
            self.client_key = os.getenv('ETRADE_PROD_KEY')
            self.client_secret = os.getenv('ETRADE_PROD_SECRET')
        
        logger.info(f"E*TRADE broker initialized ({'Sandbox' if sandbox else 'Production'} mode)")
        logger.info(f"API Key configured: {'Yes' if self.client_key else 'No'}")
    
    async def authenticate(self) -> bool:
        """Simple authentication check"""
        if self.client_key and self.client_secret:
            self.authenticated = True
            logger.info("✅ E*TRADE credentials found - ready for integration!")
            return True
        else:
            logger.error("❌ E*TRADE credentials not found")
            return False
    
    async def get_account_balance(self) -> Dict[str, float]:
        """Return demo account balance"""
        if self.sandbox:
            return {
                'total_value': 100000.00,
                'cash_available': 50000.00,
                'buying_power': 75000.00,
                'unrealized_pnl': 2500.00,
                'margin_used': 0.00
            }
        else:
            logger.warning("Production mode - would need OAuth authentication")
            return {'error': 'Production mode requires OAuth'}
    
    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Return simulated quote data"""
        # This would normally call E*TRADE API
        # For now, return demo data
        import random
        base_price = 150.0 if symbol == "AAPL" else 100.0
        
        return {
            'symbol': symbol,
            'bid': base_price - 0.05,
            'ask': base_price + 0.05,
            'last': base_price,
            'volume': random.randint(1000000, 5000000),
            'change': random.uniform(-5, 5),
            'change_pct': random.uniform(-3, 3),
            'high': base_price + random.uniform(0, 10),
            'low': base_price - random.uniform(0, 10),
            'timestamp': datetime.now()
        }
    
    async def place_order(self, symbol: str, action: str, quantity: int, 
                         order_type: str = 'MARKET', price: float = None) -> Dict[str, Any]:
        """Simulate order placement"""
        logger.info(f"{'SANDBOX' if self.sandbox else 'PRODUCTION'} order: {action} {quantity} {symbol}")
        
        return {
            'success': True,
            'order_id': f"{'DEMO' if self.sandbox else 'PROD'}_{int(datetime.now().timestamp())}",
            'symbol': symbol,
            'action': action,
            'quantity': quantity,
            'order_type': order_type,
            'price': price,
            'status': 'SIMULATED' if self.sandbox else 'NEEDS_OAUTH'
        }
    
    async def get_positions(self) -> List[Dict[str, Any]]:
        """Return demo positions"""
        if self.sandbox:
            return [
                {
                    'symbol': 'AAPL',
                    'quantity': 10,
                    'price_paid': 145.00,
                    'current_price': 150.00,
                    'market_value': 1500.00,
                    'unrealized_pnl': 50.00,
                    'product_type': 'EQUITY'
                }
            ]
        return []
    
    def is_market_open(self) -> bool:
        """Check if market is open (including pre-market and extended hours)"""
        now = datetime.now()
        if now.weekday() >= 5:  # Weekend
            return False
        # Extended hours: 4:00 AM - 8:00 PM ET (pre-market + regular + after-hours)
        return 4 <= now.hour <= 20
