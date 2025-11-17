#!/usr/bin/env python3
"""
WEB OPTIONS TRADING DASHBOARD
Clean web interface for viewing options trading signals
"""

from flask import Flask, render_template, jsonify
import asyncio
import json
import sys
import os
from datetime import datetime
import threading
import time

sys.path.append('src')

# Import our trading assistant
from manual_trading_assistant import ManualTradingAssistant

app = Flask(__name__)

# Global variables to store trading data
trading_assistant = None
current_signals = []
trading_status = {"running": False, "last_update": None, "balance": 50.00}

class WebTradingAssistant(ManualTradingAssistant):
    """Modified trading assistant for web dashboard"""
    
    def __init__(self, balance=50.00):
        super().__init__(balance)
        self.web_signals = []
        self.web_status = {"running": False, "last_scan": None}
        
    async def scan_and_update_web(self):
        """Scan for signals and update web data"""
        try:
            self.web_status["running"] = True
            self.web_status["last_scan"] = datetime.now().strftime("%H:%M:%S")
            
            # Build stock universe if needed
            if not self.stock_universe:
                await self.build_stock_universe()
            
            # Scan for signals
            signals = await self.scan_for_signals()
            
            # Sort by confidence
            self.web_signals = sorted(signals, key=lambda x: x['confidence'], reverse=True)
            
            # Update global variables for web
            global current_signals, trading_status
            current_signals = self.web_signals
            trading_status.update({
                "running": True,
                "last_update": datetime.now().strftime("%H:%M:%S"),
                "balance": self.buying_power,
                "signals_found": len(self.web_signals),
                "universe_size": len(self.stock_universe)
            })
            
        except Exception as e:
            print(f"Scan error: {e}")
            self.web_status["running"] = False

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('options_dashboard.html')

