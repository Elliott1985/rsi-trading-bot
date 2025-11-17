#!/usr/bin/env python3
"""
E*TRADE Live Trading Bot
Connects to real E*TRADE account and executes trades
"""

import asyncio
import sys
import time
from datetime import datetime

# Add src to path
sys.path.append('src')

from trading.etrade_real import ETradeBroker
from utils.config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)

class ETradeBot:
    """Simple E*TRADE trading bot"""
    
    def __init__(self, sandbox=True):
        self.config = Config()
        self.broker = ETradeBroker(self.config, sandbox=sandbox)
        self.sandbox = sandbox
        self.running = False
        
    async def start(self):
        """Start the trading bot"""
        print("🚀 Starting E*TRADE Trading Bot")
        print(f"Mode: {'SANDBOX' if self.sandbox else '🚨 LIVE PRODUCTION'}")
        print("="*60)
        
        # Authenticate
        print("🔐 Authenticating with E*TRADE...")
        if not await self.broker.authenticate():
            print("❌ Authentication failed!")
            return False
            
        print("✅ Authentication successful!")
        print(f"Account Key: {self.broker.account_key}")
        
        # Show status
        await self.show_status()
        
        # Main trading loop
        self.running = True
        
        if not self.sandbox:
            confirm = input("\n⚠️  This will start LIVE trading with real money. Continue? (yes/no): ")
            if confirm.lower() != 'yes':
                print("Trading cancelled.")
                return False
                
        print(f"\n{'🔴 LIVE' if not self.sandbox else '🟡 SANDBOX'} Trading Bot Started!")
        print("Press Ctrl+C to stop...")
        
        try:
            while self.running:
                await self.trading_cycle()
                await asyncio.sleep(10)  # Wait 10 seconds between cycles
                
        except KeyboardInterrupt:
            print("\n🛑 Bot stopped by user")
        except Exception as e:
            logger.error(f"Bot error: {e}")
        finally:
            self.running = False
            
        return True
    
    async def show_status(self):
        """Show current account status"""
        print("\n📊 Account Status:")
        print("-" * 30)
        
        try:
            balance = await self.broker.get_account_balance()
            print(f"Total Value: ${balance.get('total_value', 0):,.2f}")
            print(f"Cash Available: ${balance.get('cash_available', 0):,.2f}")
            print(f"Buying Power: ${balance.get('buying_power', 0):,.2f}")
            
        except Exception as e:
            print(f"Unable to get balance: {e}")
            print("Account authenticated but balance unavailable")
    
    async def trading_cycle(self):
        """One cycle of trading logic"""
        try:
            # For demo, just log that we're running
            now = datetime.now().strftime("%H:%M:%S")
            print(f"[{now}] 🔄 Trading cycle running...")
            
            # Here you would add your trading logic:
            # - Get market data
            # - Analyze signals
            # - Place trades if conditions are met
            
            # Example: Check a simple condition
            await self.check_simple_strategy()
            
        except Exception as e:
            logger.error(f"Trading cycle error: {e}")
    
    async def check_simple_strategy(self):
        """Example simple trading strategy"""
        try:
            # Get quote for AAPL (example)
            quote = await self.broker.get_quote("AAPL")
            print(f"  📈 AAPL: ${quote['last']:.2f} (Change: {quote['change']:+.2f})")
            
            # Simple logic: if down more than 1%, consider buying
            if quote['change_pct'] < -1.0:
                print(f"  🔍 AAPL down {quote['change_pct']:.2f}% - potential buy signal")
                
                if not self.sandbox:
                    print("  ⚠️  Would place buy order in production mode")
                else:
                    print("  🟡 Sandbox mode - no actual order placed")
            
        except Exception as e:
            logger.error(f"Strategy check error: {e}")

async def main():
    """Main function"""
    print("E*TRADE Live Trading Bot")
    print("=" * 40)
    
    # Choose mode
    print("Select mode:")
    print("1. Sandbox (safe testing)")
    print("2. Live Production (real money)")
    
    choice = input("Enter choice (1/2): ").strip()
    
    if choice == "2":
        print("\n⚠️  WARNING: PRODUCTION MODE")
        print("This will connect to your real E*TRADE account!")
        confirm = input("Are you sure? Type 'PRODUCTION' to confirm: ")
        
        if confirm != "PRODUCTION":
            print("Production mode cancelled.")
            return
            
        sandbox = False
        print("🚨 PRODUCTION MODE SELECTED")
    else:
        sandbox = True
        print("🟡 SANDBOX MODE SELECTED")
    
    # Start bot
    bot = ETradeBot(sandbox=sandbox)
    await bot.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")