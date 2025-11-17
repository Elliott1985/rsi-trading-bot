#!/usr/bin/env python3
"""
Alpaca API Client
Handles all interactions with Alpaca for trading and market data.
"""

try:
    # Try new alpaca-py library first
    from alpaca.trading.client import TradingClient
    from alpaca.data.historical import CryptoHistoricalDataClient, StockHistoricalDataClient
    from alpaca.data.requests import CryptoBarsRequest, StockBarsRequest
    from alpaca.data.timeframe import TimeFrame
    from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
    from alpaca.trading.enums import OrderSide as AlpacaOrderSide, TimeInForce as AlpacaTimeInForce
    NEW_ALPACA = True
except ImportError:
    # Fallback to old library
    import alpaca_trade_api as tradeapi
    NEW_ALPACA = False

import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from enum import Enum
import time

class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"

class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"

class TimeInForce(Enum):
    DAY = "day"
    GTC = "gtc"  # Good Till Canceled
    IOC = "ioc"  # Immediate Or Cancel
    FOK = "fok"  # Fill Or Kill

@dataclass
class Position:
    """Portfolio position data"""
    symbol: str
    qty: float
    side: str
    market_value: float
    cost_basis: float
    unrealized_pl: float
    unrealized_plpc: float
    avg_entry_price: float

@dataclass
class Order:
    """Order data"""
    id: str
    symbol: str
    qty: float
    side: str
    order_type: str
    status: str
    filled_qty: float
    filled_avg_price: float
    created_at: datetime
    updated_at: datetime

@dataclass
class AccountInfo:
    """Account information"""
    buying_power: float
    portfolio_value: float
    equity: float
    long_market_value: float
    short_market_value: float
    cash: float
    day_trading_buying_power: float
    status: str

