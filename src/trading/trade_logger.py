"""
Trade Lifecycle Logging Module
Handles complete trade tracking from entry to exit with SQLite database
"""

import sqlite3
import pandas as pd
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import json
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class TradeEntry:
    """Trade entry record"""
    trade_id: str
    symbol: str
    trade_type: str  # 'buy', 'sell', 'call_option', 'put_option'
    entry_price: float
    entry_time: datetime
    quantity: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    confidence_score: Optional[float] = None
    technical_indicators: Optional[Dict] = None
    sentiment_score: Optional[float] = None
    strategy: Optional[str] = None
    notes: Optional[str] = None

@dataclass
class TradeExit:
    """Trade exit record"""
    trade_id: str
    exit_price: float
    exit_time: datetime
    exit_reason: str  # 'stop_loss', 'take_profit', 'manual', 'time_exit', 'strategy_exit'
    profit_loss: float
    profit_loss_pct: float
    holding_period: timedelta
    notes: Optional[str] = None

@dataclass
class TradeUpdate:
    """Trade update/monitoring record"""
    trade_id: str
    update_time: datetime
    current_price: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    technical_update: Optional[Dict] = None
    notes: Optional[str] = None

class TradeLogger:
    """
    TRADE LIFECYCLE LOGGING SYSTEM - MODIFY FOR DIFFERENT STORAGE BACKENDS
    
    This module provides complete trade tracking:
    - Entry logging with all relevant data
    - Real-time trade updates and monitoring
    - Exit logging with P&L calculation
    - Performance analytics and reporting
    - SQLite database for persistence
    
    CUSTOMIZE: Add new fields, modify analytics, integrate with different databases
    """
    
    def __init__(self, db_path: str = "data/trades.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
    def _init_database(self):
        """
        Initialize SQLite database with trade tables
        
        DATABASE SCHEMA - MODIFY TO ADD NEW FIELDS:
        - trades: Main trade records
        - trade_updates: Real-time monitoring data  
        - trade_performance: Aggregated performance metrics
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Main trades table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    trade_id TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    trade_type TEXT NOT NULL,
                    entry_price REAL NOT NULL,
                    entry_time TEXT NOT NULL,
                    exit_price REAL,
                    exit_time TEXT,
                    exit_reason TEXT,
                    quantity REAL NOT NULL,
                    stop_loss REAL,
                    take_profit REAL,
                    profit_loss REAL,
                    profit_loss_pct REAL,
                    holding_period TEXT,
                    confidence_score REAL,
                    technical_indicators TEXT,
                    sentiment_score REAL,
                    strategy TEXT,
                    status TEXT DEFAULT 'open',
                    notes TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Trade updates table for monitoring
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trade_updates (
                    update_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trade_id TEXT NOT NULL,
                    update_time TEXT NOT NULL,
                    current_price REAL NOT NULL,
                    unrealized_pnl REAL,
                    unrealized_pnl_pct REAL,
                    technical_update TEXT,
                    notes TEXT,
                    FOREIGN KEY (trade_id) REFERENCES trades (trade_id)
                )
            ''')
            
            # Performance tracking table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    date TEXT PRIMARY KEY,
                    total_trades INTEGER,
                    winning_trades INTEGER,
                    losing_trades INTEGER,
                    win_rate REAL,
                    avg_profit REAL,
                    avg_loss REAL,
                    profit_factor REAL,
                    total_pnl REAL,
                    best_trade REAL,
                    worst_trade REAL,
                    avg_holding_period REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            logger.info(f"Initialized trade database at {self.db_path}")
    
    def log_trade_entry(self, trade_entry: TradeEntry) -> bool:
        """
        Log a new trade entry
        
        TRADE ENTRY LOGGING - CAPTURE ALL RELEVANT DATA:
        - Technical indicators at entry
        - Sentiment scores
        - Confidence levels
        - Strategy context
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Serialize complex data
                technical_json = json.dumps(trade_entry.technical_indicators) if trade_entry.technical_indicators else None
                
                cursor.execute('''
                    INSERT INTO trades (
                        trade_id, symbol, trade_type, entry_price, entry_time, quantity,
                        stop_loss, take_profit, confidence_score, technical_indicators,
                        sentiment_score, strategy, notes, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    trade_entry.trade_id,
                    trade_entry.symbol,
                    trade_entry.trade_type,
                    trade_entry.entry_price,
                    trade_entry.entry_time.isoformat(),
                    trade_entry.quantity,
                    trade_entry.stop_loss,
                    trade_entry.take_profit,
                    trade_entry.confidence_score,
                    technical_json,
                    trade_entry.sentiment_score,
                    trade_entry.strategy,
                    trade_entry.notes,
                    'open'
                ))
                
                conn.commit()
                logger.info(f"Logged trade entry: {trade_entry.trade_id} - {trade_entry.symbol}")
                return True
                
        except Exception as e:
            logger.error(f"Error logging trade entry {trade_entry.trade_id}: {e}")
            return False
    
    def log_trade_update(self, trade_update: TradeUpdate) -> bool:
        """
        Log trade monitoring update
        
        TRADE MONITORING - TRACK REAL-TIME PROGRESS:
        - Current price and P&L
        - Technical indicator updates
        - Risk management alerts
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Serialize technical update data
                technical_json = json.dumps(trade_update.technical_update) if trade_update.technical_update else None
                
                cursor.execute('''
                    INSERT INTO trade_updates (
                        trade_id, update_time, current_price, unrealized_pnl,
                        unrealized_pnl_pct, technical_update, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    trade_update.trade_id,
                    trade_update.update_time.isoformat(),
                    trade_update.current_price,
                    trade_update.unrealized_pnl,
                    trade_update.unrealized_pnl_pct,
                    technical_json,
                    trade_update.notes
                ))
                
                conn.commit()
                logger.debug(f"Logged trade update: {trade_update.trade_id} - P&L: {trade_update.unrealized_pnl:.2f}")
                return True
                
        except Exception as e:
            logger.error(f"Error logging trade update {trade_update.trade_id}: {e}")
            return False
    
    def log_trade_exit(self, trade_exit: TradeExit) -> bool:
        """
        Log trade exit and close position
        
        TRADE EXIT LOGGING - CAPTURE FINAL RESULTS:
        - Exit price and reason
        - Final P&L calculation
        - Holding period analysis
        - Performance attribution
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE trades SET
                        exit_price = ?,
                        exit_time = ?,
                        exit_reason = ?,
                        profit_loss = ?,
                        profit_loss_pct = ?,
                        holding_period = ?,
                        status = 'closed',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE trade_id = ?
                ''', (
                    trade_exit.exit_price,
                    trade_exit.exit_time.isoformat(),
                    trade_exit.exit_reason,
                    trade_exit.profit_loss,
                    trade_exit.profit_loss_pct,
                    str(trade_exit.holding_period),
                    trade_exit.trade_id
                ))
                
                conn.commit()
                logger.info(f"Logged trade exit: {trade_exit.trade_id} - P&L: {trade_exit.profit_loss:.2f} ({trade_exit.profit_loss_pct:.1f}%)")
                
                # Update performance metrics
                self._update_performance_metrics()
                
                return True
                
        except Exception as e:
            logger.error(f"Error logging trade exit {trade_exit.trade_id}: {e}")
            return False
    
    def get_open_trades(self) -> List[Dict[str, Any]]:
        """
        Get all currently open trades
        
        OPEN TRADES QUERY - FOR MONITORING ACTIVE POSITIONS:
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM trades WHERE status = 'open'
                    ORDER BY entry_time DESC
                ''')
                
                columns = [description[0] for description in cursor.description]
                trades = []
                
                for row in cursor.fetchall():
                    trade_dict = dict(zip(columns, row))
                    # Parse JSON fields
                    if trade_dict['technical_indicators']:
                        trade_dict['technical_indicators'] = json.loads(trade_dict['technical_indicators'])
                    trades.append(trade_dict)
                
                return trades
                
        except Exception as e:
            logger.error(f"Error getting open trades: {e}")
            return []
    
    def get_trade_history(self, 
                         symbol: Optional[str] = None,
                         days: int = 30,
                         limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get trade history with optional filtering
        
        TRADE HISTORY QUERY - FOR ANALYSIS AND REPORTING:
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Build query with filters
                query = '''
                    SELECT * FROM trades WHERE entry_time >= ?
                '''
                params = [datetime.now() - timedelta(days=days)]
                
                if symbol:
                    query += ' AND symbol = ?'
                    params.append(symbol)
                
                query += ' ORDER BY entry_time DESC'
                
                if limit:
                    query += ' LIMIT ?'
                    params.append(limit)
                
                cursor.execute(query, params)
                
                columns = [description[0] for description in cursor.description]
                trades = []
                
                for row in cursor.fetchall():
                    trade_dict = dict(zip(columns, row))
                    # Parse JSON fields
                    if trade_dict['technical_indicators']:
                        trade_dict['technical_indicators'] = json.loads(trade_dict['technical_indicators'])
                    trades.append(trade_dict)
                
                return trades
                
        except Exception as e:
            logger.error(f"Error getting trade history: {e}")
            return []
    
    def get_performance_summary(self, days: int = 30) -> Dict[str, Any]:
        """
        Get comprehensive performance summary
        
        PERFORMANCE ANALYTICS - KEY TRADING METRICS:
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get trades from specified period
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_trades,
                        SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as winning_trades,
                        SUM(CASE WHEN profit_loss < 0 THEN 1 ELSE 0 END) as losing_trades,
                        AVG(CASE WHEN profit_loss > 0 THEN profit_loss ELSE NULL END) as avg_profit,
                        AVG(CASE WHEN profit_loss < 0 THEN profit_loss ELSE NULL END) as avg_loss,
                        SUM(profit_loss) as total_pnl,
                        MAX(profit_loss) as best_trade,
                        MIN(profit_loss) as worst_trade,
                        AVG(profit_loss_pct) as avg_return_pct
                    FROM trades 
                    WHERE entry_time >= ? AND status = 'closed'
                ''', [datetime.now() - timedelta(days=days)])
                
                row = cursor.fetchone()
                
                if row and row[0] > 0:  # If we have trades
                    total_trades, winning_trades, losing_trades, avg_profit, avg_loss, total_pnl, best_trade, worst_trade, avg_return_pct = row
                    
                    # Calculate derived metrics
                    win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
                    profit_factor = abs(avg_profit * winning_trades / (avg_loss * losing_trades)) if avg_loss and losing_trades else 0
                    
                    return {
                        'period_days': days,
                        'total_trades': total_trades,
                        'winning_trades': winning_trades,
                        'losing_trades': losing_trades,
                        'win_rate': win_rate,
                        'avg_profit': avg_profit or 0,
                        'avg_loss': avg_loss or 0,
                        'total_pnl': total_pnl or 0,
                        'best_trade': best_trade or 0,
                        'worst_trade': worst_trade or 0,
                        'avg_return_pct': avg_return_pct or 0,
                        'profit_factor': profit_factor,
                        'expectancy': ((win_rate / 100) * (avg_profit or 0)) + (((100 - win_rate) / 100) * (avg_loss or 0))
                    }
                else:
                    return {
                        'period_days': days,
                        'total_trades': 0,
                        'message': 'No closed trades in the specified period'
                    }
                    
        except Exception as e:
            logger.error(f"Error getting performance summary: {e}")
            return {'error': str(e)}
    
    def get_symbol_performance(self, symbol: str, days: int = 90) -> Dict[str, Any]:
        """
        Get performance metrics for a specific symbol
        
        SYMBOL-SPECIFIC ANALYTICS:
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_trades,
                        SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as winning_trades,
                        SUM(profit_loss) as total_pnl,
                        AVG(profit_loss_pct) as avg_return_pct,
                        MAX(profit_loss) as best_trade,
                        MIN(profit_loss) as worst_trade
                    FROM trades 
                    WHERE symbol = ? AND entry_time >= ? AND status = 'closed'
                ''', [symbol, datetime.now() - timedelta(days=days)])
                
                row = cursor.fetchone()
                
                if row and row[0] > 0:
                    total_trades, winning_trades, total_pnl, avg_return_pct, best_trade, worst_trade = row
                    win_rate = (winning_trades / total_trades) * 100
                    
                    return {
                        'symbol': symbol,
                        'total_trades': total_trades,
                        'win_rate': win_rate,
                        'total_pnl': total_pnl,
                        'avg_return_pct': avg_return_pct,
                        'best_trade': best_trade,
                        'worst_trade': worst_trade
                    }
                else:
                    return {'symbol': symbol, 'message': 'No trades found for this symbol'}
                    
        except Exception as e:
            logger.error(f"Error getting symbol performance for {symbol}: {e}")
            return {'error': str(e)}
    
    def _update_performance_metrics(self):
        """Update daily performance metrics table"""
        try:
            today = datetime.now().date().isoformat()
            performance = self.get_performance_summary(days=1)
            
            if performance.get('total_trades', 0) > 0:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO performance_metrics (
                            date, total_trades, winning_trades, losing_trades,
                            win_rate, avg_profit, avg_loss, profit_factor,
                            total_pnl, best_trade, worst_trade
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        today,
                        performance['total_trades'],
                        performance['winning_trades'],
                        performance['losing_trades'],
                        performance['win_rate'],
                        performance['avg_profit'],
                        performance['avg_loss'],
                        performance['profit_factor'],
                        performance['total_pnl'],
                        performance['best_trade'],
                        performance['worst_trade']
                    ))
                    
                    conn.commit()
                    
        except Exception as e:
            logger.error(f"Error updating performance metrics: {e}")
    
    def export_trades_to_csv(self, filename: Optional[str] = None, days: int = 30) -> str:
        """
        Export trade history to CSV file
        
        TRADE DATA EXPORT - FOR EXTERNAL ANALYSIS:
        """
        try:
            if not filename:
                filename = f"trades_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            trades = self.get_trade_history(days=days)
            
            if trades:
                df = pd.DataFrame(trades)
                # Remove JSON columns that don't export well
                if 'technical_indicators' in df.columns:
                    df = df.drop('technical_indicators', axis=1)
                
                export_path = Path("exports") / filename
                export_path.parent.mkdir(exist_ok=True)
                
                df.to_csv(export_path, index=False)
                logger.info(f"Exported {len(trades)} trades to {export_path}")
                return str(export_path)
            else:
                logger.warning("No trades to export")
                return ""
                
        except Exception as e:
            logger.error(f"Error exporting trades to CSV: {e}")
            return ""
    
    def cleanup_old_updates(self, days_to_keep: int = 90):
        """
        Clean up old trade update records to manage database size
        
        DATABASE MAINTENANCE:
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cutoff_date = datetime.now() - timedelta(days=days_to_keep)
                
                cursor.execute('''
                    DELETE FROM trade_updates 
                    WHERE update_time < ?
                ''', [cutoff_date.isoformat()])
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                if deleted_count > 0:
                    logger.info(f"Cleaned up {deleted_count} old trade update records")
                    
        except Exception as e:
            logger.error(f"Error cleaning up old trade updates: {e}")