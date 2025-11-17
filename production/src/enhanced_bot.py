#!/usr/bin/env python3
"""
Enhanced Autonomous Trading Bot
Focused on AMD stocks and SOL crypto with advanced sentiment analysis,
SMS notifications, and comprehensive risk management.
"""

import sys
import os
import time
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import signal
import threading
from dataclasses import dataclass, asdict
import pytz

# Add src directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import modules
from utils.config_manager import get_config, ConfigManager
from api.alpaca_client import AlpacaClient, OrderSide, OrderType
from strategy.technical_analysis import TechnicalAnalyzer, SignalType
from strategy.simple_sentiment import SimpleSentimentAnalyzer
from utils.risk_manager import RiskManager
from utils.logger import TradingLogger
from utils.notifications import NotificationManager

@dataclass
class BotStatus:
    """Bot status tracking"""
    enabled: bool = True
    running: bool = False
    last_scan: Optional[str] = None
    active_trades: int = 0
    daily_pnl: float = 0.0
    scan_count: int = 0
    error_count: int = 0

@dataclass
class ActiveTrade:
    """Active trade tracking"""
    symbol: str
    side: str
    quantity: float
    entry_price: float
    entry_time: datetime
    stop_loss: float
    take_profit: float
    current_price: float
    unrealized_pnl: float
    order_id: str
    reasons: List[str]

