#!/usr/bin/env python3
"""
Comprehensive Logging and Performance Tracking System
Handles trade logging, performance analysis, and strategy adaptation.
"""

import csv
import json
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging
import os
from collections import defaultdict

@dataclass
class TradeLog:
    """Trade execution log entry"""
    timestamp: str
    symbol: str
    action: str  # BUY, SELL
    quantity: int
    entry_price: float
    exit_price: float
    duration_minutes: int
    pnl: float
    pnl_percent: float
    strategy_signals: str
    sentiment_score: float
    confidence: float
    risk_reward_ratio: float
    stop_loss_price: float
    take_profit_price: float
    exit_reason: str
    fees: float

@dataclass
class PerformanceMetrics:
    """Daily/weekly/monthly performance metrics"""
    date: str
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    max_profit: float
    max_loss: float
    avg_profit: float
    avg_loss: float
    profit_factor: float
    sharpe_ratio: float
    max_drawdown: float
    portfolio_value: float

@dataclass
class SymbolPerformance:
    """Performance tracking per symbol"""
    symbol: str
    total_trades: int
    winning_trades: int
    win_rate: float
    total_pnl: float
    avg_hold_time: float
    best_trade: float
    worst_trade: float
    success_score: float  # Weighted score for future decisions

class TradingLogger:
    """Advanced logging and performance tracking system"""
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.logger = logging.getLogger(__name__)
        
        # Get log file paths
        self.log_paths = config_manager.get_log_paths()
        
        # Ensure log directories exist
        for path in self.log_paths.values():
            os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Initialize log files with headers if they don't exist
        self.initialize_log_files()
        
        # In-memory caches for performance
        self.daily_metrics = {}
        self.symbol_performance = {}
        
        # Load existing performance data
        self.load_performance_data()
    
    def initialize_log_files(self):
        """Initialize CSV log files with appropriate headers"""
        try:
            # Trade log headers
            trade_headers = [
                'timestamp', 'symbol', 'action', 'quantity', 'entry_price', 'exit_price',
                'duration_minutes', 'pnl', 'pnl_percent', 'strategy_signals', 'sentiment_score',
                'confidence', 'risk_reward_ratio', 'stop_loss_price', 'take_profit_price',
                'exit_reason', 'fees'
            ]
            
            if not os.path.exists(self.log_paths['trade_log']):
                with open(self.log_paths['trade_log'], 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(trade_headers)
            
            # Performance log headers
            perf_headers = [
                'date', 'total_trades', 'winning_trades', 'losing_trades', 'win_rate',
                'total_pnl', 'max_profit', 'max_loss', 'avg_profit', 'avg_loss',
                'profit_factor', 'sharpe_ratio', 'max_drawdown', 'portfolio_value'
            ]
            
            if not os.path.exists(self.log_paths['performance_log']):
                with open(self.log_paths['performance_log'], 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(perf_headers)
        
        except Exception as e:
            self.logger.error(f"Failed to initialize log files: {e}")
    
    def log_trade(self, trade_data: Dict):
        """Log a completed trade"""
        try:
            # Create trade log entry
            trade_log = TradeLog(
                timestamp=datetime.now().isoformat(),
                symbol=trade_data['symbol'],
                action=trade_data['action'],
                quantity=trade_data['quantity'],
                entry_price=trade_data['entry_price'],
                exit_price=trade_data['exit_price'],
                duration_minutes=trade_data.get('duration_minutes', 0),
                pnl=trade_data['pnl'],
                pnl_percent=trade_data['pnl_percent'],
                strategy_signals=trade_data.get('strategy_signals', ''),
                sentiment_score=trade_data.get('sentiment_score', 0.0),
                confidence=trade_data.get('confidence', 0.0),
                risk_reward_ratio=trade_data.get('risk_reward_ratio', 0.0),
                stop_loss_price=trade_data.get('stop_loss_price', 0.0),
                take_profit_price=trade_data.get('take_profit_price', 0.0),
                exit_reason=trade_data.get('exit_reason', 'MANUAL'),
                fees=trade_data.get('fees', 0.0)
            )
            
            # Write to CSV
            with open(self.log_paths['trade_log'], 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(list(asdict(trade_log).values()))
            
            # Update performance metrics
            self.update_symbol_performance(trade_log)
            self.update_daily_metrics(trade_log)
            
            self.logger.info(f"Trade logged: {trade_log.symbol} P&L: ${trade_log.pnl:.2f}")
            
        except Exception as e:
            self.logger.error(f"Failed to log trade: {e}")
    
    def update_symbol_performance(self, trade_log: TradeLog):
        """Update performance metrics for a specific symbol"""
        try:
            symbol = trade_log.symbol
            
            if symbol not in self.symbol_performance:
                self.symbol_performance[symbol] = {
                    'total_trades': 0,
                    'winning_trades': 0,
                    'total_pnl': 0.0,
                    'hold_times': [],
                    'pnl_history': []
                }
            
            perf = self.symbol_performance[symbol]
            perf['total_trades'] += 1
            perf['total_pnl'] += trade_log.pnl
            perf['hold_times'].append(trade_log.duration_minutes)
            perf['pnl_history'].append(trade_log.pnl)
            
            if trade_log.pnl > 0:
                perf['winning_trades'] += 1
            
            # Calculate success score (weighted by recency and profitability)
            recent_trades = perf['pnl_history'][-10:]  # Last 10 trades
            if recent_trades:
                recent_win_rate = sum(1 for pnl in recent_trades if pnl > 0) / len(recent_trades)
                avg_pnl = sum(recent_trades) / len(recent_trades)
                perf['success_score'] = (recent_win_rate * 0.6) + (min(avg_pnl / 100, 0.4))
            
        except Exception as e:
            self.logger.error(f"Failed to update symbol performance: {e}")
    
    def update_daily_metrics(self, trade_log: TradeLog):
        """Update daily performance metrics"""
        try:
            date = datetime.fromisoformat(trade_log.timestamp).strftime('%Y-%m-%d')
            
            if date not in self.daily_metrics:
                self.daily_metrics[date] = {
                    'trades': [],
                    'total_pnl': 0.0,
                    'portfolio_values': []
                }
            
            daily = self.daily_metrics[date]
            daily['trades'].append(trade_log)
            daily['total_pnl'] += trade_log.pnl
            
        except Exception as e:
            self.logger.error(f"Failed to update daily metrics: {e}")
    
    def calculate_performance_metrics(self, start_date: str = None, end_date: str = None) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics"""
        try:
            # Load trade data
            df = self.load_trade_history()
            if df.empty:
                return None
            
            # Filter by date range if specified
            if start_date or end_date:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                if start_date:
                    df = df[df['timestamp'] >= pd.to_datetime(start_date)]
                if end_date:
                    df = df[df['timestamp'] <= pd.to_datetime(end_date)]
            
            # Calculate basic metrics
            total_trades = len(df)
            winning_trades = len(df[df['pnl'] > 0])
            losing_trades = len(df[df['pnl'] < 0])
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            
            total_pnl = df['pnl'].sum()
            max_profit = df['pnl'].max()
            max_loss = df['pnl'].min()
            
            # Calculate averages
            winning_df = df[df['pnl'] > 0]
            losing_df = df[df['pnl'] < 0]
            
            avg_profit = winning_df['pnl'].mean() if not winning_df.empty else 0
            avg_loss = losing_df['pnl'].mean() if not losing_df.empty else 0
            
            # Profit factor
            gross_profit = winning_df['pnl'].sum() if not winning_df.empty else 0
            gross_loss = abs(losing_df['pnl'].sum()) if not losing_df.empty else 0
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
            
            # Sharpe ratio (simplified)
            if not df.empty and df['pnl'].std() > 0:
                sharpe_ratio = (df['pnl'].mean() * 252) / (df['pnl'].std() * (252 ** 0.5))
            else:
                sharpe_ratio = 0
            
            # Maximum drawdown
            cumulative_pnl = df['pnl'].cumsum()
            rolling_max = cumulative_pnl.expanding().max()
            drawdown = cumulative_pnl - rolling_max
            max_drawdown = drawdown.min()
            
            return PerformanceMetrics(
                date=datetime.now().strftime('%Y-%m-%d'),
                total_trades=total_trades,
                winning_trades=winning_trades,
                losing_trades=losing_trades,
                win_rate=win_rate,
                total_pnl=total_pnl,
                max_profit=max_profit,
                max_loss=max_loss,
                avg_profit=avg_profit,
                avg_loss=avg_loss,
                profit_factor=profit_factor,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                portfolio_value=0.0  # Would need to be passed from account
            )
            
        except Exception as e:
            self.logger.error(f"Failed to calculate performance metrics: {e}")
            return None
    
    def get_symbol_rankings(self) -> List[SymbolPerformance]:
        """Get symbols ranked by performance"""
        try:
            rankings = []
            
            for symbol, perf_data in self.symbol_performance.items():
                if perf_data['total_trades'] < 2:  # Need minimum trades
                    continue
                
                win_rate = perf_data['winning_trades'] / perf_data['total_trades']
                avg_hold_time = sum(perf_data['hold_times']) / len(perf_data['hold_times'])
                best_trade = max(perf_data['pnl_history'])
                worst_trade = min(perf_data['pnl_history'])
                
                symbol_perf = SymbolPerformance(
                    symbol=symbol,
                    total_trades=perf_data['total_trades'],
                    winning_trades=perf_data['winning_trades'],
                    win_rate=win_rate,
                    total_pnl=perf_data['total_pnl'],
                    avg_hold_time=avg_hold_time,
                    best_trade=best_trade,
                    worst_trade=worst_trade,
                    success_score=perf_data.get('success_score', 0.5)
                )
                
                rankings.append(symbol_perf)
            
            # Sort by success score
            return sorted(rankings, key=lambda x: x.success_score, reverse=True)
            
        except Exception as e:
            self.logger.error(f"Failed to get symbol rankings: {e}")
            return []
    
    def load_trade_history(self) -> pd.DataFrame:
        """Load trade history from CSV"""
        try:
            if os.path.exists(self.log_paths['trade_log']):
                return pd.read_csv(self.log_paths['trade_log'])
            else:
                return pd.DataFrame()
                
        except Exception as e:
            self.logger.error(f"Failed to load trade history: {e}")
            return pd.DataFrame()
    
    def load_performance_data(self):
        """Load existing performance data into memory"""
        try:
            df = self.load_trade_history()
            if not df.empty:
                # Rebuild symbol performance from trade history
                for _, row in df.iterrows():
                    trade_log = TradeLog(**row.to_dict())
                    self.update_symbol_performance(trade_log)
                    
        except Exception as e:
            self.logger.error(f"Failed to load performance data: {e}")
    
    def save_daily_performance(self, portfolio_value: float):
        """Save daily performance summary"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            metrics = self.calculate_performance_metrics(start_date=today, end_date=today)
            
            if metrics:
                metrics.portfolio_value = portfolio_value
                
                # Write to performance log
                with open(self.log_paths['performance_log'], 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(list(asdict(metrics).values()))
                
        except Exception as e:
            self.logger.error(f"Failed to save daily performance: {e}")
    
    def get_strategy_effectiveness(self) -> Dict[str, float]:
        """Analyze effectiveness of different strategy signals"""
        try:
            df = self.load_trade_history()
            if df.empty:
                return {}
            
            # Group by strategy signals and calculate success rate
            strategy_performance = {}
            
            for _, row in df.iterrows():
                signals = row.get('strategy_signals', 'UNKNOWN')
                if signals not in strategy_performance:
                    strategy_performance[signals] = {'wins': 0, 'total': 0, 'pnl': 0}
                
                strategy_performance[signals]['total'] += 1
                strategy_performance[signals]['pnl'] += row['pnl']
                
                if row['pnl'] > 0:
                    strategy_performance[signals]['wins'] += 1
            
            # Calculate win rates
            effectiveness = {}
            for signal, data in strategy_performance.items():
                win_rate = data['wins'] / data['total'] if data['total'] > 0 else 0
                avg_pnl = data['pnl'] / data['total'] if data['total'] > 0 else 0
                effectiveness[signal] = {
                    'win_rate': win_rate,
                    'avg_pnl': avg_pnl,
                    'total_trades': data['total'],
                    'effectiveness_score': win_rate * 0.7 + min(avg_pnl / 50, 0.3)
                }
            
            return effectiveness
            
        except Exception as e:
            self.logger.error(f"Failed to analyze strategy effectiveness: {e}")
            return {}
    
    def get_risk_analysis(self) -> Dict:
        """Analyze risk patterns in trading history"""
        try:
            df = self.load_trade_history()
            if df.empty:
                return {}
            
            # Risk metrics
            risk_analysis = {}
            
            # Drawdown analysis
            cumulative_pnl = df['pnl'].cumsum()
            rolling_max = cumulative_pnl.expanding().max()
            drawdowns = cumulative_pnl - rolling_max
            
            risk_analysis['max_drawdown'] = drawdowns.min()
            risk_analysis['avg_drawdown'] = drawdowns[drawdowns < 0].mean() if any(drawdowns < 0) else 0
            risk_analysis['drawdown_periods'] = len(drawdowns[drawdowns < 0])
            
            # Loss streaks
            loss_streak = 0
            max_loss_streak = 0
            current_streak = 0
            
            for pnl in df['pnl']:
                if pnl < 0:
                    current_streak += 1
                    max_loss_streak = max(max_loss_streak, current_streak)
                else:
                    current_streak = 0
            
            risk_analysis['max_loss_streak'] = max_loss_streak
            
            # Risk-adjusted returns
            if df['pnl'].std() > 0:
                risk_analysis['sharpe_ratio'] = df['pnl'].mean() / df['pnl'].std()
            else:
                risk_analysis['sharpe_ratio'] = 0
            
            # Large loss analysis
            large_losses = df[df['pnl'] < -100]  # Losses > $100
            risk_analysis['large_loss_count'] = len(large_losses)
            risk_analysis['large_loss_percent'] = len(large_losses) / len(df) * 100
            
            return risk_analysis
            
        except Exception as e:
            self.logger.error(f"Failed to perform risk analysis: {e}")
            return {}
    
    def generate_performance_report(self) -> Dict:
        """Generate comprehensive performance report"""
        try:
            metrics = self.calculate_performance_metrics()
            symbol_rankings = self.get_symbol_rankings()
            strategy_effectiveness = self.get_strategy_effectiveness()
            risk_analysis = self.get_risk_analysis()
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'overall_performance': asdict(metrics) if metrics else {},
                'top_symbols': [asdict(s) for s in symbol_rankings[:10]],
                'worst_symbols': [asdict(s) for s in symbol_rankings[-5:]],
                'strategy_effectiveness': strategy_effectiveness,
                'risk_analysis': risk_analysis,
                'recommendations': self.generate_recommendations()
            }
            
            # Save report to file
            report_path = os.path.join(
                os.path.dirname(self.log_paths['trade_log']), 
                f"performance_report_{datetime.now().strftime('%Y%m%d')}.json"
            )
            
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to generate performance report: {e}")
            return {}
    
    def generate_recommendations(self) -> List[str]:
        """Generate trading recommendations based on performance analysis"""
        try:
            recommendations = []
            
            # Analyze recent performance
            df = self.load_trade_history()
            if df.empty:
                return ["Insufficient trade history for recommendations"]
            
            recent_trades = df.tail(20) if len(df) >= 20 else df
            recent_win_rate = len(recent_trades[recent_trades['pnl'] > 0]) / len(recent_trades)
            
            # Win rate recommendations
            if recent_win_rate < 0.4:
                recommendations.append("Consider tightening entry criteria - recent win rate is low")
            elif recent_win_rate > 0.7:
                recommendations.append("Current strategy performing well - maintain approach")
            
            # Risk recommendations
            large_losses = recent_trades[recent_trades['pnl'] < -100]
            if len(large_losses) > 0:
                recommendations.append("Review risk management - recent large losses detected")
            
            # Symbol-specific recommendations
            symbol_rankings = self.get_symbol_rankings()
            if symbol_rankings:
                top_performers = [s.symbol for s in symbol_rankings[:3]]
                poor_performers = [s.symbol for s in symbol_rankings[-3:]]
                
                recommendations.append(f"Focus on top performers: {', '.join(top_performers)}")
                recommendations.append(f"Avoid or reduce exposure to: {', '.join(poor_performers)}")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Failed to generate recommendations: {e}")
            return ["Error generating recommendations"]