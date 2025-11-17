#!/usr/bin/env python3
"""
Trading Bot Dashboard
Simple Flask web interface for monitoring bot performance and configuration.
"""

import sys
import os
import json
from flask import Flask, render_template, jsonify, request, redirect, url_for
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config_manager import get_config
from api.alpaca_client import AlpacaClient
from utils.logger import TradingLogger

app = Flask(__name__)
app.secret_key = 'trading-bot-dashboard-key'  # Change in production

# Global objects
config_manager = None
alpaca_client = None
trading_logger = None

def initialize_components():
    """Initialize bot components"""
    global config_manager, alpaca_client, trading_logger
    try:
        config_manager = get_config()
        alpaca_client = AlpacaClient(config_manager)
        trading_logger = TradingLogger(config_manager)
        return True
    except Exception as e:
        print(f"Failed to initialize components: {e}")
        return False

@app.route('/')
def dashboard():
    """Main dashboard"""
    try:
        # Get account information
        account = alpaca_client.get_account()
        positions = alpaca_client.get_positions()
        
        # Get recent orders
        orders = alpaca_client.get_orders(status="all", limit=10)
        
        # Calculate portfolio metrics
        portfolio_data = {
            'value': account.portfolio_value,
            'buying_power': account.buying_power,
            'cash': account.cash,
            'equity': account.equity,
            'day_trading_power': account.day_trading_buying_power,
            'status': account.status
        }
        
        # Position summary
        position_data = []
        total_unrealized_pl = 0
        
        for pos in positions:
            position_data.append({
                'symbol': pos.symbol,
                'qty': pos.qty,
                'market_value': pos.market_value,
                'unrealized_pl': pos.unrealized_pl,
                'unrealized_plpc': pos.unrealized_plpc * 100,
                'avg_entry_price': pos.avg_entry_price
            })
            total_unrealized_pl += pos.unrealized_pl
        
        # Recent orders
        order_data = []
        for order in orders:
            order_data.append({
                'symbol': order.symbol,
                'side': order.side,
                'qty': order.qty,
                'status': order.status,
                'order_type': order.order_type,
                'created_at': order.created_at.strftime('%Y-%m-%d %H:%M:%S') if order.created_at else 'N/A'
            })
        
        # Performance metrics
        performance = trading_logger.calculate_performance_metrics()
        perf_data = {}
        if performance:
            perf_data = {
                'total_trades': performance.total_trades,
                'win_rate': performance.win_rate * 100,
                'total_pnl': performance.total_pnl,
                'avg_profit': performance.avg_profit,
                'avg_loss': performance.avg_loss,
                'profit_factor': performance.profit_factor,
                'sharpe_ratio': performance.sharpe_ratio,
                'max_drawdown': performance.max_drawdown
            }
        
        return render_template('dashboard.html',
                             portfolio=portfolio_data,
                             positions=position_data,
                             orders=order_data,
                             performance=perf_data,
                             total_unrealized_pl=total_unrealized_pl)
        
    except Exception as e:
        return f"Error loading dashboard: {e}", 500

@app.route('/api/account')
def api_account():
    """API endpoint for account data"""
    try:
        account = alpaca_client.get_account()
        return jsonify({
            'portfolio_value': float(account.portfolio_value),
            'buying_power': float(account.buying_power),
            'cash': float(account.cash),
            'equity': float(account.equity),
            'status': account.status
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/positions')
def api_positions():
    """API endpoint for positions data"""
    try:
        positions = alpaca_client.get_positions()
        position_data = []
        
        for pos in positions:
            position_data.append({
                'symbol': pos.symbol,
                'qty': float(pos.qty),
                'market_value': float(pos.market_value),
                'unrealized_pl': float(pos.unrealized_pl),
                'unrealized_plpc': float(pos.unrealized_plpc) * 100,
                'avg_entry_price': float(pos.avg_entry_price),
                'side': pos.side
            })
        
        return jsonify(position_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/performance')
def api_performance():
    """API endpoint for performance metrics"""
    try:
        performance = trading_logger.calculate_performance_metrics()
        
        if not performance:
            return jsonify({'error': 'No performance data available'})
        
        return jsonify({
            'total_trades': performance.total_trades,
            'winning_trades': performance.winning_trades,
            'losing_trades': performance.losing_trades,
            'win_rate': performance.win_rate,
            'total_pnl': performance.total_pnl,
            'max_profit': performance.max_profit,
            'max_loss': performance.max_loss,
            'avg_profit': performance.avg_profit,
            'avg_loss': performance.avg_loss,
            'profit_factor': performance.profit_factor,
            'sharpe_ratio': performance.sharpe_ratio,
            'max_drawdown': performance.max_drawdown
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/symbol_rankings')
def api_symbol_rankings():
    """API endpoint for symbol performance rankings"""
    try:
        rankings = trading_logger.get_symbol_rankings()
        
        ranking_data = []
        for rank in rankings[:20]:  # Top 20
            ranking_data.append({
                'symbol': rank.symbol,
                'total_trades': rank.total_trades,
                'win_rate': rank.win_rate,
                'total_pnl': rank.total_pnl,
                'success_score': rank.success_score
            })
        
        return jsonify(ranking_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/config')
def config_page():
    """Configuration management page"""
    try:
        config = config_manager.config
        return render_template('config.html', config=config)
    except Exception as e:
        return f"Error loading config: {e}", 500

@app.route('/api/config', methods=['GET', 'POST'])
def api_config():
    """API endpoint for configuration management"""
    if request.method == 'GET':
        try:
            return jsonify(config_manager.config)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            # Update specific configuration parameters
            if 'section' in data and 'param' in data and 'value' in data:
                success = config_manager.update_trading_param(
                    data['section'], data['param'], data['value']
                )
                
                if success:
                    config_manager.save_config()
                    return jsonify({'success': True, 'message': 'Configuration updated'})
                else:
                    return jsonify({'error': 'Failed to update configuration'}), 400
            
            return jsonify({'error': 'Invalid request format'}), 400
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/trades')
def trades_page():
    """Trade history page"""
    try:
        # Load trade history
        df = trading_logger.load_trade_history()
        
        if df.empty:
            trades = []
        else:
            # Convert to list of dictionaries for template
            trades = df.tail(50).to_dict('records')  # Last 50 trades
            
            # Format timestamps
            for trade in trades:
                if 'timestamp' in trade:
                    try:
                        dt = datetime.fromisoformat(trade['timestamp'])
                        trade['timestamp'] = dt.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        pass
        
        return render_template('trades.html', trades=trades)
        
    except Exception as e:
        return f"Error loading trades: {e}", 500

@app.route('/api/market_status')
def api_market_status():
    """API endpoint for market status"""
    try:
        is_open = alpaca_client.is_market_open()
        calendar = alpaca_client.get_market_calendar()
        
        next_open = None
        next_close = None
        
        if calendar:
            today = datetime.now().date()
            for day in calendar:
                if day['date'] >= today:
                    if not is_open:
                        next_open = f"{day['date']} {day['open']}"
                    next_close = f"{day['date']} {day['close']}"
                    break
        
        return jsonify({
            'is_open': is_open,
            'next_open': next_open,
            'next_close': next_close,
            'current_time': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    if not initialize_components():
        print("Failed to initialize dashboard components")
        sys.exit(1)
    
    print("🚀 Starting Trading Bot Dashboard")
    print("📊 Dashboard will be available at: http://localhost:5000")
    
    app.run(host='0.0.0.0', port=5001, debug=False)