@app.route('/api/signals')
def get_signals():
    """API endpoint for current signals"""
    return jsonify({
        "signals": current_signals,
        "status": trading_status,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/start_scanning')
def start_scanning():
    """Start the scanning process"""
    def run_scanner():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        global trading_assistant
        trading_assistant = WebTradingAssistant(balance=50.00)
        
        while True:
            try:
                loop.run_until_complete(trading_assistant.scan_and_update_web())
                time.sleep(30)  # Scan every 30 seconds
            except Exception as e:
                print(f"Scanner error: {e}")
                time.sleep(10)
    
    # Start scanner in background thread
    scanner_thread = threading.Thread(target=run_scanner, daemon=True)
    scanner_thread.start()
    
    return jsonify({"status": "Scanner started"})

# Create the HTML template
template_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎯 Options Trading Dashboard ($50 Budget)</title>
    <style>
        body {
            font-family: 'Monaco', 'Menlo', monospace;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .status-bar {
            background: rgba(255,255,255,0.1);
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .signals-grid {
            display: grid;
            gap: 20px;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        }
        .signal-card {
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
            transition: transform 0.3s ease;
        }
        .signal-card:hover {
            transform: translateY(-5px);
            background: rgba(255,255,255,0.2);
        }
        .signal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .symbol {
            font-size: 24px;
            font-weight: bold;
            color: #FFD700;
        }
        .confidence {
            font-size: 18px;
            color: #90EE90;
            font-weight: bold;
        }
        .option-type {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .call { background: #4CAF50; }
        .put { background: #FF5722; }
        .details {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin: 15px 0;
        }
        .detail-item {
            background: rgba(0,0,0,0.2);
            padding: 8px 12px;
            border-radius: 8px;
            font-size: 14px;
        }
        .execution-box {
            background: rgba(0,0,0,0.3);
            padding: 15px;
            border-radius: 10px;
            margin-top: 15px;
        }
        .btn {
            background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            cursor: pointer;
            font-weight: bold;
            transition: transform 0.2s;
        }
        .btn:hover {
            transform: scale(1.05);
        }
        .no-signals {
            text-align: center;
            padding: 40px;
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
        }
        .loading {
            text-align: center;
            font-size: 18px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Options Trading Dashboard</h1>
            <h2>$50 Budget • High-Leverage Plays</h2>
        </div>

        <div class="status-bar">
            <div>
                💰 Balance: $<span id="balance">50.00</span> | 
                📊 Signals: <span id="signal-count">0</span> | 
                🔍 Universe: <span id="universe-size">0</span> stocks
            </div>
            <div>
                <button class="btn" onclick="startScanning()">🚀 Start Scanning</button>
                Last Update: <span id="last-update">Never</span>
            </div>
        </div>

        <div id="signals-container">
            <div class="loading">
                <h3>🔄 Click "Start Scanning" to find options plays</h3>
            </div>
        </div>
    </div>

    <script>
        let scanningActive = false;

        function startScanning() {
            if (scanningActive) return;
            
            fetch('/api/start_scanning')
                .then(response => response.json())
                .then(data => {
                    scanningActive = true;
                    updateSignals();
                    // Update every 5 seconds
                    setInterval(updateSignals, 5000);
                });
        }

        function updateSignals() {
            fetch('/api/signals')
                .then(response => response.json())
                .then(data => {
                    updateStatusBar(data.status);
                    renderSignals(data.signals);
                })
                .catch(error => console.error('Error:', error));
        }

        function updateStatusBar(status) {
            document.getElementById('balance').textContent = status.balance?.toFixed(2) || '50.00';
            document.getElementById('signal-count').textContent = status.signals_found || '0';
            document.getElementById('universe-size').textContent = status.universe_size || '0';
            document.getElementById('last-update').textContent = status.last_update || 'Never';
        }

        function renderSignals(signals) {
            const container = document.getElementById('signals-container');
            
            if (!signals || signals.length === 0) {
                container.innerHTML = `
                    <div class="no-signals">
                        <h3>📊 No signals found</h3>
                        <p>Scanning for high-confidence options plays...</p>
                    </div>
                `;
                return;
            }

            container.innerHTML = `
                <div class="signals-grid">
                    ${signals.map((signal, index) => `
                        <div class="signal-card">
                            <div class="signal-header">
                                <div class="symbol">${signal.symbol}</div>
                                <div class="confidence">${signal.confidence.toFixed(0)}%</div>
                            </div>
                            
                            <div class="option-type ${signal.option_type.toLowerCase()}">
                                ${signal.option_type} OPTION
                            </div>
                            
                            <div class="details">
                                <div class="detail-item">
                                    💰 Stock: $${signal.stock_price.toFixed(2)}
                                </div>
                                <div class="detail-item">
                                    🚀 Momentum: ${signal.momentum > 0 ? '+' : ''}${signal.momentum.toFixed(1)}%
                                </div>
                                <div class="detail-item">
                                    💎 Strike: $${signal.strike_price.toFixed(2)}
                                </div>
                                <div class="detail-item">
                                    📅 Exp: ${signal.expiration}
                                </div>
                                <div class="detail-item">
                                    📈 Contracts: ${signal.contracts}
                                </div>
                                <div class="detail-item">
                                    💸 Cost: $${signal.cost.toFixed(0)}
                                </div>
                            </div>
                            
                            <div class="execution-box">
                                <strong>🎯 EXECUTE:</strong><br>
                                BUY ${signal.contracts} contracts of<br>
                                <strong>${signal.symbol} ${signal.strike_price} ${signal.option_type}</strong><br>
                                Exp: ${signal.expiration}<br>
                                Est. Price: $${signal.estimated_option_price.toFixed(2)}
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        }
    </script>
</body>
</html>'''

# Create templates directory and save HTML
import os
os.makedirs('templates', exist_ok=True)
with open('templates/options_dashboard.html', 'w') as f:
    f.write(template_html)

if __name__ == '__main__':
    print("🚀 Starting Options Trading Web Dashboard...")
    print("📊 Dashboard will be available at: http://localhost:5001")
    print("💡 Open this URL in your browser to see the dashboard")
    print()
    
    app.run(host='0.0.0.0', port=5001, debug=True)
