#!/usr/bin/env python3
"""
Command-line interface for the Autonomous Trading AI
"""

import argparse
import asyncio
import sys
from typing import List, Optional
from datetime import datetime
from src.analysis.technical_analyzer import TechnicalAnalyzer
from src.trading.portfolio_manager import PortfolioManager
from src.notifications.notifier import NotificationManager
from src.utils.config import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class TradingCLI:
    """Command-line interface for the trading bot"""
    
    def __init__(self):
        self.config = Config()
        self.technical_analyzer = TechnicalAnalyzer()
        self.portfolio_manager = PortfolioManager()
        self.notification_manager = NotificationManager()
    
    async def initialize(self):
        """Initialize all components"""
        await self.technical_analyzer.initialize()
        await self.portfolio_manager.initialize()
        await self.notification_manager.initialize()
    
    async def scan_markets(self, symbols: Optional[List[str]] = None):
        """Scan markets for trading opportunities"""
        print("🔍 Scanning markets for opportunities...")
        
        # Run market scans
        stock_opportunities = await self.technical_analyzer.scan_stocks(symbols)
        crypto_opportunities = await self.technical_analyzer.scan_crypto()
        
        total_opportunities = len(stock_opportunities) + len(crypto_opportunities)
        
        print(f"\n📊 Market Scan Results:")
        print(f"   Stock opportunities: {len(stock_opportunities)}")
        print(f"   Crypto opportunities: {len(crypto_opportunities)}")
        print(f"   Total opportunities: {total_opportunities}")
        
        # Display top opportunities
        if stock_opportunities:
            print(f"\n📈 Top Stock Opportunities:")
            for i, opp in enumerate(stock_opportunities[:5], 1):
                print(f"   {i}. {opp.symbol} - {opp.strategy}")
                print(f"      Entry: ${opp.entry_price:.2f} | Target: ${opp.target_price:.2f} | Stop: ${opp.stop_loss:.2f}")
                print(f"      Confidence: {opp.confidence_score:.1%}")
        
        if crypto_opportunities:
            print(f"\n💰 Top Crypto Opportunities:")
            for i, opp in enumerate(crypto_opportunities[:5], 1):
                print(f"   {i}. {opp.symbol} - {opp.strategy}")
                print(f"      Entry: ${opp.entry_price:.2f} | Target: ${opp.target_price:.2f} | Stop: ${opp.stop_loss:.2f}")
                print(f"      Confidence: {opp.confidence_score:.1%}")
        
        return stock_opportunities, crypto_opportunities
    
    async def analyze_trades(self, budget: float, profit_goal: float, symbols: Optional[List[str]] = None):
        """Analyze and suggest trades based on budget and goals"""
        print(f"💡 Analyzing trades with ${budget:.2f} budget and {profit_goal}% profit goal...")
        
        # Get opportunities
        stock_opportunities, crypto_opportunities = await self.scan_markets(symbols)
        
        if not stock_opportunities and not crypto_opportunities:
            print("❌ No trading opportunities found at this time.")
            return
        
        # Generate trade suggestions
        suggestions = await self.portfolio_manager.generate_trade_suggestions(
            stock_opportunities, crypto_opportunities, budget, profit_goal
        )
        
        if not suggestions:
            print("❌ No suitable trade suggestions could be generated.")
            return
        
        # Calculate portfolio metrics
        risk_metrics = self.portfolio_manager.calculate_portfolio_risk(suggestions)
        
        # Display results
        print(f"\n💼 Trade Suggestions ({len(suggestions)} total):")
        print(f"   Budget allocated: ${risk_metrics['total_position_value']:.2f}")
        print(f"   Total risk exposure: ${risk_metrics['total_max_risk']:.2f}")
        print(f"   Portfolio risk: {risk_metrics['risk_percentage']:.2f}%")
        
        print(f"\n📋 Asset Allocation:")
        print(f"   Stocks: {risk_metrics['stock_allocation_pct']:.1f}%")
        print(f"   Options: {risk_metrics['options_allocation_pct']:.1f}%")
        print(f"   Crypto: {risk_metrics['crypto_allocation_pct']:.1f}%")
        
        print(f"\n🎯 Recommended Trades:")
        for i, suggestion in enumerate(suggestions[:10], 1):
            trade_emoji = "📈" if "buy" in suggestion.trade_type else "📉" if "sell" in suggestion.trade_type else "⚡"
            
            print(f"   {i}. {trade_emoji} {suggestion.symbol} ({suggestion.trade_type})")
            print(f"      Strategy: {suggestion.strategy}")
            print(f"      Entry: ${suggestion.entry_price:.2f} | Target: ${suggestion.target_price:.2f} | Stop: ${suggestion.stop_loss:.2f}")
            print(f"      Position size: ${suggestion.position_size:.2f}")
            print(f"      Risk/Reward: {suggestion.risk_reward_ratio:.2f} | Confidence: {suggestion.confidence:.1%}")
            
            if suggestion.option_strike:
                print(f"      Option Strike: ${suggestion.option_strike:.2f} | Expiry: {suggestion.option_expiry}")
            
            print()
        
        # Send summary notification
        await self.notification_manager.send_market_summary(
            len(stock_opportunities) + len(crypto_opportunities),
            budget,
            len(suggestions)
        )
    
    async def analyze_symbol(self, symbol: str):
        """Analyze a specific symbol"""
        print(f"🔍 Analyzing {symbol}...")
        
        signal = self.technical_analyzer.analyze_symbol(symbol.upper())
        
        if not signal:
            print(f"❌ Could not analyze {symbol}. Symbol may not exist or data unavailable.")
            return
        
        print(f"\n📊 Technical Analysis for {signal.symbol}:")
        print(f"   Current Price: ${signal.price:.2f}")
        print(f"   Volume: {signal.volume:,}")
        print(f"   RSI: {signal.rsi_value:.2f}")
        print(f"   MACD: {signal.macd_value:.4f}")
        print(f"   MACD Signal: {signal.macd_signal:.4f}")
        print(f"   Signal: {signal.signal_type.upper()}")
        print(f"   Confidence: {signal.confidence:.1%}")
        
        # Signal interpretation
        if signal.rsi_value:
            if signal.rsi_value < 30:
                print(f"   🟢 RSI indicates oversold condition")
            elif signal.rsi_value > 70:
                print(f"   🔴 RSI indicates overbought condition")
            else:
                print(f"   🟡 RSI in neutral territory")
        
        if signal.macd_histogram:
            if signal.macd_histogram > 0:
                print(f"   📈 MACD histogram is positive (bullish momentum)")
            else:
                print(f"   📉 MACD histogram is negative (bearish momentum)")
    
    async def monitor_positions(self):
        """Monitor existing positions (placeholder for future implementation)"""
        print("👀 Position monitoring is not yet implemented.")
        print("This feature will track your open trades and send alerts when exit conditions are met.")
    
    def display_config(self):
        """Display current configuration"""
        print("⚙️  Current Configuration:")
        print(f"   Max position size: {self.config.trading.max_position_size_pct:.1%}")
        print(f"   Max daily risk: {self.config.trading.max_daily_risk_pct:.1%}")
        print(f"   Min risk/reward ratio: {self.config.trading.min_risk_reward_ratio:.1f}")
        print(f"   RSI period: {self.config.trading.rsi_period}")
        print(f"   RSI oversold: {self.config.trading.rsi_oversold}")
        print(f"   RSI overbought: {self.config.trading.rsi_overbought}")
        
        # Validate config
        status = self.config.validate_config()
        if status['warnings']:
            print(f"\n⚠️  Configuration Warnings:")
            for warning in status['warnings']:
                print(f"   • {warning}")