class EnhancedTradingBot:
    """Enhanced autonomous trading bot for AMD and SOL"""
    
    def __init__(self):
        self.setup_logging()
        self.running = False
        self.status = BotStatus()
        
        try:
            # Initialize configuration
            self.config_manager = get_config()
            self.config = self.config_manager.trading_config
            
            if not self.config_manager.validate_config():
                raise ValueError("Configuration validation failed")
            
            # Initialize components
            self.alpaca_client = AlpacaClient(self.config_manager)
            self.technical_analyzer = TechnicalAnalyzer()
            self.sentiment_analyzer = SimpleSentimentAnalyzer(self.config_manager)
            self.risk_manager = RiskManager(self.config_manager, self.alpaca_client)
            self.trading_logger = TradingLogger(self.config_manager)
            self.notification_manager = NotificationManager(self.config_manager)
            
            # Bot state
            self.active_trades: Dict[str, ActiveTrade] = {}
            self.last_scan_time = None
            self.daily_stats = {
                'trades_executed': 0,
                'profit_loss': 0.0,
                'start_portfolio_value': 0.0
            }
            
            # Status file for dashboard communication
            self.status_file = os.path.join(
                os.path.dirname(__file__), '..', 'data', 'bot_status.json'
            )
            self.ensure_data_dir()
            
            self.logger.info("✅ Enhanced Trading Bot initialized successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Bot initialization failed: {e}")
            raise
    
    def setup_logging(self):
        """Configure logging system"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('enhanced_bot.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def ensure_data_dir(self):
        """Ensure data directory exists"""
        data_dir = os.path.dirname(self.status_file)
        os.makedirs(data_dir, exist_ok=True)
    
    def save_status(self):
        """Save bot status to file for dashboard"""
        try:
            status_data = {
                'status': asdict(self.status),
                'active_trades': {k: asdict(v) for k, v in self.active_trades.items()},
                'daily_stats': self.daily_stats,
                'timestamp': datetime.now().isoformat()
            }
            
            with open(self.status_file, 'w') as f:
                json.dump(status_data, f, indent=2, default=str)
                
        except Exception as e:
            self.logger.error(f"Failed to save status: {e}")
    
    def load_bot_control(self) -> Dict:
        """Load bot control settings from config"""
        try:
            return self.config_manager.config.get('bot_control', {
                'enabled': True,
                'scan_interval_seconds': 30
            })
        except:
            return {'enabled': True, 'scan_interval_seconds': 30}
    
    def is_market_hours_for_stocks(self) -> bool:
        """Check if current time is within stock market hours (premarket + regular)"""
        try:
            # US Eastern timezone
            et_tz = pytz.timezone('US/Eastern')
            current_et = datetime.now(et_tz)
            
            weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            current_weekday_name = weekday_names[current_et.weekday()]
            
            self.logger.info(f"🕐 Current ET time: {current_et.strftime('%A, %B %d, %Y at %I:%M:%S %p ET')}")
            
            # Skip weekends (Saturday=5, Sunday=6)
            if current_et.weekday() >= 5:
                self.logger.info(f"📅 Weekend detected ({current_weekday_name}) - stock market closed")
                return False
            
            current_time = current_et.time()
            
            # Premarket: 4:00 AM - 9:30 AM ET
            # Regular market: 9:30 AM - 4:00 PM ET
            premarket_start = current_time.replace(hour=4, minute=0, second=0, microsecond=0)
            market_close = current_time.replace(hour=16, minute=0, second=0, microsecond=0)
            
            is_market_open = premarket_start <= current_time <= market_close
            
            if is_market_open:
                if current_time < current_time.replace(hour=9, minute=30):
                    self.logger.info(f"🌅 Premarket hours ({current_weekday_name}) - AMD scanning enabled")
                else:
                    self.logger.info(f"🏢 Regular market hours ({current_weekday_name}) - AMD scanning enabled")
            else:
                if current_time < premarket_start:
                    self.logger.info(f"🌙 Before premarket ({current_weekday_name}) - AMD scanning disabled")
                else:
                    self.logger.info(f"🌆 After market close ({current_weekday_name}) - AMD scanning disabled")
            
            return is_market_open
            
        except Exception as e:
            self.logger.warning(f"Error checking market hours: {e}")
            # Default to NOT allowing trading if we can't determine market hours (safer)
            return False
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.shutdown()
    
    def start(self):
        """Start the enhanced trading bot"""
        try:
            # Register signal handlers
            signal.signal(signal.SIGINT, self.signal_handler)
            signal.signal(signal.SIGTERM, self.signal_handler)
            
            self.running = True
            self.status.running = True
            self.status.enabled = self.load_bot_control().get('enabled', True)
            
            self.logger.info("🚀 Starting Enhanced Trading Bot (AMD + SOL)")
            
            # Initialize daily stats
            account = self.alpaca_client.get_account()
            self.daily_stats['start_portfolio_value'] = account.portfolio_value
            
            # Send startup notification
            self.notification_manager.send_system_alert(
                f"Trading bot started\nFocus: AMD + SOL\nBalance: ${account.portfolio_value:.2f}",
                "SUCCESS"
            )
            
            # Start main loop
            self.main_trading_loop()
            
        except Exception as e:
            self.logger.error(f"❌ Bot startup failed: {e}")
            self.notification_manager.send_system_alert(f"Bot startup failed: {e}", "ERROR")
            self.shutdown()
    
    def shutdown(self):
        """Shutdown bot gracefully"""
        try:
            self.running = False
            self.status.running = False
            self.logger.info("🛑 Shutting down Enhanced Trading Bot")
            
            # Cancel all pending orders
            if hasattr(self, 'alpaca_client'):
                self.alpaca_client.cancel_all_orders()
            
            # Generate final performance report
            if hasattr(self, 'trading_logger'):
                report = self.trading_logger.generate_performance_report()
                self.logger.info("📊 Final performance report generated")
            
            # Log daily summary
            account = self.alpaca_client.get_account()
            daily_pnl = account.portfolio_value - self.daily_stats['start_portfolio_value']
            
            summary = f"""Daily Summary:
