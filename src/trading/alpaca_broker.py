"""
ALPACA BROKER - RELIABLE TRADING & MARKET DATA
Much more reliable than E*TRADE with excellent API support
"""

import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import alpaca_trade_api as tradeapi
from utils.logger import setup_logger
from utils.config import Config

logger = setup_logger(__name__)

class AlpacaBroker:
    """Alpaca broker for reliable trading with real-time market data"""
    
    def __init__(self, config: Config, paper_trading: bool = True):
        self.config = config
        self.paper_trading = paper_trading
        
        # Get Alpaca credentials
        if paper_trading:
            self.api_key = os.getenv('ALPACA_PAPER_KEY_ID')
            self.api_secret = os.getenv('ALPACA_PAPER_SECRET_KEY') 
            self.base_url = 'https://paper-api.alpaca.markets'  # Paper trading
        else:
            self.api_key = os.getenv('ALPACA_LIVE_KEY_ID')
            self.api_secret = os.getenv('ALPACA_LIVE_SECRET_KEY')
            self.base_url = 'https://api.alpaca.markets'  # Live trading
        
        if not self.api_key or not self.api_secret:
            raise ValueError(f"Alpaca credentials not found for {'paper' if paper_trading else 'live'} trading")
            
        # Initialize Alpaca API
        self.api = tradeapi.REST(
            self.api_key,
            self.api_secret, 
            self.base_url,
            api_version='v2'
        )
        
        self.authenticated = False
        self.account_info = None
        
        logger.info(f"Alpaca broker initialized ({'Paper' if paper_trading else 'Live'} trading)")
    
    async def authenticate(self) -> bool:
        """Authenticate with Alpaca (much simpler than E*TRADE!)"""
        try:
            # Test the connection by getting account info
            account = self.api.get_account()
            
            if account:
                self.authenticated = True
                self.account_info = account
                
                print(f"✅ Alpaca {'Paper' if self.paper_trading else 'Live'} Trading Connected!")
                print(f"   Account Status: {account.status}")
                print(f"   Buying Power: ${float(account.buying_power):,.2f}")
                print(f"   Cash: ${float(account.cash):,.2f}")
                
                logger.info("✅ Alpaca authentication successful!")
                return True
            else:
                logger.error("Failed to get account info")
                return False
                
        except Exception as e:
            logger.error(f"Alpaca authentication failed: {e}")
            return False
    
    async def get_account_balance(self) -> Dict[str, float]:
        """Get account balance"""
        try:
            if not self.authenticated:
                raise Exception("Not authenticated")
            
            account = self.api.get_account()
            
            return {
                'total_value': float(account.equity),
                'cash_available': float(account.cash),
                'buying_power': float(account.buying_power),
                'unrealized_pnl': float(account.unrealized_pl),
                'day_trade_buying_power': float(account.daytrading_buying_power or 0)
            }
            
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            raise
    
    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get real-time stock quote (much more reliable than E*TRADE!)"""
        try:
            # Get latest trade data
            latest_trade = self.api.get_latest_trade(symbol)
            
            if latest_trade:
                return {
                    'symbol': symbol,
                    'last': float(latest_trade.price),
                    'timestamp': latest_trade.timestamp,
                    'size': latest_trade.size,
                    'conditions': latest_trade.conditions
                }
            
            # Fallback to daily bars if latest trade unavailable  
            bars = self.api.get_bars(symbol, tradeapi.TimeFrame.Day, limit=1).df
            if not bars.empty:
                latest_price = float(bars.iloc[-1]['close'])
                return {
                    'symbol': symbol,
                    'last': latest_price,
                    'timestamp': datetime.now()
                }
            
            raise Exception(f"No price data available for {symbol}")
            
        except Exception as e:
            logger.error(f"Failed to get quote for {symbol}: {e}")
            raise
    
    async def place_order(self, symbol: str, action: str, quantity: int, 
                         order_type: str = 'market', price: float = None) -> Dict[str, Any]:
        """Place order (much simpler than E*TRADE!)"""
        try:
            if not self.authenticated:
                raise Exception("Not authenticated")
            
            logger.info(f"🚨 PLACING {'PAPER' if self.paper_trading else 'LIVE'} ORDER: {action} {quantity} {symbol}")
            
            # Convert action to Alpaca format
            side = 'buy' if action.upper() == 'BUY' else 'sell'
            
            # Place the order
            if order_type.lower() == 'market':
                order = self.api.submit_order(
                    symbol=symbol,
                    qty=quantity,
                    side=side,
                    type='market',
                    time_in_force='day'
                )
            else:  # limit order
                if not price:
                    raise ValueError("Price required for limit orders")
                    
                order = self.api.submit_order(
                    symbol=symbol,
                    qty=quantity,
                    side=side,
                    type='limit',
                    limit_price=price,
                    time_in_force='day'
                )
            
            if order:
                logger.info(f"✅ {'PAPER' if self.paper_trading else 'LIVE'} ORDER PLACED: ID {order.id}")
                
                return {
                    'success': True,
                    'order_id': order.id,
                    'symbol': symbol,
                    'action': action,
                    'quantity': quantity,
                    'order_type': order_type,
                    'price': price,
                    'status': order.status,
                    'filled_qty': order.filled_qty or 0,
                    'paper_trading': self.paper_trading
                }
            else:
                raise Exception("Order submission failed")
                
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
        try:
            positions = self.api.list_positions()
            
            result = []
            for pos in positions:
                result.append({
                    'symbol': pos.symbol,
                    'quantity': float(pos.qty),
                    'market_value': float(pos.market_value or 0),
                    'cost_basis': float(pos.cost_basis or 0),
                    'unrealized_pl': float(pos.unrealized_pl or 0),
                    'unrealized_plpc': float(pos.unrealized_plpc or 0),
                    'current_price': float(pos.current_price or 0),
                    'lastday_price': float(pos.lastday_price or 0),
                    'change_today': float(pos.change_today or 0)
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            return []
    
    def is_market_open(self) -> bool:
        """Check if market is open"""
        try:
            clock = self.api.get_clock()
            return clock.is_open
        except:
            # Fallback to time-based check
            now = datetime.now()
            if now.weekday() >= 5:  # Weekend
                return False
            # Market hours: 9:30 AM - 4:00 PM ET
            return (now.hour == 9 and now.minute >= 30) or (10 <= now.hour < 16)
    
    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Get order status"""
        try:
            order = self.api.get_order(order_id)
            
            return {
                'order_id': order.id,
                'status': order.status,
                'symbol': order.symbol,
                'qty': float(order.qty),
                'filled_qty': float(order.filled_qty or 0),
                'filled_avg_price': float(order.filled_avg_price or 0),
                'created_at': order.created_at,
                'updated_at': order.updated_at
            }
            
        except Exception as e:
            logger.error(f"Failed to get order status: {e}")
            return {'error': str(e)}