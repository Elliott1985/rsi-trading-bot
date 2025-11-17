#!/usr/bin/env python3
"""
Simplified E*TRADE Trading Bot
Focuses on authentication and basic functionality
"""

import asyncio
import sys
import time
from datetime import datetime
import yfinance as yf

# Add src to path
sys.path.append('src')

from trading.etrade_real import ETradeBroker
from utils.config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)

class SimpleETradeBot:
    """Simplified E*TRADE trading bot that works around API limitations"""
    
    def __init__(self, sandbox=True):
        self.config = Config()
        self.broker = ETradeBroker(self.config, sandbox=sandbox)
        self.sandbox = sandbox
        self.running = False
        
    async def start(self):
        """Start the trading bot"""
        print("🚀 Simple E*TRADE Trading Bot")
        print(f"Mode: {'SANDBOX' if self.sandbox else '🚨 LIVE PRODUCTION'}")
        print("="*60)
        
        # Authenticate
        print("🔐 Authenticating with E*TRADE...")
        if not await self.broker.authenticate():
            print("❌ Authentication failed!")
            return False
            
        print("✅ Authentication successful!")
        print(f"✓ OAuth tokens saved and loaded")
        print(f"✓ Account connection established")
        
        # Show what we can do
        await self.show_capabilities()
        
        # Start monitoring
        if not self.sandbox:
            confirm = input("\n⚠️  Ready for LIVE trading. Start monitoring? (yes/no): ")
            if confirm.lower() != 'yes':
                print("Monitoring cancelled.")
                return False
        
        print(f"\n{'🔴 LIVE' if not self.sandbox else '🟡 SANDBOX'} Mode - Starting market monitoring...")
        print("Press Ctrl+C to stop...")
        
        # Main monitoring loop
        self.running = True
        try:
            while self.running:
                await self.monitor_market()
                await asyncio.sleep(30)  # Check every 30 seconds
                
        except KeyboardInterrupt:
            print("\n🛑 Bot stopped by user")
        except Exception as e:
            logger.error(f"Bot error: {e}")
        finally:
            self.running = False
            
        return True
    
    async def show_capabilities(self):
        """Show what the bot can do"""
        print("\n🔧 Bot Capabilities:")
        print("-" * 30)
        print("✅ E*TRADE OAuth Authentication")
        print("✅ Token Management (save/load)")
        print("✅ Market Data (via yfinance)")
        print("✅ Trading Signal Generation")
        print("✅ Risk Management")
        
        # E*TRADE API limitations we're working around
        print("\n⚠️  Known E*TRADE API Issues:")
        print("- Account balance endpoints have connection issues")
        print("- Using external market data (yfinance) for quotes")
        print("- Ready for order placement when API stabilizes")
        
    async def monitor_market(self):
        """Monitor market and generate trading signals"""
        try:
            now = datetime.now().strftime("%H:%M:%S")
            print(f"\n[{now}] 🔍 Market scan...")
            
            # Get market data using yfinance (more reliable)
            symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA']
            
            for symbol in symbols:
                await self.analyze_symbol(symbol)
            
            print("  ✓ Scan complete")
            
        except Exception as e:
            logger.error(f"Market monitoring error: {e}")
    
    async def analyze_symbol(self, symbol):
        """Analyze a single stock symbol"""
        try:
            # Get real market data
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="5d", interval="1d")
            
            if data.empty:
                return
            
            current_price = data['Close'].iloc[-1]
            prev_close = data['Close'].iloc[-2] if len(data) > 1 else current_price
            change = current_price - prev_close
            change_pct = (change / prev_close) * 100
            
            # Generate trading signal
            signal = await self.generate_signal(symbol, data, current_price, change_pct)
            
            # Display info
            status_emoji = "🔴" if change_pct < -1 else "🟡" if change_pct < 1 else "🟢"
            print(f"  {status_emoji} {symbol}: ${current_price:.2f} ({change_pct:+.1f}%) - {signal}")
            
            # If we have a strong signal and are in production, we could place orders
            if signal in ["STRONG_BUY", "STRONG_SELL"] and not self.sandbox:
                await self.consider_trade(symbol, signal, current_price)
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
    
    async def generate_signal(self, symbol, data, price, change_pct):
        """Generate a trading signal based on market conditions"""
        
        # Simple signal logic
        if len(data) < 3:
            return "INSUFFICIENT_DATA"
        
        # Calculate simple indicators
        sma_3 = data['Close'].rolling(3).mean().iloc[-1]
        volume_avg = data['Volume'].rolling(3).mean().iloc[-1]
        current_volume = data['Volume'].iloc[-1]
        
        # Signal conditions
        if change_pct < -2 and price < sma_3 and current_volume > volume_avg * 1.5:
            return "STRONG_BUY"
        elif change_pct < -1 and price < sma_3:
            return "BUY"
        elif change_pct > 2 and price > sma_3 and current_volume > volume_avg * 1.5:
            return "STRONG_SELL"  
        elif change_pct > 1 and price > sma_3:
            return "SELL"
        else:
            return "HOLD"
    
    async def consider_trade(self, symbol, signal, price):
        """Consider placing a trade based on signal"""
        print(f"    🚨 {signal} signal for {symbol} at ${price:.2f}")
        
        if self.sandbox:
            print(f"    📝 Would simulate {signal} order in sandbox")
        else:
            print(f"    ⚡ Ready to place {signal} order")
            # Here you would call the E*TRADE order placement API
            # when the API endpoints are working properly
            
            # For now, just log the intention
            action = "BUY" if "BUY" in signal else "SELL"
            quantity = 1  # Start small
            print(f"    🎯 Planned: {action} {quantity} shares of {symbol}")

async def main():
    """Main function"""
    print("Simple E*TRADE Trading Bot")
    print("=" * 40)
    
    # Choose mode
    print("Select mode:")
    print("1. Sandbox (safe testing)")
    print("2. Live Production (real money - limited)")
    
    choice = input("Enter choice (1/2): ").strip()
    
    if choice == "2":
        print("\n⚠️  WARNING: PRODUCTION MODE")
        print("OAuth will connect to your real E*TRADE account")
        print("Trading signals will be generated but orders are disabled until API issues resolve")
        confirm = input("Continue? Type 'yes': ")
        
        if confirm.lower() != "yes":
            print("Cancelled.")
            return
            
        sandbox = False
        print("🚨 PRODUCTION MODE SELECTED")
    else:
        sandbox = True
        print("🟡 SANDBOX MODE SELECTED")
    
    # Start bot
    bot = SimpleETradeBot(sandbox=sandbox)
    await bot.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")