Trades: {self.daily_stats['trades_executed']}
P&L: ${daily_pnl:.2f}
Portfolio: ${account.portfolio_value:.2f}"""
            
            self.logger.info(f"📈 {summary}")
            
            # Send shutdown notification
            self.notification_manager.send_system_alert(summary, "INFO")
            
            # Save final status
            self.save_status()
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
        
        finally:
            self.logger.info("✅ Bot shutdown complete")
    
    def main_trading_loop(self):
        """Enhanced main trading loop"""
        while self.running:
            try:
                # Load current bot control settings
                bot_control = self.load_bot_control()
                scan_interval = bot_control.get('scan_interval_seconds', 30)
                
                # Check if bot is enabled
                if not bot_control.get('enabled', True):
                    self.status.enabled = False
                    time.sleep(10)
                    continue
                
                self.status.enabled = True
                current_time = time.time()
                
                # Monitor existing positions (every cycle)
                self.monitor_positions()
                
                # Scan for new opportunities
                if (self.last_scan_time is None or 
                    current_time - self.last_scan_time >= scan_interval):
                    
                    self.scan_for_opportunities()
                    self.last_scan_time = current_time
                    self.status.last_scan = datetime.now().isoformat()
                    self.status.scan_count += 1
                
                # Update and save status
                self.update_status()
                self.save_status()
                
                # Brief pause
                time.sleep(5)
                
            except Exception as e:
                self.logger.error(f"❌ Error in main loop: {e}")
                self.status.error_count += 1
                self.notification_manager.send_system_alert(f"Bot error: {e}", "ERROR")
                time.sleep(30)  # Wait before retrying
    
    def scan_for_opportunities(self):
        """Enhanced opportunity scanning"""
        try:
            self.logger.info("🔍 Scanning AMD & SOL for opportunities...")
            
            account = self.alpaca_client.get_account()
            
            # Check if we can make new trades
            if len(self.active_trades) >= self.config.max_positions:
                self.logger.info(f"⏭️ Max positions reached ({len(self.active_trades)})")
                return
            
            # Check market hours for stock scanning
            is_market_open = self.is_market_hours_for_stocks()
            
            # Scan each symbol with market hours consideration
            symbols_to_scan = []
            
            # AMD - only during market hours (premarket + regular)
            if is_market_open:
                symbols_to_scan.append('AMD')
            else:
                self.logger.info("⏰ Market closed - skipping AMD (stocks only trade during market hours)")
            
            # SOL - always (crypto trades 24/7)
            symbols_to_scan.append('SOL/USD')
            
            if not symbols_to_scan:
                self.logger.info("⏭️ No symbols to scan at this time")
                return
            
            for symbol in symbols_to_scan:
                try:
                    if symbol in self.active_trades:
                        continue  # Skip if we already have position
                    
                    # Analyze symbol
                    signal = self.analyze_symbol(symbol, account)
                    
                    if signal and signal['should_trade']:
                        self.execute_trade(signal, account)
                        
                except Exception as e:
                    self.logger.error(f"Error analyzing {symbol}: {e}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Error in opportunity scanning: {e}")
    
    def analyze_symbol(self, symbol: str, account) -> Optional[Dict]:
        """Comprehensive symbol analysis"""
        try:
            self.logger.info(f"📊 Analyzing {symbol}...")
            
            # Technical analysis  
            self.logger.info(f"    💾 Requesting 100 daily bars for {symbol}...")
            df = self.alpaca_client.get_bars(symbol, timeframe='1Day', limit=100)
            
            if df is None:
                self.logger.warning(f"⚠️ get_bars returned None for {symbol}")
                return None
                
            if df.empty:
                self.logger.warning(f"⚠️ get_bars returned empty DataFrame for {symbol}")
                return None
            
            self.logger.info(f"    📈 Retrieved {len(df)} bars for {symbol}, latest price: ${df['close'].iloc[-1]:.2f}")
            self.logger.info(f"    🗺 Date range: {df.index[0]} to {df.index[-1]}")
            
            if len(df) < 10:  # Reduced requirement for testing
                self.logger.warning(f"    ⚠️ Insufficient data for {symbol}: {len(df)} bars < 10 required")
                
                # Try alternative data source for crypto
                if '/' in symbol:
                    self.logger.info(f"    🔄 Trying alternative data source for {symbol}...")
                    df_alt = self.get_alternative_crypto_data(symbol)
                    if df_alt is not None and len(df_alt) >= 10:
                        df = df_alt
                        self.logger.info(f"    ✅ Alternative data retrieved: {len(df)} bars")
                    else:
                        return None
                else:
                    return None
            
            self.logger.info(f"    📋 Config type: {type(self.config)}, has momentum_lookback: {hasattr(self.config, 'momentum_lookback')}")
            
            technical_signal = self.technical_analyzer.analyze_stock(symbol, df, self.config)
            
            if technical_signal is None:
                self.logger.info(f"    ⚠️ Technical analyzer returned None for {symbol}")
            
            if not technical_signal:
                self.logger.info(f"📊 {symbol}: ❌ No technical signal generated (insufficient data or calculation error)")
                return None
                
            if technical_signal.confidence < 0.35:  # Lowered for testing
                self.logger.info(f"📊 {symbol}: ❌ Low technical confidence ({technical_signal.confidence:.2f} < 0.35 required)")
                self.logger.info(f"    📈 Price: ${technical_signal.price:.2f}")
                self.logger.info(f"    📊 Signal: {technical_signal.signal_type}")
                self.logger.info(f"    🎯 RSI: {technical_signal.rsi_value:.1f}" if technical_signal.rsi_value else "    🎯 RSI: N/A")
                self.logger.info(f"    💡 Reasons: {', '.join(technical_signal.reasons) if technical_signal.reasons else 'No specific reasons'}")
                return None
            
            # Advanced sentiment analysis
            self.logger.info(f"    🔍 Running sentiment analysis for {symbol}...")
            sentiment_analysis = self.sentiment_analyzer.analyze_symbol_sentiment(symbol)
            
            self.logger.info(f"    💭 Sentiment: {sentiment_analysis.get('recommendation', 'UNKNOWN')} (score: {sentiment_analysis.get('sentiment_score', 0):.2f})")
            self.logger.info(f"    ⚠️ Risk Level: {sentiment_analysis.get('risk_level', 'UNKNOWN')}")
            self.logger.info(f"    📰 News Articles: {sentiment_analysis.get('news_count', 0)}")
            
            # Combine analyses
            combined_analysis = self.combine_analyses(
                symbol, technical_signal, sentiment_analysis, account
            )
            
            if not combined_analysis.get('should_trade', False):
                reason = combined_analysis.get('reason', 'Unknown reason')
                self.logger.info(f"    ❌ Trade skipped: {reason}")
            else:
                self.logger.info(f"    ✅ Trade signal generated: {combined_analysis.get('direction')} with {combined_analysis.get('confidence', 0):.2f} confidence")
            
            return combined_analysis
            
        except Exception as e:
            self.logger.error(f"Symbol analysis failed for {symbol}: {e}")
            return None
    
    def combine_analyses(self, symbol: str, technical_signal, sentiment_analysis: Dict, account) -> Dict:
        """Combine technical and sentiment analysis"""
        try:
            # Get current price
            current_price = technical_signal.price
            
            # Check sentiment recommendation
            sentiment_rec = sentiment_analysis.get('recommendation', 'HOLD')
            if sentiment_rec in ['SKIP_HIGH_RISK']:
                return {'should_trade': False, 'reason': f'High risk sentiment ({sentiment_rec})'}
            
            # Determine trade direction
            tech_signal_type = technical_signal.signal_type
            sentiment_direction = sentiment_analysis.get('momentum_direction', 'NEUTRAL')
            
            # Enhanced decision logic with detailed logging
            self.logger.info(f"    🧮 Decision Logic for {symbol}:")
            self.logger.info(f"        Technical: {tech_signal_type}")
            self.logger.info(f"        Sentiment Rec: {sentiment_rec}")
            self.logger.info(f"        Sentiment Direction: {sentiment_direction}")
            
            if (tech_signal_type == SignalType.BUY and 
                sentiment_rec in ['STRONG_BUY', 'BUY'] and
                sentiment_direction in ['BULLISH', 'NEUTRAL']):
                
                trade_direction = 'BUY'
                
            elif (tech_signal_type == SignalType.SELL and 
                  sentiment_rec in ['STRONG_SELL', 'SELL'] and
                  sentiment_direction in ['BEARISH', 'NEUTRAL']):
                
                trade_direction = 'SELL'
                
            else:
                conflict_reason = f"Tech: {tech_signal_type}, Sentiment: {sentiment_rec} ({sentiment_direction})"
                return {'should_trade': False, 'reason': f'Conflicting signals - {conflict_reason}'}
            
            # Calculate position size using full balance approach
            balance_to_use = account.buying_power * (self.config.capital_use_percentage / 100)
            position_value = balance_to_use / (len(['AMD', 'SOL/USD']) - len(self.active_trades))
            
            if '/' in symbol:  # Crypto - fractional shares
                quantity = position_value / current_price
            else:  # Stock - whole shares
                quantity = int(position_value / current_price)
                
            if quantity <= 0:
                return {'should_trade': False, 'reason': f'Insufficient funds (calculated quantity: {quantity}, balance: ${balance_to_use:.2f})'}
            
            # Calculate stop-loss and take-profit
            is_crypto = '/' in symbol
            stop_loss_pct = self.config.crypto_stop_loss_percent if is_crypto else self.config.stop_loss_percent
            take_profit_pct = self.config.crypto_take_profit_percent if is_crypto else self.config.take_profit_percent
            
            if trade_direction == 'BUY':
                stop_loss = current_price * (1 - stop_loss_pct / 100)
                take_profit = current_price * (1 + take_profit_pct / 100)
            else:
                stop_loss = current_price * (1 + stop_loss_pct / 100)
                take_profit = current_price * (1 - take_profit_pct / 100)
            
            # Calculate estimated ROI
            estimated_roi = take_profit_pct if trade_direction == 'BUY' else take_profit_pct
            
            # Compile reasons
            reasons = technical_signal.reasons.copy()
            reasons.extend([
                f"Sentiment: {sentiment_rec}",
                f"Risk Level: {sentiment_analysis.get('risk_level', 'MEDIUM')}",
                f"Themes: {', '.join(sentiment_analysis.get('key_themes', []))}"
            ])
            
            return {
                'should_trade': True,
                'symbol': symbol,
                'direction': trade_direction,
                'quantity': quantity,
                'current_price': current_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'estimated_roi': estimated_roi,
                'confidence': (technical_signal.confidence + sentiment_analysis.get('confidence', 0)) / 2,
                'reasons': reasons,
                'technical_signal': technical_signal,
                'sentiment_analysis': sentiment_analysis
            }
            
        except Exception as e:
            self.logger.error(f"Analysis combination failed: {e}")
            return {'should_trade': False, 'reason': f'Analysis error: {e}'}
    
    def execute_trade(self, signal: Dict, account):
        """Execute a trade with SMS notifications"""
        try:
            symbol = signal['symbol']
            direction = signal['direction']
            quantity = signal['quantity']
            current_price = signal['current_price']
            stop_loss = signal['stop_loss']
            take_profit = signal['take_profit']
            
            self.logger.info(f"🎯 Executing {direction} for {symbol}")
            self.logger.info(f"   Quantity: {quantity}")
            self.logger.info(f"   Price: ${current_price:.2f}")
            self.logger.info(f"   Stop Loss: ${stop_loss:.2f}")
            self.logger.info(f"   Take Profit: ${take_profit:.2f}")
            
            # Place order
            order_side = OrderSide.BUY if direction == 'BUY' else OrderSide.SELL
            order_id = self.alpaca_client.place_order(
                symbol=symbol,
                qty=quantity,
                side=order_side,
                order_type=OrderType.MARKET
            )
            
            if order_id:
                # Track active trade
                self.active_trades[symbol] = ActiveTrade(
                    symbol=symbol,
                    side=direction,
                    quantity=quantity,
                    entry_price=current_price,
                    entry_time=datetime.now(),
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    current_price=current_price,
                    unrealized_pnl=0.0,
                    order_id=order_id,
                    reasons=signal['reasons']
                )
                
                self.daily_stats['trades_executed'] += 1
                
                # Send SMS notification
                self.notification_manager.send_trade_entry_alert({
                    'symbol': symbol,
                    'action': direction,
                    'price': current_price,
                    'quantity': quantity,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'estimated_roi': signal['estimated_roi'],
                    'reason': ', '.join(signal['reasons'][:2])  # Limit for SMS
                })
                
                self.logger.info(f"✅ Trade executed: {order_id}")
                
            else:
                self.logger.error(f"❌ Failed to place order for {symbol}")
                
        except Exception as e:
            self.logger.error(f"Trade execution failed for {symbol}: {e}")
    
    def monitor_positions(self):
        """Monitor active positions for exit conditions"""
        try:
            if not self.active_trades:
                return
                
            positions = self.alpaca_client.get_positions()
            position_dict = {pos.symbol: pos for pos in positions}
            
            for symbol, trade in list(self.active_trades.items()):
                try:
                    # Check if position still exists
                    if symbol not in position_dict:
                        self.logger.info(f"📊 Position {symbol} no longer exists - removing from tracking")
                        del self.active_trades[symbol]
                        continue
                    
                    position = position_dict[symbol]
                    
                    # Update current price and P&L
                    quote = self.alpaca_client.get_latest_quote(symbol)
                    if quote:
                        trade.current_price = (quote['bid'] + quote['ask']) / 2
                        trade.unrealized_pnl = position.unrealized_pl
                    
                    # Check exit conditions
                    should_exit, exit_reason = self.should_exit_position(trade)
                    
                    if should_exit:
                        self.close_position(symbol, trade, exit_reason)
                        
                except Exception as e:
                    self.logger.error(f"Error monitoring position {symbol}: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Position monitoring error: {e}")
    
    def should_exit_position(self, trade: ActiveTrade) -> tuple[bool, str]:
        """Determine if position should be exited"""
        try:
            current_price = trade.current_price
            
            if trade.side == 'BUY':
                # Long position
                if current_price <= trade.stop_loss:
                    return True, "Stop loss triggered"
                elif current_price >= trade.take_profit:
                    return True, "Take profit triggered"
            else:
                # Short position
                if current_price >= trade.stop_loss:
                    return True, "Stop loss triggered"
                elif current_price <= trade.take_profit:
                    return True, "Take profit triggered"
            
            # Time-based exit (optional)
            hours_held = (datetime.now() - trade.entry_time).total_seconds() / 3600
            if hours_held > 24:  # 24 hour max hold
                return True, "Maximum hold time reached"
                
            return False, "Continue holding"
            
        except Exception as e:
            self.logger.error(f"Exit condition check failed: {e}")
            return False, "Error checking exit conditions"
    
    def close_position(self, symbol: str, trade: ActiveTrade, reason: str):
        """Close position and log results"""
        try:
            self.logger.info(f"🔄 Closing {symbol}: {reason}")
            
            # Close position
            close_order_id = self.alpaca_client.close_position(symbol)
            
            if close_order_id:
                # Calculate final P&L
                exit_price = trade.current_price
                pnl = trade.unrealized_pnl
                pnl_percent = ((exit_price - trade.entry_price) / trade.entry_price) * 100
                duration = (datetime.now() - trade.entry_time).total_seconds() / 60
                
                if trade.side == 'SELL':  # Short position
                    pnl_percent = -pnl_percent
                
                # Log trade
                trade_data = {
                    'symbol': symbol,
                    'action': 'SELL' if trade.side == 'BUY' else 'BUY',
                    'quantity': trade.quantity,
                    'entry_price': trade.entry_price,
                    'exit_price': exit_price,
                    'pnl': pnl,
                    'pnl_percent': pnl_percent,
                    'exit_reason': reason,
                    'duration_minutes': int(duration),
                    'strategy_signals': ', '.join(trade.reasons),
                    'confidence': 0.8,  # Would get from stored data
                    'fees': 0.0
                }
                
                self.trading_logger.log_trade(trade_data)
                
                # Send SMS notification
                self.notification_manager.send_trade_exit_alert({
                    'symbol': symbol,
                    'original_action': trade.side,
                    'entry_price': trade.entry_price,
                    'exit_price': exit_price,
                    'quantity': trade.quantity,
                    'pnl': pnl,
                    'pnl_percent': pnl_percent,
                    'exit_reason': reason,
                    'duration_minutes': int(duration)
                })
                
                # Update daily stats
                self.daily_stats['profit_loss'] += pnl
                
                # Remove from active trades
                del self.active_trades[symbol]
                
                self.logger.info(f"✅ Position closed: {symbol} P&L: ${pnl:.2f} ({pnl_percent:.1f}%)")
                
        except Exception as e:
            self.logger.error(f"Error closing position {symbol}: {e}")
    
    def get_alternative_crypto_data(self, symbol: str):
        """Get crypto data from alternative source (yfinance)"""
        try:
            import yfinance as yf
            
            # Convert symbol format: SOL/USD -> SOL-USD
            yf_symbol = symbol.replace('/', '-')
            
            self.logger.info(f"    🔍 Fetching {yf_symbol} from yfinance...")
            
            ticker = yf.Ticker(yf_symbol)
            hist = ticker.history(period="6mo", interval="1d")
            
            if hist.empty:
                return None
            
            # Convert to match Alpaca format
            df = hist.copy()
            df.columns = [col.lower() for col in df.columns]
            df = df.rename(columns={'adj close': 'close'})
            
            # Ensure we have required columns
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in required_cols:
                if col not in df.columns:
                    self.logger.warning(f"Missing column {col} in alternative data")
                    return None
            
            return df
            
        except Exception as e:
            self.logger.warning(f"Alternative data fetch failed for {symbol}: {e}")
            return None
    
    def update_status(self):
        """Update bot status"""
        try:
            self.status.active_trades = len(self.active_trades)
            
            # Calculate daily P&L
            account = self.alpaca_client.get_account()
            self.status.daily_pnl = account.portfolio_value - self.daily_stats['start_portfolio_value']
            
        except Exception as e:
            self.logger.error(f"Status update error: {e}")

def main():
    """Main entry point"""
    try:
        bot = EnhancedTradingBot()
        bot.start()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Bot failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()