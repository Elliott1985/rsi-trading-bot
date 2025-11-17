#!/usr/bin/env python3
"""
MOBILE TRADING DASHBOARD
Lightweight, iPhone-optimized dashboard for your trading bot
"""

from flask import Flask, render_template_string, jsonify
import json
import os
from datetime import datetime
import sqlite3
from pathlib import Path

app = Flask(__name__)

# Mobile-optimized HTML template
MOBILE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🤖 Trading Bot</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f5f5f7;
            color: #1d1d1f;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .status-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            padding: 15px;
        }
        
        .status-card {
            background: white;
            border-radius: 12px;
            padding: 15px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .status-value {
            font-size: 1.2em;
            font-weight: 600;
            margin-top: 5px;
        }
        
        .status-label {
            font-size: 0.9em;
            color: #666;
        }
        
        .section {
            margin: 15px;
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .section-header {
            background: #f8f9fa;
            padding: 15px;
            font-weight: 600;
            border-bottom: 1px solid #e9ecef;
        }
        
        .section-content {
            padding: 15px;
        }
        
        .trade-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #f0f0f0;
        }
        
        .trade-item:last-child {
            border-bottom: none;
        }
        
        .trade-symbol {
            font-weight: 600;
            font-size: 1.1em;
        }
        
        .trade-pnl {
            font-weight: 600;
        }
        
        .positive {
            color: #34c759;
        }
        
        .negative {
            color: #ff3b30;
        }
        
        .log-item {
            padding: 8px 0;
            font-size: 0.9em;
            color: #666;
            border-bottom: 1px solid #f0f0f0;
        }
        
        .log-item:last-child {
            border-bottom: none;
        }
        
        .trade-log {
            background: #e8f5e8;
            padding: 8px;
            border-radius: 6px;
            color: #2d6a2d;
            font-weight: 500;
        }
        
        .refresh-btn {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #007aff;
            color: white;
            border: none;
            border-radius: 50%;
            width: 56px;
            height: 56px;
            font-size: 1.5em;
            box-shadow: 0 4px 12px rgba(0,122,255,0.3);
            cursor: pointer;
        }
        
        .refresh-btn:active {
            transform: scale(0.95);
        }
        
        .alert {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 12px;
            margin: 10px 0;
            font-size: 0.9em;
        }
        
        .market-closed {
            background: #f8d7da;
            color: #721c24;
        }
        
        .market-open {
            background: #d4edda;
            color: #155724;
        }
    </style>
</head>
<body>
    <div class="header">
        <div style="font-size: 1.5em; margin-bottom: 5px;">🤖 Trading Bot</div>
        <div style="font-size: 0.9em; opacity: 0.9;">Micro-Budget Live Trading</div>
        <div id="current-time" style="font-size: 0.8em; opacity: 0.8; margin-top: 8px;"></div>
    </div>

    <div class="status-grid">
        <div class="status-card">
            <div class="status-label">Bot Status</div>
            <div id="bot-status" class="status-value">🔴 LOADING</div>
        </div>
        <div class="status-card">
            <div class="status-label">Market</div>
            <div id="market-status" class="status-value">🔴 CLOSED</div>
        </div>
        <div class="status-card">
            <div class="status-label">Budget</div>
            <div class="status-value">$50.00</div>
        </div>
        <div class="status-card">
            <div class="status-label">Positions</div>
            <div id="position-count" class="status-value">0/2</div>
        </div>
    </div>

    <div id="alert-section"></div>

    <div class="section">
        <div class="section-header">📊 Recent Trades</div>
        <div class="section-content" id="trades-section">
            <div class="alert">No trades yet. Bot is scanning for opportunities...</div>
        </div>
    </div>

    <div class="section">
        <div class="section-header">🔍 Live Activity</div>
        <div class="section-content" id="logs-section">
            <div class="log-item">Bot starting up...</div>
        </div>
    </div>

    <div class="section">
        <div class="section-header">⚙️ Settings</div>
        <div class="section-content">
            <div style="line-height: 1.6; font-size: 0.95em;">
                <strong>Budget:</strong> $50.00<br>
                <strong>Max per trade:</strong> Up to $50.00<br>
                <strong>Typical trade:</strong> $25.00 (50%)<br>
                <strong>Max positions:</strong> 2 at once<br>
                <strong>Dynamic sizing:</strong> 1×$44 or 2×$12<br>
                <strong>Confidence required:</strong> 60%+<br>
                <strong>Trading hours:</strong> 4 AM - 8 PM<br>
                <strong>Focus:</strong> Stocks up to $50<br>
            </div>
        </div>
    </div>

    <button class="refresh-btn" onclick="refreshData()">🔄</button>

    <script>
        function updateTime() {
            const now = new Date();
            document.getElementById('current-time').textContent = 
                now.toLocaleTimeString('en-US', { hour12: false });
        }
        
        function checkMarketStatus() {
            const now = new Date();
            const hour = now.getHours();
            const day = now.getDay();
            
            // Check if market is open (4 AM - 8 PM, weekdays)
            const isOpen = (day >= 1 && day <= 5) && (hour >= 4 && hour <= 20);
            
            const marketElement = document.getElementById('market-status');
            if (isOpen) {
                marketElement.textContent = '🟢 OPEN';
                marketElement.className = 'status-value market-open';
            } else {
                marketElement.textContent = '🔴 CLOSED';
                marketElement.className = 'status-value market-closed';
            }
        }
        
        function refreshData() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    // Update bot status
                    const botElement = document.getElementById('bot-status');
                    if (data.bot_running) {
                        botElement.textContent = '🟢 RUNNING';
                    } else {
                        botElement.textContent = '🔴 STOPPED';
                    }
                    
                    // Update trades
                    const tradesElement = document.getElementById('trades-section');
                    if (data.trades && data.trades.length > 0) {
                        tradesElement.innerHTML = data.trades.map(trade => 
                            `<div class="trade-item">
                                <div>
                                    <div class="trade-symbol">${trade.symbol}</div>
                                    <div style="font-size: 0.8em; color: #666;">${trade.time}</div>
                                </div>
                                <div class="trade-pnl ${trade.pnl >= 0 ? 'positive' : 'negative'}">
                                    $${trade.pnl.toFixed(2)}
                                </div>
                            </div>`
                        ).join('');
                    }
                    
                    // Update logs
                    const logsElement = document.getElementById('logs-section');
                    if (data.recent_logs && data.recent_logs.length > 0) {
                        logsElement.innerHTML = data.recent_logs.slice(-5).map(log => {
                            const isTradeLog = log.includes('TRADE') || log.includes('BUY') || log.includes('SELL');
                            return `<div class="log-item ${isTradeLog ? 'trade-log' : ''}">${log}</div>`;
                        }).join('');
                    }
                    
                    // Update alerts
                    const alertElement = document.getElementById('alert-section');
                    if (data.scanning) {
                        alertElement.innerHTML = '<div class="alert">🔍 Scanning markets for opportunities...</div>';
                    } else {
                        alertElement.innerHTML = '';
                    }
                })
                .catch(error => {
                    console.log('Refresh error:', error);
                });
        }
        
        // Update time every second
        setInterval(updateTime, 1000);
        setInterval(checkMarketStatus, 60000);
        
        // Refresh data every 10 seconds
        setInterval(refreshData, 10000);
        
        // Initial load
        updateTime();
        checkMarketStatus();
        refreshData();
    </script>
