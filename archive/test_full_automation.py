#!/usr/bin/env python3
"""
TEST FULL AUTOMATION - Smart E*TRADE Bot
This script bypasses OAuth for testing full automation flow
"""

import asyncio
import sys
import os
sys.path.append('src')

# Load environment variables
from dotenv import load_dotenv
load_dotenv('api_keys.env')

from smart_etrade_bot import SmartETradeBot

class TestAutomationBot(SmartETradeBot):
    """Test version that simulates authentication"""
    
    async def start(self):
        """Override start to skip OAuth for testing"""
        print("🧪 TESTING FULL AUTOMATION")
        print("Mode: 🟡 SANDBOX SIMULATION")
        print("="*60)
        print("✅ Bypassing OAuth for automation testing")
        print("✅ Dynamic stock screening")
        print("✅ Real market data with Finnhub")
        print("✅ Intelligent position sizing")
        print("✅ Automated order placement")
        print()
        
        # Skip OAuth authentication for testing
        self.broker.authenticated = True
        self.broker.account_key = "test_account"
        print("✅ Simulated E*TRADE authentication successful!")
        
        # Get account information
        print("💰 Setting up test account...")
        await self.update_account_info()
        
        # Initialize stock universe
        print("📊 Building stock screening universe...")
        await self.build_stock_universe()
        
        print(f"\n🧪 TESTING AUTOMATION")
        print(f"Account Balance: ${self.account_balance:,.2f}")
        print(f"Buying Power: ${self.buying_power:,.2f}")
        print(f"Max positions: {self.max_positions} at once")
        print(f"Max per position: ${self.buying_power * self.max_position_pct:,.2f} ({self.max_position_pct:.0%})")
        print(f"Stock universe: {len(self.stock_universe)} symbols")
        print()
        
        print("🤖 STARTING AUTOMATED TRADING TEST...")
        print("Will run 3 trading cycles then stop")
        print("Press Ctrl+C to stop early")
        
        # Run limited test cycles
        self.running = True
        cycle_count = 0
        max_cycles = 3
        
        try:
            while self.running and cycle_count < max_cycles:
                print(f"\n[CYCLE {cycle_count + 1}/{max_cycles}] Running smart scan...")
                await self.smart_scan()
                
                cycle_count += 1
                if cycle_count < max_cycles:
                    print(f"⏳ Waiting 30 seconds before next cycle...")
                    await asyncio.sleep(30)
                    
            print(f"\n🎯 AUTOMATION TEST COMPLETE!")
            print(f"Completed {cycle_count} trading cycles")
            
        except KeyboardInterrupt:
            print(f"\n🛑 Test stopped by user after {cycle_count} cycles")
        finally:
            await self.shutdown()
            
        return True

async def main():
    """Run automation test"""
    bot = TestAutomationBot(sandbox=True)
    await bot.start()

if __name__ == "__main__":
    asyncio.run(main())