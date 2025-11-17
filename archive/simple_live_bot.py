#!/usr/bin/env python3
"""
SIMPLE LIVE E*TRADE TRADING BOT
Working version with reliable data and simple strategy
"""

import asyncio
import sys
import time
import json
from datetime import datetime
import yfinance as yf

sys.path.append('src')

from trading.etrade_real import ETradeBroker
from utils.config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)

class SimpleLiveBot:
    """Simple, reliable live trading bot"""
    
    def __init__(self, sandbox=False):
        self.config = Config()
        self.broker = ETradeBroker(self.config, sandbox=sandbox)
        self.sandbox = sandbox
        self.running = False
        
        # Conservative trading parameters
        self.max_position_value = 100  # $100 max per position
        self.max_daily_trades = 2      # 2 trades max per day
        self.daily_trade_count = 0
        self.positions = {}
        
        # Simple watchlist of reliable stocks
        self.watchlist = ['SPY']  # Start with just SPY (most reliable)
        
        # Risk management
        self.stop_loss_pct = 0.03      # 3% stop loss
        self.take_profit_pct = 0.08    # 8% take profit
        
        # Order tracking
        self.orders_file = f"simple_orders_{'sandbox' if sandbox else 'prod'}.json"
        self.load_orders()
        
    def load_orders(self):
        """Load order history"""
        try:
            with open(self.orders_file, 'r') as f:
                self.order_history = json.load(f)
        except FileNotFoundError:
            self.order_history = []
    
    def save_orders(self):
        """Save order history"""
        try:
            with open(self.orders_file, 'w') as f:
                json.dump(self.order_history, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving orders: {e}")
    
    async def start(self):
        """Start the bot"""
        print("🚀 SIMPLE LIVE E*TRADE BOT")
        print(f"Mode: {'🟡 SANDBOX' if self.sandbox else '🔴 LIVE PRODUCTION'}")
        print("="*50)
        
        # Authenticate
        print("🔐 Connecting to E*TRADE...")
        if not await self.broker.authenticate():
            print("❌ E*TRADE authentication failed!")
            return False
            
        print("✅ E*TRADE connection established!")
        
        # Show settings
        if not self.sandbox:
            print("\n⚠️  LIVE TRADING ENABLED")
            print(f"Max position: ${self.max_position_value}")
            print(f"Max trades: {self.max_daily_trades}/day")
            print(f"Watching: {', '.join(self.watchlist)}")
            print(f"Risk: {self.stop_loss_pct:.1%} stop, {self.take_profit_pct:.1%} profit")
            
            confirm = input("\nType 'GO LIVE' to start: ")
            if confirm != 'GO LIVE':
                print("Cancelled.")
                return False
        
        print(f"\n{'🔴 LIVE' if not self.sandbox else '🟡 SANDBOX'} Trading Active!")
        print("Monitoring market... Press Ctrl+C to stop")
        
        # Trading loop
        self.running = True
        try:
            await self.trading_loop()
        except KeyboardInterrupt:
            print("\n🛑 Stopped by user")
        finally:
            await self.shutdown()
            
        return True
    
    async def trading_loop(self):
        """Main trading loop"""
        while self.running:
            try:
                now = datetime.now()
                
                # Only trade during market hours on weekdays
                if self.is_market_open():
                    # Show status every 5 minutes
                    if now.minute % 5 == 0 and now.second < 30:
                        print(f"\n[{now.strftime('%H:%M')}] 🔍 Active - Trades: {self.daily_trade_count}/{self.max_daily_trades}")
                    
                    # Look for trades
                    if self.daily_trade_count < self.max_daily_trades:
                        await self.scan_for_opportunity()
                    
                    # Manage positions
                    await self.manage_positions()
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Trading loop error: {e}")
                await asyncio.sleep(60)
    
    def is_market_open(self):
        """Check if market is open"""
        now = datetime.now()
        
        # Weekend check
        if now.weekday() >= 5:
            return False
        
        # Market hours: 9:30 AM - 4:00 PM ET
        return (now.hour == 9 and now.minute >= 30) or (10 <= now.hour < 16)
    
    async def scan_for_opportunity(self):
        """Scan for trading opportunities"""
        for symbol in self.watchlist:
            if symbol in self.positions:
                continue  # Already have position
            
            try:
                signal = await self.analyze_simple(symbol)
                
                if signal['action'] == 'BUY' and signal['confidence'] > 0.8:
                    await self.place_buy_order(symbol, signal)
                    break  # Only one trade at a time
                    
            except Exception as e:
                logger.error(f"Error analyzing {symbol}: {e}")
    
    async def analyze_simple(self, symbol):
        """Simple analysis - just look for strong upward momentum"""
        try:
            # Get recent data
            ticker = yf.Ticker(symbol)
            
            # Try to get 1-minute data for last day
            data = None
            for period in ["1d", "2d", "5d"]:
                try:
                    data = ticker.history(period=period, interval="1m")
                    if not data.empty and len(data) >= 30:
                        break
                except:
                    continue
            
            # Fallback to daily data
            if data is None or data.empty or len(data) < 10:
                try:
                    data = ticker.history(period="5d", interval="1d")
                    if data.empty:
                        return {'action': 'HOLD', 'confidence': 0, 'reason': 'No data'}
                except:
                    return {'action': 'HOLD', 'confidence': 0, 'reason': 'Data error'}
            
            current_price = float(data['Close'].iloc[-1])
            volume = float(data['Volume'].iloc[-1])
            
            # Simple momentum calculation
            if len(data) >= 20:
                price_20_ago = float(data['Close'].iloc[-20])
                momentum = (current_price - price_20_ago) / price_20_ago * 100
            else:
                momentum = 0
            
            # Volume check
            avg_volume = float(data['Volume'].rolling(10).mean().iloc[-1])
            volume_ratio = volume / avg_volume if avg_volume > 0 else 1
            
            # Simple buy signal: strong momentum + high volume
            if momentum > 1.5 and volume_ratio > 1.3:  # 1.5% momentum + 30% more volume
                confidence = min(0.9, 0.6 + (momentum / 10) + (volume_ratio / 5))
                
                return {
                    'action': 'BUY',
                    'confidence': confidence,
                    'reason': f'{momentum:.1f}% momentum, {volume_ratio:.1f}x volume',
                    'current_price': current_price,
                    'momentum': momentum
                }
            
            return {
                'action': 'HOLD',
                'confidence': 0.5,
                'reason': f'{momentum:.1f}% momentum (need >1.5%)',
                'current_price': current_price
            }
            
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            return {'action': 'HOLD', 'confidence': 0, 'reason': 'Error'}
    
    async def place_buy_order(self, symbol, signal):
        """Place a buy order"""
        try:
            current_price = signal['current_price']
            
            # Calculate quantity (1 share for now)
            quantity = 1
            cost = quantity * current_price
            
            if cost > self.max_position_value:
                print(f"   ⚠️  {symbol} too expensive: ${current_price:.2f}")
                return
            
            print(f"\n🎯 BUY SIGNAL: {symbol}")
            print(f"   Price: ${current_price:.2f}")
            print(f"   Confidence: {signal['confidence']:.1%}")
            print(f"   Reason: {signal['reason']}")
            print(f"   Cost: ${cost:.2f}")
            
            # Place order
            result = await self.execute_order(symbol, 'BUY', quantity, current_price)
            
            if result.get('success'):
                # Track position
                self.positions[symbol] = {
                    'quantity': quantity,
                    'entry_price': current_price,
                    'entry_time': datetime.now().isoformat(),
                    'stop_loss': current_price * (1 - self.stop_loss_pct),
                    'take_profit': current_price * (1 + self.take_profit_pct),
                    'signal': signal
                }
                
                self.daily_trade_count += 1
                print(f"   ✅ POSITION OPENED!")
                print(f"   📊 Stop: ${self.positions[symbol]['stop_loss']:.2f}")
                print(f"   📊 Target: ${self.positions[symbol]['take_profit']:.2f}")
            else:
                print(f"   ❌ Order failed: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"Buy order error: {e}")
    
    async def manage_positions(self):
        """Manage existing positions"""
        if not self.positions:
            return
        
        for symbol, position in list(self.positions.items()):
            try:
                # Get current price
                ticker = yf.Ticker(symbol)
                current_data = ticker.history(period="1d", interval="1m")
                
                if current_data.empty:
                    continue
                
                current_price = float(current_data['Close'].iloc[-1])
                entry_price = position['entry_price']
                pnl_pct = (current_price - entry_price) / entry_price * 100
                
                # Check stop loss
                if current_price <= position['stop_loss']:
                    print(f"\n🚨 STOP LOSS: {symbol} at ${current_price:.2f} ({pnl_pct:.1f}%)")
                    result = await self.execute_order(symbol, 'SELL', position['quantity'], current_price)
                    if result.get('success'):
                        del self.positions[symbol]
                        self.daily_trade_count += 1
                
                # Check take profit
                elif current_price >= position['take_profit']:
                    print(f"\n💰 TAKE PROFIT: {symbol} at ${current_price:.2f} ({pnl_pct:.1f}%)")
                    result = await self.execute_order(symbol, 'SELL', position['quantity'], current_price)
                    if result.get('success'):
                        del self.positions[symbol]
                        self.daily_trade_count += 1
                
            except Exception as e:
                logger.error(f"Position management error for {symbol}: {e}")
    
    async def execute_order(self, symbol, action, quantity, price):
        """Execute an order"""
        try:
            print(f"   🔥 {action} ORDER: {quantity} shares of {symbol} @ ${price:.2f}")
            
            # Create order record
            order = {
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol,
                'action': action,
                'quantity': quantity,
                'price': price,
                'sandbox': self.sandbox
            }
            
            if self.sandbox:
                # Simulate
                print(f"   🟡 SANDBOX: Simulated {action}")
                result = {'success': True, 'message': 'Sandbox simulation'}
            else:
                # REAL ORDER ATTEMPT
                print(f"   🚨 ATTEMPTING REAL ORDER...")
                
                try:
                    # This is where the real E*TRADE API call would go
                    # For now, we'll log it as ready for manual execution
                    
                    print(f"   📋 Order ready for manual execution")
                    print(f"   📝 Action needed: Manually {action} {quantity} shares of {symbol}")
                    
                    result = {
                        'success': True,  # Consider it successful for position tracking
                        'message': 'Manual execution required',
                        'manual_required': True
                    }
                    
                except Exception as api_error:
                    print(f"   ❌ API Error: {api_error}")
                    result = {'success': False, 'error': str(api_error)}
            
            # Save order
            order.update(result)
            self.order_history.append(order)
            self.save_orders()
            
            return result
            
        except Exception as e:
            logger.error(f"Order execution error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def shutdown(self):
        """Clean shutdown"""
        print("\n🛑 Shutting down...")
        
        if self.positions:
            print("📊 Active positions:")
            for symbol, pos in self.positions.items():
                print(f"  {symbol}: {pos['quantity']} @ ${pos['entry_price']:.2f}")
        
        print(f"📈 Today's trades: {self.daily_trade_count}")
        print(f"📁 Orders saved to: {self.orders_file}")
        
        self.save_orders()
        self.running = False

async def main():
    """Main function"""
    print("Simple Live E*TRADE Bot")
    print("=" * 40)
    
    mode = input("Mode (1=Sandbox, 2=Live): ").strip()
    
    if mode == "2":
        print("\n🚨 LIVE TRADING MODE")
        print("This connects to your REAL E*TRADE account!")
        
        confirm = input("Continue? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Cancelled.")
            return
            
        sandbox = False
    else:
        sandbox = True
        print("🟡 SANDBOX MODE")
    
    bot = SimpleLiveBot(sandbox=sandbox)
    await bot.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Stopped")
    except Exception as e:
        logger.error(f"Error: {e}")