</body>
</html>
"""

class MobileDashboard:
    def __init__(self):
        self.data_dir = Path("data")
        self.logs_dir = Path("logs")
        self.trades_db = "data/trades.db"
        
    def get_recent_trades(self, limit=5):
        """Get recent trades from database"""
        try:
            if not os.path.exists(self.trades_db):
                return []
            
            conn = sqlite3.connect(self.trades_db)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT symbol, pnl, entry_time 
                FROM trades 
                ORDER BY entry_time DESC 
                LIMIT ?
            """, (limit,))
            
            trades = []
            for row in cursor.fetchall():
                trades.append({
                    'symbol': row[0],
                    'pnl': float(row[1]) if row[1] else 0.0,
                    'time': row[2]
                })
            
            conn.close()
            return trades
        except:
            return []
    
    def get_recent_logs(self, lines=10):
        """Get recent log entries"""
        try:
            log_file = self.logs_dir / "trading.log"
            if log_file.exists():
                with open(log_file, 'r') as f:
                    all_lines = f.readlines()
                    recent = all_lines[-lines:] if len(all_lines) > lines else all_lines
                    return [line.strip() for line in recent]
            return ["No logs available"]
        except:
            return ["Error reading logs"]

dashboard = MobileDashboard()

@app.route('/')
def mobile_dashboard():
    """Main mobile dashboard page"""
    return render_template_string(MOBILE_TEMPLATE)

@app.route('/api/status')
def api_status():
    """API endpoint for real-time data"""
    return jsonify({
        'bot_running': True,  # Would check actual bot status
        'trades': dashboard.get_recent_trades(),
        'recent_logs': dashboard.get_recent_logs(),
        'scanning': True,
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🚀 Starting mobile dashboard...")
    print("📱 Access from your iPhone at:")
    print("   http://your-computer-ip:5001")
    print("   (Find your IP with: ifconfig | grep inet)")
    
    # Run on all interfaces so iPhone can access
    app.run(host='0.0.0.0', port=5001, debug=False)