#!/usr/bin/env python3
"""
ALPACA LIVE TRADING BOT ($50 BUDGET)
Fully automated trading bot using Alpaca API
Places real trades automatically with your $50
"""

import asyncio
import sys
import time
import json
from datetime import datetime
import os

sys.path.append('src')

# Load environment variables
from dotenv import load_dotenv
load_dotenv('api_keys.env')

from utils.logger import setup_logger
import alpaca_trade_api as tradeapi

logger = setup_logger(__name__)

class AlpacaLiveBot:
    """Live trading bot optimized for $50 budget with Alpaca"""
    
    def __init__(self, paper_trading=False):
        self.paper_trading = paper_trading
        
        # Get Alpaca credentials
        if paper_trading:
            self.api_key = os.getenv('ALPACA_PAPER_KEY_ID')
            self.api_secret = os.getenv('ALPACA_PAPER_SECRET_KEY') 
            self.base_url = 'https://paper-api.alpaca.markets'
            print("🟡 PAPER TRADING MODE")
        else:
            self.api_key = os.getenv('ALPACA_LIVE_KEY_ID')
            self.api_secret = os.getenv('ALPACA_LIVE_SECRET_KEY')
            self.base_url = 'https://api.alpaca.markets'
            print("🔴 LIVE TRADING MODE")
        
        if not self.api_key or not self.api_secret:
            raise ValueError(f"Alpaca credentials not found!")
            
        # Initialize Alpaca API
        self.api = tradeapi.REST(
            self.api_key,
            self.api_secret, 
            self.base_url,
            api_version='v2'
        )
        
        # Trading parameters for $50 budget
        self.max_positions = 2          # Max 2 positions
        self.max_position_pct = 0.45    # 45% per position 
        self.max_daily_trades = 4
        self.daily_trade_count = 0
        
        # Account info
        self.account_balance = 0
        self.buying_power = 0
        self.current_positions = {}
        
        # Stock universe (affordable stocks)
        self.stock_universe = []
        
        # Risk management
        self.stop_loss_pct = 0.05   # 5% stop loss
        self.take_profit_pct = 0.12  # 12% take profit
        
        # Order tracking
        self.orders = []
        self.orders_file = f"alpaca_orders_{'paper' if paper_trading else 'live'}.json"
        self.load_orders()
        
    def load_orders(self):
        """Load order history"""
        try:
            with open(self.orders_file, 'r') as f:
                self.orders = json.load(f)
        except FileNotFoundError:
            self.orders = []
    
    def save_orders(self):
        """Save orders"""
        try:
            with open(self.orders_file, 'w') as f:
                json.dump(self.orders, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Save orders error: {e}")

    async def authenticate(self):
        """Authenticate with Alpaca"""
        try:
            # Test the connection
            account = self.api.get_account()
            
            if account:
                self.account_balance = float(account.equity)
                self.buying_power = float(account.buying_power)
                
                print(f"✅ Alpaca {'Paper' if self.paper_trading else 'Live'} Trading Connected!")
                print(f"   Account Status: {account.status}")
                print(f"   Equity: ${float(account.equity):,.2f}")
                print(f"   Buying Power: ${float(account.buying_power):,.2f}")
                print(f"   Cash: ${float(account.cash):,.2f}")
                
                return True
            else:
                print("❌ Failed to get account info")
                return False
                
        except Exception as e:
            print(f"❌ Alpaca authentication failed: {e}")
            return False

    async def get_current_price(self, symbol):
        """Get current stock price"""
        try:
            # Get latest trade
            latest_trade = self.api.get_latest_trade(symbol)
            
            if latest_trade:
                return float(latest_trade.price)
            
            # Fallback to bars
            bars = self.api.get_bars(symbol, tradeapi.TimeFrame.Day, limit=1).df
            if not bars.empty:
                return float(bars.iloc[-1]['close'])
            
            return None
            
        except Exception as e:
            logger.error(f"Price fetch error for {symbol}: {e}")
            return None

    async def get_price_momentum(self, symbol):
        """Get price momentum"""
        try:
            # Get 2-day bars to calculate momentum
            bars = self.api.get_bars(symbol, tradeapi.TimeFrame.Day, limit=2).df
            
            if len(bars) >= 2:
                current_price = float(bars.iloc[-1]['close'])
                previous_close = float(bars.iloc[-2]['close'])
                
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

    async def build_stock_universe(self):
        """Build universe of affordable stocks for $50 budget"""
        print("🔍 Building affordable stock universe...")
        
        # Focus on cheaper stocks for $50 budget
        candidates = [
            # Cheap stocks under $50
            'F', 'T', 'PFE', 'INTC', 'VZ', 'KO', 'PEP', 'BAC', 'WFC', 'USB',
            'C', 'GE', 'XOM', 'CVX', 'JNJ', 'MRK', 'WMT', 'HD', 'DIS', 'IBM',
            'MMM', 'CAT', 'SO', 'DUK', 'NEE', 'PNC', 'TFC', 'COF',
            # ETFs (fractional shares)
            'SPY', 'QQQ', 'IWM', 'XLF', 'XLE', 'XLK',
            # Some others
            'SIRI', 'NLY', 'AGNC', 'BB', 'NOK'
        ]
        
        affordable_stocks = []
        for symbol in candidates[:15]:  # Test 15 stocks
            try:
                price = await self.get_current_price(symbol)
                if price and 2.0 <= price <= 60.0:  # $2-$60 range
                    affordable_stocks.append(symbol)
                    print(f"    ✅ {symbol}: ${price:.2f}")
                elif price:
                    print(f"    ❌ {symbol}: ${price:.2f} (out of range)")
            except:
                continue
        
        self.stock_universe = affordable_stocks
        print(f"\n✅ Stock universe: {len(self.stock_universe)} symbols")
        print(f"   Symbols: {', '.join(self.stock_universe)}")

    async def scan_for_signals(self):
        """Scan for trading signals"""
        print("\n🔍 SCANNING FOR TRADE SIGNALS...")
        
        signals = []
        
        for symbol in self.stock_universe:
            try:
                momentum_data = await self.get_price_momentum(symbol)
                if not momentum_data:
                    continue
                
                current_price = momentum_data['current_price']
                momentum = momentum_data['momentum']
                
                print(f"  🧠 {symbol}: ${current_price:.2f} | Momentum: {momentum:+.2f}%")
                
                # Trading criteria
                buy_signal = False
                confidence = 0
                
                # Strong momentum signals
                if abs(momentum) > 2.0:
                    if momentum > 0:  # Upward momentum
                        buy_signal = True
                        confidence = min(95, 80 + abs(momentum) * 3)
                    elif momentum < -3.0:  # Strong dip - contrarian
                        buy_signal = True
                        confidence = min(95, 70 + abs(momentum) * 2)
                
                # Moderate signals
                elif 1.0 < abs(momentum) < 2.0:
                    if momentum > 0:
                        buy_signal = True
                        confidence = 70 + abs(momentum) * 5
                
                if buy_signal and confidence > 75:
                    # Calculate position size for $50 budget
                    max_investment = self.buying_power * self.max_position_pct
                    
                    # For fractional shares (most stocks support this now)
                    if max_investment >= 1.0:  # At least $1 position
                        quantity = max_investment / current_price
                        cost = quantity * current_price
                        
                        signal = {
                            'symbol': symbol,
                            'action': 'BUY',
                            'price': current_price,
                            'quantity': round(quantity, 6),  # Fractional shares
                            'cost': cost,
                            'momentum': momentum,
                            'confidence': confidence,
                            'stop_loss': current_price * (1 - self.stop_loss_pct),
                            'take_profit': current_price * (1 + self.take_profit_pct),
                            'timestamp': datetime.now()
                        }
                        signals.append(signal)
                        
                        print(f"     ✅ SIGNAL! {symbol} {quantity:.3f} shares @ ${current_price:.2f} = ${cost:.2f}")
                
            except Exception as e:
                logger.error(f"Signal error for {symbol}: {e}")
                continue
        
        return signals

    async def place_order(self, signal):
        """Place actual order through Alpaca"""
        try:
            symbol = signal['symbol']
            quantity = signal['quantity']
            
            print(f"🚨 PLACING {'PAPER' if self.paper_trading else 'LIVE'} ORDER...")
            print(f"   Symbol: {symbol}")
            print(f"   Quantity: {quantity:.6f}")
            print(f"   Cost: ${signal['cost']:.2f}")
            
            # Place market order
            order = self.api.submit_order(
                symbol=symbol,
                qty=quantity,
                side='buy',
                type='market',
                time_in_force='day'
            )
            
            if order:
                print(f"✅ ORDER PLACED! ID: {order.id}")
                
                # Track the order
                order_record = {
                    'timestamp': datetime.now().isoformat(),
                    'symbol': symbol,
                    'action': 'BUY',
                    'quantity': quantity,
                    'estimated_price': signal['price'],
                    'cost': signal['cost'],
                    'order_id': order.id,
                    'status': order.status,
                    'momentum': signal['momentum'],
                    'confidence': signal['confidence']
                }
                
                self.orders.append(order_record)
                self.save_orders()
                
                # Add to positions for tracking
                self.current_positions[symbol] = {
                    'symbol': symbol,
                    'quantity': quantity,
                    'entry_price': signal['price'],
                    'cost': signal['cost'],
                    'stop_loss': signal['stop_loss'],
                    'take_profit': signal['take_profit'],
                    'order_id': order.id,
                    'timestamp': datetime.now()
                }
                
                self.buying_power -= signal['cost']
                self.daily_trade_count += 1
                
                return True
            else:
                print("❌ Order failed")
                return False
                
        except Exception as e:
            print(f"❌ Order error: {e}")
            return False

    async def manage_positions(self):
        """Manage existing positions"""
        if not self.current_positions:
            return
        
        print(f"\n📊 Managing {len(self.current_positions)} positions...")
        
        for symbol, position in list(self.current_positions.items()):
            try:
                current_price = await self.get_current_price(symbol)
                if not current_price:
                    continue
                
                entry_price = position['entry_price']
                pnl_pct = (current_price - entry_price) / entry_price * 100
                pnl_dollar = (current_price - entry_price) * position['quantity']
                
                print(f"   📈 {symbol}: ${current_price:.2f} | P&L: {pnl_pct:+.1f}% (${pnl_dollar:+.2f})")
                
                # Check stop loss
                if current_price <= position['stop_loss']:
                    print(f"   🚨 STOP LOSS: {symbol}")
                    await self.sell_position(symbol, position, current_price, 'stop_loss')
                
                # Check take profit
                elif current_price >= position['take_profit']:
                    print(f"   💰 TAKE PROFIT: {symbol}")
                    await self.sell_position(symbol, position, current_price, 'take_profit')
                    
            except Exception as e:
                logger.error(f"Position management error for {symbol}: {e}")

    async def sell_position(self, symbol, position, current_price, reason):
        """Sell a position"""
        try:
            quantity = position['quantity']
            
            print(f"🔥 SELLING {quantity:.6f} shares of {symbol}")
            print(f"   Reason: {reason}")
            print(f"   Current price: ${current_price:.2f}")
            
            # Place sell order
            order = self.api.submit_order(
                symbol=symbol,
                qty=quantity,
                side='sell',
                type='market',
                time_in_force='day'
            )
            
            if order:
                print(f"✅ SELL ORDER PLACED! ID: {order.id}")
                
                # Calculate P&L
                entry_price = position['entry_price']
                pnl = (current_price - entry_price) * quantity
                pnl_pct = (current_price - entry_price) / entry_price * 100
                
                # Log the sell
                sell_record = {
                    'timestamp': datetime.now().isoformat(),
                    'symbol': symbol,
                    'action': 'SELL',
                    'quantity': quantity,
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'reason': reason,
                    'order_id': order.id,
                    'status': order.status
                }
                
                self.orders.append(sell_record)
                self.save_orders()
                
                # Remove from positions
                del self.current_positions[symbol]
                
                # Update buying power (approximate)
                self.buying_power += quantity * current_price
                self.daily_trade_count += 1
                
                print(f"💰 P&L: ${pnl:+.2f} ({pnl_pct:+.1f}%)")
                
                return True
                
        except Exception as e:
            print(f"❌ Sell error: {e}")
            return False

    async def run_trading_bot(self):
        """Main trading loop"""
        print("🚀 ALPACA LIVE TRADING BOT STARTING")
        print("="*60)
        
        # Authenticate
        if not await self.authenticate():
            print("❌ Authentication failed!")
            return
        
        # Build stock universe
        await self.build_stock_universe()
        
        if not self.stock_universe:
            print("❌ No affordable stocks found!")
            return
        
        print(f"\n🎯 STARTING AUTOMATED TRADING...")
        print(f"💰 Account Equity: ${self.account_balance:.2f}")
        print(f"💵 Buying Power: ${self.buying_power:.2f}")
        print(f"📊 Max Positions: {self.max_positions}")
        print(f"💸 Max Per Position: ${self.buying_power * self.max_position_pct:.2f}")
        
        if not self.paper_trading:
            print("\n⚠️  LIVE TRADING MODE - REAL MONEY!")
            confirm = input("Type 'START BOT' to begin: ")
            if confirm != 'START BOT':
                print("Bot cancelled.")
                return
        
        print(f"\n🤖 {'LIVE' if not self.paper_trading else 'PAPER'} TRADING ACTIVE!")
        print("Press Ctrl+C to stop")
        
        cycle = 0
        while True:
            try:
                cycle += 1
                print(f"\n[CYCLE {cycle}] {datetime.now().strftime('%H:%M:%S')}")
                
                # Manage existing positions first
                await self.manage_positions()
                
                # Look for new opportunities
                if len(self.current_positions) < self.max_positions and self.daily_trade_count < self.max_daily_trades:
                    signals = await self.scan_for_signals()
                    
                    if signals:
                        # Take the best signal
                        best_signal = max(signals, key=lambda x: x['confidence'])
                        print(f"\n🎯 BEST SIGNAL: {best_signal['symbol']} ({best_signal['confidence']:.1f}% confidence)")
                        
                        # Place the order
                        success = await self.place_order(best_signal)
                        if success:
                            print("✅ Order placed successfully!")
                        else:
                            print("❌ Order failed")
                    else:
                        print("📊 No strong signals found")
                else:
                    print(f"📋 Limits reached - Positions: {len(self.current_positions)}/{self.max_positions}, Trades: {self.daily_trade_count}/{self.max_daily_trades}")
                
                print(f"\n⏳ Waiting 60 seconds...")
                await asyncio.sleep(60)
                
            except KeyboardInterrupt:
                print("\n🛑 Bot stopped by user")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                await asyncio.sleep(10)

async def main():
    """Main function"""
    print("🎯 ALPACA LIVE TRADING BOT ($50 BUDGET)")
    print("="*50)
    
    mode = input("Select mode:\n1. Paper Trading (safe testing)\n2. Live Trading (REAL MONEY)\nChoice (1/2): ")
    
    paper_trading = mode != '2'
    
    if not paper_trading:
        print("\n🚨 LIVE TRADING MODE")
        print("⚠️  This will trade with REAL MONEY!")
        print("⚠️  Make sure you understand the risks!")
        confirm = input("\nProceed with live trading? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Cancelled.")
            return
    
    bot = AlpacaLiveBot(paper_trading=paper_trading)
    await bot.run_trading_bot()

if __name__ == "__main__":
    asyncio.run(main())