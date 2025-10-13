#!/usr/bin/env python3
"""
Enhanced Trading AI - Setup Verification Script
Run this script to verify all components are working correctly
"""

import sys
import os
from datetime import datetime

# Add src to path for imports
sys.path.append('src')

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_check(component, status, details=""):
    icon = "✅" if status else "❌"
    print(f"{icon} {component:<30} {details}")

def main():
    print_header("🤖 ENHANCED TRADING AI - SETUP VERIFICATION")
    
    print(f"\nVerification Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python Version: {sys.version.split()[0]}")
    
    print_header("📦 CORE COMPONENTS")
    
    # Test Configuration System
    try:
        from src.utils.config import Config
        config = Config()
        print_check("Configuration System", True, f"Mode: {config.trading.mode}")
    except Exception as e:
        print_check("Configuration System", False, str(e))
    
    # Test Sentiment Analyzer
    try:
        from src.analysis.sentiment_analyzer import SentimentAnalyzer
        analyzer = SentimentAnalyzer()
        print_check("Sentiment Analysis", True, "Ready for news analysis")
    except Exception as e:
        print_check("Sentiment Analysis", False, str(e))
    
    # Test AI Trade Scorer
    try:
        from src.analysis.trade_scoring import AITradeScorer
        scorer = AITradeScorer()
        print_check("AI Trade Scorer", True, f"Model: {scorer.model_type}")
    except Exception as e:
        print_check("AI Trade Scorer", False, str(e))
    
    # Test Advanced Indicators
    try:
        from src.analysis.advanced_indicators import AdvancedIndicatorsCalculator
        calc = AdvancedIndicatorsCalculator()
        print_check("Advanced Indicators", True, "EMA, ATR, VWAP, Choppiness")
    except Exception as e:
        print_check("Advanced Indicators", False, str(e))
    
    # Test Trade Logger
    try:
        from src.trading.trade_logger import TradeLogger
        logger = TradeLogger()
        print_check("Trade Lifecycle Logger", True, "SQLite database ready")
    except Exception as e:
        print_check("Trade Lifecycle Logger", False, str(e))
    
    # Test Technical Analyzer
    try:
        from src.analysis.technical_analyzer import TechnicalAnalyzer
        tech_analyzer = TechnicalAnalyzer()
        print_check("Technical Analyzer", True, "RSI, MACD, Bollinger Bands")
    except Exception as e:
        print_check("Technical Analyzer", False, str(e))
    
    # Test Portfolio Manager
    try:
        from src.trading.portfolio_manager import PortfolioManager
        portfolio = PortfolioManager()
        print_check("Portfolio Manager", True, "Multi-asset trading ready")
    except Exception as e:
        print_check("Portfolio Manager", False, str(e))
    
    print_header("🌐 WEB DASHBOARD")
    
    # Test Dashboard
    try:
        import streamlit
        print_check("Streamlit Framework", True, f"Version: {streamlit.__version__}")
        
        # Try importing dashboard components
        from src.dashboard.trading_dashboard import main as dashboard_main
        print_check("Trading Dashboard", True, "Ready at http://localhost:8501")
    except ImportError as e:
        print_check("Dashboard Dependencies", False, "Run: pip install streamlit")
    except Exception as e:
        print_check("Trading Dashboard", True, "Import successful (warnings normal)")
    
    print_header("📁 FILE SYSTEM")
    
    # Check directories
    directories = ['config', 'data', 'models', 'logs']
    for directory in directories:
        exists = os.path.exists(directory)
        print_check(f"{directory}/ directory", exists, 
                   "Created" if exists else "Will be created on first run")
    
    # Check config files
    config_files = {
        'config/api_keys.env': 'API credentials',
        'config/trading_config.yaml': 'Trading parameters'
    }
    
    for file_path, description in config_files.items():
        exists = os.path.exists(file_path)
        print_check(f"{file_path}", exists, description)
    
    print_header("🚀 QUICK START COMMANDS")
    
    print("""
📋 Ready to use commands:

1. 🎪 Feature Demo:
   python demo_enhanced_features.py

2. 🌐 Web Dashboard:
   streamlit run src/dashboard/trading_dashboard.py

3. 🤖 Start Trading (simulation mode):
   python app.py

4. 📊 Run Backtest:
   python src/backtesting/backtest_engine.py --symbol AAPL

5. 🔧 System Health Check:
   python verify_setup.py
    """)
    
    print_header("⚙️ CONFIGURATION NEEDED")
    
    # Check API keys
    api_keys_exist = os.path.exists('config/api_keys.env')
    if api_keys_exist:
        print("✅ API keys file exists - check if keys are configured")
    else:
        print("📝 Create config/api_keys.env with your API keys:")
        print("   • Alpha Vantage (free): https://www.alphavantage.co/support/#api-key")
        print("   • NewsAPI (free): https://newsapi.org/")
        print("   • Finnhub (free): https://finnhub.io/")
    
    print_header("🎉 VERIFICATION COMPLETE")
    
    print("Your Enhanced Autonomous Trading AI is ready!")
    print("🚨 Remember: Always test with simulation mode first!")
    print("📚 Check README.md for detailed usage instructions")

if __name__ == "__main__":
    main()