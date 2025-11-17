#!/usr/bin/env python3
"""
Autonomous Trading Bot - Startup Script
Main entry point for running the production trading bot.
"""

import sys
import os
import argparse
import subprocess
from datetime import datetime

def print_banner():
    """Print startup banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════════╗
    ║                                                                  ║
    ║                 🤖 AUTONOMOUS TRADING BOT 🤖                     ║
    ║                                                                  ║
    ║                      Production Version                          ║
    ║                                                                  ║
    ╚══════════════════════════════════════════════════════════════════╝
    
    🚀 Starting up...
    📅 Current time: {current_time}
    
    ⚠️  WARNING: This bot uses LIVE trading with real money!
    Make sure your Alpaca account is properly funded and configured.
    
    """.format(current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    print(banner)

def check_dependencies():
    """Check if all required packages are installed"""
    required_packages = [
        'alpaca-trade-api',
        'pandas',
        'numpy',
        'textblob',
        'flask',
        'requests'
    ]
    
    print("🔍 Checking dependencies...")
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print(f"💡 Install with: pip3 install {' '.join(missing_packages)}")
        return False
    
    print("✅ All dependencies satisfied")
    return True

def check_config():
    """Check if configuration is valid"""
    print("🔧 Checking configuration...")
    
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
        from utils.config_manager import get_config
        
        config_manager = get_config()
        if config_manager.validate_config():
            print("✅ Configuration valid")
            return True
        else:
            print("❌ Configuration validation failed")
            return False
            
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def test_alpaca_connection():
    """Test Alpaca API connection"""
    print("🔗 Testing Alpaca connection...")
    
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
        from utils.config_manager import get_config
        from api.alpaca_client import AlpacaClient
        
        config_manager = get_config()
        alpaca_client = AlpacaClient(config_manager)
        
        account = alpaca_client.get_account()
        print(f"✅ Connected to Alpaca")
        print(f"   Account Status: {account.status}")
        print(f"   Portfolio Value: ${account.portfolio_value:.2f}")
        print(f"   Buying Power: ${account.buying_power:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Alpaca connection failed: {e}")
        return False

def run_bot():
    """Run the main trading bot"""
    print("🤖 Starting autonomous trading bot...")
    
    try:
        # Change to src directory
        bot_path = os.path.join(os.path.dirname(__file__), 'src', 'main_bot.py')
        
        # Run the bot
        subprocess.run([sys.executable, bot_path], check=True)
        
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Bot execution failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def run_dashboard():
    """Run the web dashboard"""
    print("📊 Starting web dashboard...")
    
    try:
        # Change to dashboard directory
        dashboard_path = os.path.join(os.path.dirname(__file__), 'src', 'dashboard', 'app.py')
        
        # Run the dashboard
        subprocess.run([sys.executable, dashboard_path], check=True)
        
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Dashboard execution failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Autonomous Trading Bot')
    parser.add_argument('--mode', choices=['bot', 'dashboard', 'both'], default='bot',
                       help='Run mode: bot only, dashboard only, or both')
    parser.add_argument('--skip-checks', action='store_true',
                       help='Skip dependency and configuration checks')
    
    args = parser.parse_args()
    
    print_banner()
    
    if not args.skip_checks:
        # Pre-flight checks
        if not check_dependencies():
            sys.exit(1)
        
        if not check_config():
            sys.exit(1)
        
        if not test_alpaca_connection():
            sys.exit(1)
        
        print("✅ All pre-flight checks passed!\n")
    
    # Confirm before starting
    if not args.skip_checks:
        response = input("🚨 Ready to start live trading? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("👋 Startup cancelled by user")
            sys.exit(0)
    
    # Run based on mode
    if args.mode == 'dashboard':
        run_dashboard()
    elif args.mode == 'both':
        print("🚀 Running both bot and dashboard is not yet supported")
        print("💡 Run them in separate terminals:")
        print("   Terminal 1: python3 run_bot.py --mode bot")
        print("   Terminal 2: python3 run_bot.py --mode dashboard")
    else:
        run_bot()

if __name__ == "__main__":
    main()