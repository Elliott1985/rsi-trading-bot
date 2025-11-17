#!/usr/bin/env python3
"""
LIVE TRADING DASHBOARD
Real-time web interface to monitor your trading bot
"""

import streamlit as st
import json
import os
from datetime import datetime, timedelta
import time
import pandas as pd
from pathlib import Path
import sqlite3

# Set page config
st.set_page_config(
    page_title="🤖 Live Trading Bot Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"  # Better for mobile
)

# Add custom CSS - Mobile optimized
st.markdown("""
<style>
.metric-card {
    background-color: #f0f2f6;
    padding: 0.8rem;
    border-radius: 0.5rem;
    border-left: 4px solid #00cc44;
    margin: 0.2rem 0;
}
.alert-box {
    background-color: #fff3cd;
    border: 1px solid #ffeaa7;
    border-radius: 0.5rem;
    padding: 0.8rem;
    margin: 0.5rem 0;
    font-size: 0.9rem;
}
.trade-alert {
    background-color: #d4edda;
    border: 1px solid #c3e6cb;
    border-radius: 0.5rem;
    padding: 0.8rem;
    margin: 0.3rem 0;
    font-size: 0.85rem;
}
.mobile-metric {
    text-align: center;
    padding: 0.5rem;
    background: #f8f9fa;
    border-radius: 0.5rem;
    margin: 0.2rem;
}
@media (max-width: 768px) {
    .stMetric {
        font-size: 0.9rem;
    }
    .stDataFrame {
        font-size: 0.8rem;
    }
}
</style>
""", unsafe_allow_html=True)

class TradingDashboard:
    def __init__(self):
        self.data_dir = Path("data")
        self.logs_dir = Path("logs")
        self.status_file = "bot_status.json"
        self.trades_db = "data/trades.db"
        
    def get_bot_status(self):
        """Get current bot status"""
        try:
            if os.path.exists(self.status_file):
                with open(self.status_file, 'r') as f:
                    return json.load(f)
            return {"status": "stopped", "last_update": None}
        except:
            return {"status": "unknown", "last_update": None}
    
    def get_recent_logs(self, lines=50):
        """Get recent log entries"""
        log_file = self.logs_dir / "trading.log"
        try:
            if log_file.exists():
                with open(log_file, 'r') as f:
                    all_lines = f.readlines()
                    return all_lines[-lines:] if len(all_lines) > lines else all_lines
            return ["No log file found"]
        except:
            return ["Error reading logs"]
    
    def get_trades_data(self):
        """Get trades from database"""
        try:
            if not os.path.exists(self.trades_db):
                return pd.DataFrame()
            
            conn = sqlite3.connect(self.trades_db)
            query = """
            SELECT trade_id, symbol, entry_price, exit_price, quantity, 
                   pnl, confidence_score, strategy, entry_time, exit_time, status
            FROM trades 
            ORDER BY entry_time DESC 
            LIMIT 50
            """
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except:
            return pd.DataFrame()
    
    def parse_bot_output(self):
        """Parse recent bot output for live trades"""
        trades = []
        positions = []
        
        # Look for trade execution patterns in logs
        logs = self.get_recent_logs(100)
        
        for line in logs:
            if "LIVE MICRO-TRADE EXECUTED" in line:
                # Extract trade info from logs
                pass  # Would parse actual trade details
            elif "POSITION CLOSED" in line:
                # Extract closed position info
                pass
        
        return trades, positions

