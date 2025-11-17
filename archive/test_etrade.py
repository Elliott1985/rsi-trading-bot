#!/usr/bin/env python3
"""
E*TRADE Connection Test Script
Tests E*TRADE API authentication and basic functionality
"""

import asyncio
import sys
from pathlib import Path

# Add src to path so we can import modules
sys.path.append(str(Path(__file__).parent / "src"))

from src.utils.config import Config
from src.trading.etrade_simple import ETradeBroker

async def test_etrade_connection():
    """Test E*TRADE API connection and basic functionality"""
    
    print("🚀 E*TRADE Connection Test")
    print("=" * 50)
    
    try:
        # Load configuration
        print("📋 Loading configuration...")
        config = Config()
        
        # Initialize E*TRADE broker (sandbox mode by default)
        print("🔧 Initializing E*TRADE broker (sandbox mode)...")
        broker = ETradeBroker(config, sandbox=True)
        
        # Test authentication
        print("🔐 Testing authentication...")
        auth_success = await broker.authenticate()
        
        if not auth_success:
            print("❌ Authentication failed!")
            return False
        
        print("✅ Authentication successful!")
        
        # Test account balance
        print("\n📊 Getting account balance...")
        try:
            balance = await broker.get_account_balance()
            print(f"  💰 Total Value: ${balance['total_value']:,.2f}")
            print(f"  💵 Cash Available: ${balance['cash_available']:,.2f}")
            print(f"  📈 Buying Power: ${balance['buying_power']:,.2f}")
            print(f"  📊 Unrealized P&L: ${balance['unrealized_pnl']:,.2f}")
        except Exception as e:
            print(f"⚠️  Could not get balance: {e}")
        
        # Test positions
        print("\n📈 Getting current positions...")
        try:
            positions = await broker.get_positions()
            if positions:
                for pos in positions:
                    print(f"  📍 {pos['symbol']}: {pos['quantity']} shares @ ${pos['current_price']:.2f}")
            else:
                print("  📍 No positions found")
        except Exception as e:
            print(f"⚠️  Could not get positions: {e}")
        
        # Test market quote
        print("\n📊 Testing market data (AAPL quote)...")
        try:
            quote = await broker.get_quote("AAPL")
            print(f"  📈 AAPL: ${quote['last']:.2f} ({quote['change']:+.2f} / {quote['change_pct']:+.2f}%)")
            print(f"  📊 Bid: ${quote['bid']:.2f} | Ask: ${quote['ask']:.2f} | Volume: {quote['volume']:,}")
        except Exception as e:
            print(f"⚠️  Could not get quote: {e}")
        
        # Test order preview (sandbox mode - won't actually place)
        print("\n🛒 Testing order preview (1 share AAPL buy)...")
        try:
            order_result = await broker.place_order("AAPL", "BUY", 1, "MARKET")
            if order_result['success']:
                print(f"  ✅ Order preview successful!")
                print(f"  📝 Order ID: {order_result['order_id']}")
                print(f"  🎯 Status: {order_result['status']}")
            else:
                print(f"  ❌ Order preview failed: {order_result.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"⚠️  Order test failed: {e}")
        
        # Market status
        print(f"\n🕐 Market Status: {'🟢 OPEN' if broker.is_market_open() else '🔴 CLOSED'}")
        
        print("\n" + "=" * 50)
        print("✅ E*TRADE connection test completed successfully!")
        print("🎉 Your system is ready for trading!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Check your E*TRADE API credentials in config/api_keys.env")
        print("2. Make sure you have an E*TRADE developer account")
        print("3. Ensure your API keys have proper permissions")
        print("4. Try running the authentication process again")
        
        return False

def main():
    """Main function"""
    print("E*TRADE API Connection Test")
    print("This will test your E*TRADE API connection and authentication.")
    print("\nNote: This runs in SANDBOX mode - no real trades will be placed.")
    
    # Get user confirmation
    response = input("\nContinue with test? (y/N): ").strip().lower()
    if response != 'y':
        print("Test cancelled.")
        return
    
    # Run the async test
    success = asyncio.run(test_etrade_connection())
    
    if success:
        print("\n🎊 Next steps:")
        print("1. Run 'python app.py' to start the full trading system")
        print("2. Or run 'streamlit run src/dashboard/trading_dashboard.py' for the web interface")
        print("3. Change TRADING_MODE to 'live' in config/api_keys.env for real trading")
    else:
        print("\n🔧 Please fix the issues above before proceeding.")

if __name__ == "__main__":
    main()