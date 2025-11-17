#!/usr/bin/env python3
"""
Enhanced Autonomous Trading AI - Feature Demo
Demonstrates all the new AI-powered features and capabilities
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.analysis.sentiment_analyzer import SentimentAnalyzer
from src.analysis.trade_scoring import AITradeScorer
from src.analysis.advanced_indicators import AdvancedIndicatorsCalculator
from src.analysis.technical_analyzer import TechnicalAnalyzer, TechnicalSignal
from src.trading.trade_logger import TradeLogger, TradeEntry
from src.utils.config import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def print_header(title: str):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_section(title: str):
    """Print a formatted section"""
    print(f"\n{'-'*40}")
    print(f"  {title}")
    print(f"{'-'*40}")

async def demo_sentiment_analysis():
    """Demo sentiment analysis features"""
    print_section("🔍 NEWS SENTIMENT ANALYSIS DEMO")
    
    analyzer = SentimentAnalyzer()
    
    # Test symbols
    symbols = ['AAPL', 'TSLA', 'BTC-USD']
    
    print("Analyzing news sentiment for popular symbols...")
    print("(Note: Requires NewsAPI or Finnhub API key for full functionality)")
    
    for symbol in symbols:
        print(f"\n📰 Analyzing {symbol}:")
        
        sentiment = await analyzer.get_sentiment_score(symbol, lookback_hours=24)
        
        if sentiment:
            print(f"   Overall Sentiment: {sentiment.overall_sentiment:.3f} (-1.0 to +1.0)")
            print(f"   Confidence: {sentiment.confidence:.3f}")
            print(f"   Article Count: {sentiment.article_count}")
            print(f"   Sources: {', '.join(sentiment.sources)}")
            
            # Interpret sentiment
            if sentiment.overall_sentiment > 0.1:
                sentiment_desc = "🟢 BULLISH"
            elif sentiment.overall_sentiment < -0.1:
                sentiment_desc = "🔴 BEARISH"
            else:
                sentiment_desc = "🟡 NEUTRAL"
            
            print(f"   Interpretation: {sentiment_desc}")
        else:
            print(f"   ⚠️ No sentiment data available (API key needed)")

def demo_advanced_indicators():
    """Demo advanced technical indicators"""
    print_section("📈 ADVANCED TECHNICAL INDICATORS DEMO")
    
    calc = AdvancedIndicatorsCalculator()
    
    symbols = ['AAPL', 'ETH-USD']
    
    for symbol in symbols:
        print(f"\n🔍 Analyzing {symbol} with advanced indicators:")
        
        indicators = calc.calculate_all_indicators(symbol)
        
        if indicators:
            print(f"   EMA Crossover: {indicators.ema_crossover}")
            print(f"   VWAP Signal: {indicators.vwap_signal}")
            print(f"   Market Condition: {'Choppy' if indicators.is_choppy else 'Trending'}")
            print(f"   Multi-timeframe Bias: {indicators.multi_timeframe_bias}")
            
            if indicators.atr_stop_loss:
                print(f"   ATR Stop Loss: ${indicators.atr_stop_loss:.2f}")
            
            # Get composite signal
            signal_type, signal_strength = calc.calculate_composite_signal(indicators)
            print(f"   Composite Signal: {signal_type.upper()} (strength: {signal_strength:.2f})")
            
            # Get indicator summary
            summary = calc.get_indicator_summary(indicators)
            print(f"   Indicator Summary: {summary}")
        else:
            print(f"   ⚠️ Could not calculate indicators for {symbol}")

async def demo_ai_trade_scoring():
    """Demo AI trade scoring system"""
    print_section("🤖 AI TRADE SCORING DEMO")
    
    scorer = AITradeScorer()
    analyzer = TechnicalAnalyzer()
    sentiment_analyzer = SentimentAnalyzer()
    
    symbols = ['AAPL', 'TSLA']
    
    for symbol in symbols:
        print(f"\n🎯 AI Scoring for {symbol}:")
        
        # Get technical signal
        technical_signal = analyzer.analyze_symbol(symbol)
        
        if technical_signal:
            # Get sentiment (optional)
            sentiment = await sentiment_analyzer.get_sentiment_score(symbol)
            
            # Calculate AI score
            trade_score = scorer.calculate_trade_score(
                symbol=symbol,
                technical_signal=technical_signal,
                sentiment_score=sentiment
            )
            
            print(f"   AI Confidence Score: {trade_score.confidence_score:.3f}")
            print(f"   Signal Strength: {trade_score.signal_strength.upper()}")
            print(f"   Component Breakdown:")
            for component, score in trade_score.components.items():
                print(f"     - {component}: {score:.3f}")
            
            # Trading recommendation
            if trade_score.confidence_score >= 0.8:
                recommendation = "🟢 STRONG TRADE"
            elif trade_score.confidence_score >= 0.6:
                recommendation = "🟡 CONSIDER TRADE"
            else:
                recommendation = "🔴 AVOID TRADE"
            
            print(f"   Recommendation: {recommendation}")
        else:
            print(f"   ⚠️ Could not analyze {symbol}")

def demo_trade_logging():
    """Demo trade lifecycle logging"""
    print_section("📊 TRADE LIFECYCLE LOGGING DEMO")
    
    logger_instance = TradeLogger()
    
    print("Trade logging system capabilities:")
    print("✅ SQLite database for persistence")
    print("✅ Complete trade lifecycle tracking")
    print("✅ Performance analytics")
    print("✅ CSV export functionality")
    
    # Demo trade entry
    demo_trade = TradeEntry(
        trade_id="DEMO_001",
        symbol="AAPL",
        trade_type="buy",
        entry_price=150.00,
        entry_time=datetime.now(),
        quantity=10,
        stop_loss=142.50,
        take_profit=165.00,
        confidence_score=0.85,
        strategy="AI Enhanced Momentum",
        notes="Demo trade for system testing"
    )
    
    # Log the demo trade
    success = logger_instance.log_trade_entry(demo_trade)
    if success:
        print(f"\n✅ Demo trade logged: {demo_trade.trade_id}")
    
    # Show performance summary
    performance = logger_instance.get_performance_summary(days=30)
    print(f"\n📈 Performance Summary (30 days):")
    print(f"   Total Trades: {performance.get('total_trades', 0)}")
    print(f"   Win Rate: {performance.get('win_rate', 0):.1f}%")
    print(f"   Total P&L: ${performance.get('total_pnl', 0):.2f}")
    
    # Show open trades
    open_trades = logger_instance.get_open_trades()
    print(f"\n💼 Open Positions: {len(open_trades)}")

def demo_configuration_system():
    """Demo the enhanced configuration system"""
    print_section("⚙️ ENHANCED CONFIGURATION SYSTEM")
    
    config = Config()
    
    print("Configuration file locations:")
    print(f"✅ API Keys: {config.config_dir}/api_keys.env")
    print(f"✅ Trading Config: {config.config_dir}/trading_config.yaml")
    
    print(f"\n🔧 Current Trading Parameters:")
    print(f"   RSI Oversold: {config.trading.rsi_oversold}")
    print(f"   RSI Overbought: {config.trading.rsi_overbought}")
    print(f"   Max Position Size: {config.trading.max_position_size_pct*100:.1f}%")
    print(f"   Max Daily Risk: {config.trading.max_daily_risk_pct*100:.1f}%")
    print(f"   Min Risk/Reward: {config.trading.min_risk_reward_ratio:.1f}")
    
    # Validate configuration
    validation = config.validate_config()
    print(f"\n✅ Configuration Status:")
    print(f"   Valid: {validation['valid']}")
    if validation.get('warnings'):
        print(f"   Warnings: {len(validation['warnings'])}")
    if validation.get('errors'):
        print(f"   Errors: {len(validation['errors'])}")

def demo_dynamic_position_sizing():
    """Demo dynamic position sizing based on confidence"""
    print_section("💰 DYNAMIC POSITION SIZING DEMO")
    
    print("Dynamic position sizing examples:")
    
    # Sample confidence scores and their position sizes
    confidence_scenarios = [
        (0.9, "Very Strong Signal"),
        (0.8, "Strong Signal"), 
        (0.7, "Good Signal"),
        (0.6, "Moderate Signal"),
        (0.5, "Weak Signal")
    ]
    
    base_size = 0.05  # 5% base
    max_bonus = 0.10  # 10% max bonus
    
    print(f"\nBase Position Size: {base_size*100:.1f}%")
    print(f"Max Confidence Bonus: {max_bonus*100:.1f}%")
    print(f"Position Size Formula: base_size + (confidence * max_bonus)")
    
    print(f"\n{'Confidence':<12} {'Signal Strength':<18} {'Position Size':<15}")
    print("-" * 50)
    
    for confidence, description in confidence_scenarios:
        position_size = base_size + (confidence * max_bonus)
        position_size = min(position_size, 0.15)  # Cap at 15%
        
        print(f"{confidence:<12.1f} {description:<18} {position_size*100:<15.1f}%")

def demo_portfolio_mode():
    """Demo portfolio mode capabilities"""
    print_section("📊 PORTFOLIO MODE DEMO")
    
    print("Portfolio management features:")
    print("✅ Multi-ticker concurrent scanning")
    print("✅ Capital allocation based on confidence scores")
    print("✅ Maximum concurrent trade limits")
    print("✅ Portfolio heat management (total risk)")
    print("✅ Correlation analysis to avoid similar trades")
    
    # Sample portfolio allocation
    sample_trades = [
        {"symbol": "AAPL", "confidence": 0.85, "allocation": "$850"},
        {"symbol": "TSLA", "confidence": 0.75, "allocation": "$750"},
        {"symbol": "BTC-USD", "confidence": 0.70, "allocation": "$700"},
        {"symbol": "ETH-USD", "confidence": 0.65, "allocation": "$650"},
        {"symbol": "MSFT", "confidence": 0.60, "allocation": "$600"}
    ]
    
    print(f"\n💼 Sample Portfolio Allocation:")
    print(f"{'Symbol':<10} {'Confidence':<12} {'Allocation':<12}")
    print("-" * 35)
    
    for trade in sample_trades:
        print(f"{trade['symbol']:<10} {trade['confidence']:<12.2f} {trade['allocation']:<12}")
    
    total_allocation = sum(int(t['allocation'].replace('$', '')) for t in sample_trades)
    print(f"\nTotal Allocated: ${total_allocation:,}")
    print(f"Portfolio Heat: {(total_allocation / 10000) * 100:.1f}% of $10,000 account")

def display_system_summary():
    """Display comprehensive system capabilities"""
    print_header("🤖 AUTONOMOUS TRADING AI - ENHANCED SYSTEM SUMMARY")
    
    print("""
