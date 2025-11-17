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
from src.analysis.sentiment_analyzer import SentimentAnalyzer
from src.analysis.trade_scoring import AITradeScorer
from src.analysis.advanced_indicators import AdvancedIndicatorsCalculator
from src.trading.portfolio_manager import PortfolioManager
from src.trading.trade_logger import TradeLogger
from src.notifications.notifier import NotificationManager
from src.utils.config import Config

logger = setup_logger(__name__)

class TradingBot:
    """
    ENHANCED AUTONOMOUS TRADING BOT - FULL AI SUITE
    
    Now includes:
    - AI-powered trade scoring with machine learning
    - Advanced sentiment analysis from news sources
    - Enhanced technical indicators (EMA, ATR, VWAP, Choppiness)
    - Complete trade lifecycle logging
    - Dynamic position sizing based on confidence
    - Multi-timeframe analysis
    
    CUSTOMIZE: All modules are configurable via trading_config.yaml
    """
    
    def __init__(self):
        self.config = Config()
        
        # Core analysis engines
        self.technical_analyzer = TechnicalAnalyzer()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.trade_scorer = AITradeScorer()
        self.advanced_indicators = AdvancedIndicatorsCalculator()
        
        # Trading and logging
        self.portfolio_manager = PortfolioManager()
        self.trade_logger = TradeLogger()
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
        """Run enhanced market scan with AI scoring and sentiment analysis"""
        logger.info("Starting enhanced AI market scan...")
        
        # Get initial technical opportunities
        stock_opportunities = await self.technical_analyzer.scan_stocks()
        crypto_opportunities = await self.technical_analyzer.scan_crypto()
        
        # Enhance with sentiment analysis and AI scoring
        enhanced_stock_opportunities = await self._enhance_opportunities_with_ai(
            stock_opportunities, 'stock'
        )
        enhanced_crypto_opportunities = await self._enhance_opportunities_with_ai(
            crypto_opportunities, 'crypto'
        )
        
        # Filter by minimum confidence score
        min_confidence = getattr(self.config.trading, 'min_confidence_score', 0.6)
        
        filtered_stocks = [
            opp for opp in enhanced_stock_opportunities 
            if opp.get('ai_score', 0) >= min_confidence
        ]
        filtered_crypto = [
            opp for opp in enhanced_crypto_opportunities 
            if opp.get('ai_score', 0) >= min_confidence
        ]
        
        logger.info(f"Found {len(filtered_stocks)}/{len(stock_opportunities)} qualifying stock opportunities")
        logger.info(f"Found {len(filtered_crypto)}/{len(crypto_opportunities)} qualifying crypto opportunities")
        
        return filtered_stocks, filtered_crypto
    
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
    
    async def _enhance_opportunities_with_ai(self, opportunities, asset_type: str):
        """
        Enhance trading opportunities with AI scoring and sentiment analysis
        
        AI ENHANCEMENT PIPELINE - MODIFY FOR DIFFERENT SCORING APPROACHES:
        1. Get sentiment score from news analysis
        2. Calculate advanced technical indicators 
        3. Generate AI confidence score
        4. Apply dynamic position sizing
        """
        enhanced_opportunities = []
        
        for opportunity in opportunities:
            try:
                symbol = opportunity.symbol
                
                # Get sentiment analysis
                sentiment_score = await self.sentiment_analyzer.get_sentiment_score(symbol)
                
                # Get advanced indicators
                advanced_indicators = self.advanced_indicators.calculate_all_indicators(symbol)
                
                # Get technical signal from opportunity
                technical_signal = opportunity.technical_signals[0] if opportunity.technical_signals else None
                
                if technical_signal:
                    # Calculate AI trade score
                    trade_score = self.trade_scorer.calculate_trade_score(
                        symbol=symbol,
                        technical_signal=technical_signal,
                        sentiment_score=sentiment_score,
                        volume_data=None,  # Could enhance with volume analysis
                        market_data=None   # Could enhance with market regime data
                    )
                    
                    # Calculate dynamic position size based on confidence
                    base_size = getattr(self.config.trading, 'base_position_size_pct', 0.05)
                    confidence_bonus = getattr(self.config.trading, 'max_confidence_bonus_pct', 0.10)
                    
                    dynamic_position_size = base_size + (trade_score.confidence_score * confidence_bonus)
                    dynamic_position_size = min(dynamic_position_size, 0.15)  # Cap at 15%
                    
                    # Create enhanced opportunity
                    enhanced_opp = {
                        'symbol': symbol,
                        'asset_type': asset_type,
                        'entry_price': opportunity.entry_price,
                        'target_price': opportunity.target_price,
                        'stop_loss': opportunity.stop_loss,
                        'strategy': opportunity.strategy,
                        'confidence_score': opportunity.confidence_score,
                        'ai_score': trade_score.confidence_score,
                        'signal_strength': trade_score.signal_strength,
                        'sentiment_score': sentiment_score.overall_sentiment if sentiment_score else 0.0,
                        'sentiment_confidence': sentiment_score.confidence if sentiment_score else 0.0,
                        'dynamic_position_size': dynamic_position_size,
                        'technical_signals': opportunity.technical_signals,
                        'advanced_indicators': advanced_indicators,
                        'trade_score_components': trade_score.components
                    }
                    
                    enhanced_opportunities.append(enhanced_opp)
                    
                    logger.debug(f"Enhanced {symbol}: AI Score {trade_score.confidence_score:.3f}, "
                               f"Sentiment {sentiment_score.overall_sentiment:.3f} if sentiment_score else 0.0, "
                               f"Position Size {dynamic_position_size:.3f}")
                    
            except Exception as e:
                logger.error(f"Error enhancing opportunity for {opportunity.symbol}: {e}")
                # Fallback to original opportunity
                enhanced_opportunities.append({
                    'symbol': opportunity.symbol,
                    'asset_type': asset_type,
                    'entry_price': opportunity.entry_price,
                    'target_price': opportunity.target_price,
                    'stop_loss': opportunity.stop_loss,
                    'strategy': opportunity.strategy,
                    'confidence_score': opportunity.confidence_score,
                    'ai_score': 0.5,  # Neutral score on error
                    'signal_strength': 'weak'
                })
        
        return enhanced_opportunities

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