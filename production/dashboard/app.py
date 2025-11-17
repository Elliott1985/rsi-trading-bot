#!/usr/bin/env python3
"""
Enhanced Trading Bot Dashboard Server
Real-time dashboard with bot control and monitoring capabilities
"""

import sys
import os
import json
import time
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, send_from_directory
import logging
from typing import Dict, Any

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import bot modules
from utils.config_manager import get_config, ConfigManager
from utils.logger import TradingLogger
from api.alpaca_client import AlpacaClient

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Global variables
config_manager = None
trading_logger = None
alpaca_client = None

def initialize_components():
    """Initialize dashboard components"""
    global config_manager, trading_logger, alpaca_client
    
    try:
        config_manager = get_config()
        trading_logger = TradingLogger(config_manager)
        alpaca_client = AlpacaClient(config_manager)
        
        logging.info("Dashboard components initialized successfully")
        
    except Exception as e:
        logging.error(f"Failed to initialize dashboard components: {e}")
        config_manager = None
        trading_logger = None
        alpaca_client = None

def load_bot_status() -> Dict[str, Any]:
    """Load bot status from status file"""
    try:
        status_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'bot_status.json')
        
        if not os.path.exists(status_file):
            return {
                'status': {
                    'enabled': False,
                    'running': False,
                    'last_scan': None,
                    'active_trades': 0,
                    'daily_pnl': 0.0,
                    'scan_count': 0,
                    'error_count': 0
                },
                'active_trades': {},
                'daily_stats': {
                    'trades_executed': 0,
                    'profit_loss': 0.0,
                    'start_portfolio_value': 0.0
                },
                'timestamp': datetime.now().isoformat()
            }
        
        with open(status_file, 'r') as f:
            data = json.load(f)
            
        # Check if data is recent (within last 2 minutes)
        if 'timestamp' in data:
            timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
            if datetime.now() - timestamp.replace(tzinfo=None) > timedelta(minutes=2):
                # Mark as potentially stopped if data is old
                if 'status' in data:
                    data['status']['running'] = False
        
        return data
        
    except Exception as e:
        logging.error(f"Error loading bot status: {e}")
        return {
            'status': {'enabled': False, 'running': False, 'error': str(e)},
            'active_trades': {},
            'daily_stats': {},
            'timestamp': datetime.now().isoformat()
        }

def save_bot_control(settings: Dict[str, Any]) -> bool:
    """Save bot control settings to config"""
    try:
        if not config_manager:
            return False
            
        # Update bot control settings
        config_manager.config['bot_control'] = config_manager.config.get('bot_control', {})
        config_manager.config['bot_control'].update(settings)
        
        # Save to file
        config_file = os.path.join(os.path.dirname(__file__), '..', 'config.json')
        with open(config_file, 'w') as f:
            json.dump(config_manager.config, f, indent=2)
        
        return True
        
    except Exception as e:
        logging.error(f"Error saving bot control settings: {e}")
        return False

# Routes
@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/trade-history')
def trade_history():
    """Trade history page"""
    return render_template('trade_history.html')

@app.route('/config')
def config_page():
    """Configuration page"""
    return render_template('config.html')

@app.route('/analytics')
def analytics():
    """Analytics page"""
    return render_template('analytics.html')