🚀 CORE AI ENHANCEMENTS:
   ✅ AI-Powered Trade Scoring (0.0-1.0 confidence)
   ✅ Real-time News Sentiment Analysis  
   ✅ Advanced Technical Indicators (EMA, ATR, VWAP, Choppiness)
   ✅ Multi-timeframe Analysis
   ✅ Dynamic Position Sizing

📊 TRADING FEATURES:
   ✅ Portfolio Mode (3-5 concurrent trades)
   ✅ Complete Trade Lifecycle Logging
   ✅ Performance Analytics & Reporting
   ✅ Risk Management & Portfolio Heat
   ✅ Multiple Trading Modes (Live/Demo/Simulation)

🎛️ CONTROL INTERFACES:
   ✅ Web Dashboard (Streamlit-based)
   ✅ Enhanced Configuration System
   ✅ Weekly Performance Reports
   ✅ CSV Export & Data Analysis
   ✅ Real-time System Monitoring

🔍 ANALYSIS ENGINES:
   ✅ Technical: RSI, MACD, Bollinger Bands, EMA, ATR, VWAP
   ✅ Sentiment: NewsAPI, Finnhub integration
   ✅ ML Scoring: LightGBM/XGBoost ready
   ✅ Volume Profile & Market Regime Analysis

⚙️ CUSTOMIZATION OPTIONS:
   ✅ Adjustable confidence thresholds
   ✅ Configurable risk parameters  
   ✅ Flexible technical indicator settings
   ✅ Multiple news sources & timeframes
   ✅ Custom ML model integration
