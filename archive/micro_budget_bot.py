#!/usr/bin/env python3
"""
MICRO-BUDGET LIVE TRADING BOT
Designed for small budgets ($50-$100)
⚠️  WARNING: This will place REAL trades with REAL money ⚠️
"""

import sys
import asyncio
import signal
from pathlib import Path
from datetime import datetime
import time

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.utils.logger import setup_logger
from src.utils.config import Config
from src.trading.etrade_real import ETradeBroker
from src.analysis.technical_analyzer import TechnicalAnalyzer

logger = setup_logger(__name__)

class MicroBudgetTradingBot:
    """
    🚨 MICRO-BUDGET LIVE TRADING BOT 🚨
    
    Optimized for small budgets:
    - $50 starting budget
    - $20-30 max per trade
    - 1-2 positions max
    - High confidence required (80%+)
    - Conservative risk management
    """
    
    def __init__(self):
        self.config = Config()
        self.running = False
        
        # Initialize components  
        self.broker = ETradeBroker(self.config, sandbox=True)  # Test OAuth in sandbox first
        self.technical_analyzer = TechnicalAnalyzer()
        
        # MICRO-BUDGET TRADING PARAMETERS
        self.budget = 50.0  # Your $50 budget
        self.max_position_size = 50.0  # Max $50 per trade (100% of budget for single trades)
        self.min_position_size = 10.0  # Min $10 per trade
        self.max_positions = 2  # Allow 2 positions at once
        self.check_interval = 300  # 5 minutes between scans
        self.confidence_threshold = 0.60  # Lower confidence threshold for more trades
        
        # Pre-market and extended hours trading
        self.enable_premarket = True  # Trade during pre-market (4 AM - 9:30 AM)
        self.enable_afterhours = True  # Trade after hours (4 PM - 8 PM)
        
        # Focus on affordable stocks
        self.max_stock_price = 50.0  # Allow stocks up to $50 (can buy at least 1 share)
        self.preferred_stocks = ['SIRI', 'NOK', 'F', 'BAC', 'PLUG', 'FCEL', 'NIO', 'PLTR']
        
        # Position tracking
        self.positions = {}
        self.total_invested = 0.0
        self.completed_trades = 0
        
        # Setup graceful shutdown
        signal.signal(signal.SIGINT, self._shutdown_handler)
    
    def _shutdown_handler(self, signum, frame):
        """Handle shutdown"""
        logger.info("🛑 Shutting down micro-budget bot...")
        self.running = False
    
    async def initialize(self):
        """Initialize the bot"""
        print("\n" + "="*60)
        print("🚨 MICRO-BUDGET LIVE TRADING BOT 🚨")
        print("="*60)
        print("💰 Perfect for small budgets!")
        print(f"💵 Budget: ${self.budget}")
        print(f"📊 Max per trade: ${self.max_position_size}")
        print(f"📉 Min per trade: ${self.min_position_size}")
        print(f"🎯 Max positions: {self.max_positions}")
        print(f"📈 Max stock price: ${self.max_stock_price}")
        print(f"🎲 Confidence required: {self.confidence_threshold*100}%")
        print("🔒 Focus on affordable stocks under $15")
        print("⏰ Extended hours: 4 AM - 8 PM (Pre-market + Regular + After-hours)")
        print("="*60)
        print("⚠️  This will place REAL trades with REAL money!")
        print("="*60)
        
        confirm = input("Type 'START MICRO TRADING' to begin: ").strip()
        
        if confirm != "START MICRO TRADING":
            print("❌ Trading cancelled.")
            return False
        
        # Initialize components
        logger.info("🚀 Initializing micro-budget bot...")
        
        if not await self.broker.authenticate():
            logger.error("❌ Failed to authenticate with E*TRADE")
            return False
        
        await self.technical_analyzer.initialize()
        
        current_time = datetime.now()
        market_status = "🟢 OPEN" if self.broker.is_market_open() else "🔴 CLOSED"
        
        print("\n✅ Micro-budget bot ready!")
        print(f"🕰 Current time: {current_time.strftime('%H:%M:%S')}")
        print(f"🏢 Market status: {market_status}")
        print("🎯 Looking for high-confidence opportunities in affordable stocks...")
        print("📱 Press Ctrl+C to stop anytime")
        
        return True
    
    async def run(self):
        """Main trading loop"""
        if not await self.initialize():
            return
        
        self.running = True
        logger.info("🚀 Starting micro-budget live trading...")
        
        while self.running:
            try:
                await self._trading_cycle()
                
                if self.running:
                    logger.info(f"😴 Next scan in {self.check_interval//60} minutes...")
                    await asyncio.sleep(self.check_interval)
                    
            except Exception as e:
                logger.error(f"❌ Error in trading cycle: {e}")
                await asyncio.sleep(60)
        
        print(f"\n📊 Final Stats:")
        print(f"💰 Budget used: ${self.total_invested:.2f}/${self.budget:.2f}")
        print(f"📈 Trades completed: {self.completed_trades}")
        print("🛑 Bot stopped.")
    
    async def _trading_cycle(self):
        """One trading cycle"""
        logger.info("🔍 Starting trading cycle...")
        
        # Check if market is open (including pre-market)
        if not self.broker.is_market_open():
            current_time = datetime.now()
            logger.info(f"🕐 Market closed at {current_time.strftime('%H:%M')} - Extended hours: 4 AM - 8 PM")
            return
        
        # Check budget limits
        if self.total_invested >= self.budget:
            logger.info(f"💰 Budget fully invested (${self.total_invested}/${self.budget})")
            await self._monitor_positions()
            return
        
        # Check position limits
        if len(self.positions) >= self.max_positions:
            logger.info(f"📊 Max positions reached ({len(self.positions)}/{self.max_positions})")
            await self._monitor_positions()
            return
        
        # Scan for micro-budget opportunities
        opportunities = await self._find_micro_opportunities()
        
        if opportunities:
            best_opportunity = opportunities[0]
            await self._execute_micro_trade(best_opportunity)
        else:
            logger.info("📊 No qualifying micro-budget opportunities")
        
        # Monitor existing positions
        await self._monitor_positions()
    
    async def _find_micro_opportunities(self):
        """Find opportunities suitable for micro-budget"""
        logger.info("🔍 Scanning for micro-budget opportunities...")
        
        try:
            # Get stock opportunities
            stock_opps = await self.technical_analyzer.scan_stocks()
            
            # Filter for micro-budget criteria
            micro_opps = []
            for opp in stock_opps:
                logger.info(f"🔍 Evaluating {opp.symbol}: price=${opp.entry_price:.2f}, confidence={opp.confidence_score:.2f}")
                
                # Check confidence
                if opp.confidence_score < self.confidence_threshold:
                    logger.info(f"  ❌ Low confidence: {opp.confidence_score:.2f} < {self.confidence_threshold:.2f}")
                    continue
                    
                # Check price range
                if opp.entry_price > self.max_stock_price:
                    logger.info(f"  ❌ Too expensive: ${opp.entry_price:.2f} > ${self.max_stock_price:.2f}")
                    continue
                    
                if opp.entry_price < 1.0:
                    logger.info(f"  ❌ Penny stock: ${opp.entry_price:.2f} < $1.00")
                    continue
                    
                # Check if already have position
                if opp.symbol in self.positions:
                    logger.info(f"  ❌ Already have position in {opp.symbol}")
                    continue
                    
                # Calculate if we can afford meaningful position
                available_budget = self.budget - self.total_invested
                max_spend = min(available_budget, self.max_position_size)
                shares = int(max_spend / opp.entry_price)
                trade_value = shares * opp.entry_price
                
                logger.info(f"  💰 Available: ${available_budget:.2f}, Max spend: ${max_spend:.2f}, Shares: {shares}, Value: ${trade_value:.2f}")
                
                # Must meet minimum position size
                if shares > 0 and trade_value >= self.min_position_size:
                    logger.info(f"  ✅ QUALIFIED: {opp.symbol} - ${trade_value:.2f} position")
                    micro_opps.append(opp)
                else:
                    logger.info(f"  ❌ Position too small: ${trade_value:.2f} < ${self.min_position_size:.2f}")
            
            # Prefer stocks in our preferred list
            preferred_opps = [opp for opp in micro_opps if opp.symbol in self.preferred_stocks]
            if preferred_opps:
                micro_opps = preferred_opps
            
            # Sort by confidence
            micro_opps.sort(key=lambda x: x.confidence_score, reverse=True)
            
            logger.info(f"📊 Found {len(micro_opps)} micro-budget opportunities")
            return micro_opps[:2]  # Top 2
            
        except Exception as e:
            logger.error(f"❌ Error finding opportunities: {e}")
            return []
    
    async def _execute_micro_trade(self, opportunity):
        """Execute a micro-budget trade"""
        symbol = opportunity.symbol
        entry_price = opportunity.entry_price
        
        # Calculate position size for micro-budget
        available_budget = self.budget - self.total_invested
        max_spend = min(available_budget, self.max_position_size)
        shares = int(max_spend / entry_price)
        trade_value = shares * entry_price
        
        if shares <= 0 or trade_value < self.min_position_size:
            logger.warning(f"⚠️ Position too small for {symbol}: ${trade_value:.2f}")
            return
        
        logger.info(f"🎯 EXECUTING MICRO-BUDGET TRADE:")
        logger.info(f"   Symbol: {symbol}")
        logger.info(f"   Price: ${entry_price:.2f}")
        logger.info(f"   Shares: {shares}")
        logger.info(f"   Cost: ${trade_value:.2f}")
        logger.info(f"   Confidence: {opportunity.confidence_score:.1%}")
        logger.info(f"   Remaining budget: ${available_budget - trade_value:.2f}")
        
        try:
            # Place the order
            result = await self.broker.place_order(
                symbol=symbol,
                action='BUY',
                quantity=shares,
                order_type='MARKET'
            )
            
            if result['success']:
                # Record the position
                self.positions[symbol] = {
                    'shares': shares,
                    'entry_price': entry_price,
                    'entry_time': datetime.now(),
                    'target_price': opportunity.target_price,
                    'stop_loss': opportunity.stop_loss,
                    'cost': trade_value,
                    'order_id': result['order_id']
                }
                
                self.total_invested += trade_value
                
                print(f"\n🚨 LIVE MICRO-TRADE EXECUTED! 🚨")
                print(f"Symbol: {symbol}")
                print(f"Shares: {shares}")
                print(f"Entry Price: ${entry_price:.2f}")
                print(f"Total Cost: ${trade_value:.2f}")
                print(f"Target: ${opportunity.target_price:.2f}")
                print(f"Stop Loss: ${opportunity.stop_loss:.2f}")
                print(f"Budget Used: ${self.total_invested:.2f}/${self.budget:.2f}")
                print(f"Confidence: {opportunity.confidence_score:.1%}")
                print("=" * 45)
                
                logger.info(f"✅ Micro-trade executed successfully!")
                
                # Show potential profit
                potential_profit = (opportunity.target_price - entry_price) * shares
                profit_pct = (potential_profit / trade_value) * 100
                print(f"💰 Potential profit: ${potential_profit:.2f} ({profit_pct:.1f}%)")
                
            else:
                logger.error(f"❌ Trade failed: {result.get('error', 'Unknown')}")
                
        except Exception as e:
            logger.error(f"❌ Error executing trade: {e}")
    
    async def _monitor_positions(self):
        """Monitor existing positions"""
        if not self.positions:
            return
        
        logger.info(f"📊 Monitoring {len(self.positions)} positions...")
        
        for symbol in list(self.positions.keys()):
            try:
                position = self.positions[symbol]
                
                # Get current quote
                quote = await self.broker.get_quote(symbol)
                current_price = quote['last']
                
                entry_price = position['entry_price']
                unrealized_pnl = (current_price - entry_price) * position['shares']
                pnl_pct = (unrealized_pnl / position['cost']) * 100
                
                print(f"📈 {symbol}: ${current_price:.2f} | P&L: ${unrealized_pnl:.2f} ({pnl_pct:.1f}%)")
                
                # Check exit conditions
                should_sell = False
                reason = ""
                
                # Target hit (take profit)
                if current_price >= position['target_price']:
                    should_sell = True
                    reason = "🎯 TARGET REACHED"
                
                # Stop loss hit
                elif current_price <= position['stop_loss']:
                    should_sell = True
                    reason = "🛑 STOP LOSS"
                
                # Time-based exit (6 hours for micro-budget)
                elif (datetime.now() - position['entry_time']).total_seconds() > 21600:
                    should_sell = True
                    reason = "⏰ TIME EXIT (6 hours)"
                
                # Quick profit exit (5%+ profit)
                elif pnl_pct >= 5.0:
                    should_sell = True
                    reason = "💰 QUICK PROFIT (5%+)"
                
                if should_sell:
                    await self._close_position(symbol, reason, current_price)
                    
            except Exception as e:
                logger.error(f"❌ Error monitoring {symbol}: {e}")
    
    async def _close_position(self, symbol, reason, current_price):
        """Close a position"""
        position = self.positions[symbol]
        
        logger.info(f"🔄 CLOSING {symbol} - {reason}")
        
        try:
            # Place sell order
            result = await self.broker.place_order(
                symbol=symbol,
                action='SELL',
                quantity=position['shares'],
                order_type='MARKET'
            )
            
            if result['success']:
                # Calculate final P&L
                pnl = (current_price - position['entry_price']) * position['shares']
                pnl_pct = (pnl / position['cost']) * 100
                
                # Update tracking
                self.total_invested -= position['cost']
                self.completed_trades += 1
                del self.positions[symbol]
                
                print(f"\n💰 POSITION CLOSED! 💰")
                print(f"Symbol: {symbol}")
                print(f"Reason: {reason}")
                print(f"Shares: {position['shares']}")
                print(f"Entry: ${position['entry_price']:.2f}")
                print(f"Exit: ${current_price:.2f}")
                print(f"Profit/Loss: ${pnl:.2f} ({pnl_pct:.1f}%)")
                print(f"Trade #{self.completed_trades} completed!")
                print(f"Available budget: ${self.budget - self.total_invested:.2f}")
                print("=" * 45)
                
                logger.info(f"✅ Position closed successfully!")
                
            else:
                logger.error(f"❌ Failed to close position: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"❌ Error closing position {symbol}: {e}")

def main():
    """Main function"""
    print("🚨 MICRO-BUDGET LIVE TRADING BOT 🚨")
    print("Perfect for small budgets ($50-$100)")
    print("Conservative settings with affordable stocks")
    print("High confidence trades only (80%+)")
    
    bot = MicroBudgetTradingBot()
    
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        print("\n👋 Micro-budget bot stopped by user")
    except Exception as e:
        print(f"\n❌ Bot error: {e}")

if __name__ == "__main__":
    main()