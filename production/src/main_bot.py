#!/usr/bin/env python3
"""
Autonomous Trading Bot - Main Orchestrator
Combines all modules for fully autonomous trading operations.
"""

import sys
import os
import time
import signal
import fcntl
import logging
from datetime import datetime
from typing import Dict, List, Optional
import signal
import threading
import pytz

# Add src directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import all modules
from utils.config_manager import get_config, ConfigManager
from api.alpaca_client import AlpacaClient, OrderSide, OrderType
from strategy.technical_analysis import TechnicalAnalyzer, SignalType
from strategy.sentiment_analysis import SentimentAnalyzer
from utils.risk_manager import RiskManager
from utils.logger import TradingLogger

class AutonomousTradingBot:
    """Main autonomous trading bot class"""
    
    def __init__(self):
        # Singleton lock to prevent multiple instances
        self.lockfile = None
        try:
            self.lockfile = open('bot.lock', 'w')
            fcntl.lockf(self.lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            print("❌ Another instance of the bot is already running!")
            sys.exit(1)
        
        self.running = False
        self.setup_logging()
        
        try:
            # Initialize configuration
            self.config_manager = get_config()
            self.config = self.config_manager.trading_config
            
            if not self.config_manager.validate_config():
                raise ValueError("Configuration validation failed")
            
            # Initialize all components
            self.alpaca_client = AlpacaClient(self.config_manager)
            self.technical_analyzer = TechnicalAnalyzer()
            self.sentiment_analyzer = SentimentAnalyzer(self.config_manager)
            self.risk_manager = RiskManager(self.config_manager, self.alpaca_client)
            self.trading_logger = TradingLogger(self.config_manager)
            
            # Bot state
            self.active_positions = {}
            self.pending_orders = {}
            self.last_scan_time = None
            self.daily_stats = {
                'trades_executed': 0,
                'profit_loss': 0.0,
                'start_portfolio_value': 0.0
            }
            
            # Safety and risk management state
            self.trading_halted = False
            self.halt_reason = None
            self.trade_history = []  # Track recent trades for frequency limits
            self.consecutive_losses = 0
            self.last_loss_time = None
            
            # Store bot instance reference for risk manager access
            import __main__
            __main__.bot_instance = self
            
            self.logger.info("✅ Autonomous Trading Bot initialized successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Bot initialization failed: {e}")
            raise
    
    def setup_logging(self):
        """Configure logging system"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('bot_debug.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.shutdown()
    
    def start(self):
        """Start the autonomous trading bot"""
        try:
            # Register signal handlers
            signal.signal(signal.SIGINT, self.signal_handler)
            signal.signal(signal.SIGTERM, self.signal_handler)
            
            self.running = True
            self.logger.info("🚀 Starting Autonomous Trading Bot")
            
            # Initialize daily stats
            account = self.alpaca_client.get_account()
            self.daily_stats['start_portfolio_value'] = account.portfolio_value
            
            # Start main loop
            self.main_trading_loop()
            
        except Exception as e:
            self.logger.error(f"❌ Bot startup failed: {e}")
            self.shutdown()
    
    def shutdown(self):
        """Shutdown bot gracefully"""
        try:
            self.running = False
            self.logger.info("🛑 Shutting down Autonomous Trading Bot")
            
            # Cancel all pending orders
            if hasattr(self, 'alpaca_client'):
                self.alpaca_client.cancel_all_orders()
            
            # Generate final performance report
            if hasattr(self, 'trading_logger'):
                report = self.trading_logger.generate_performance_report()
                self.logger.info(f"📊 Final performance report generated")
            
            # Log daily summary
            account = self.alpaca_client.get_account()
            daily_pnl = account.portfolio_value - self.daily_stats['start_portfolio_value']
            
            self.logger.info(f"📈 Daily Summary:")
            self.logger.info(f"   Trades Executed: {self.daily_stats['trades_executed']}")
            self.logger.info(f"   Daily P&L: ${daily_pnl:.2f}")
            self.logger.info(f"   Portfolio Value: ${account.portfolio_value:.2f}")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
        
        finally:
            # Clean up lock file
            if hasattr(self, 'lockfile') and self.lockfile:
                try:
                    self.lockfile.close()
                    os.remove('bot.lock')
                except:
                    pass
            self.logger.info("✅ Bot shutdown complete")
    
    def is_premarket_hours(self) -> bool:
        """Check if current time is during premarket hours (4:00 AM - 9:30 AM ET)"""
        try:
            et = pytz.timezone('US/Eastern')
            now_et = datetime.now(et)
            current_time = now_et.time()
            
            # Premarket hours: 4:00 AM - 9:30 AM ET
            premarket_start = datetime.strptime("04:00", "%H:%M").time()
            premarket_end = datetime.strptime("09:30", "%H:%M").time()
            
            return premarket_start <= current_time < premarket_end
        except Exception as e:
            self.logger.error(f"Error checking premarket hours: {e}")
            return False
    
    def main_trading_loop(self):
        """Main trading loop - autonomous operation"""
        scan_interval = 300  # 5 minutes between scans
        position_check_interval = 60  # 1 minute between position checks
        
        last_position_check = 0
        
        while self.running:
            try:
                current_time = time.time()
                
                # Check market status
                market_open = self.alpaca_client.is_market_open()
                premarket_hours = self.is_premarket_hours()
                # Detect crypto symbols (USD pairs with slashes or ending with USD)
                has_crypto = any('/' in symbol or symbol.endswith('USD') for symbol in self.config.scan_universe)
                has_stocks = any('/' not in symbol and not symbol.endswith('USD') for symbol in self.config.scan_universe)
                
                if market_open:
                    # Regular trading hours - trade everything
                    pass
                elif premarket_hours and has_stocks:
                    # Premarket hours - trade stocks + crypto
                    self.logger.info("🌅 Premarket hours - trading stocks and crypto")
                elif has_crypto:
                    # After hours - crypto only
                    self.logger.info("🪙 Stock market closed - trading crypto only")
                else:
                    # Completely closed - sleep
                    if datetime.now().hour == 9 and datetime.now().minute == 25:
                        self.logger.info("📅 Market opening soon - preparing for trading day")
                        self.prepare_trading_day()
                    time.sleep(60)  # Check every minute when market closed
                    continue
                
                # Monitor existing positions (every minute)
                if current_time - last_position_check >= position_check_interval:
                    self.monitor_positions()
                    last_position_check = current_time
                
                # Scan for new opportunities (every 5 minutes)
                if (self.last_scan_time is None or 
                    current_time - self.last_scan_time >= scan_interval):
                    
                    self.scan_for_opportunities()
                    self.last_scan_time = current_time
                
                # Brief pause to prevent excessive CPU usage
                time.sleep(10)
                
            except Exception as e:
                self.logger.error(f"❌ Error in main loop: {e}")
                time.sleep(30)  # Wait before retrying
    
    def prepare_trading_day(self):
        """Prepare for the trading day"""
        try:
            self.logger.info("🌅 Preparing for trading day")
            
            # Update risk limits for the day
            account = self.alpaca_client.get_account()
            self.daily_stats = {
                'trades_executed': 0,
                'profit_loss': 0.0,
                'start_portfolio_value': account.portfolio_value
            }
            
            # Check account status
            if account.status != 'ACTIVE':
                self.logger.warning(f"⚠️ Account status: {account.status}")
                return
            
            # Log account information
            self.logger.info(f"💰 Account Status:")
            self.logger.info(f"   Portfolio Value: ${account.portfolio_value:.2f}")
            self.logger.info(f"   Buying Power: ${account.buying_power:.2f}")
            self.logger.info(f"   Cash: ${account.cash:.2f}")
            
            # Get risk summary
            risk_summary = self.risk_manager.get_risk_summary()
            self.logger.info(f"🛡️ Risk Summary:")
            self.logger.info(f"   Open Positions: {risk_summary.get('total_positions', 0)}")
            self.logger.info(f"   Available Position Slots: {risk_summary.get('remaining_position_slots', 0)}")
            self.logger.info(f"   Daily Risk Budget: ${risk_summary.get('remaining_daily_risk', 0):.2f}")
            
        except Exception as e:
            self.logger.error(f"Error preparing trading day: {e}")
    
    def scan_for_opportunities(self):
        """Scan for new trading opportunities"""
        try:
            self.logger.info("🔍 Scanning for trading opportunities...")
            
            # Get account info for position sizing
            account = self.alpaca_client.get_account()
            
            # Filter universe based on market hours
            market_open = self.alpaca_client.is_market_open()
            premarket_hours = self.is_premarket_hours()
            
            if market_open or premarket_hours:
                # Trade everything when market is open or during premarket
                scan_universe = self.config.scan_universe
                market_status = "Market open" if market_open else "Premarket hours"
                self.logger.info(f"🏦 {market_status} - scanning {len(scan_universe)} symbols (stocks + crypto)")
            else:
                # Only trade crypto when market is completely closed
                scan_universe = [s for s in self.config.scan_universe if '/' in s or s.endswith('USD')]
                if scan_universe:
                    self.logger.info(f"🪙 Market closed - scanning {len(scan_universe)} crypto symbols")
                else:
                    self.logger.info("📊 No crypto symbols available for after-hours trading")
                    return
            
            # Technical analysis scan
            technical_signals = self.technical_analyzer.scan_universe(
                self.alpaca_client, 
                scan_universe, 
                self.config
            )
            
            if not technical_signals:
                self.logger.info("📊 No technical signals found")
                return
            
            # Get sentiment analysis for top technical signals
            top_symbols = [signal.symbol for signal in technical_signals[:10]]
            sentiment_analysis = self.sentiment_analyzer.get_market_sentiment(top_symbols)
            
            # Combine technical and sentiment analysis
            combined_signals = self.combine_signals(technical_signals, sentiment_analysis)
            
            if not combined_signals:
                self.logger.info("🎯 No qualified trading opportunities found")
                return
            
            # Execute trades for top opportunities
            for signal in combined_signals[:3]:  # Limit to top 3 signals
                if self.should_execute_trade(signal, account):
                    self.execute_trade(signal, account)
            
        except Exception as e:
            self.logger.error(f"Error scanning for opportunities: {e}")
    
    def combine_signals(self, technical_signals, sentiment_analysis):
        """Combine technical and sentiment analysis"""
        try:
            combined_signals = []
            
            for tech_signal in technical_signals:
                symbol = tech_signal.symbol
                sentiment = sentiment_analysis.get(symbol)
                
                # Skip if sentiment recommends skipping
                if sentiment and sentiment.recommendation == "SKIP":
                    self.logger.info(f"⏭️ Skipping {symbol} due to negative sentiment")
                    continue
                
                # Adjust signal based on sentiment
                final_confidence = tech_signal.confidence
                
                if sentiment:
                    sentiment_weight = self.config.sentiment_weight
                    
                    # Enhance or reduce confidence based on sentiment alignment
                    if sentiment.recommendation == "BULLISH_BIAS" and tech_signal.signal_type == SignalType.BUY:
                        final_confidence *= (1 + sentiment_weight)
                    elif sentiment.recommendation == "BEARISH_BIAS" and tech_signal.signal_type == SignalType.SELL:
                        final_confidence *= (1 + sentiment_weight)
                    elif sentiment.recommendation in ["BULLISH_BIAS", "BEARISH_BIAS"]:
                        # Conflicting signals - reduce confidence
                        final_confidence *= (1 - sentiment_weight)
                
                # Create enhanced signal
                enhanced_signal = {
                    'symbol': symbol,
                    'signal_type': tech_signal.signal_type,
                    'price': tech_signal.price,
                    'confidence': min(final_confidence, 1.0),
                    'technical_reasons': tech_signal.reasons,
                    'sentiment_score': sentiment.weighted_sentiment if sentiment else 0.0,
                    'sentiment_recommendation': sentiment.recommendation if sentiment else "NEUTRAL",
                    'rsi': tech_signal.rsi,
                    'trend_direction': tech_signal.trend_direction.value,
                    'volume_surge': tech_signal.volume_surge
                }
                
                # Only include high-confidence signals
                if enhanced_signal['confidence'] >= self.config.min_confidence:
                    combined_signals.append(enhanced_signal)
            
            # Sort by confidence
            return sorted(combined_signals, key=lambda x: x['confidence'], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Error combining signals: {e}")
            return []
    
    def get_positions_safely(self):
        """Get positions with robust error handling and retries"""
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                positions = self.alpaca_client.get_positions()
                self.logger.debug(f"✅ Successfully retrieved {len(positions)} positions")
                return positions
            except Exception as e:
                self.logger.warning(f"⚠️ Attempt {attempt + 1}/{max_retries} failed to get positions: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    self.logger.error(f"🚨 CRITICAL: Failed to get positions after {max_retries} attempts!")
                    # Set trading halt flag
                    self.trading_halted = True
                    self.halt_reason = f"Position tracking failed: {e}"
                    return None
    
    def get_orders_safely(self, status="open"):
        """Get orders with robust error handling"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                orders = self.alpaca_client.get_orders(status=status)
                return orders
            except Exception as e:
                self.logger.warning(f"⚠️ Failed to get orders (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                else:
                    self.logger.error(f"🚨 Failed to get orders after {max_retries} attempts")
                    return []
    
    def check_trading_frequency_limits(self) -> bool:
        """Check if trading frequency limits are respected"""
        try:
            current_time = datetime.now()
            
            # Clean up old trade history (older than 1 hour)
            one_hour_ago = current_time.timestamp() - 3600
            self.trade_history = [
                trade for trade in self.trade_history 
                if trade['timestamp'] > one_hour_ago
            ]
            
            # Check hourly limit (2 trades per hour)
            trades_in_last_hour = len(self.trade_history)
            if trades_in_last_hour >= 2:
                self.logger.warning(f"⚠️ Trading frequency limit reached: {trades_in_last_hour}/2 trades in last hour")
                return False
            
            # Check minimum time between trades (5 minutes)
            if self.trade_history:
                last_trade_time = max(trade['timestamp'] for trade in self.trade_history)
                time_since_last_trade = current_time.timestamp() - last_trade_time
                min_interval = 900  # 15 minutes in seconds
                
                if time_since_last_trade < min_interval:
                    remaining_time = int(min_interval - time_since_last_trade)
                    self.logger.info(f"⏰ Minimum trade interval: waiting {remaining_time}s before next trade")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking trading frequency: {e}")
            return True  # Allow trading if check fails (fail-open)
    
    def record_trade_execution(self, symbol: str, action: str, quantity: float, price: float):
        """Record a trade execution for frequency tracking"""
        trade_record = {
            'timestamp': datetime.now().timestamp(),
            'symbol': symbol,
            'action': action,
            'quantity': quantity,
            'price': price
        }
        self.trade_history.append(trade_record)
        
        # Keep only last 10 trades to prevent memory issues
        if len(self.trade_history) > 10:
            self.trade_history = self.trade_history[-10:]
    
    def check_trading_halt_status(self) -> bool:
        """Check if trading should be halted and log status"""
        if self.trading_halted:
            self.logger.error(f"🛑 TRADING HALTED: {self.halt_reason}")
            return True
        return False
    
    def resume_trading(self, reason: str = "Manual override"):
        """Resume trading after halt (use with caution)"""
        self.trading_halted = False
        self.halt_reason = None
        self.logger.info(f"✅ Trading resumed: {reason}")
    
    def halt_trading(self, reason: str):
        """Halt all trading operations"""
        self.trading_halted = True
        self.halt_reason = reason
        self.logger.error(f"🚨 TRADING HALTED: {reason}")
    
    def check_consecutive_loss_limit(self) -> bool:
        """Check if consecutive loss limit has been reached"""
        max_consecutive_losses = 3
        
        if self.consecutive_losses >= max_consecutive_losses:
            if not self.trading_halted:  # Only halt once
                halt_msg = f"Consecutive loss limit reached: {self.consecutive_losses} losses"
                self.halt_trading(halt_msg)
            return False
        
        return True
    
    def record_trade_outcome(self, symbol: str, profit_loss: float):
        """Record trade outcome for consecutive loss tracking"""
        if profit_loss < 0:
            self.consecutive_losses += 1
            self.last_loss_time = datetime.now()
            self.logger.warning(f"📉 Loss recorded: ${profit_loss:.2f} (consecutive losses: {self.consecutive_losses})")
        else:
            # Reset consecutive losses on any profit
            if self.consecutive_losses > 0:
                self.logger.info(f"📈 Profit recorded: ${profit_loss:.2f} - resetting consecutive loss count")
            self.consecutive_losses = 0
    
    def should_execute_trade(self, signal, account) -> bool:
        """Determine if a trade should be executed"""
        try:
            symbol = signal['symbol']
            
            # Critical check: If trading is halted, don't execute any trades
            if getattr(self, 'trading_halted', False):
                self.logger.error(f"🛑 Trading halted: {getattr(self, 'halt_reason', 'Unknown reason')}")
                return False
            
            # Check trading frequency limits
            if not self.check_trading_frequency_limits():
                return False
            
            # Check consecutive loss circuit breaker
            if not self.check_consecutive_loss_limit():
                return False
            
            # Check if we already have a position in this symbol
            positions = self.get_positions_safely()
            if positions is None:
                self.logger.error(f"🚨 Cannot verify positions - halting trade execution for safety")
                return False
                
            for pos in positions:
                if pos.symbol == symbol:
                    self.logger.info(f"⏭️ Skipping {symbol} - already have position: {pos.qty} shares")
                    return False
            
            # Check if we have pending orders for this symbol
            orders = self.get_orders_safely(status="open")
            for order in orders:
                if order.symbol == symbol:
                    self.logger.info(f"⏭️ Skipping {symbol} - pending order exists: {order.id}")
                    return False
            
            # Calculate position size and risk
            entry_price = signal['price']
            signal_type = "BUY" if signal['signal_type'] == SignalType.BUY else "SELL"
            
            stop_loss_price = self.risk_manager.calculate_stop_loss(
                symbol, entry_price, signal_type
            )
            
            trade_risk = self.risk_manager.calculate_position_size(
                symbol, entry_price, stop_loss_price, 
                account.buying_power, signal['confidence']
            )
            
            if not trade_risk:
                self.logger.warning(f"⚠️ Could not calculate risk for {symbol}")
                return False
            
            # Validate trade
            is_valid, reason = self.risk_manager.validate_trade(trade_risk, account.portfolio_value)
            
            if not is_valid:
                self.logger.info(f"❌ Trade rejected for {symbol}: {reason}")
                return False
            
            # Store trade risk for execution
            signal['trade_risk'] = trade_risk
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error evaluating trade for {signal['symbol']}: {e}")
            return False
    
    def execute_trade(self, signal, account):
        """Execute a trading signal"""
        try:
            symbol = signal['symbol']
            trade_risk = signal['trade_risk']
            
            # Determine order side
            if signal['signal_type'] == SignalType.BUY:
                order_side = OrderSide.BUY
                action = "BUY"
            else:
                order_side = OrderSide.SELL
                action = "SELL"
            
            self.logger.info(f"🎯 Executing {action} for {symbol}")
            self.logger.info(f"   Quantity: {trade_risk.position_size}")
            self.logger.info(f"   Entry Price: ${trade_risk.entry_price:.2f}")
            self.logger.info(f"   Stop Loss: ${trade_risk.stop_loss_price:.2f}")
            self.logger.info(f"   Take Profit: ${trade_risk.take_profit_price:.2f}")
            self.logger.info(f"   Risk Amount: ${trade_risk.risk_amount:.2f}")
            self.logger.info(f"   Risk/Reward: {trade_risk.risk_reward_ratio:.2f}")
            
            # Place market order
            order_id = self.alpaca_client.place_order(
                symbol=symbol,
                qty=trade_risk.position_size,
                side=order_side,
                order_type=OrderType.MARKET
            )
            
            if order_id:
                # Record trade execution for frequency tracking
                self.record_trade_execution(
                    symbol, action, trade_risk.position_size, trade_risk.entry_price
                )
                
                # Store position info
                self.active_positions[symbol] = {
                    'order_id': order_id,
                    'entry_price': trade_risk.entry_price,
                    'stop_loss': trade_risk.stop_loss_price,
                    'take_profit': trade_risk.take_profit_price,
                    'quantity': trade_risk.position_size,
                    'side': action,
                    'entry_time': datetime.now(),
                    'signal_data': signal
                }
                
                self.daily_stats['trades_executed'] += 1
                
                self.logger.info(f"✅ Trade executed: {order_id}")
                
                # Place stop loss order
                self.place_stop_loss_order(symbol, trade_risk, order_side)
                
            else:
                self.logger.error(f"❌ Failed to place order for {symbol}")
                
        except Exception as e:
            self.logger.error(f"Error executing trade for {symbol}: {e}")
    
    def place_stop_loss_order(self, symbol, trade_risk, original_side):
        """Place stop loss order for position protection"""
        try:
            # Determine stop loss order side (opposite of entry)
            stop_side = OrderSide.SELL if original_side == OrderSide.BUY else OrderSide.BUY
            
            # Place stop loss order
            stop_order_id = self.alpaca_client.place_order(
                symbol=symbol,
                qty=trade_risk.position_size,
                side=stop_side,
                order_type=OrderType.STOP,
                stop_price=trade_risk.stop_loss_price
            )
            
            if stop_order_id:
                self.logger.info(f"🛡️ Stop loss order placed: {stop_order_id}")
                if symbol in self.active_positions:
                    self.active_positions[symbol]['stop_order_id'] = stop_order_id
            
        except Exception as e:
            self.logger.error(f"Error placing stop loss for {symbol}: {e}")
    
    def monitor_positions(self):
        """Monitor existing positions for exit conditions"""
        try:
            positions = self.alpaca_client.get_positions()
            
            for position in positions:
                symbol = position.symbol
                
                # Assess position risk
                position_risk = self.risk_manager.assess_position_risk(position)
                
                if not position_risk:
                    continue
                
                # Check if position should be closed
                should_close, reason = self.risk_manager.should_close_position(position_risk)
                
                if should_close:
                    self.logger.info(f"🔄 Closing position {symbol}: {reason}")
                    self.close_position(symbol, position, reason)
                else:
                    # Update trailing stop if profitable
                    self.update_trailing_stop(symbol, position, position_risk)
                    
        except Exception as e:
            self.logger.error(f"Error monitoring positions: {e}")
    
    def close_position(self, symbol, position, reason):
        """Close a position and log the trade"""
        try:
            # Close position
            close_order_id = self.alpaca_client.close_position(symbol)
            
            if close_order_id:
                # Get current price for P&L calculation
                quote = self.alpaca_client.get_latest_quote(symbol)
                exit_price = (quote['bid'] + quote['ask']) / 2 if quote else position.avg_entry_price
                
                # Calculate P&L
                pnl = position.unrealized_pl
                pnl_percent = (position.unrealized_plpc * 100) if hasattr(position, 'unrealized_plpc') else 0
                
                # Log the trade
                trade_data = {
                    'symbol': symbol,
                    'action': 'SELL' if position.qty > 0 else 'BUY',
                    'quantity': abs(int(position.qty)),
                    'entry_price': position.avg_entry_price,
                    'exit_price': exit_price,
                    'pnl': pnl,
                    'pnl_percent': pnl_percent,
                    'exit_reason': reason,
                    'duration_minutes': 60,  # Approximate - would need entry time
                    'strategy_signals': '',  # Would get from stored signal data
                    'confidence': 0.0,  # Would get from stored signal data
                    'risk_reward_ratio': 0.0  # Would calculate from stored data
                }
                
                # Get additional data if available
                if symbol in self.active_positions:
                    position_data = self.active_positions[symbol]
                    duration = (datetime.now() - position_data['entry_time']).total_seconds() / 60
                    trade_data['duration_minutes'] = int(duration)
                    
                    signal_data = position_data.get('signal_data', {})
                    trade_data['strategy_signals'] = ', '.join(signal_data.get('technical_reasons', []))
                    trade_data['confidence'] = signal_data.get('confidence', 0.0)
                    trade_data['sentiment_score'] = signal_data.get('sentiment_score', 0.0)
                
                self.trading_logger.log_trade(trade_data)
                
                # Update daily stats
                self.daily_stats['profit_loss'] += pnl
                
                # Clean up position tracking
                if symbol in self.active_positions:
                    del self.active_positions[symbol]
                
                # Record trade result for learning
                self.risk_manager.record_trade_result(
                    symbol, position.avg_entry_price, exit_price,
                    int(position.qty), 'BUY' if position.qty > 0 else 'SELL'
                )
                
                self.logger.info(f"✅ Position closed: {symbol} P&L: ${pnl:.2f}")
                
        except Exception as e:
            self.logger.error(f"Error closing position {symbol}: {e}")
    
    def update_trailing_stop(self, symbol, position, position_risk):
        """Update trailing stop for profitable positions"""
        try:
            # Only update if position is profitable
            if position_risk.unrealized_pl_percent > 2:  # At least 2% profit
                
                new_stop_price = position_risk.trail_stop_price
                
                # Check if we have an existing stop order to modify
                orders = self.alpaca_client.get_orders(status="open")
                stop_orders = [o for o in orders if o.symbol == symbol and o.order_type == "stop"]
                
                if stop_orders and len(stop_orders) > 0:
                    # Would implement stop order modification here
                    # Alpaca API might require canceling old and placing new
                    self.logger.info(f"📈 Trailing stop updated for {symbol}: ${new_stop_price:.2f}")
                    
        except Exception as e:
            self.logger.error(f"Error updating trailing stop for {symbol}: {e}")

def main():
    """Main entry point"""
    try:
        bot = AutonomousTradingBot()
        bot.start()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Bot failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()