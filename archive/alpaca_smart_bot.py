#!/usr/bin/env python3
"""
ALPACA SMART TRADING BOT
- Reliable market data from Alpaca
- Paper trading support for safe testing
- Real-time quotes without API limits
- Easy order placement
"""

import asyncio
import sys
import time
import json
from datetime import datetime, timedelta
import os
import random

sys.path.append('src')

from trading.alpaca_broker import AlpacaBroker
from utils.config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)

class AlpacaSmartBot:
    """Smart trading bot powered by Alpaca's reliable API"""
    
    def __init__(self, paper_trading: bool = True):
        self.config = Config()
        self.broker = AlpacaBroker(self.config, paper_trading=paper_trading)
        self.paper_trading = paper_trading
        self.running = False
        
        # Account data (will be populated from Alpaca)
        self.account_balance = 0
        self.buying_power = 0
        self.current_positions = {}
        
        # Trading parameters (optimized for your $50 account)
        self.max_positions = 2          # Max 2 positions at once
        self.max_position_pct = 0.50    # 50% per position (allows 2 full positions)
        self.max_daily_trades = 4       # Max trades per day
        self.daily_trade_count = 0
        self.positions = {}
        
        # Stock filtering criteria
        self.min_stock_price = 2.00     # Allow cheaper stocks (but not penny stocks)
        self.max_stock_price = 50.00    # Upper limit for your account
        
        # Dynamic stock universe
        self.stock_universe = []
        self.last_universe_update = None
        
        # Risk management
        self.stop_loss_pct = 0.05       # 5% stop loss
        self.take_profit_pct = 0.12     # 12% take profit
        
        # Order tracking
        self.orders_file = f"alpaca_orders_{'paper' if paper_trading else 'live'}.json"
        self.load_orders()
        
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
        print("🚀 ALPACA SMART TRADING BOT")
        print(f"Mode: {'📝 PAPER TRADING' if self.paper_trading else '💰 LIVE TRADING'}")
        print("="*60)
        print("✅ Reliable Alpaca market data")
        print("✅ Real-time quotes without limits")
        print("✅ Intelligent position sizing")
        print("✅ Commission-free trading")
        print()
        
        # Authenticate with Alpaca
        print("🔐 Connecting to Alpaca...")
        if not await self.broker.authenticate():
            print("❌ Alpaca authentication failed!")
            return False
            
        # Get account information
        print("💰 Fetching account information...")
        await self.update_account_info()
        
        # Initialize stock universe
        print("📊 Building stock screening universe...")
        await self.build_stock_universe()
        
        # Show configuration
        if not self.paper_trading:
            print(f"\\n⚠️  LIVE TRADING MODE")
            print(f"Account Balance: ${self.account_balance:,.2f}")
            print(f"Buying Power: ${self.buying_power:,.2f}")
            print(f"Max positions: {self.max_positions} at once")
            print(f"Max per position: ${self.buying_power * self.max_position_pct:,.2f} ({self.max_position_pct:.0%})")
            print(f"Max daily trades: {self.max_daily_trades}")
            print(f"Stock universe: {len(self.stock_universe)} symbols")
            
            confirm = input("\\nReady for LIVE TRADING. Type 'START LIVE BOT': ")
            if confirm != 'START LIVE BOT':
                print("Trading cancelled.")
                return False
        
        print(f"\\n{'💰 LIVE' if not self.paper_trading else '📝 PAPER'} TRADING ACTIVE!")
        print("Bot is scanning for opportunities...")
        print("Press Ctrl+C to stop")
        
        # Main trading loop
        self.running = True
        try:
            await self.smart_trading_loop()
        except KeyboardInterrupt:
            print("\\n🛑 Smart bot stopped by user")
        finally:
            await self.shutdown()
            
        return True
    
    async def update_account_info(self):
        """Get real account balance from Alpaca"""
        try:
            balance_info = await self.broker.get_account_balance()
            
            if self.paper_trading:
                # Use actual paper trading balance or simulate your real balance
                self.account_balance = min(balance_info['cash_available'], 100000.00)  # Cap at $100k for testing
                self.buying_power = self.account_balance
                print(f"📝 Paper Trading Balance: ${self.account_balance:,.2f}")
            else:
                # Use actual live balance
                self.account_balance = balance_info['cash_available']
                self.buying_power = balance_info['buying_power']
                print(f"💰 Live Trading Balance: ${self.account_balance:,.2f}")
            
            print(f"   Max 2 positions of ${self.account_balance * 0.5:.2f} each")
            print("   (Optimized for full account usage)")
                
        except Exception as e:
            logger.error(f"Account info error: {e}")
            # Use safe defaults for your $50 account
            self.account_balance = 50.00
            self.buying_power = 50.00
            print(f"⚠️  Using default balance: ${self.account_balance:,.2f}")
    
    async def build_stock_universe(self):
        """Build universe of tradeable stocks using Alpaca's reliable data"""
        try:
            # Popular affordable stocks for small accounts
            popular_stocks = [
                'F', 'GE', 'T', 'PFE', 'INTC', 'BAC', 'WFC', 'C', 'KO', 'PEP',
                'XOM', 'CVX', 'JNJ', 'MRK', 'WMT', 'VZ', 'IBM', 'CAT', 'JPM',
                'SIRI', 'NLY', 'USB', 'PNC', 'TFC', 'COF', 'AXP', 'SLB', 'HAL', 
                'SO', 'DUK', 'NEE', 'AEP', 'SPY', 'QQQ', 'IWM', 'VTI'
            ]
            
            print(f"🔍 Screening {len(popular_stocks)} stocks with Alpaca...")
            
            affordable_stocks = []
            
            # Test first 10 stocks to verify API is working
            for i, symbol in enumerate(popular_stocks[:15]):
                try:
                    if i > 0 and i % 5 == 0:
                        print(f"  📈 Screened {i}/15 stocks...")
                    
                    print(f"  🔍 Fetching {symbol}...")
                    quote_data = await self.broker.get_quote(symbol)
                    
                    if quote_data and 'last' in quote_data:
                        price = float(quote_data['last'])
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
                    
                    # Small delay to be respectful to API
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    print(f"    ❌ Error with {symbol}: {e}")
                    continue
            
            # If we got good results, continue with more stocks
            if len(affordable_stocks) >= 5:
                print(f"  🎆 Found {len(affordable_stocks)} stocks, expanding search...")
                for symbol in popular_stocks[15:25]:
                    try:
                        quote_data = await self.broker.get_quote(symbol)
                        if quote_data and 'last' in quote_data:
                            price = float(quote_data['last'])
                            if self.min_stock_price <= price <= self.buying_power:
                                affordable_stocks.append({
                                    'symbol': symbol,
                                    'price': price,
                                    'affordable': True
                                })
                        await asyncio.sleep(1)
                    except:
                        continue
            
            self.stock_universe = affordable_stocks
            self.last_universe_update = datetime.now()
            
            print(f"✅ Stock universe built: {len(self.stock_universe)} tradeable stocks")
            print(f"   Price range: ${self.min_stock_price:.2f} - ${self.buying_power:.2f}")
            
            # Show examples
            if self.stock_universe:
                print("   Examples:")
                for stock in self.stock_universe[:5]:
                    print(f"     {stock['symbol']}: ${stock['price']:.2f}")
                if len(self.stock_universe) > 5:
                    print(f"     ... and {len(self.stock_universe) - 5} more")
                    
        except Exception as e:
            logger.error(f"Build universe error: {e}")
            # Fallback to basic list (won't trade without real prices)
            self.stock_universe = []
            print("⚠️  Failed to build stock universe - bot will retry")
    
    async def smart_trading_loop(self):
        """Main trading loop"""
        last_status_time = datetime.now()
        last_universe_update = datetime.now()
        
        while self.running:
            try:
                now = datetime.now()
                
                # Update stock universe every 2 hours
                if (now - last_universe_update).total_seconds() >= 7200:
                    print(f"\\n🔄 Updating stock universe...")
                    await self.build_stock_universe()
                    last_universe_update = now
                
                # Show status every 3 minutes
                if (now - last_status_time).total_seconds() >= 180:
                    await self.show_status()
                    last_status_time = now
                
                # Active trading during market hours
                if self.broker.is_market_open():
                    if self.daily_trade_count < self.max_daily_trades:
                        print(f"\\n[{now.strftime('%H:%M:%S')}] 🚀 Alpaca smart scan starting...")
                        await self.smart_scan()
                    
                    # Manage positions
                    if self.positions:
                        await self.manage_positions()
                else:
                    print(f"\\n[{now.strftime('%H:%M:%S')}] 🌙 Market closed - waiting...")
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Smart trading loop error: {e}")
                await asyncio.sleep(60)
    
    async def show_status(self):
        """Show detailed bot status"""
        print(f"\\n📊 ALPACA BOT STATUS")
        print(f"   💰 Buying Power: ${self.buying_power:,.2f}")
        print(f"   📈 Trades Today: {self.daily_trade_count}/{self.max_daily_trades}")
        print(f"   📋 Positions: {len(self.positions)}/{self.max_positions}")
        print(f"   🔍 Stock Universe: {len(self.stock_universe)} symbols")
        print(f"   {'📝 PAPER' if self.paper_trading else '💰 LIVE'} Trading Mode")
        
        max_position = self.buying_power * self.max_position_pct
        print(f"   🎯 Max Per Position: ${max_position:,.2f} ({self.max_position_pct:.0%})")
    
    async def smart_scan(self):
        """Smart stock scanning with Alpaca data"""
        if not self.stock_universe:
            print("⚠️  No stocks in universe - rebuilding...")
            await self.build_stock_universe()
            return
        
        # Check position limit
        if len(self.positions) >= self.max_positions:
            print(f"📋 Position limit reached ({len(self.positions)}/{self.max_positions})")
            return
        
        # Randomly select stocks to scan
        available_stocks = [s for s in self.stock_universe if s['symbol'] not in self.positions]
        if not available_stocks:
            print("📋 All affordable stocks already have positions")
            return
        
        # Sample up to 5 stocks for this scan
        scan_count = min(5, len(available_stocks))
        stocks_to_scan = random.sample(available_stocks, scan_count)
        
        print(f"🔍 Scanning {scan_count} stocks with Alpaca...")
        
        for stock_data in stocks_to_scan:
            symbol = stock_data['symbol']
            
            try:
                print(f"  🚀 Analyzing {symbol}...")
                
                # Get fresh quote from Alpaca
                quote_data = await self.broker.get_quote(symbol)
                
                if quote_data and 'last' in quote_data:
                    current_price = float(quote_data['last'])
                    cached_price = stock_data['price']
                    
                    # Calculate momentum from price change
                    momentum = (current_price - cached_price) / cached_price * 100
                    
                    print(f"     💰 Current: ${current_price:.2f} | Momentum: {momentum:.2f}%")
                    
                    # Smart trading logic
                    if await self.should_buy(symbol, current_price, momentum):
                        await self.smart_buy(symbol, current_price, momentum)
                        break  # Only one trade per scan
                else:
                    print(f"     ⚠️  No quote data for {symbol}")
                
                # Small delay
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"     ❌ Error with {symbol}: {e}")
                
        print("✅ Alpaca scan complete")
    
    async def should_buy(self, symbol, price, momentum):
        """Trading decision logic"""
        # Can afford any stock up to full balance
        if price > self.buying_power:
            print(f"     ❌ {symbol}: Too expensive ${price:.2f} > ${self.buying_power:.2f}")
            return False
        
        # Lowered thresholds for more opportunities (as requested)
        momentum_threshold = 0.3  # 0.3% minimum momentum
        confidence_threshold = 0.60  # 60% confidence threshold
        
        if abs(momentum) >= momentum_threshold:
            # Calculate confidence (starts at 60% base)
            confidence = min(0.95, 0.60 + (abs(momentum) / 4))
            
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
        """Execute buy with dynamic position sizing"""
        try:
            # Dynamic position sizing: use target $25 position OR whatever fits
            target_position_value = self.buying_power * self.max_position_pct  # Target amount
            
            # If stock is expensive, buy what we can afford
            if price <= target_position_value:
                quantity = int(target_position_value / price)  # Normal position
            else:
                quantity = 1  # Expensive stock: buy 1 share
            
            if quantity < 1:
                print(f"     ⚠️  Cannot afford even 1 share of {symbol}")
                return
            
            cost = quantity * price
            
            print(f"\\n🎯 ALPACA BUY SIGNAL: {symbol}")
            print(f"   💰 Price: ${price:.2f}")
            print(f"   📊 Momentum: {momentum:.2f}%") 
            print(f"   📈 Quantity: {quantity} shares")
            print(f"   💸 Cost: ${cost:.2f} ({cost/self.buying_power:.1%} of buying power)")
            print(f"   {'📝 PAPER' if self.paper_trading else '💰 LIVE'} ORDER")
            
            # Place order through Alpaca
            result = await self.broker.place_order(symbol, 'BUY', quantity, 'market')
            
            if result.get('success'):
                # Track position
                self.positions[symbol] = {
                    'quantity': quantity,
                    'entry_price': price,
                    'entry_time': datetime.now().isoformat(),
                    'stop_loss': price * (1 - self.stop_loss_pct),
                    'take_profit': price * (1 + self.take_profit_pct),
                    'momentum': momentum,
                    'cost': cost,
                    'order_id': result.get('order_id')
                }
                
                self.daily_trade_count += 1
                print(f"   ✅ POSITION OPENED! Order ID: {result.get('order_id')}")
                print(f"   📉 Stop Loss: ${self.positions[symbol]['stop_loss']:.2f} (-{self.stop_loss_pct:.0%})")
                print(f"   📈 Take Profit: ${self.positions[symbol]['take_profit']:.2f} (+{self.take_profit_pct:.0%})")
            else:
                print(f"   ❌ Order failed: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"Smart buy error: {e}")
    
    async def manage_positions(self):
        """Position management"""
        if not self.positions:
            return
        
        print(f"📊 Managing {len(self.positions)} positions...")
        
        for symbol, position in list(self.positions.items()):
            try:
                # Get current price from Alpaca
                quote_data = await self.broker.get_quote(symbol)
                if not quote_data or 'last' not in quote_data:
                    continue
                
                current_price = float(quote_data['last'])
                entry_price = position['entry_price']
                pnl_pct = (current_price - entry_price) / entry_price * 100
                pnl_dollar = (current_price - entry_price) * position['quantity']
                
                print(f"   📈 {symbol}: ${current_price:.2f} | P&L: {pnl_pct:+.1f}% (${pnl_dollar:+.2f})")
                
                # Stop loss
                if current_price <= position['stop_loss']:
                    print(f"   🚨 STOP LOSS: {symbol}")
                    result = await self.broker.place_order(symbol, 'SELL', position['quantity'], 'market')
                    if result.get('success'):
                        del self.positions[symbol]
                        self.daily_trade_count += 1
                
                # Take profit
                elif current_price >= position['take_profit']:
                    print(f"   💰 TAKE PROFIT: {symbol}")
                    result = await self.broker.place_order(symbol, 'SELL', position['quantity'], 'market')
                    if result.get('success'):
                        del self.positions[symbol]
                        self.daily_trade_count += 1
                
            except Exception as e:
                logger.error(f"Position management error for {symbol}: {e}")
    
    async def shutdown(self):
        """Shutdown with summary"""
        print("\\n🚀 Shutting down Alpaca Smart Bot...")
        
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
        print(f"   Trading Mode: {'Paper' if self.paper_trading else 'Live'}")
        
        self.save_orders()
        self.running = False

async def main():
    """Main function"""
    print("Alpaca Smart Trading Bot")
    print("=" * 50)
    print("🚀 Reliable Alpaca market data")
    print("💰 Commission-free trading")
    print("📝 Paper trading for safe testing")
    print("🎯 Optimized for small accounts")
    print()
    
    mode = input("Select mode:\\n1. Paper Trading (safe testing)\\n2. Live Trading (REAL MONEY)\\nChoice (1/2): ").strip()
    
    if mode == "2":
        print("\\n🚨 LIVE TRADING MODE")
        print("⚠️  This will place real orders with real money!")
        print("⚠️  Make sure you have funded your Alpaca account!")
        
        confirm = input("\\nProceed with LIVE trading? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Cancelled.")
            return
            
        paper_trading = False
    else:
        print("📝 PAPER TRADING MODE - Safe for testing!")
        paper_trading = True
    
    # Start the bot
    bot = AlpacaSmartBot(paper_trading=paper_trading)
    await bot.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\\n👋 Bot stopped")
    except Exception as e:
        logger.error(f"Bot error: {e}")
        print(f"\\n❌ Error: {e}")