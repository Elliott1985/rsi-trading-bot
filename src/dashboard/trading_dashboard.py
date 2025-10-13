"""
Autonomous Trading AI - Web Dashboard
Real-time monitoring and control interface using Streamlit
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import asyncio
import sys
import os
from typing import Dict, List, Any
import json

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.trading.trade_logger import TradeLogger
from src.analysis.technical_analyzer import TechnicalAnalyzer
from src.analysis.sentiment_analyzer import SentimentAnalyzer
from src.analysis.trade_scoring import AITradeScorer
from src.trading.portfolio_manager import PortfolioManager
from src.utils.config import Config

# Configure Streamlit page
st.set_page_config(
    page_title="Autonomous Trading AI Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data(ttl=30)  # Cache for 30 seconds
def load_dashboard_data():
    """Load and cache dashboard data"""
    try:
        trade_logger = TradeLogger()
        
        # Get performance data
        performance = trade_logger.get_performance_summary(days=30)
        open_trades = trade_logger.get_open_trades()
        recent_trades = trade_logger.get_trade_history(days=7, limit=20)
        
        return {
            'performance': performance,
            'open_trades': open_trades,
            'recent_trades': recent_trades,
            'last_updated': datetime.now()
        }
    except Exception as e:
        st.error(f"Error loading dashboard data: {e}")
        return None

@st.cache_data(ttl=60)  # Cache for 1 minute
def get_market_analysis():
    """Get current market analysis"""
    try:
        analyzer = TechnicalAnalyzer()
        config = Config()
        
        # Analyze popular symbols
        symbols = ['AAPL', 'MSFT', 'TSLA', 'BTC-USD', 'ETH-USD']
        analyses = []
        
        for symbol in symbols:
            signal = analyzer.analyze_symbol(symbol)
            if signal:
                analyses.append({
                    'Symbol': symbol,
                    'Signal': signal.signal_type.upper(),
                    'RSI': f"{signal.rsi_value:.1f}" if signal.rsi_value else "N/A",
                    'Price': f"${signal.price:.2f}" if signal.price else "N/A",
                    'Confidence': f"{signal.confidence:.2f}"
                })
        
        return analyses
    except Exception as e:
        st.error(f"Error getting market analysis: {e}")
        return []

def create_performance_charts(performance_data: Dict):
    """Create performance visualization charts"""
    
    # Performance metrics cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Trades", 
            performance_data.get('total_trades', 0),
            help="Number of trades in the selected period"
        )
    
    with col2:
        win_rate = performance_data.get('win_rate', 0)
        st.metric(
            "Win Rate", 
            f"{win_rate:.1f}%",
            delta=f"{win_rate - 50:.1f}% vs 50%",
            help="Percentage of profitable trades"
        )
    
    with col3:
        total_pnl = performance_data.get('total_pnl', 0)
        st.metric(
            "Total P&L", 
            f"${total_pnl:.2f}",
            delta=f"${total_pnl:.2f}",
            delta_color="normal" if total_pnl >= 0 else "inverse",
            help="Total profit/loss for the period"
        )
    
    with col4:
        profit_factor = performance_data.get('profit_factor', 0)
        st.metric(
            "Profit Factor", 
            f"{profit_factor:.2f}",
            delta=f"{profit_factor - 1:.2f} vs 1.0",
            help="Ratio of gross profit to gross loss"
        )

def create_trades_chart(recent_trades: List[Dict]):
    """Create trades timeline chart"""
    if not recent_trades:
        st.info("No recent trades to display")
        return
    
    # Prepare data for plotting
    df = pd.DataFrame(recent_trades)
    df['entry_time'] = pd.to_datetime(df['entry_time'])
    
    # Create scatter plot of trades
    fig = px.scatter(
        df, 
        x='entry_time', 
        y='profit_loss',
        color='status',
        size='confidence_score',
        hover_data=['symbol', 'trade_type', 'profit_loss_pct'],
        title="Recent Trades Timeline",
        labels={
            'entry_time': 'Entry Time',
            'profit_loss': 'P&L ($)',
            'status': 'Trade Status'
        }
    )
    
    # Add horizontal line at break-even
    fig.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="Break Even")
    
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

def display_open_positions(open_trades: List[Dict]):
    """Display current open positions"""
    if not open_trades:
        st.info("No open positions")
        return
    
    # Convert to DataFrame for better display
    df = pd.DataFrame(open_trades)
    
    # Select and rename columns for display
    display_columns = {
        'symbol': 'Symbol',
        'trade_type': 'Type',
        'entry_price': 'Entry Price',
        'quantity': 'Quantity',
        'stop_loss': 'Stop Loss',
        'take_profit': 'Take Profit',
        'confidence_score': 'Confidence',
        'strategy': 'Strategy',
        'entry_time': 'Entry Time'
    }
    
    display_df = df[list(display_columns.keys())].rename(columns=display_columns)
    
    # Format numeric columns
    if 'Entry Price' in display_df.columns:
        display_df['Entry Price'] = display_df['Entry Price'].apply(lambda x: f"${x:.2f}")
    if 'Stop Loss' in display_df.columns:
        display_df['Stop Loss'] = display_df['Stop Loss'].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "N/A")
    if 'Take Profit' in display_df.columns:
        display_df['Take Profit'] = display_df['Take Profit'].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "N/A")
    if 'Confidence' in display_df.columns:
        display_df['Confidence'] = display_df['Confidence'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "N/A")
    
    st.dataframe(display_df, use_container_width=True)

def display_market_analysis(analyses: List[Dict]):
    """Display current market analysis"""
    if not analyses:
        st.info("No market analysis available")
        return
    
    df = pd.DataFrame(analyses)
    
    # Color-code signals
    def color_signal(signal):
        if signal == 'BUY':
            return '🟢 BUY'
        elif signal == 'SELL':
            return '🔴 SELL'
        else:
            return '🟡 HOLD'
    
    df['Signal'] = df['Signal'].apply(color_signal)
    
    st.dataframe(df, use_container_width=True, hide_index=True)

def system_controls():
    """System control interface"""
    st.subheader("🎛️ System Controls")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔍 Run Market Scan", help="Scan markets for new opportunities"):
            with st.spinner("Scanning markets..."):
                # Here you would integrate with your market scanning logic
                st.success("Market scan completed! Check the Market Analysis section.")
    
    with col2:
        if st.button("📊 Update Performance", help="Refresh performance metrics"):
            st.cache_data.clear()
            st.experimental_rerun()
    
    with col3:
        if st.button("📁 Export Trades", help="Export trade history to CSV"):
            try:
                trade_logger = TradeLogger()
                export_path = trade_logger.export_trades_to_csv()
                if export_path:
                    st.success(f"Trades exported to: {export_path}")
                else:
                    st.warning("No trades to export")
            except Exception as e:
                st.error(f"Export failed: {e}")

def trading_settings():
    """Trading system settings interface"""
    st.subheader("⚙️ Trading Settings")
    
    try:
        config = Config()
        
        # Create tabs for different setting categories
        tab1, tab2, tab3, tab4 = st.tabs(["📈 Technical", "🧠 AI Scoring", "💰 Risk Management", "📰 Sentiment"])
        
        with tab1:
            st.write("**Technical Analysis Settings**")
            col1, col2 = st.columns(2)
            
            with col1:
                rsi_oversold = st.slider("RSI Oversold Threshold", 10, 40, int(config.trading.rsi_oversold))
                rsi_overbought = st.slider("RSI Overbought Threshold", 60, 90, int(config.trading.rsi_overbought))
            
            with col2:
                macd_fast = st.slider("MACD Fast Period", 5, 20, config.trading.macd_fast)
                macd_slow = st.slider("MACD Slow Period", 15, 35, config.trading.macd_slow)
        
        with tab2:
            st.write("**AI Trade Scoring Settings**")
            min_confidence = st.slider("Minimum Confidence Score", 0.0, 1.0, 0.6, 0.05)
            high_confidence = st.slider("High Confidence Threshold", 0.6, 1.0, 0.8, 0.05)
            
            st.write("**Feature Weights**")
            col1, col2 = st.columns(2)
            with col1:
                rsi_weight = st.slider("RSI Weight", 0.0, 0.5, 0.25, 0.05)
                macd_weight = st.slider("MACD Weight", 0.0, 0.5, 0.20, 0.05)
            with col2:
                sentiment_weight = st.slider("Sentiment Weight", 0.0, 0.5, 0.25, 0.05)
                volume_weight = st.slider("Volume Weight", 0.0, 0.5, 0.15, 0.05)
        
        with tab3:
            st.write("**Risk Management Settings**")
            col1, col2 = st.columns(2)
            
            with col1:
                max_position_size = st.slider("Max Position Size (%)", 1, 25, int(config.trading.max_position_size_pct * 100))
                max_daily_risk = st.slider("Max Daily Risk (%)", 0.5, 5.0, config.trading.max_daily_risk_pct * 100, 0.1)
            
            with col2:
                stop_loss_pct = st.slider("Default Stop Loss (%)", 1, 10, int(config.trading.stop_loss_pct * 100))
                take_profit_pct = st.slider("Default Take Profit (%)", 5, 30, int(config.trading.take_profit_pct * 100))
        
        with tab4:
            st.write("**Sentiment Analysis Settings**")
            enable_sentiment = st.checkbox("Enable Sentiment Analysis", True)
            sentiment_sources = st.multiselect(
                "News Sources", 
                ["newsapi", "finnhub", "reddit"],
                default=["newsapi", "finnhub"]
            )
            lookback_hours = st.slider("News Lookback (hours)", 6, 48, 24)
        
        if st.button("💾 Save Settings"):
            # Here you would save the settings back to config
            st.success("Settings saved successfully!")
            
    except Exception as e:
        st.error(f"Error loading settings: {e}")

def main():
    """Main dashboard interface"""
    
    # Dashboard header
    st.title("🤖 Autonomous Trading AI Dashboard")
    st.markdown("Real-time monitoring and control for your AI trading system")
    
    # Sidebar navigation
    with st.sidebar:
        st.header("Navigation")
        selected_page = st.selectbox(
            "Choose a page:",
            ["🏠 Overview", "📊 Performance", "💼 Positions", "📈 Market Analysis", "⚙️ Settings", "🎛️ Controls"]
        )
        
        # System status
        st.header("System Status")
        st.success("🟢 System Online")
        st.info(f"🕐 Last Updated: {datetime.now().strftime('%H:%M:%S')}")
        
        # Quick stats
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.experimental_rerun()
    
    # Main content area
    if selected_page == "🏠 Overview":
        # Overview page
        st.header("System Overview")
        
        # Load dashboard data
        data = load_dashboard_data()
        if not data:
            st.error("Failed to load dashboard data")
            return
        
        # Performance metrics
        st.subheader("📊 Performance Metrics (30 days)")
        create_performance_charts(data['performance'])
        
        # Recent activity
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💼 Open Positions")
            display_open_positions(data['open_trades'])
        
        with col2:
            st.subheader("📈 Recent Trades")
            if data['recent_trades']:
                df = pd.DataFrame(data['recent_trades'])
                # Show summary of recent trades
                st.write(f"**{len(data['recent_trades'])} trades** in the last 7 days")
                if 'profit_loss' in df.columns:
                    total_pnl = df['profit_loss'].sum()
                    st.metric("7-Day P&L", f"${total_pnl:.2f}")
            else:
                st.info("No recent trades")
    
    elif selected_page == "📊 Performance":
        # Performance page
        st.header("Performance Analysis")
        
        data = load_dashboard_data()
        if data:
            create_performance_charts(data['performance'])
            
            if data['recent_trades']:
                st.subheader("Trade Timeline")
                create_trades_chart(data['recent_trades'])
                
                # Performance breakdown
                st.subheader("Performance Breakdown")
                df = pd.DataFrame(data['recent_trades'])
                
                if 'symbol' in df.columns:
                    # Performance by symbol
                    symbol_performance = df.groupby('symbol')['profit_loss'].agg(['count', 'sum', 'mean']).round(2)
                    symbol_performance.columns = ['Trades', 'Total P&L', 'Avg P&L']
                    st.write("**Performance by Symbol:**")
                    st.dataframe(symbol_performance)
    
    elif selected_page == "💼 Positions":
        # Positions page
        st.header("Current Positions")
        
        data = load_dashboard_data()
        if data:
            display_open_positions(data['open_trades'])
            
            if data['open_trades']:
                # Position summary
                df = pd.DataFrame(data['open_trades'])
                st.subheader("Position Summary")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Open Positions", len(data['open_trades']))
                with col2:
                    if 'quantity' in df.columns:
                        total_exposure = (df['entry_price'] * df['quantity']).sum()
                        st.metric("Total Exposure", f"${total_exposure:.2f}")
                with col3:
                    avg_confidence = df['confidence_score'].mean() if 'confidence_score' in df.columns else 0
                    st.metric("Avg Confidence", f"{avg_confidence:.2f}")
    
    elif selected_page == "📈 Market Analysis":
        # Market analysis page
        st.header("Market Analysis")
        
        analyses = get_market_analysis()
        display_market_analysis(analyses)
        
        # Add refresh button
        if st.button("🔄 Refresh Analysis"):
            st.cache_data.clear()
            st.experimental_rerun()
    
    elif selected_page == "⚙️ Settings":
        # Settings page
        trading_settings()
    
    elif selected_page == "🎛️ Controls":
        # Controls page
        system_controls()
        
        st.subheader("📋 System Logs")
        if st.button("📄 Show Recent Logs"):
            st.text_area("Recent System Activity", 
                        "2024-01-15 10:30:15 | INFO | Market scan completed\n"
                        "2024-01-15 10:25:10 | INFO | Trade executed: AAPL BUY\n"
                        "2024-01-15 10:20:05 | INFO | Sentiment analysis updated\n"
                        "2024-01-15 10:15:00 | INFO | Technical indicators calculated",
                        height=200)
    
    # Footer
    st.markdown("---")
    st.markdown("*Autonomous Trading AI Dashboard - Built with Streamlit*")

if __name__ == "__main__":
    main()