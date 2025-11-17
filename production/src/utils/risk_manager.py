#!/usr/bin/env python3
"""
Risk Management Module
Handles position sizing, stop losses, and capital allocation.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import json
import os

@dataclass
class TradeRisk:
    """Risk assessment for a potential trade"""
    symbol: str
    entry_price: float
    stop_loss_price: float
    take_profit_price: float
    position_size: int
    risk_amount: float
    reward_amount: float
    risk_reward_ratio: float
    max_loss_percent: float
    confidence_score: float

@dataclass
class PositionRisk:
    """Risk metrics for an existing position"""
    symbol: str
    current_price: float
    entry_price: float
    quantity: int
    market_value: float
    unrealized_pl: float
    unrealized_pl_percent: float
    stop_loss_price: float
    take_profit_price: float
    trail_stop_price: float
    days_held: int
    risk_level: str  # LOW, MEDIUM, HIGH

class RiskManager:
    """Advanced risk management for trading operations"""
    
    def __init__(self, config_manager, alpaca_client):
        self.config = config_manager
        self.alpaca = alpaca_client
        self.logger = logging.getLogger(__name__)
        
        # Load historical risk data
        self.daily_losses = []
        self.position_history = []
        self.risk_metrics_path = os.path.join(
            os.path.dirname(config_manager.config_path), '..', 'data', 'risk_metrics.json'
        )
        self.load_risk_history()
    
    def load_risk_history(self):
        """Load historical risk data"""
        try:
            if os.path.exists(self.risk_metrics_path):
                with open(self.risk_metrics_path, 'r') as f:
                    data = json.load(f)
                    self.daily_losses = data.get('daily_losses', [])
                    self.position_history = data.get('position_history', [])
            
        except Exception as e:
            self.logger.error(f"Failed to load risk history: {e}")
    
    def save_risk_history(self):
        """Save risk data to file"""
        try:
            os.makedirs(os.path.dirname(self.risk_metrics_path), exist_ok=True)
            
            data = {
                'daily_losses': self.daily_losses[-30:],  # Keep last 30 days
                'position_history': self.position_history[-100:],  # Keep last 100 positions
                'updated_at': datetime.now().isoformat()
            }
            
            with open(self.risk_metrics_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save risk history: {e}")
    
    def calculate_position_size(self, symbol: str, entry_price: float, stop_loss_price: float, 
                               account_balance: float, confidence: float = 1.0) -> TradeRisk:
        """Calculate optimal position size based on risk parameters"""
        try:
            config = self.config.trading_config
            
            # Calculate risk per share
            risk_per_share = abs(entry_price - stop_loss_price)
            if risk_per_share <= 0:
                raise ValueError("Invalid stop loss price")
            
            # Base risk amount (percentage of account)
            base_risk_percent = config.stop_loss_percent / 100
            
            # Adjust risk based on confidence
            confidence_multiplier = min(confidence * 1.5, 2.0)  # Max 2x position size
            adjusted_risk_percent = base_risk_percent * confidence_multiplier
            
            # Scale down position size based on consecutive losses (if bot instance available)
            try:
                import __main__
                if hasattr(__main__, 'bot_instance'):
                    consecutive_losses = getattr(__main__.bot_instance, 'consecutive_losses', 0)
                    if consecutive_losses > 0:
                        loss_scaling = max(0.5, 1.0 - (consecutive_losses * 0.2))  # Reduce by 20% per loss, min 50%
                        adjusted_risk_percent *= loss_scaling
                        self.logger.info(f"📉 Scaling position size due to {consecutive_losses} consecutive losses: {loss_scaling:.2f}x")
            except:
                pass  # Fail silently if bot instance not available
            
            # Maximum position size limit
            max_position_value = account_balance * config.max_position_size
            max_risk_amount = account_balance * adjusted_risk_percent
            
            # Calculate position size
            position_size_by_risk = int(max_risk_amount / risk_per_share)
            position_size_by_value = int(max_position_value / entry_price)
            
            # Use the smaller of the two
            position_size = min(position_size_by_risk, position_size_by_value)
            
            # Ensure minimum trade amount meets Alpaca's $1 minimum order requirement
            min_notional_value = max(config.min_trade_amount, 1.0)  # At least $1
            min_shares_by_amount = max(1, int(min_notional_value / entry_price))
            
            # For fractional shares (crypto), ensure minimum $1 notional value
            is_crypto = symbol and ('/' in symbol or symbol.endswith('USD'))
            self.logger.info(f"Position size calculation for {symbol}: is_crypto={is_crypto}, initial_size={position_size}")
            if is_crypto:  # Crypto pair
                min_position_size = min_notional_value / entry_price
                position_size = max(position_size, min_position_size)
                self.logger.info(f"Crypto: min_notional=${min_notional_value}, min_size={min_position_size}, final_size={position_size}")
            else:
                # For stocks, use integer shares
                position_size = max(position_size, min_shares_by_amount)
                self.logger.info(f"Stock: min_shares={min_shares_by_amount}, final_size={position_size}")
            
            # Calculate actual risk and reward
            actual_risk = position_size * risk_per_share
            
            # Calculate take profit price (risk/reward ratio)
            take_profit_distance = risk_per_share * (config.take_profit_percent / config.stop_loss_percent)
            take_profit_price = entry_price + take_profit_distance if entry_price > stop_loss_price else entry_price - take_profit_distance
            
            actual_reward = position_size * abs(take_profit_price - entry_price)
            risk_reward_ratio = actual_reward / actual_risk if actual_risk > 0 else 0
            
            return TradeRisk(
                symbol=symbol,
                entry_price=entry_price,
                stop_loss_price=stop_loss_price,
                take_profit_price=take_profit_price,
                position_size=position_size,
                risk_amount=actual_risk,
                reward_amount=actual_reward,
                risk_reward_ratio=risk_reward_ratio,
                max_loss_percent=(actual_risk / account_balance) * 100,
                confidence_score=confidence
            )
            
        except Exception as e:
            self.logger.error(f"Position size calculation error for {symbol}: {e}")
            return None
    
    def check_daily_loss_limit(self, account_balance: float) -> bool:
        """Check if daily loss limit has been reached"""
        try:
            config = self.config.trading_config
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Calculate today's loss
            todays_loss = sum(
                loss['amount'] for loss in self.daily_losses 
                if loss['date'] == today
            )
            
            max_daily_loss = config.max_daily_loss
            if todays_loss >= max_daily_loss:
                self.logger.warning(f"Daily loss limit reached: ${todays_loss:.2f} >= ${max_daily_loss:.2f}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Daily loss limit check error: {e}")
            return True  # Allow trading if check fails
    
    def check_max_positions(self) -> bool:
        """Check if maximum position limit has been reached"""
        try:
            positions = self.alpaca.get_positions()
            config = self.config.trading_config
            
            if len(positions) >= config.max_positions:
                self.logger.warning(f"Max positions limit reached: {len(positions)} >= {config.max_positions}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Max positions check error: {e}")
            return True
    
    def validate_trade(self, trade_risk: TradeRisk, account_balance: float) -> Tuple[bool, str]:
        """Validate if a trade should be executed"""
        try:
            # Check daily loss limit
            if not self.check_daily_loss_limit(account_balance):
                return False, "Daily loss limit reached"
            
            # Check max positions
            if not self.check_max_positions():
                return False, "Maximum positions limit reached"
            
            # Check minimum risk/reward ratio
            if trade_risk.risk_reward_ratio < 1.5:
                return False, f"Poor risk/reward ratio: {trade_risk.risk_reward_ratio:.2f}"
            
            # Check maximum loss percentage (more lenient for small accounts)
            max_risk_percent = 25.0 if account_balance < 100 else 10.0  # 25% for accounts under $100, 10% otherwise
            if trade_risk.max_loss_percent > max_risk_percent:
                return False, f"Risk too high: {trade_risk.max_loss_percent:.1f}% (max {max_risk_percent:.0f}%)"
            
            # Check minimum notional value (Alpaca requires at least $1)
            required_capital = trade_risk.position_size * trade_risk.entry_price
            if required_capital < 1.0:
                return False, f"Order value too small: ${required_capital:.2f} (minimum $1.00)"
            
            # Check minimum position size for non-crypto assets
            is_crypto = '/' in trade_risk.symbol or trade_risk.symbol.endswith('USD')
            if not is_crypto and trade_risk.position_size < 1:
                return False, "Position size too small for stocks"
            
            # Check if enough buying power
            if required_capital > account_balance * 0.95:  # Leave 5% buffer
                return False, "Insufficient buying power"
            
            return True, "Trade validated"
            
        except Exception as e:
            self.logger.error(f"Trade validation error: {e}")
            return False, f"Validation error: {e}"
    
    def calculate_stop_loss(self, symbol: str, entry_price: float, signal_type: str, atr: float = None) -> float:
        """Calculate dynamic stop loss price"""
        try:
            config = self.config.trading_config
            
            # Use crypto-specific parameters if it's a crypto symbol
            is_crypto = '/' in symbol
            if is_crypto:
                stop_loss_percent = getattr(config, 'crypto_stop_loss_percent', config.stop_loss_percent) / 100
            else:
                stop_loss_percent = config.stop_loss_percent / 100
            
            # Use ATR for dynamic stop loss if available
            if atr and atr > 0:
                # Use 2x ATR as stop loss distance
                stop_distance = atr * 2
            else:
                # Fallback to percentage-based stop loss
                stop_distance = entry_price * stop_loss_percent
            
            if signal_type.upper() == 'BUY':
                return entry_price - stop_distance
            else:
                return entry_price + stop_distance
                
        except Exception as e:
            self.logger.error(f"Stop loss calculation error for {symbol}: {e}")
            return entry_price * (1 - config.stop_loss_percent / 100)
    
    def calculate_trailing_stop(self, symbol: str, entry_price: float, current_price: float, 
                               signal_type: str, highest_price: float = None) -> float:
        """Calculate trailing stop price"""
        try:
            config = self.config.trading_config
            trail_percent = config.trailing_stop_percent / 100
            
            if signal_type.upper() == 'BUY':
                # For long positions, trail below the highest price
                reference_price = highest_price if highest_price else current_price
                return reference_price * (1 - trail_percent)
            else:
                # For short positions, trail above the lowest price
                reference_price = highest_price if highest_price else current_price  # Should be lowest_price
                return reference_price * (1 + trail_percent)
                
        except Exception as e:
            self.logger.error(f"Trailing stop calculation error for {symbol}: {e}")
            return current_price * (1 - trail_percent)
    
    def assess_position_risk(self, position) -> PositionRisk:
        """Assess risk for existing position"""
        try:
            # Get current market data
            quote = self.alpaca.get_latest_quote(position.symbol)
            current_price = (quote['bid'] + quote['ask']) / 2 if quote else position.avg_entry_price
            
            # Calculate days held (approximate)
            days_held = 1  # Would need order history for accurate calculation
            
            # Determine risk level
            unrealized_pl_percent = (position.unrealized_plpc * 100) if hasattr(position, 'unrealized_plpc') else 0
            
            if unrealized_pl_percent < -5:
                risk_level = "HIGH"
            elif unrealized_pl_percent < -2:
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"
            
            # Calculate stop losses and targets
            config = self.config.trading_config
            stop_loss_price = self.calculate_stop_loss(position.symbol, position.avg_entry_price, 
                                                     "BUY" if position.qty > 0 else "SELL")
            
            take_profit_distance = abs(position.avg_entry_price - stop_loss_price) * (config.take_profit_percent / config.stop_loss_percent)
            take_profit_price = position.avg_entry_price + take_profit_distance if position.qty > 0 else position.avg_entry_price - take_profit_distance
            
            trail_stop_price = self.calculate_trailing_stop(position.symbol, position.avg_entry_price, 
                                                          current_price, "BUY" if position.qty > 0 else "SELL")
            
            return PositionRisk(
                symbol=position.symbol,
                current_price=current_price,
                entry_price=position.avg_entry_price,
                quantity=int(position.qty),
                market_value=position.market_value,
                unrealized_pl=position.unrealized_pl,
                unrealized_pl_percent=unrealized_pl_percent,
                stop_loss_price=stop_loss_price,
                take_profit_price=take_profit_price,
                trail_stop_price=trail_stop_price,
                days_held=days_held,
                risk_level=risk_level
            )
            
        except Exception as e:
            self.logger.error(f"Position risk assessment error for {position.symbol}: {e}")
            return None
    
    def should_close_position(self, position_risk: PositionRisk) -> Tuple[bool, str]:
        """Determine if a position should be closed"""
        try:
            # Stop loss hit
            if position_risk.quantity > 0:  # Long position
                if position_risk.current_price <= position_risk.stop_loss_price:
                    return True, "Stop loss triggered"
                if position_risk.current_price >= position_risk.take_profit_price:
                    return True, "Take profit triggered"
            else:  # Short position
                if position_risk.current_price >= position_risk.stop_loss_price:
                    return True, "Stop loss triggered"
                if position_risk.current_price <= position_risk.take_profit_price:
                    return True, "Take profit triggered"
            
            # Time-based exit (hold for too long)
            if position_risk.days_held > 5 and position_risk.unrealized_pl_percent < -1:
                return True, "Position held too long with loss"
            
            # High risk position with significant loss
            if position_risk.risk_level == "HIGH" and position_risk.unrealized_pl_percent < -8:
                return True, "High risk position with large loss"
            
            return False, "Hold position"
            
        except Exception as e:
            self.logger.error(f"Position close decision error: {e}")
            return False, "Error in decision making"
    
    def record_trade_result(self, symbol: str, entry_price: float, exit_price: float, 
                           quantity: int, trade_type: str):
        """Record trade result for learning"""
        try:
            pl_amount = (exit_price - entry_price) * quantity if trade_type == "BUY" else (entry_price - exit_price) * quantity
            
            trade_record = {
                'symbol': symbol,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'quantity': quantity,
                'trade_type': trade_type,
                'pl_amount': pl_amount,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'timestamp': datetime.now().isoformat()
            }
            
            self.position_history.append(trade_record)
            
            # Record daily loss if applicable
            if pl_amount < 0:
                today = datetime.now().strftime('%Y-%m-%d')
                daily_loss = {
                    'date': today,
                    'amount': abs(pl_amount),
                    'symbol': symbol
                }
                self.daily_losses.append(daily_loss)
            
            # Save to file
            self.save_risk_history()
            
            self.logger.info(f"Trade recorded: {symbol} P&L: ${pl_amount:.2f}")
            
        except Exception as e:
            self.logger.error(f"Trade recording error: {e}")
    
    def get_risk_summary(self) -> Dict:
        """Get overall risk summary"""
        try:
            positions = self.alpaca.get_positions()
            account = self.alpaca.get_account()
            
            total_exposure = sum(abs(pos.market_value) for pos in positions)
            total_unrealized_pl = sum(pos.unrealized_pl for pos in positions)
            
            # Calculate today's performance
            today = datetime.now().strftime('%Y-%m-%d')
            todays_loss = sum(
                loss['amount'] for loss in self.daily_losses 
                if loss['date'] == today
            )
            
            return {
                'total_positions': len(positions),
                'total_exposure': total_exposure,
                'exposure_percent': (total_exposure / account.portfolio_value) * 100 if account.portfolio_value > 0 else 0,
                'total_unrealized_pl': total_unrealized_pl,
                'todays_loss': todays_loss,
                'daily_loss_limit': self.config.trading_config.max_daily_loss,
                'remaining_daily_risk': max(0, self.config.trading_config.max_daily_loss - todays_loss),
                'max_positions': self.config.trading_config.max_positions,
                'remaining_position_slots': max(0, self.config.trading_config.max_positions - len(positions))
            }
            
        except Exception as e:
            self.logger.error(f"Risk summary error: {e}")
            return {}
    
    def optimize_portfolio(self) -> List[Dict]:
        """Suggest portfolio optimizations"""
        try:
            suggestions = []
            positions = self.alpaca.get_positions()
            
            # Assess all positions
            high_risk_positions = []
            for pos in positions:
                risk = self.assess_position_risk(pos)
                if risk and risk.risk_level == "HIGH":
                    high_risk_positions.append(risk)
            
            if high_risk_positions:
                suggestions.append({
                    'type': 'REDUCE_RISK',
                    'message': f"Consider closing {len(high_risk_positions)} high-risk positions",
                    'positions': [pos.symbol for pos in high_risk_positions]
                })
            
            # Check concentration risk
            position_values = {pos.symbol: abs(pos.market_value) for pos in positions}
            total_value = sum(position_values.values())
            
            for symbol, value in position_values.items():
                if value / total_value > 0.25:  # More than 25% in one position
                    suggestions.append({
                        'type': 'CONCENTRATION_RISK',
                        'message': f"{symbol} represents {(value/total_value)*100:.1f}% of portfolio",
                        'symbol': symbol
                    })
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Portfolio optimization error: {e}")
            return []