# API Routes
@app.route('/api/status')
def api_status():
    """Get current bot status"""
    try:
        bot_data = load_bot_status()
        
        # Add real-time account data if available
        if alpaca_client:
            try:
                account = alpaca_client.get_account()
                bot_data['account'] = {
                    'portfolio_value': float(account.portfolio_value),
                    'buying_power': float(account.buying_power),
                    'cash': float(account.cash)
                }
                
                # Update portfolio value in daily stats if not set
                if bot_data['daily_stats'].get('start_portfolio_value', 0) == 0:
                    bot_data['daily_stats']['start_portfolio_value'] = float(account.portfolio_value)
                    
            except Exception as e:
                logging.warning(f"Could not fetch account data: {e}")
        
        return jsonify({
            'success': True,
            'data': bot_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logging.error(f"Error in /api/status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/toggle-bot', methods=['POST'])
def api_toggle_bot():
    """Toggle bot enable/disable"""
    try:
        data = request.get_json()
        enabled = data.get('enabled', False)
        
        # Save bot control setting
        success = save_bot_control({'enabled': enabled})
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Bot {"enabled" if enabled else "disabled"}',
                'enabled': enabled
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to update bot settings'
            }), 500
            
    except Exception as e:
        logging.error(f"Error in /api/toggle-bot: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/update-settings', methods=['POST'])
def api_update_settings():
    """Update bot settings"""
    try:
        data = request.get_json()
        
        # Validate settings
        settings = {}
        if 'scan_interval_seconds' in data:
            interval = int(data['scan_interval_seconds'])
            if 10 <= interval <= 300:
                settings['scan_interval_seconds'] = interval
            else:
                return jsonify({
                    'success': False,
                    'error': 'Scan interval must be between 10-300 seconds'
                }), 400
        
        if 'max_positions' in data:
            max_pos = int(data['max_positions'])
            if 1 <= max_pos <= 10:
                # Update trading config if available
                if config_manager and hasattr(config_manager, 'trading_config'):
                    config_manager.trading_config.max_positions = max_pos
                settings['max_positions'] = max_pos
            else:
                return jsonify({
                    'success': False,
                    'error': 'Max positions must be between 1-10'
                }), 400
        
        # Save settings
        success = save_bot_control(settings)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Settings updated successfully',
                'settings': settings
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to save settings'
            }), 500
            
    except Exception as e:
        logging.error(f"Error in /api/update-settings: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/trades')
def api_trades():
    """Get trade history"""
    try:
        if not trading_logger:
            return jsonify({
                'success': False,
                'error': 'Trading logger not available'
            }), 500
        
        # Get recent trades
        trades = trading_logger.get_recent_trades(limit=50)
        
        return jsonify({
            'success': True,
            'data': trades,
            'count': len(trades)
        })
        
    except Exception as e:
        logging.error(f"Error in /api/trades: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/positions')
def api_positions():
    """Get current positions from Alpaca"""
    try:
        if not alpaca_client:
            return jsonify({
                'success': False,
                'error': 'Alpaca client not available'
            }), 500
        
        positions = alpaca_client.get_positions()
        position_data = []
        
        for position in positions:
            position_data.append({
                'symbol': position.symbol,
                'quantity': float(position.qty),
                'side': 'long' if float(position.qty) > 0 else 'short',
                'market_value': float(position.market_value),
                'avg_entry_price': float(position.avg_entry_price),
                'unrealized_pl': float(position.unrealized_pl),
                'unrealized_plpc': float(position.unrealized_plpc) * 100,
                'current_price': float(position.current_price) if position.current_price else 0
            })
        
        return jsonify({
            'success': True,
            'data': position_data,
            'count': len(position_data)
        })
        
    except Exception as e:
        logging.error(f"Error in /api/positions: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/performance')
def api_performance():
    """Get performance metrics"""
    try:
        if not trading_logger:
            return jsonify({
                'success': False,
                'error': 'Trading logger not available'
            }), 500
        
        # Generate performance report
        performance = trading_logger.generate_performance_report()
        
        return jsonify({
            'success': True,
            'data': performance
        })
        
    except Exception as e:
        logging.error(f"Error in /api/performance: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/config')
def api_config():
    """Get current configuration"""
    try:
        if not config_manager:
            return jsonify({
                'success': False,
                'error': 'Configuration manager not available'
            }), 500
        
        # Get sanitized config (remove sensitive data)
        config_data = config_manager.config.copy()
        
        # Remove sensitive keys
        sensitive_keys = ['alpaca_key', 'alpaca_secret', 'twilio_auth_token', 'news_api_key']
        for key in sensitive_keys:
            if key in config_data:
                config_data[key] = '***HIDDEN***'
        
        return jsonify({
            'success': True,
            'data': config_data
        })
        
    except Exception as e:
        logging.error(f"Error in /api/config: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/logs')
def api_logs():
    """Get recent system logs"""
    try:
        log_file = os.path.join(os.path.dirname(__file__), '..', 'enhanced_bot.log')
        
        if not os.path.exists(log_file):
            return jsonify({
                'success': True,
                'data': ['No logs available yet'],
                'count': 0
            })
        
        # Read last 50 lines
        with open(log_file, 'r') as f:
            lines = f.readlines()
            recent_lines = lines[-50:] if len(lines) > 50 else lines
        
        # Clean up lines
        logs = [line.strip() for line in recent_lines if line.strip()]
        
        return jsonify({
            'success': True,
            'data': logs,
            'count': len(logs)
        })
        
    except Exception as e:
        logging.error(f"Error in /api/logs: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

def create_app():
    """Factory function to create Flask app"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize components
    initialize_components()
    
    return app

def main():
    """Main entry point for dashboard server"""
    app = create_app()
    
    print("🚀 Starting Enhanced Trading Bot Dashboard")
    print("📊 Dashboard available at: http://localhost:5001")
    print("🔧 API endpoints:")
    print("   - GET  /api/status        - Bot status")
    print("   - POST /api/toggle-bot    - Enable/disable bot")
    print("   - POST /api/update-settings - Update bot settings")
    print("   - GET  /api/trades        - Trade history")
    print("   - GET  /api/positions     - Current positions")
    print("   - GET  /api/performance   - Performance metrics")
    print("   - GET  /api/config        - Configuration")
    print("   - GET  /api/logs          - System logs")
    print("Press Ctrl+C to stop...")
    
    try:
        app.run(
            host='0.0.0.0',
            port=5001,
            debug=False,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n👋 Dashboard server stopped")

if __name__ == '__main__':
    main()