""")

def show_next_steps():
    """Show next steps for users"""
    print_header("🎯 NEXT STEPS & USAGE")
    
    print("""
🏃‍♂️ QUICK START:
   1. Configure API keys in config/api_keys.env
   2. Adjust trading parameters in config/trading_config.yaml  
   3. Run: python app.py (for full AI analysis)
   4. Run: streamlit run src/dashboard/trading_dashboard.py (for web dashboard)

🔧 CONFIGURATION:
   • Set NewsAPI key for sentiment analysis
   • Configure Finnhub for financial news
   • Adjust confidence thresholds (0.6-0.8 recommended)
   • Set position sizing and risk parameters

📈 TRADING MODES:
   • simulation: Test with fake money
   • demo: Use sample data for testing
   • live: Real trading (requires broker API setup)

🎛️ WEB DASHBOARD ACCESS:
   • URL: http://localhost:8501
   • Real-time performance monitoring
   • Interactive settings adjustment
   • Trade history analysis
   • System status monitoring

📁 KEY FILES TO CUSTOMIZE:
   • config/trading_config.yaml - All trading parameters
   • src/analysis/trade_scoring.py - AI scoring logic
   • src/analysis/sentiment_analyzer.py - News sentiment weights
   • src/analysis/advanced_indicators.py - Technical indicators
""")

async def main():
    """Run the comprehensive demo"""
    display_system_summary()
    
    # Run all demos
    await demo_sentiment_analysis()
    demo_advanced_indicators()
    await demo_ai_trade_scoring()
    demo_trade_logging()
    demo_configuration_system()
    demo_dynamic_position_sizing()
    demo_portfolio_mode()
    
    show_next_steps()
    
    print_header("🎉 DEMO COMPLETE")
    print("Your Autonomous Trading AI system is ready!")
    print("Check the web dashboard and start trading with confidence! 🚀")

if __name__ == "__main__":
    asyncio.run(main())