class AlpacaClient:
    """Alpaca API client for trading operations"""
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.logger = logging.getLogger(__name__)
        
        # Get API credentials
        credentials = config_manager.get_api_credentials()
        
        # Initialize Alpaca API with library detection
        try:
            if NEW_ALPACA:
                # Use new alpaca-py library
                self.trading_client = TradingClient(
                    credentials['ALPACA_API_KEY'],
                    credentials['ALPACA_SECRET_KEY'],
                    paper=False  # Set to False for live trading
                )
                self.crypto_data_client = CryptoHistoricalDataClient()
                self.stock_data_client = StockHistoricalDataClient(
                    credentials['ALPACA_API_KEY'],
                    credentials['ALPACA_SECRET_KEY']
                )
                
                # Test connection
                account = self.trading_client.get_account()
                self.logger.info(f"Connected to Alpaca (new API) - Account Status: {account.status}")
                
            else:
                # Fallback to old library
                self.api = tradeapi.REST(
                    credentials['ALPACA_API_KEY'],
                    credentials['ALPACA_SECRET_KEY'],
                    'https://api.alpaca.markets',
                    api_version='v2'
                )
                
                # Test connection
                account = self.api.get_account()
                self.logger.info(f"Connected to Alpaca (old API) - Account Status: {account.status}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Alpaca API: {e}")
            raise
    
    def get_account(self) -> AccountInfo:
        """Get current account information"""
        try:
            if NEW_ALPACA:
                account = self.trading_client.get_account()
            else:
                account = self.api.get_account()
            
            return AccountInfo(
                buying_power=float(account.buying_power),
                portfolio_value=float(account.portfolio_value),
                equity=float(account.equity),
                long_market_value=float(account.long_market_value),
                short_market_value=float(account.short_market_value),
                cash=float(account.cash),
                day_trading_buying_power=float(account.daytrading_buying_power),
                status=str(account.status)
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get account info: {e}")
            raise
    
    def get_positions(self) -> List[Position]:
        """Get all current positions"""
        try:
            if NEW_ALPACA:
                positions = self.trading_client.get_all_positions()
            else:
                positions = self.api.list_positions()
            
            result = []
            for pos in positions:
                result.append(Position(
                    symbol=pos.symbol,
                    qty=float(pos.qty),
                    side=pos.side,
                    market_value=float(pos.market_value),
                    cost_basis=float(pos.cost_basis),
                    unrealized_pl=float(pos.unrealized_pl),
                    unrealized_plpc=float(pos.unrealized_plpc),
                    avg_entry_price=float(pos.avg_entry_price)
                ))
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to get positions: {e}")
            return []
    
    def get_orders(self, status: str = "all", limit: int = 100) -> List[Order]:
        """Get orders with optional status filter"""
        try:
            if NEW_ALPACA:
                from alpaca.trading.enums import QueryOrderStatus
                # Convert status string to enum if needed
                if status == "open":
                    order_status = QueryOrderStatus.OPEN
                elif status == "closed":
                    order_status = QueryOrderStatus.CLOSED
                else:
                    order_status = QueryOrderStatus.ALL
                
                from alpaca.trading.requests import GetOrdersRequest
                request = GetOrdersRequest(status=order_status, limit=limit)
                orders = self.trading_client.get_orders(request)
            else:
                orders = self.api.list_orders(status=status, limit=limit)
            
            result = []
            for order in orders:
                result.append(Order(
                    id=str(order.id),
                    symbol=order.symbol,
                    qty=float(order.qty),
                    side=order.side.value if hasattr(order.side, 'value') else str(order.side),
                    order_type=order.order_type.value if hasattr(order.order_type, 'value') else str(order.order_type),
                    status=order.status.value if hasattr(order.status, 'value') else str(order.status),
                    filled_qty=float(order.filled_qty or 0),
                    filled_avg_price=float(order.filled_avg_price or 0) if order.filled_avg_price else 0.0,
                    created_at=order.created_at,
                    updated_at=order.updated_at
                ))
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to get orders: {e}")
            return []
    
    def get_bars_new(self, symbol: str, timeframe: str = '1Day', limit: int = 100, retry_count: int = 3) -> Optional[pd.DataFrame]:
        """Get historical bars using new alpaca-py library with retry logic"""
        for attempt in range(retry_count):
            try:
                # Convert timeframe
                if timeframe == '1Day':
                    tf = TimeFrame.Day
                elif timeframe == '1Hour':
                    tf = TimeFrame.Hour
                elif timeframe == '1Min':
                    tf = TimeFrame.Minute
                else:
                    tf = TimeFrame.Day
                
                is_crypto = '/' in symbol or symbol.endswith('USD')
                
                # Calculate date range - use date objects only (no time) for Alpaca API
                end_date = datetime.now().date()
                start_date = (datetime.now() - timedelta(days=min(limit * 2, 365))).date()
                
                if attempt == 0:
                    self.logger.info(f"New API: Requesting {symbol} ({'crypto' if is_crypto else 'stock'}) from {start_date} to {end_date}")
                else:
                    self.logger.info(f"Retry attempt {attempt + 1}/{retry_count} for {symbol}")
                
                if is_crypto:
                    request = CryptoBarsRequest(
                        symbol_or_symbols=[symbol],
                        timeframe=tf,
                        start=start_date,
                        end=end_date
                    )
                    bars_response = self.crypto_data_client.get_crypto_bars(request)
                    bars = bars_response[symbol]
                else:
                    request = StockBarsRequest(
                        symbol_or_symbols=[symbol],
                        timeframe=tf,
                        start=start_date,
                        end=end_date
                    )
                    bars_response = self.stock_data_client.get_stock_bars(request)
                    bars = bars_response[symbol]
                
                if not bars or len(bars) == 0:
                    self.logger.warning(f"No bars returned from new API for {symbol}")
                    return None
                
                # Convert to DataFrame
                data = []
                for bar in bars:
                    data.append({
                        'timestamp': bar.timestamp,
                        'open': float(bar.open),
                        'high': float(bar.high),
                        'low': float(bar.low),
                        'close': float(bar.close),
                        'volume': float(bar.volume) if bar.volume else 0
                    })
                
                df = pd.DataFrame(data)
                df.set_index('timestamp', inplace=True)
                df = df.tail(limit)  # Get only the requested amount
                
                self.logger.info(f"New API: Retrieved {len(df)} bars for {symbol}")
                return df
                
            except (ConnectionResetError, ConnectionError, ConnectionAbortedError) as e:
                if attempt < retry_count - 1:
                    wait_time = (attempt + 1) * 2  # Exponential backoff: 2s, 4s, 6s
                    self.logger.warning(f"Connection error for {symbol} (attempt {attempt + 1}): {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"New API failed for {symbol} after {retry_count} attempts: {e}")
                    return None
            except Exception as e:
                self.logger.error(f"New API failed for {symbol}: {e}")
                return None
        
        return None
    
    def get_bars(self, symbol: str, timeframe: str = '1Day', limit: int = 100, start: datetime = None, end: datetime = None) -> Optional[pd.DataFrame]:
        """Get historical bars for a symbol with enhanced crypto support"""
        # Try new API first if available
        if NEW_ALPACA:
            result = self.get_bars_new(symbol, timeframe, limit)
            if result is not None:
                return result
            self.logger.info(f"New API failed for {symbol}, trying fallback...")
        
        # Fallback to old API or yfinance
        try:
            # Convert timeframe
            if timeframe == '1Day':
                tf = tradeapi.rest.TimeFrame.Day
            elif timeframe == '1Hour':
                tf = tradeapi.rest.TimeFrame.Hour
            elif timeframe == '1Min':
                tf = tradeapi.rest.TimeFrame.Minute
            else:
                tf = tradeapi.rest.TimeFrame.Day
            
            # Check if this is a crypto symbol
            is_crypto = '/' in symbol
            
            # For crypto, ensure we have proper date range with correct format
            if not start and not end:
                end = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                start = end - timedelta(days=200)  # Get more data for crypto
            
            self.logger.info(f"Requesting {symbol} data: crypto={is_crypto}, timeframe={timeframe}, limit={limit}")
            if start and end:
                self.logger.info(f"Date range: {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}")
            
            # Get bars - use crypto endpoint if needed
            try:
                if is_crypto:
                    # Use crypto API with date range for better results
                    bars = self.api.get_crypto_bars(symbol, tf, start=start, end=end, limit=limit)
                else:
                    bars = self.api.get_bars(symbol, tf, start=start, end=end, limit=limit)
            except Exception as api_error:
                self.logger.warning(f"Primary API call failed for {symbol}: {api_error}")
                # Fallback: try different approach
                if is_crypto:
                    try:
                        # Try without limit for crypto
                        bars = self.api.get_crypto_bars(symbol, tf, start=start, end=end)
                    except Exception:
                        # Final fallback: try stock API for crypto (some work)
                        self.logger.info(f"Trying stock API for crypto symbol {symbol}")
                        bars = self.api.get_bars(symbol, tf, start=start, end=end, limit=limit)
                else:
                    raise api_error
            
            if not bars or len(bars) == 0:
                self.logger.warning(f"No bars returned for {symbol}")
                return None
            
            self.logger.info(f"Retrieved {len(bars)} bars for {symbol}")
            
            # Convert to DataFrame
            data = []
            for bar in bars:
                data.append({
                    'timestamp': bar.t,
                    'open': float(bar.o),
                    'high': float(bar.h),
                    'low': float(bar.l),
                    'close': float(bar.c),
                    'volume': int(bar.v)
                })
            
            df = pd.DataFrame(data)
            df.set_index('timestamp', inplace=True)
            return df
            
        except Exception as e:
            self.logger.warning(f"Old API failed for {symbol}: {e}")
            
            # Final fallback: yfinance for crypto
            if '/' in symbol:
                self.logger.info(f"Trying yfinance fallback for {symbol}...")
                try:
                    import yfinance as yf
                    yf_symbol = symbol.replace('/', '-')
                    ticker = yf.Ticker(yf_symbol)
                    hist = ticker.history(period="6mo", interval="1d")
                    
                    if not hist.empty:
                        df = hist.copy()
                        df.columns = [col.lower() for col in df.columns]
                        df = df.tail(limit)
                        self.logger.info(f"Yfinance fallback: Retrieved {len(df)} bars for {symbol}")
                        return df
                except Exception as yf_error:
                    self.logger.warning(f"Yfinance fallback failed for {symbol}: {yf_error}")
            
            self.logger.error(f"All methods failed to get bars for {symbol}")
            return None
    
    def get_latest_trade(self, symbol: str) -> Optional[Dict]:
        """Get latest trade for a symbol"""
        try:
            trade = self.api.get_latest_trade(symbol)
            
            return {
                'symbol': symbol,
                'price': float(trade.price),
                'size': int(trade.size),
                'timestamp': trade.timestamp
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get latest trade for {symbol}: {e}")
            return None
    
    def get_latest_quote(self, symbol: str) -> Optional[Dict]:
        """Get latest quote for a symbol"""
        try:
            if NEW_ALPACA:
                # Use new API - not all symbols support quotes, fallback to trades
                try:
                    if '/' in symbol:  # Crypto
                        # For crypto, get latest trade instead of quote
                        from alpaca.data.requests import LatestCryptoTradesRequest
                        request = LatestCryptoTradesRequest(symbol_or_symbols=[symbol])
                        trade_response = self.crypto_data_client.get_crypto_latest_trades(request)
                        trade = trade_response[symbol]
                        # Use trade price as both bid and ask
                        return {
                            'symbol': symbol,
                            'bid': float(trade.price),
                            'ask': float(trade.price),
                            'bid_size': int(trade.size),
                            'ask_size': int(trade.size),
                            'timestamp': trade.timestamp
                        }
                    else:  # Stock
                        from alpaca.data.requests import LatestQuotesRequest
                        request = LatestQuotesRequest(symbol_or_symbols=[symbol])
                        quote_response = self.stock_data_client.get_stock_latest_quotes(request)
                        quote = quote_response[symbol]
                        return {
                            'symbol': symbol,
                            'bid': float(quote.bid_price),
                            'ask': float(quote.ask_price),
                            'bid_size': int(quote.bid_size),
                            'ask_size': int(quote.ask_size),
                            'timestamp': quote.timestamp
                        }
                except Exception:
                    # Fallback to getting price from recent bars
                    bars = self.get_bars(symbol, limit=1)
                    if bars is not None and not bars.empty:
                        last_close = float(bars['close'].iloc[-1])
                        return {
                            'symbol': symbol,
                            'bid': last_close,
                            'ask': last_close,
                            'bid_size': 0,
                            'ask_size': 0,
                            'timestamp': bars.index[-1]
                        }
                    return None
            else:
                # Use old API
                quote = self.api.get_latest_quote(symbol)
                return {
                    'symbol': symbol,
                    'bid': float(quote.bid_price),
                    'ask': float(quote.ask_price),
                    'bid_size': int(quote.bid_size),
                    'ask_size': int(quote.ask_size),
                    'timestamp': quote.timestamp
                }
            
        except Exception as e:
            self.logger.error(f"Failed to get quote for {symbol}: {e}")
            return None
    
    def place_order(self, 
                   symbol: str, 
                   qty: float, 
                   side: OrderSide, 
                   order_type: OrderType = OrderType.MARKET,
                   time_in_force: TimeInForce = TimeInForce.DAY,
                   limit_price: float = None,
                   stop_price: float = None,
                   trail_percent: float = None,
                   trail_price: float = None) -> Optional[str]:
        """Place a trading order"""
        try:
            if NEW_ALPACA:
                # Use new API
                # Use appropriate time-in-force based on asset type
                is_crypto = '/' in symbol or symbol.endswith('USD')
                tif = AlpacaTimeInForce.GTC if is_crypto else AlpacaTimeInForce.DAY
                
                if order_type == OrderType.MARKET:
                    order_request = MarketOrderRequest(
                        symbol=symbol,
                        qty=qty,
                        side=AlpacaOrderSide.BUY if side == OrderSide.BUY else AlpacaOrderSide.SELL,
                        time_in_force=tif
                    )
                else:
                    order_request = LimitOrderRequest(
                        symbol=symbol,
                        qty=qty,
                        side=AlpacaOrderSide.BUY if side == OrderSide.BUY else AlpacaOrderSide.SELL,
                        time_in_force=tif,
                        limit_price=limit_price
                    )
                
                order = self.trading_client.submit_order(order_data=order_request)
                self.logger.info(f"Order placed (new API): {order.id} - {side.value} {qty} {symbol}")
                return str(order.id)
                
            else:
                # Use old API
                order_params = {
                    'symbol': symbol,
                    'qty': qty,
                    'side': side.value,
                    'type': order_type.value,
                    'time_in_force': time_in_force.value
                }
                
                if limit_price:
                    order_params['limit_price'] = limit_price
                if stop_price:
                    order_params['stop_price'] = stop_price
                if trail_percent:
                    order_params['trail_percent'] = trail_percent
                if trail_price:
                    order_params['trail_price'] = trail_price
                
                order = self.api.submit_order(**order_params)
                self.logger.info(f"Order placed (old API): {order.id} - {side.value} {qty} {symbol}")
                return order.id
            
        except Exception as e:
            self.logger.error(f"Failed to place order for {symbol}: {e}")
            return None
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        try:
            self.api.cancel_order(order_id)
            self.logger.info(f"Order cancelled: {order_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cancel order {order_id}: {e}")
            return False
    
    def cancel_all_orders(self) -> bool:
        """Cancel all open orders"""
        try:
            if NEW_ALPACA:
                self.trading_client.cancel_orders()
            else:
                self.api.cancel_all_orders()
            self.logger.info("All orders cancelled")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cancel all orders: {e}")
            return False
    
    def close_position(self, symbol: str, qty: float = None, percentage: float = None) -> Optional[str]:
        """Close a position (partial or full)"""
        try:
            if NEW_ALPACA:
                # Use new API - close position by placing opposite order
                positions = self.trading_client.get_all_positions()
                position = None
                for pos in positions:
                    if pos.symbol == symbol:
                        position = pos
                        break
                
                if not position:
                    self.logger.warning(f"No position found for {symbol}")
                    return None
                
                # Determine close quantity
                if qty:
                    close_qty = qty
                elif percentage:
                    close_qty = abs(float(position.qty)) * (percentage / 100)
                else:
                    close_qty = abs(float(position.qty))  # Close entire position
                
                # Determine order side (opposite of current position)
                side = AlpacaOrderSide.SELL if float(position.qty) > 0 else AlpacaOrderSide.BUY
                
                # Place market order to close position
                # For crypto, try GTC (Good Till Canceled) which is more widely supported
                is_crypto = '/' in symbol or symbol.endswith('USD')
                if is_crypto:
                    tif = AlpacaTimeInForce.GTC
                else:
                    tif = AlpacaTimeInForce.DAY
                
                order_request = MarketOrderRequest(
                    symbol=symbol,
                    qty=close_qty,
                    side=side,
                    time_in_force=tif
                )
                
                order = self.trading_client.submit_order(order_data=order_request)
                self.logger.info(f"Position closed (new API): {symbol} - {close_qty} shares")
                return str(order.id)
                
            else:
                # Use old API
                if qty:
                    order = self.api.close_position(symbol, qty=qty)
                elif percentage:
                    order = self.api.close_position(symbol, percentage=percentage)
                else:
                    order = self.api.close_position(symbol)
                
                self.logger.info(f"Position closed (old API): {symbol}")
                return order.id if hasattr(order, 'id') else str(order)
            
        except Exception as e:
            self.logger.error(f"Failed to close position for {symbol}: {e}")
            return None
    
    def get_portfolio_history(self, timeframe: str = '1D', extended_hours: bool = False) -> Optional[Dict]:
        """Get portfolio performance history"""
        try:
            history = self.api.get_portfolio_history(
                timeframe=timeframe,
                extended_hours=extended_hours
            )
            
            return {
                'timestamp': history.timestamp,
                'equity': history.equity,
                'profit_loss': history.profit_loss,
                'profit_loss_pct': history.profit_loss_pct,
                'base_value': history.base_value
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get portfolio history: {e}")
            return None
    
    def is_market_open(self) -> bool:
        """Check if market is currently open with retry logic"""
        for attempt in range(3):
            try:
                if NEW_ALPACA:
                    clock = self.trading_client.get_clock()
                else:
                    clock = self.api.get_clock()
                return clock.is_open
            except (ConnectionResetError, ConnectionError, ConnectionAbortedError) as e:
                if attempt < 2:
                    time.sleep(2)
                    continue
                else:
                    self.logger.warning(f"Failed to get market status after retries, assuming closed: {e}")
                    return False
            except Exception as e:
                self.logger.error(f"Failed to get market status: {e}")
                return False
        return False
    
    def get_market_calendar(self, start: datetime = None, end: datetime = None) -> List[Dict]:
        """Get market calendar"""
        try:
            if not start:
                start = datetime.now()
            if not end:
                end = start + timedelta(days=7)
            
            calendar = self.api.get_calendar(start=start.strftime('%Y-%m-%d'), 
                                          end=end.strftime('%Y-%m-%d'))
            
            result = []
            for day in calendar:
                result.append({
                    'date': day.date,
                    'open': day.open,
                    'close': day.close
                })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to get market calendar: {e}")
            return []
    
    def calculate_position_size(self, symbol: str, risk_amount: float, stop_loss_price: float) -> int:
        """Calculate position size based on risk management"""
        try:
            # Get current price
            quote = self.get_latest_quote(symbol)
            if not quote:
                return 0
            
            current_price = (quote['bid'] + quote['ask']) / 2
            risk_per_share = abs(current_price - stop_loss_price)
            
            if risk_per_share <= 0:
                return 0
            
            position_size = int(risk_amount / risk_per_share)
            return max(1, position_size)
            
        except Exception as e:
            self.logger.error(f"Failed to calculate position size for {symbol}: {e}")
            return 0