def create_parser():
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="Autonomous Trading AI - Market Analysis and Trading Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.cli scan                              # Scan markets for opportunities
  python -m src.cli analyze --budget 1000 --goal 15  # Analyze trades for $1000 budget
  python -m src.cli symbol AAPL                       # Analyze specific symbol
  python -m src.cli config                            # Show configuration
  python -m src.cli monitor                           # Monitor positions (future)
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Scan command
    scan_parser = subparsers.add_parser('scan', help='Scan markets for opportunities')
    scan_parser.add_argument('--symbols', nargs='+', help='Specific symbols to scan')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Generate trade suggestions')
    analyze_parser.add_argument('--budget', type=float, required=True, 
                               help='Trading budget in dollars')
    analyze_parser.add_argument('--goal', type=float, default=15.0,
                               help='Profit goal percentage (default: 15)')
    analyze_parser.add_argument('--symbols', nargs='+', help='Specific symbols to analyze')
    
    # Symbol command
    symbol_parser = subparsers.add_parser('symbol', help='Analyze specific symbol')
    symbol_parser.add_argument('symbol', help='Symbol to analyze (e.g., AAPL, BTC-USD)')
    
    # Monitor command
    subparsers.add_parser('monitor', help='Monitor existing positions')
    
    # Config command
    subparsers.add_parser('config', help='Show configuration')
    
    return parser

async def main():
    """Main CLI entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = TradingCLI()
    
    try:
        await cli.initialize()
        
        if args.command == 'scan':
            await cli.scan_markets(args.symbols)
        
        elif args.command == 'analyze':
            await cli.analyze_trades(args.budget, args.goal, args.symbols)
        
        elif args.command == 'symbol':
            await cli.analyze_symbol(args.symbol)
        
        elif args.command == 'monitor':
            await cli.monitor_positions()
        
        elif args.command == 'config':
            cli.display_config()
    
    except KeyboardInterrupt:
        print("\n👋 Trading bot interrupted by user")
    
    except Exception as e:
        logger.error(f"CLI error: {e}")
        print(f"❌ Error: {e}")
    
    finally:
        # Cleanup
        await cli.notification_manager.shutdown()

if __name__ == "__main__":
    asyncio.run(main())