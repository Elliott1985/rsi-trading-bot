"""
Portfolio Management Module
Handles trade suggestions, position sizing, and risk management
"""

import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import pandas as pd
from src.analysis.technical_analyzer import MarketOpportunity
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class TradeSuggestion:
    """Complete trade suggestion with entry, exit, and risk parameters"""
    symbol: str
    trade_type: str  # 'stock_buy', 'stock_sell', 'call_option', 'put_option', 'crypto_buy', 'crypto_sell'
    entry_price: float
    target_price: float
    stop_loss: float
    position_size: float  # Dollar amount or number of shares/contracts
    risk_reward_ratio: float
    max_risk: float  # Maximum dollar risk
    strategy: str
    confidence: float
    expiration: Optional[datetime] = None
    option_strike: Optional[float] = None
    option_expiry: Optional[str] = None

@dataclass
class OptionsStrategy:
    """Options trading strategy details"""
    symbol: str
    strategy_name: str  # 'call', 'put', 'straddle', 'iron_condor'
    contracts: List[Dict[str, Any]]
    total_cost: float
    max_profit: float
    max_loss: float
    breakeven_points: List[float]
    expiration: datetime

class PortfolioManager:
    """Main portfolio and trade management engine"""
    
    def __init__(self):
        self.max_position_size_pct = 0.10  # Max 10% of portfolio per trade
        self.max_daily_risk_pct = 0.02     # Max 2% daily risk
        self.min_risk_reward_ratio = 2.0   # Minimum 2:1 risk/reward
        
    async def initialize(self):
        """Initialize the portfolio manager"""
        logger.info("Initializing Portfolio Manager...")
    
    async def generate_trade_suggestions(self, stock_opportunities: List[MarketOpportunity], 
                                       crypto_opportunities: List[MarketOpportunity],
                                       budget: float, profit_goal: float) -> List[TradeSuggestion]:
        """Generate comprehensive trade suggestions based on opportunities and budget"""
        logger.info(f"Generating trade suggestions for ${budget} budget with {profit_goal}% profit goal")
        
        suggestions = []
        remaining_budget = budget
        
        # Process stock opportunities
        for opportunity in stock_opportunities:
            if remaining_budget <= 0:
                break
                
            stock_suggestions = await self._create_stock_suggestions(
                opportunity, remaining_budget, profit_goal
            )
            
            for suggestion in stock_suggestions:
                if suggestion.position_size <= remaining_budget:
                    suggestions.append(suggestion)
                    remaining_budget -= suggestion.position_size
        
        # Process crypto opportunities
        for opportunity in crypto_opportunities:
            if remaining_budget <= 0:
                break
                
            crypto_suggestion = await self._create_crypto_suggestion(
                opportunity, remaining_budget, profit_goal
            )
            
            if crypto_suggestion and crypto_suggestion.position_size <= remaining_budget:
                suggestions.append(crypto_suggestion)
                remaining_budget -= crypto_suggestion.position_size
        
        # Sort by risk-adjusted return potential
        suggestions.sort(key=lambda x: x.confidence * x.risk_reward_ratio, reverse=True)
        
        logger.info(f"Generated {len(suggestions)} trade suggestions using ${budget - remaining_budget:.2f} of budget")
        return suggestions[:15]  # Return top 15 suggestions
    
    async def _create_stock_suggestions(self, opportunity: MarketOpportunity, 
                                      budget: float, profit_goal: float) -> List[TradeSuggestion]:
        """Create stock and options trade suggestions"""
        suggestions = []
        max_position = min(budget * self.max_position_size_pct, budget * 0.3)  # Max 30% for single stock
        
        # Calculate position sizing
        risk_per_share = abs(opportunity.entry_price - opportunity.stop_loss)
        max_shares = int(max_position / opportunity.entry_price)
        risk_adjusted_shares = int((max_position * 0.02) / risk_per_share)  # 2% max risk
        
        position_shares = min(max_shares, risk_adjusted_shares, int(budget / opportunity.entry_price))
        
        if position_shares <= 0:
            return suggestions
        
        position_value = position_shares * opportunity.entry_price
        max_risk = position_shares * risk_per_share
        risk_reward = abs(opportunity.target_price - opportunity.entry_price) / risk_per_share
        
        # Stock position suggestion
        if opportunity.technical_signals[0].signal_type == 'buy':
            trade_type = 'stock_buy'
        else:
            trade_type = 'stock_sell'
        
        stock_suggestion = TradeSuggestion(
            symbol=opportunity.symbol,
            trade_type=trade_type,
            entry_price=opportunity.entry_price,
            target_price=opportunity.target_price,
            stop_loss=opportunity.stop_loss,
            position_size=position_value,
            risk_reward_ratio=risk_reward,
            max_risk=max_risk,
            strategy=f"Stock {opportunity.strategy}",
            confidence=opportunity.confidence_score
        )
        
        if risk_reward >= self.min_risk_reward_ratio:
            suggestions.append(stock_suggestion)
        
        # Options suggestions
        options_suggestions = await self._create_options_suggestions(opportunity, budget * 0.15)  # 15% max for options
        suggestions.extend(options_suggestions)
        
        return suggestions
    
    async def _create_options_suggestions(self, opportunity: MarketOpportunity, 
                                        max_options_budget: float) -> List[TradeSuggestion]:
        """Create options trading suggestions"""
        suggestions = []
        signal = opportunity.technical_signals[0]
        current_price = opportunity.entry_price
        
        # Calculate option parameters (simplified - would need real options data)
        days_to_expiry = 30  # Target 30 days
        expiry_date = datetime.now() + timedelta(days=days_to_expiry)
        
        if signal.signal_type == 'buy':
            # Call option suggestions
            strike_prices = [
                current_price * 1.02,  # 2% OTM
                current_price * 1.05,  # 5% OTM
            ]
            
            for strike in strike_prices:
                # Estimate option premium (simplified calculation)
                option_premium = self._estimate_option_premium(current_price, strike, days_to_expiry, 'call')
                contracts = int(max_options_budget / (option_premium * 100))
                
                if contracts > 0:
                    total_cost = contracts * option_premium * 100
                    target_premium = option_premium * 3  # Target 200% gain
                    
                    suggestion = TradeSuggestion(
                        symbol=opportunity.symbol,
                        trade_type='call_option',
                        entry_price=option_premium,
                        target_price=target_premium,
                        stop_loss=option_premium * 0.5,  # 50% stop loss
                        position_size=total_cost,
                        risk_reward_ratio=2.0,
                        max_risk=total_cost * 0.5,
                        strategy=f"Call Option {int((strike/current_price - 1) * 100)}% OTM",
                        confidence=opportunity.confidence_score * 0.8,  # Lower confidence for options
                        expiration=expiry_date,
                        option_strike=strike,
                        option_expiry=f"{days_to_expiry}d"
                    )
                    suggestions.append(suggestion)
        
        elif signal.signal_type == 'sell':
            # Put option suggestions
            strike_prices = [
                current_price * 0.98,  # 2% OTM
                current_price * 0.95,  # 5% OTM
            ]
            
            for strike in strike_prices:
                option_premium = self._estimate_option_premium(current_price, strike, days_to_expiry, 'put')
                contracts = int(max_options_budget / (option_premium * 100))
                
                if contracts > 0:
                    total_cost = contracts * option_premium * 100
                    target_premium = option_premium * 3
                    
                    suggestion = TradeSuggestion(
                        symbol=opportunity.symbol,
                        trade_type='put_option',
                        entry_price=option_premium,
                        target_price=target_premium,
                        stop_loss=option_premium * 0.5,
                        position_size=total_cost,
                        risk_reward_ratio=2.0,
                        max_risk=total_cost * 0.5,
                        strategy=f"Put Option {int((1 - strike/current_price) * 100)}% OTM",
                        confidence=opportunity.confidence_score * 0.8,
                        expiration=expiry_date,
                        option_strike=strike,
                        option_expiry=f"{days_to_expiry}d"
                    )
                    suggestions.append(suggestion)
        
        return suggestions
    
    def _estimate_option_premium(self, current_price: float, strike: float, 
                               days_to_expiry: int, option_type: str) -> float:
        """Simplified option premium estimation (would use Black-Scholes in production)"""
        time_value = days_to_expiry / 365.0
        volatility = 0.3  # Assume 30% implied volatility
        
        if option_type == 'call':
            intrinsic = max(0, current_price - strike)
            time_premium = (current_price * volatility * (time_value ** 0.5)) * 0.4
        else:  # put
            intrinsic = max(0, strike - current_price)
            time_premium = (current_price * volatility * (time_value ** 0.5)) * 0.4
        
        return max(intrinsic + time_premium, 0.05)  # Minimum $0.05
    
    async def _create_crypto_suggestion(self, opportunity: MarketOpportunity, 
                                      budget: float, profit_goal: float) -> Optional[TradeSuggestion]:
        """Create cryptocurrency trade suggestion"""
        max_position = min(budget * self.max_position_size_pct, budget * 0.25)  # Max 25% for single crypto
        
        # Calculate position sizing for crypto
        risk_per_unit = abs(opportunity.entry_price - opportunity.stop_loss)
        max_units = max_position / opportunity.entry_price
        risk_adjusted_units = (max_position * 0.03) / risk_per_unit  # 3% max risk for crypto (more volatile)
        
        position_units = min(max_units, risk_adjusted_units)
        
        if position_units <= 0:
            return None
        
        position_value = position_units * opportunity.entry_price
        max_risk = position_units * risk_per_unit
        risk_reward = abs(opportunity.target_price - opportunity.entry_price) / risk_per_unit
        
        if opportunity.technical_signals[0].signal_type == 'buy':
            trade_type = 'crypto_buy'
        else:
            trade_type = 'crypto_sell'
        
        return TradeSuggestion(
            symbol=opportunity.symbol,
            trade_type=trade_type,
            entry_price=opportunity.entry_price,
            target_price=opportunity.target_price,
            stop_loss=opportunity.stop_loss,
            position_size=position_value,
            risk_reward_ratio=risk_reward,
            max_risk=max_risk,
            strategy=f"Crypto {opportunity.strategy}",
            confidence=opportunity.confidence_score
        )
    
    def calculate_portfolio_risk(self, suggestions: List[TradeSuggestion]) -> Dict[str, float]:
        """Calculate overall portfolio risk metrics"""
        total_position_value = sum(s.position_size for s in suggestions)
        total_max_risk = sum(s.max_risk for s in suggestions)
        
        # Asset allocation
        stock_allocation = sum(s.position_size for s in suggestions if 'stock' in s.trade_type)
        options_allocation = sum(s.position_size for s in suggestions if 'option' in s.trade_type)
        crypto_allocation = sum(s.position_size for s in suggestions if 'crypto' in s.trade_type)
        
        return {
            'total_position_value': total_position_value,
            'total_max_risk': total_max_risk,
            'risk_percentage': (total_max_risk / total_position_value) * 100 if total_position_value > 0 else 0,
            'stock_allocation_pct': (stock_allocation / total_position_value) * 100 if total_position_value > 0 else 0,
            'options_allocation_pct': (options_allocation / total_position_value) * 100 if total_position_value > 0 else 0,
            'crypto_allocation_pct': (crypto_allocation / total_position_value) * 100 if total_position_value > 0 else 0,
        }