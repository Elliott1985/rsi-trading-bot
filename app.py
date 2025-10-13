#!/usr/bin/env python3
"""
Autonomous Trading AI - Main Application
A modular AI-powered trading assistant for stocks and crypto
"""

import sys
import asyncio
from pathlib import Path
from src.utils.logger import setup_logger
from src.analysis.technical_analyzer import TechnicalAnalyzer
from src.trading.portfolio_manager import PortfolioManager
from src.notifications.notifier import NotificationManager
from src.utils.config import Config

logger = setup_logger(__name__)

class TradingBot:
    """Main trading bot orchestrator"""
    
    def __init__(self):
        self.config = Config()
        self.technical_analyzer = TechnicalAnalyzer()
        self.portfolio_manager = PortfolioManager()
        self.notification_manager = NotificationManager()
        
    async def initialize(self):
        """Initialize all bot components"""
        logger.info("Initializing Autonomous Trading AI...")
        
        # Initialize components
        await self.technical_analyzer.initialize()
        await self.portfolio_manager.initialize()
        await self.notification_manager.initialize()
        
        logger.info("Bot initialization complete!")
        
    async def run_market_scan(self):
        """Run pre-market scan for optimal trading opportunities"""
        logger.info("Starting market scan...")
        
        # Analyze stocks and crypto for optimal trades
        stock_opportunities = await self.technical_analyzer.scan_stocks()
        crypto_opportunities = await self.technical_analyzer.scan_crypto()
        
        # Log opportunities
        logger.info(f"Found {len(stock_opportunities)} stock opportunities")
        logger.info(f"Found {len(crypto_opportunities)} crypto opportunities")
        
        return stock_opportunities, crypto_opportunities
    
    async def analyze_trades(self, budget: float, profit_goal: float):
        """Analyze and suggest optimal trades based on budget and goals"""
        logger.info(f"Analyzing trades with budget: ${budget}, profit goal: {profit_goal}%")
        
        # Get current opportunities
        stock_opportunities, crypto_opportunities = await self.run_market_scan()
        
        # Generate trade suggestions
        suggestions = await self.portfolio_manager.generate_trade_suggestions(
            stock_opportunities, crypto_opportunities, budget, profit_goal
        )
        
        return suggestions
    
    async def run(self):
        """Main bot execution loop"""
        try:
            await self.initialize()
            
            # Example usage - this will be expanded based on CLI commands
            budget = 1000.0
            profit_goal = 15.0
            
            suggestions = await self.analyze_trades(budget, profit_goal)
            
            for suggestion in suggestions:
                logger.info(f"Trade suggestion: {suggestion}")
                
        except Exception as e:
            logger.error(f"Bot execution error: {e}")
            raise

def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command in ['--help', '-h']:
            print("Autonomous Trading AI Bot")
            print("Usage: python app.py [scan|analyze|monitor]")
            return
    
    # Run the bot
    bot = TradingBot()
    asyncio.run(bot.run())

if __name__ == "__main__":
    main()