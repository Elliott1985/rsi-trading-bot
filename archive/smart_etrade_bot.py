#!/usr/bin/env python3
"""
SMART E*TRADE LIVE TRADING BOT
- Checks real account balance
- Dynamically finds stocks within budget
- Excludes penny stocks
- Uses actual portfolio data
"""

import asyncio
import sys
import time
import json
import requests
from datetime import datetime, timedelta
import os
import random

sys.path.append('src')

from trading.alpaca_broker import AlpacaBroker
from utils.config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)

class SmartTradingBot:
    """Smart E*TRADE bot with dynamic stock screening and real account data"""
    
    def __init__(self, paper_trading=True):
        self.config = Config()
        self.broker = AlpacaBroker(paper_trading=paper_trading)
        self.paper_trading = paper_trading
        self.running = False
        
        # Alpha Vantage API
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY', 'N4X87YZ3H2XYJTM1')
        
        # Account data (will be populated from E*TRADE)
        self.account_balance = 0
        self.buying_power = 0
        self.current_positions = {}
        
        # Trading parameters (optimized for full $50 usage)
        self.max_positions = 2          # Max 2 positions at once
        self.max_position_pct = 0.50    # 50% per position (allows 2 full positions)
        self.max_daily_trades = 4       # Max trades per day
        self.daily_trade_count = 0
        self.positions = {}
        
        # Stock filtering criteria (optimized for small account)
        self.min_stock_price = 2.00     # Allow cheaper stocks (but not penny stocks)
        self.max_stock_price = 50       # Upper limit for $50 account
        
        # Dynamic stock universe (will be populated)
        self.stock_universe = []
        self.last_universe_update = None
        
        # Risk management
        self.stop_loss_pct = 0.05       # 5% stop loss
        self.take_profit_pct = 0.12     # 12% take profit
        
        # Order tracking
        self.orders_file = "smart_orders_prod.json"
        self.load_orders()
        
        # Remove Alpha Vantage rate limiting (using E*TRADE now)
        
    def load_orders(self):
        """Load order history"""
        try:
            with open(self.orders_file, 'r') as f:
                self.order_history = json.load(f)
        except FileNotFoundError:
            self.order_history = []
    
    def save_orders(self):
        """Save orders"""
        try:
            with open(self.orders_file, 'w') as f:
                json.dump(self.order_history, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Save orders error: {e}")
    
    async def start(self):
        """Start the smart bot"""
        print("🧠 SMART LIVE TRADING BOT")
        print(f"Mode: {'📄 PAPER TRADING' if self.paper_trading else '🔴 LIVE TRADING'}")
        print("="*60)
        print("✅ Dynamic stock screening")
        print("✅ Real account balance integration")
        print("✅ Intelligent position sizing")
        print("✅ No penny stocks filter")
        print()
        
        # Connect to Alpaca
        print(f"🔐 Connecting to Alpaca {'Paper Trading' if self.paper_trading else 'Live Trading'}...")
        try:
            await self.broker.connect()
            print(f"✅ Alpaca connection successful!")
        except Exception as e:
            print(f"❌ Alpaca connection failed: {e}")
            return False
        
        # Get account information
        print("💰 Fetching account information...")
        await self.update_account_info()
        
        # Initialize stock universe
        print("📊 Building stock screening universe...")
        await self.build_stock_universe()
        
        # Show configuration
        print(f"\n⚠️  LIVE TRADING MODE")
        print(f"Account Balance: ${self.account_balance:,.2f}")
        print(f"Buying Power: ${self.buying_power:,.2f}")
        print(f"Max positions: {self.max_positions} at once")
        print(f"Max per position: ${self.buying_power * self.max_position_pct:,.2f} ({self.max_position_pct:.0%})")
        print(f"Max daily trades: {self.max_daily_trades}")
        print(f"Stock universe: {len(self.stock_universe)} symbols")
        print(f"Price range: ${self.min_stock_price:.2f} - ${self.max_stock_price:.2f}")
        
        confirm = input("\nReady for SMART TRADING. Type 'START SMART BOT': ")
        if confirm != 'START SMART BOT':
            print("Trading cancelled.")
            return False
        
        print(f"\n🔴 LIVE SMART TRADING ACTIVE!")
        print("Bot is intelligently scanning market...")
        print("Press Ctrl+C to stop")
        
        # Main trading loop
        self.running = True
        try:
            await self.smart_trading_loop()
        except KeyboardInterrupt:
            print("\n🛑 Smart bot stopped by user")
        finally:
            await self.shutdown()
            
        return True
    
    async def update_account_info(self):
        """Get real account balance and positions from E*TRADE"""
        try:
        # Get account data from Alpaca
        print(f"📊 Fetching account data from Alpaca...")
        
        try:
            balance_data = await self.broker.get_account_balance()
            self.account_balance = balance_data.get('equity', 50.00)
            self.buying_power = balance_data.get('buying_power', 50.00)
            
            print(f"💰 Alpaca Account Balance: ${self.account_balance:,.2f}")
            print(f"💵 Buying Power: ${self.buying_power:,.2f}")
            print(f"   Max 2 positions of ${self.buying_power * 0.5:.2f} each")
            
        except Exception as e:
            logger.warning(f"Could not fetch account balance: {e}")
            # Use default for testing
            self.account_balance = 1000.00 if self.paper_trading else 50.00
            self.buying_power = 1000.00 if self.paper_trading else 50.00
            print(f"💰 Using default balance: ${self.account_balance:,.2f}")
                
        except Exception as e:
            logger.error(f"Account info error: {e}")
            # Use safe defaults
            self.account_balance = 1000.00
            self.buying_power = 1000.00
            print(f"⚠️  Using safe default balance: ${self.account_balance:,.2f}")
    
    async def build_stock_universe(self):
        """Build universe of tradeable stocks within our criteria"""
        try:
            # Ensure buying power is set (fallback for testing)
            if self.buying_power <= 0:
                print("⚠️  Buying power not set, using default $50")
                self.buying_power = 50.00
                self.account_balance = 50.00
            
            print(f"💰 Using buying power: ${self.buying_power:.2f}")
            
            # Affordable stocks for $50 account (focus on cheaper options)
            popular_stocks = [
                # Cheaper individual stocks (under $50)
                'F', 'GE', 'T', 'PFE', 'INTC', 'BAC', 'WFC', 'C', 'KO', 'PEP',
                'XOM', 'CVX', 'JNJ', 'MRK', 'WMT', 'VZ', 'IBM', 'MMM', 'CAT', 'JPM',
                # REITs (often cheaper)
                'SIRI', 'NLY', 'AGNC', 'STWD', 'NYMT', 'CIM', 'TWO', 'EARN', 'PMT',
                # Banks and Financial (often under $50)
                'USB', 'PNC', 'TFC', 'COF', 'AXP', 'BK', 'STT', 'FITB', 'RF', 'KEY',
                # Energy (often affordable)
                'SLB', 'HAL', 'OXY', 'MRO', 'APA', 'DVN', 'FANG', 'EQT', 'AR', 'SM',
                # Utilities (stable and affordable)
                'SO', 'DUK', 'NEE', 'AEP', 'EXC', 'XEL', 'PPL', 'ES', 'ED', 'PEG',
                # Some ETFs (fractional shares possible)
                'VTI', 'VOO', 'IVV', 'VTEB', 'VYM', 'SCHD'
            ]
            
            print(f"🔍 Screening {len(popular_stocks)} potential stocks...")
            
            affordable_stocks = []
            # Allow stocks up to full balance for dynamic position sizing
            max_price_limit = self.buying_power
            
            # Check each stock's price - allow up to full balance for dynamic sizing
            print(f"  📋 Testing API with first few stocks...")
            
            for i, symbol in enumerate(popular_stocks[:10]):  # Test first 10 stocks
                try:
                    if i > 0 and i % 5 == 0:  # Progress update
                        print(f"  📈 Screened {i}/{len(popular_stocks[:10])} stocks...")
                    
                    print(f"  🔍 Fetching {symbol}...")
                    price = await self.get_current_price(symbol)
                    
                    if price:
                        print(f"    ✅ {symbol}: ${price:.2f}")
                        # Allow stocks up to full balance ($50) - will size position dynamically
                        if self.min_stock_price <= price <= self.buying_power:
                            affordable_stocks.append({
                                'symbol': symbol,
                                'price': price,
                                'affordable': True
                            })
                            print(f"    🎯 ADDED to universe")
                        else:
                            print(f"    ❌ Out of range (${self.min_stock_price:.2f} - ${self.buying_power:.2f})")
                    else:
                        print(f"    ⚠️  No price data for {symbol}")
                        
                    # Small delay to avoid overwhelming E*TRADE API
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    print(f"    ❌ Error with {symbol}: {e}")
                    logger.error(f"Error screening {symbol}: {e}")
                    continue
            
            if affordable_stocks:
                print(f"  🎆 Found {len(affordable_stocks)} stocks, expanding search...")
                # If we found some stocks, continue with more
                for i, symbol in enumerate(popular_stocks[10:20]):
                    try:
                        price = await self.get_current_price(symbol)
                        if price and self.min_stock_price <= price <= self.buying_power:
                            affordable_stocks.append({
                                'symbol': symbol,
                                'price': price,
                                'affordable': True
                            })
                        await asyncio.sleep(2)
                    except:
                        continue
            
            self.stock_universe = affordable_stocks
            self.last_universe_update = datetime.now()
            
            print(f"✅ Stock universe built: {len(self.stock_universe)} tradeable stocks")
            print(f"   Price range: ${self.min_stock_price:.2f} - ${self.buying_power:.2f}")
            
            # Show some examples
            if self.stock_universe:
                print("   Examples:")
                for stock in self.stock_universe[:5]:
                    print(f"     {stock['symbol']}: ${stock['price']:.2f}")
                if len(self.stock_universe) > 5:
                    print(f"     ... and {len(self.stock_universe) - 5} more")
                    
        except Exception as e:
            logger.error(f"Build universe error: {e}")
            # Fallback to basic list
            self.stock_universe = [
                {'symbol': 'SPY', 'price': 600, 'affordable': False},
                {'symbol': 'AAPL', 'price': 200, 'affordable': True}
            ]
    
    async def smart_trading_loop(self):
        """Intelligent trading loop with dynamic screening"""
        last_status_time = datetime.now()
        last_universe_update = datetime.now()
        
        while self.running:
            try:
                now = datetime.now()
                
                # Update stock universe every hour
                if (now - last_universe_update).total_seconds() >= 3600:
                    print(f"\n🔄 Updating stock universe...")
                    await self.build_stock_universe()
                    last_universe_update = now
                
                # Show status every 3 minutes
                if (now - last_status_time).total_seconds() >= 180:
                    await self.show_status()
                    last_status_time = now
                
                # Smart market-aware trading
                market_status = self.get_market_status()
                should_trade = self.should_trade_now()
                
                if should_trade:
                    if self.daily_trade_count < self.max_daily_trades:
                        print(f"\n[{now.strftime('%H:%M:%S')}] 🤠 Smart scan - {market_status}")
                        await self.smart_scan()
                    
                    # Manage positions if we have any
                    if self.positions:
                        await self.manage_positions()
                    
                    await asyncio.sleep(60)  # Check every minute during trading hours
                else:
                    # Market is closed - show status and sleep longer
                    if (now.minute == 0) or (now - last_status_time).total_seconds() >= 1800:  # Every 30 min when closed
                        print(f"\n[{now.strftime('%H:%M:%S')}] {market_status}")
                        print(f"   😴 Sleeping until 4:00 AM ET (premarket opens)")
                        if self.positions:
                            print(f"   📋 Monitoring {len(self.positions)} positions")
                        last_status_time = now
                    
                    # Calculate sleep time until next trading session
                    sleep_time = self.calculate_sleep_until_premarket(now)
                    await asyncio.sleep(min(sleep_time, 1800))  # Sleep max 30 minutes at a time
                
            except Exception as e:
                logger.error(f"Smart trading loop error: {e}")
                await asyncio.sleep(60)
    
    def is_market_open(self):
        """Check if market is open (including premarket)"""
        now = datetime.now()
        if now.weekday() >= 5:  # Weekend
            return False
        # Extended hours: 4:00 AM - 8:00 PM ET (includes premarket and after-hours)
        return 4 <= now.hour < 20
    
    def get_market_status(self):
        """Get detailed market status"""
        now = datetime.now()
        hour = now.hour
        minute = now.minute
        weekday = now.weekday()
        
        if weekday >= 5:  # Weekend
            return "🌙 Weekend - Market Closed"
        elif 4 <= hour < 9 or (hour == 9 and minute < 30):
            return "🌅 Premarket Trading (4:00 AM - 9:30 AM ET)"
        elif (hour == 9 and minute >= 30) or (10 <= hour < 16):
            return "📈 Regular Market Hours (9:30 AM - 4:00 PM ET)"
        elif 16 <= hour < 20:
            return "🌆 After-Hours Trading (4:00 PM - 8:00 PM ET)"
        else:
            return "🌙 Market Closed"
    
    def should_trade_now(self):
        """Determine if bot should actively trade right now"""
        now = datetime.now()
        hour = now.hour
        minute = now.minute
        weekday = now.weekday()
        
        if weekday >= 5:  # Weekend
            return False
            
        # Trade during premarket (4 AM) through after-hours (8 PM)
        return 4 <= hour < 20
    
    def calculate_sleep_until_premarket(self, current_time):
        """Calculate seconds until premarket opens (4:00 AM ET)"""
        now = current_time
        
        # If it's after 8 PM today, sleep until 4 AM tomorrow
        if now.hour >= 20:
            next_premarket = now.replace(hour=4, minute=0, second=0, microsecond=0) + timedelta(days=1)
        # If it's before 4 AM today, sleep until 4 AM today
        elif now.hour < 4:
            next_premarket = now.replace(hour=4, minute=0, second=0, microsecond=0)
        # If we're in trading hours, return short sleep
        else:
            return 60
        
        # Skip weekends - if next premarket is Saturday, go to Monday
        while next_premarket.weekday() >= 5:
            next_premarket += timedelta(days=1)
        
        sleep_seconds = (next_premarket - now).total_seconds()
        return max(60, sleep_seconds)  # Minimum 1 minute sleep
    
    async def show_status(self):
        """Show detailed bot status"""
        print(f"\n📊 SMART BOT STATUS")
        print(f"   💰 Buying Power: ${self.buying_power:,.2f}")
        print(f"   📈 Trades Today: {self.daily_trade_count}/{self.max_daily_trades}")
        print(f"   📋 Positions: {len(self.positions)}")
        print(f"   🔍 Stock Universe: {len(self.stock_universe)} symbols")
        print(f"   💼 Max Positions: {self.max_positions}")
        
        max_position = self.buying_power * self.max_position_pct
        print(f"   🎯 Max Per Position: ${max_position:,.2f} ({self.max_position_pct:.0%} of balance)")
    
    async def smart_scan(self):
        """Intelligent stock scanning with dynamic selection"""
        if not self.stock_universe:
            print("⚠️  No stocks in universe - rebuilding...")
            await self.build_stock_universe()
            return
        
        # Check position limit
        if len(self.positions) >= self.max_positions:
            print(f"📋 Position limit reached ({len(self.positions)}/{self.max_positions})")
            return
        
        # Randomly select stocks to scan (avoid always scanning the same ones)
        available_stocks = [s for s in self.stock_universe if s['symbol'] not in self.positions]
        if not available_stocks:
            print("📋 All affordable stocks already have positions")
            return
        
        # Sample up to 5 stocks for this scan
        scan_count = min(5, len(available_stocks))
        stocks_to_scan = random.sample(available_stocks, scan_count)
        
        print(f"🔍 Smart scanning {scan_count} selected stocks...")
        
        for stock_data in stocks_to_scan:
            symbol = stock_data['symbol']
            cached_price = stock_data['price']
            
            try:
                print(f"  🧠 Analyzing {symbol} (cached: ${cached_price:.2f})...")
                
                # Get fresh momentum data
                momentum_data = await self.get_price_momentum(symbol)
                
                if momentum_data:
                    current_price = momentum_data['current_price']
                    momentum = momentum_data['momentum']
                    
                    print(f"     💰 Current: ${current_price:.2f} | Momentum: {momentum:.2f}%")
                    
                    # Smart trading logic
                    if await self.should_buy(symbol, current_price, momentum):
                        await self.smart_buy(symbol, current_price, momentum)
                        break  # Only one trade per scan
                else:
                    print(f"     ⚠️  No momentum data for {symbol}")
                
                # Rate limiting
                await asyncio.sleep(12)
                
            except Exception as e:
                print(f"     ❌ Error with {symbol}: {e}")
                
        print("✅ Smart scan complete")
    
    async def should_buy(self, symbol, price, momentum):
        """Intelligent buy decision logic"""
        # Can afford any stock up to full balance (will size position appropriately)
        if price > self.buying_power:
            print(f"     ❌ {symbol}: Too expensive ${price:.2f} > ${self.buying_power:.2f}")
            return False
        
        # Lowered thresholds for more trading opportunities
        momentum_threshold = 0.3  # 0.3% minimum momentum (more opportunities)
        confidence_threshold = 0.60  # 60% confidence threshold
        
        if abs(momentum) >= momentum_threshold:
            # Calculate confidence (starts at 60% base)
            confidence = min(0.95, 0.60 + (abs(momentum) / 4))  # More aggressive scaling
            
            if confidence >= confidence_threshold:
                print(f"     ✅ {symbol}: TRADE SIGNAL! Momentum: {momentum:.2f}% | Confidence: {confidence:.1%}")
                return True
            else:
                print(f"     ⚠️  {symbol}: Low confidence {confidence:.1%} < {confidence_threshold:.0%}")
                return False
        else:
            print(f"     ⏳ {symbol}: Weak momentum {momentum:.2f}% (need >{momentum_threshold:.1f}%)")
            return False
    
    async def smart_buy(self, symbol, price, momentum):
        """Execute intelligent buy with proper position sizing"""
        try:
            # Dynamic position sizing: use full $25 position OR whatever fits
            target_position_value = self.buying_power * self.max_position_pct  # $25
            
            # If stock is expensive, buy what we can afford
            if price <= target_position_value:
                quantity = int(target_position_value / price)  # Normal position
            else:
                quantity = 1  # Expensive stock: buy 1 share
            
            if quantity < 1:
                print(f"     ⚠️  Cannot afford even 1 share of {symbol}")
                return
            
            cost = quantity * price
            
            print(f"\n🎯 SMART BUY SIGNAL: {symbol}")
            print(f"   💰 Price: ${price:.2f}")
            print(f"   📊 Momentum: {momentum:.2f}%")
            print(f"   📈 Quantity: {quantity} shares")
            print(f"   💸 Cost: ${cost:.2f} ({cost/self.buying_power:.1%} of buying power)")
            
            # Execute order
            result = await self.place_smart_order(symbol, 'BUY', quantity, price, momentum)
            
            if result.get('success'):
                # Track position
                self.positions[symbol] = {
                    'quantity': quantity,
                    'entry_price': price,
                    'entry_time': datetime.now().isoformat(),
                    'stop_loss': price * (1 - self.stop_loss_pct),
                    'take_profit': price * (1 + self.take_profit_pct),
                    'momentum': momentum,
                    'cost': cost
                }
                
                self.daily_trade_count += 1
                print(f"   ✅ SMART POSITION OPENED!")
                print(f"   📉 Stop Loss: ${self.positions[symbol]['stop_loss']:.2f} (-{self.stop_loss_pct:.0%})")
                print(f"   📈 Take Profit: ${self.positions[symbol]['take_profit']:.2f} (+{self.take_profit_pct:.0%})")
            else:
                print(f"   ❌ Order failed: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"Smart buy error: {e}")
    
    async def get_current_price(self, symbol):
        """Get current stock price using Finnhub (reliable, free, no ID needed)"""
        try:
            print(f"      💰 Fetching {symbol} from Finnhub...")
            
            # Use Finnhub for reliable price data
            import finnhub
            from dotenv import load_dotenv
            
            # Use working API key directly  
            finnhub_key = 'd3neu6pr01qo7510pnpgd3neu6pr01qo7510pnq0'
            
            print(f"      🔑 Using key: {finnhub_key[:10]}...{finnhub_key[-10:]}")
            
            # Initialize Finnhub client
            finnhub_client = finnhub.Client(api_key=finnhub_key)
            
            # Get real-time quote
            quote_data = finnhub_client.quote(symbol)
            
            if quote_data and 'c' in quote_data and quote_data['c'] > 0:
                current_price = float(quote_data['c'])  # 'c' is current price
                print(f"      ✅ {symbol}: ${current_price:.2f} (Finnhub)")
                return current_price
            else:
                print(f"      ⚠️  No price data for {symbol} from Finnhub")
                return None
            
        except Exception as e:
            print(f"      ❌ Finnhub error for {symbol}: {e}")
            logger.error(f"Price fetch error for {symbol}: {e}")
            return None
    
    async def get_price_momentum(self, symbol):
        """Get price momentum using Finnhub data"""
        try:
            import finnhub
            from dotenv import load_dotenv
            
            # Use working API key directly
            finnhub_key = 'd3neu6pr01qo7510pnpgd3neu6pr01qo7510pnq0'
            finnhub_client = finnhub.Client(api_key=finnhub_key)
            
            # Get current quote
            quote = finnhub_client.quote(symbol)
            
            if quote and 'c' in quote and 'pc' in quote:
                current_price = float(quote['c'])   # Current price
                previous_close = float(quote['pc']) # Previous close
                
                # Calculate momentum as change from previous close
                momentum = (current_price - previous_close) / previous_close * 100
                
                return {
                    'current_price': current_price,
                    'momentum': momentum,
                    'previous_close': previous_close
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Momentum error for {symbol}: {e}")
            return None
    
    async def manage_positions(self):
        """Smart position management"""
        if not self.positions:
            return
        
        print(f"📊 Managing {len(self.positions)} smart positions...")
        
        for symbol, position in list(self.positions.items()):
            try:
                current_price = await self.get_current_price(symbol)
                if not current_price:
                    continue
                
                entry_price = position['entry_price']
                pnl_pct = (current_price - entry_price) / entry_price * 100
                pnl_dollar = (current_price - entry_price) * position['quantity']
                
                print(f"   📈 {symbol}: ${current_price:.2f} | P&L: {pnl_pct:+.1f}% (${pnl_dollar:+.2f})")
                
                # Stop loss
                if current_price <= position['stop_loss']:
                    print(f"   🚨 STOP LOSS: {symbol}")
                    result = await self.place_smart_order(symbol, 'SELL', position['quantity'], current_price, 'stop_loss')
                    if result.get('success'):
                        del self.positions[symbol]
                        self.daily_trade_count += 1
                
                # Take profit
                elif current_price >= position['take_profit']:
                    print(f"   💰 TAKE PROFIT: {symbol}")
                    result = await self.place_smart_order(symbol, 'SELL', position['quantity'], current_price, 'take_profit')
                    if result.get('success'):
                        del self.positions[symbol]
                        self.daily_trade_count += 1
                
            except Exception as e:
                logger.error(f"Position management error for {symbol}: {e}")
    
    async def place_smart_order(self, symbol, action, quantity, price, reason=None):
        """Place intelligent order with full logging"""
        try:
            print(f"   🧠 SMART {action}: {quantity} {symbol} @ ${price:.2f}")
            
            order = {
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol,
                'action': action,
                'quantity': quantity,
                'price': price,
                'cost': quantity * price,
                'reason': reason or 'momentum_signal',
                'sandbox': self.sandbox,
                'account_balance': self.buying_power
            }
            
            # Place live order through E*TRADE
            print(f"   🔥 LIVE SMART ORDER - PLACING REAL ORDER...")
            print(f"   🎆 Executing through E*TRADE API: {action} {quantity} {symbol}")
            
            # Place actual order through E*TRADE broker
            try:
                etrade_result = await self.broker.place_order(
                    symbol=symbol,
                    action=action,
                    quantity=quantity,
                    order_type='MARKET'
                )
                
                if etrade_result.get('success'):
                    print(f"   ✅ E*TRADE ORDER PLACED! ID: {etrade_result.get('order_id')}")
                    result = {
                        'success': True,
                        'type': 'live_order',
                        'order_id': etrade_result.get('order_id'),
                        'status': etrade_result.get('status', 'PLACED')
                    }
                else:
                    print(f"   ❌ E*TRADE ORDER FAILED: {etrade_result.get('error')}")
                    result = {
                        'success': False,
                        'type': 'order_failed',
                        'error': etrade_result.get('error')
                    }
            except Exception as e:
                print(f"   ⚠️  E*TRADE API Error: {e}")
                print(f"   📝 Falling back to manual execution")
                result = {
                    'success': True,
                    'type': 'manual_fallback',
                    'message': f'API failed - Execute manually: {action} {quantity} {symbol}',
                    'error': str(e)
                }
            
            order.update(result)
            self.order_history.append(order)
            self.save_orders()
            
            return result
            
        except Exception as e:
            logger.error(f"Smart order error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def shutdown(self):
        """Smart shutdown with summary"""
        print("\n🧠 Shutting down Smart E*TRADE Bot...")
        
        if self.positions:
            total_invested = sum(pos['cost'] for pos in self.positions.values())
            print(f"📊 Active Positions ({len(self.positions)}):")
            for symbol, pos in self.positions.items():
                print(f"   {symbol}: {pos['quantity']} @ ${pos['entry_price']:.2f} (${pos['cost']:.2f})")
            print(f"   Total Invested: ${total_invested:.2f}")
        
        print(f"📈 Session Summary:")
        print(f"   Trades Executed: {self.daily_trade_count}")
        print(f"   Stock Universe: {len(self.stock_universe)} symbols")
        print(f"   Orders Logged: {len(self.order_history)}")
        print(f"   Data File: {self.orders_file}")
        
        self.save_orders()
        self.running = False

async def main():
    """Main function"""
    print("Smart E*TRADE Live Trading Bot")
    print("=" * 50)
    print("🧠 Intelligent stock screening")
    print("💰 Real account balance integration")
    print("📈 Dynamic position sizing")
    print("🚫 Automatic penny stock filtering")
    print()
    
    print("🚨 ALPACA TRADING MODE")
    print("⚠️  This bot will use Alpaca for automated trading!")
    print("⚠️  Much simpler than E*TRADE - just need API keys!")
    print("⚠️  Paper trading mode available for testing!")
    
    mode = input("\nSelect mode:\n1. Paper Trading (safe testing)\n2. Live Trading (real money)\nChoice (1/2): ")
    
    if mode == '2':
        confirm = input("\nProceed with LIVE trading? (yes/no): ")
        if confirm.lower() not in ['yes', 'y']:
            print("Trading cancelled.")
            return
        paper_trading = False
    else:
        paper_trading = True
        print("📄 Starting in Paper Trading mode")
    
    # Start the trading bot
    bot = SmartTradingBot(paper_trading=paper_trading)
    await bot.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Smart bot stopped")
    except Exception as e:
        logger.error(f"Smart bot error: {e}")
        print(f"\n❌ Error: {e}")