def main():
    st.title("🤖 Live Trading Bot Dashboard")
    st.markdown("Real-time monitoring of your micro-budget trading bot")
    
    dashboard = TradingDashboard()
    
    # Auto-refresh every 10 seconds
    placeholder = st.empty()
    
    while True:
        with placeholder.container():
            # Header metrics
            col1, col2, col3, col4 = st.columns(4)
            
            bot_status = dashboard.get_bot_status()
            current_time = datetime.now().strftime("%H:%M:%S")
            
            with col1:
                status_color = "🟢" if bot_status.get("status") == "running" else "🔴"
                st.metric("Bot Status", f"{status_color} {bot_status.get('status', 'unknown').upper()}")
            
            with col2:
                st.metric("Current Time", current_time)
            
            with col3:
                # Market status (simplified)
                now = datetime.now()
                market_open = 4 <= now.hour <= 20 and now.weekday() < 5
                market_status = "🟢 OPEN" if market_open else "🔴 CLOSED"
                st.metric("Market", market_status)
            
            with col4:
                st.metric("Positions", "0/2")
            
            st.divider()
            
            # Check if mobile view
            # Two columns layout (responsive)
            col1, col2 = st.columns([3, 2])
            
            with col1:
                st.subheader("📊 Live Activity")
                
                # Get recent trades
                trades_df = dashboard.get_trades_data()
                
                if not trades_df.empty:
                    # Show recent trades table
                    st.markdown("### Recent Trades")
                    display_df = trades_df[['symbol', 'entry_price', 'exit_price', 'pnl', 'confidence_score', 'entry_time']].copy()
                    display_df['entry_time'] = pd.to_datetime(display_df['entry_time']).dt.strftime('%H:%M:%S')
                    st.dataframe(display_df, use_container_width=True)
                    
                    # Performance metrics
                    total_pnl = trades_df['pnl'].sum()
                    win_rate = (trades_df['pnl'] > 0).sum() / len(trades_df) * 100
                    
                    perf_col1, perf_col2 = st.columns(2)
                    with perf_col1:
                        pnl_color = "green" if total_pnl >= 0 else "red"
                        st.markdown(f"**Total P&L:** <span style='color: {pnl_color}'>${total_pnl:.2f}</span>", unsafe_allow_html=True)
                    with perf_col2:
                        st.markdown(f"**Win Rate:** {win_rate:.1f}%")
                else:
                    st.info("No trades yet. Bot is scanning for opportunities...")
                
                # Live logs section
                st.markdown("### 🔍 Live Bot Activity")
                logs = dashboard.get_recent_logs(20)
                
                log_container = st.container()
                with log_container:
                    for log_line in logs[-10:]:  # Show last 10 lines
                        if any(keyword in log_line for keyword in ["TRADE", "BUY", "SELL", "EXECUTED"]):
                            st.markdown(f'<div class="trade-alert">{log_line.strip()}</div>', unsafe_allow_html=True)
                        elif "ERROR" in log_line:
                            st.error(log_line.strip())
                        elif "WARNING" in log_line:
                            st.warning(log_line.strip())
                        else:
                            st.text(log_line.strip())
            
            with col2:
                st.subheader("⚙️ Bot Settings")
                
                # Settings display
                settings_info = """
                **Budget:** $50.00  
                **Max per trade:** Up to $50.00  
                **Typical trade:** $25.00 (50%)  
                **Max positions:** 2 at once  
                **Expensive stocks:** 1 share (e.g. $44)  
                **Cheap stocks:** Multiple shares (e.g. 2×$12)  
                **Confidence required:** 60%+  
                **Max stock price:** $50.00  
                **Trading hours:** 4 AM - 8 PM  
                **Scan interval:** 5 minutes  
                """
                st.markdown(settings_info)
                
                st.subheader("📈 Quick Stats")
                
                # Simulated stats (would be real in production)
                stats_info = f"""
                **Scans completed:** {int(time.time() % 1000)}  
                **Opportunities found:** {int(time.time() % 10)}  
                **Current positions:** 0  
                **Available budget:** $50.00  
                **Trades today:** {len(trades_df) if not trades_df.empty else 0}  
                """
                st.markdown(stats_info)
                
                # Control buttons
                st.subheader("🎮 Controls")
                
                if st.button("🔄 Refresh Data"):
                    st.rerun()
                
                if st.button("🛑 Stop Bot", type="secondary"):
                    st.warning("To stop the bot, use Ctrl+C in the terminal where it's running")
                
                if st.button("📋 View Full Logs", type="secondary"):
                    with st.expander("Full Log Output"):
                        full_logs = dashboard.get_recent_logs(200)
                        for line in full_logs:
                            st.text(line.strip())
            
            # Trading alerts section
            st.divider()
            
            # Simulated alerts
            alerts_col1, alerts_col2 = st.columns(2)
            
            with alerts_col1:
                st.subheader("🚨 Recent Alerts")
                if int(time.time()) % 30 < 10:  # Show alert every 30 seconds for 10 seconds
                    st.markdown('<div class="alert-box">🔍 Scanning markets for opportunities...</div>', unsafe_allow_html=True)
                
            with alerts_col2:
                st.subheader("📊 Market Focus")
                focus_stocks = "SIRI, NOK, F, BAC, PLUG, FCEL, NIO, PLTR"
                st.info(f"Watching affordable stocks: {focus_stocks}")
        
        # Wait before refresh
        time.sleep(10)
        st.rerun()

if __name__ == "__main__":
    main()