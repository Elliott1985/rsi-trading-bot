# 🤖 RSI Trading Bot - Alpaca Integration

**An AI-powered trading bot using Alpaca API with RSI strategies, sentiment analysis, advanced technical indicators, and intelligent trade scoring.**

![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Trading](https://img.shields.io/badge/trading-AI%20Enhanced-green.svg)
![Status](https://img.shields.io/badge/status-Production%20Ready-brightgreen.svg)

---

## 🚀 **What's New - Major AI Enhancements**

This system has been completely upgraded with cutting-edge AI capabilities:

### 🧠 **Core AI Features**
- **AI-Powered Trade Scoring** (0.0-1.0 confidence) with 5-component analysis
- **Real-time News Sentiment Analysis** from NewsAPI and Finnhub
- **Advanced Technical Indicators** (EMA, ATR, VWAP, Choppiness Index, Volume Profile)  
- **Multi-timeframe Analysis** with higher timeframe bias detection
- **Dynamic Position Sizing** based on AI confidence scores
- **Portfolio Mode** supporting 3-5 concurrent trades with risk management

### 📊 **Trading Intelligence**
- **Complete Trade Lifecycle Logging** with SQLite persistence
- **Performance Analytics & Reporting** with win rates and P&L tracking
- **Risk Management** with portfolio heat and correlation analysis
- **Backtesting Engine** for strategy validation
- **Web Dashboard** for real-time monitoring and control

---

## 📋 **Quick Start Guide**

### 1. **Installation**

```bash
# Clone the repository
git clone <your-repo-url>
cd autonomous-trading-ai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the feature demo
python demo_enhanced_features.py
```

### 2. **Configuration Setup**

#### **API Keys Configuration** (`config/api_keys.env`)

```env
# Financial Data APIs
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here
FINNHUB_API_KEY=your_finnhub_key_here

# News Sentiment APIs (Optional but recommended)
NEWSAPI_KEY=your_newsapi_key_here
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret

# Broker APIs (for live trading)
ALPACA_API_KEY=your_alpaca_api_key
ALPACA_SECRET_KEY=your_alpaca_secret_key
ALPACA_BASE_URL=https://paper-api.alpaca.markets  # Use https://api.alpaca.markets for live

# System Configuration
SIMULATION_MODE=true  # Set to false for live trading
```

#### **Trading Parameters** (`config/trading_config.yaml`)

```yaml
# Core Trading Settings
trading:
  mode: "simulation"           # simulation/demo/live
  default_position_size_pct: 0.05  # 5% base position
  max_position_size_pct: 0.15      # 15% maximum position
  max_daily_risk_pct: 0.02         # 2% daily risk limit
  min_confidence_threshold: 0.6    # Minimum AI confidence
  
# AI Scoring Configuration
ai_scoring:
  enabled: true
  model_type: "manual"       # manual/xgboost
  confidence_threshold: 0.6
  sentiment_weight: 0.25     # 25% weight for sentiment
  technical_weight: 0.75     # 75% weight for technical
  
# Technical Indicators
technical_analysis:
  rsi_period: 14
  rsi_oversold: 30.0
  rsi_overbought: 70.0
  macd_fast: 12
  macd_slow: 26
  macd_signal: 9
  bb_period: 20
  bb_std: 2.0
  
# Advanced Indicators  
advanced_indicators:
  ema_short: 9
  ema_long: 21
  atr_period: 14
  atr_multiplier: 2.0
  vwap_period: 20
  choppiness_period: 14
  volume_sma_period: 20
```

### 3. **Get API Keys**

#### **Free APIs (Recommended)**
- **Alpha Vantage**: [Get free key](https://www.alphavantage.co/support/#api-key) (500 calls/day)
- **NewsAPI**: [Get free key](https://newsapi.org/) (1000 articles/day)
- **Finnhub**: [Get free key](https://finnhub.io/) (60 calls/minute)

#### **Broker API (For Live Trading)**
- **Alpaca**: [Get API keys](https://alpaca.markets/) - Commission-free trading with paper trading support

---

## 🎯 **How to Run**

### **Demo Mode** (Test with fake data)
```bash
python demo_enhanced_features.py  # Feature demonstration
python app.py                     # Full trading simulation
```

### **Web Dashboard** (Recommended)
```bash
streamlit run src/dashboard/trading_dashboard.py
# Access at: http://localhost:8501
```

### **Live Trading** (After API setup)
```bash
# Edit config/api_keys.env with real keys
# Set SIMULATION_MODE=false in api_keys.env
python app.py
```

### **Backtesting**
```bash
python src/backtesting/backtest_engine.py --symbol AAPL --start-date 2024-01-01 --end-date 2024-12-01
```

---

## 🧠 **AI Strategy Explained**

### **Trade Scoring Algorithm**

The AI system combines 5 components to generate a confidence score (0.0-1.0):

1. **Technical Indicators** (35% weight)
   - RSI momentum and overbought/oversold levels
   - MACD histogram and crossover signals
   - Bollinger Bands squeeze and expansion

2. **Sentiment Analysis** (25% weight)
   - News sentiment from multiple sources
   - Social media sentiment (Reddit, Twitter)
   - Confidence based on article volume

3. **Advanced Indicators** (20% weight)  
   - EMA crossovers and trend strength
   - VWAP position and mean reversion
   - Volume profile and institutional activity

4. **Market Conditions** (10% weight)
   - Volatility regime (ATR analysis)
   - Choppiness vs trending conditions
   - Multi-timeframe bias alignment

5. **Risk Assessment** (10% weight)
   - Position correlation analysis
   - Portfolio heat management
   - Historical pattern recognition

### **Position Sizing Formula**

```python
position_size = base_size + (confidence_score * bonus_multiplier)
position_size = min(position_size, max_position_limit)

# Example:
# Base: 5%, Max Bonus: 10%, Confidence: 0.8
# Position = 5% + (0.8 * 10%) = 13% of portfolio
```

### **Risk Management Rules**

- **Maximum 15% position size** per trade
- **Maximum 2% daily risk** (stop losses)
- **Maximum 5 concurrent trades** in portfolio mode
- **Correlation limits** to avoid similar positions
- **Dynamic stop losses** using ATR-based trailing stops

---

## ⚙️ **Configuration Guide**

### **Trading Mode Settings**

| Mode | Description | Use Case |
|------|-------------|----------|
| `simulation` | Fake money, real market data | Safe testing |
| `demo` | Sample data, no API calls | Development |  
| `live` | Real money, real trading | Production |

### **AI Confidence Thresholds**

| Confidence | Action | Position Size |
|------------|--------|---------------|
| 0.8+ | Strong Trade | 13-15% |
| 0.7-0.8 | Good Trade | 11-13% |
| 0.6-0.7 | Consider Trade | 9-11% |
| 0.5-0.6 | Weak Signal | 7-9% |
| <0.5 | Avoid Trade | 0% |

### **Advanced Configuration**

#### **Sentiment Analysis Settings**
```yaml
sentiment_analysis:
  enabled: true
  sources: ["newsapi", "finnhub", "reddit"]
  lookback_hours: 24
  min_articles: 3
  confidence_threshold: 0.1
```

#### **Portfolio Management**
```yaml  
portfolio:
  max_concurrent_trades: 5
  max_correlation: 0.7
  rebalance_frequency: "daily"
  heat_limit: 0.35  # 35% of portfolio at risk
```

#### **Dashboard Settings**
```yaml
dashboard:
  refresh_interval: 30  # seconds
  chart_timeframe: "1h"
  performance_period: 30  # days
  enable_alerts: true
```

---

## 🔌 **Broker Integration**

### **Alpaca Setup**

1. **Create Alpaca Account**
   - Visit [Alpaca](https://alpaca.markets/) and sign up
   - Free account with paper trading included
   - No minimum deposit required for paper trading

2. **Get API Keys**
   - Log in to Alpaca dashboard
   - Navigate to "Paper Trading" section
   - Generate API Key and Secret Key
   - Copy both keys (you'll need them for configuration)

3. **Configure API Keys**
   ```env
   ALPACA_API_KEY=your_api_key_here
   ALPACA_SECRET_KEY=your_secret_key_here
   ALPACA_BASE_URL=https://paper-api.alpaca.markets  # Paper trading
   # For live trading: ALPACA_BASE_URL=https://api.alpaca.markets
   ```

4. **Features**
   - Commission-free stock trading
   - Real-time market data
   - Paper trading environment for testing
   - REST API and WebSocket streams
   - Support for market, limit, stop, and bracket orders

---

## 📈 **Backtesting & Performance**

### **Run Backtests**

```bash
# Single symbol backtest
python src/backtesting/backtest_engine.py --symbol AAPL --start 2024-01-01 --end 2024-12-01

# Portfolio backtest  
python src/backtesting/backtest_engine.py --portfolio tech_stocks.yaml --start 2024-01-01

# Strategy comparison
python src/backtesting/backtest_engine.py --compare-strategies --symbols AAPL,TSLA,MSFT
```

### **Performance Metrics**

The system tracks comprehensive performance metrics:

- **Total Return** and **Max Drawdown**
- **Sharpe Ratio** and **Sortino Ratio**  
- **Win Rate** and **Average Trade Duration**
- **Risk-Adjusted Returns** and **Volatility**
- **Monthly/Quarterly Performance** breakdown

### **Weekly Performance Reports**

Automated PDF reports include:
- Trade summary with P&L analysis
- AI confidence score performance
- Risk metrics and portfolio heat
- Strategy recommendations

---

## 🎛️ **Web Dashboard Features**

Access the dashboard at `http://localhost:8501`

### **Real-time Monitoring**
- Live portfolio performance and P&L
- Current AI confidence scores  
- Active trade tracking with stop/target levels
- Market analysis with sentiment indicators

### **Interactive Controls**
- Start/stop trading engine
- Adjust confidence thresholds
- Emergency position exit
- Export trade history

### **Analytics & Reporting**
- Performance charts and metrics
- Trade analysis by symbol/strategy
- Risk breakdown and correlation analysis
- System health monitoring

---

## 🛠️ **Customization Guide**

### **Adding New Indicators**

Edit `src/analysis/advanced_indicators.py`:

```python
def calculate_custom_indicator(self, symbol: str, data: pd.DataFrame) -> float:
    """Add your custom technical indicator"""
    # Your indicator logic here
    return indicator_value

# Register in calculate_all_indicators():
indicators.custom_signal = self.calculate_custom_indicator(symbol, data)
```

### **Modifying AI Scoring Logic**

Edit `src/analysis/trade_scoring.py`:

```python
def _calculate_component_scores(self, features: Dict[str, float]) -> Dict[str, float]:
    """Customize scoring components and weights"""
    
    # Add new scoring components
    components['new_component'] = your_scoring_logic(features)
    
    # Adjust weights  
    weights = {
        'technical': 0.4,    # 40%
        'sentiment': 0.3,    # 30% 
        'new_component': 0.3 # 30%
    }
```

### **Adding New Data Sources**

Edit `src/analysis/sentiment_analyzer.py`:

```python
async def _get_custom_sentiment(self, symbol: str) -> Dict:
    """Add custom news/sentiment source"""
    # Your API integration here
    return sentiment_data
```

---

## 📊 **Database & Logging**

### **Trade Database Schema**

SQLite database at `data/trades.db`:

```sql
-- Trades table structure
trades (
    id INTEGER PRIMARY KEY,
    trade_id TEXT UNIQUE,
    symbol TEXT,
    entry_price REAL,
    exit_price REAL,
    quantity INTEGER,
    pnl REAL,
    confidence_score REAL,
    strategy TEXT,
    entry_time TIMESTAMP,
    exit_time TIMESTAMP
)
```

### **Export Trade Data**

```python
# Export to CSV
trade_logger = TradeLogger()
trade_logger.export_to_csv("trades_export.csv", days=30)

# Performance summary
performance = trade_logger.get_performance_summary(days=30)
```

---

## 🚨 **Safety Features**

### **Risk Controls**
- **Kill Switch**: Emergency stop all trading
- **Position Limits**: Maximum position sizes enforced
- **Daily Loss Limits**: Automatic shutdown on excessive losses  
- **Correlation Limits**: Avoid over-concentration in similar trades
- **API Rate Limiting**: Prevent API quota exhaustion

### **Simulation Mode**
- Default to simulation mode for safety
- Fake money with real market data
- No actual trades executed
- Full system testing capability

### **Alerts & Notifications**
- Trade execution confirmations
- Risk limit warnings
- System error notifications
- Performance milestone alerts

---

## 🔧 **Troubleshooting**

### **Common Issues**

**1. API Rate Limits**
```bash
# Error: API quota exceeded
# Solution: Use multiple API keys or reduce scan frequency
```

**2. Missing Dependencies**
```bash
# Error: ModuleNotFoundError
pip install -r requirements.txt

# For ML dependencies (optional):
pip install lightgbm xgboost
```

**3. Data Connection Issues**  
```bash
# Error: Data retrieval failed
# Check API keys and network connection
# Verify symbol format (AAPL vs AAPL.US)
```

**4. Dashboard Not Loading**
```bash
# Error: Streamlit connection refused
# Check if port 8501 is available
streamlit run src/dashboard/trading_dashboard.py --server.port 8502
```

### **Debug Mode**
```bash
# Enable detailed logging
export LOG_LEVEL=DEBUG
python app.py
```

### **System Health Check**
```bash
python -c "
import sys
sys.path.append('src')
from src.utils.config import Config
config = Config()
print('✅ Configuration loaded successfully!')
print(f'Mode: {config.trading.mode}')
print(f'API Keys configured: {len([k for k in config.api_keys.__dict__.values() if k])}')
"
```

---

## 🎓 **Learning Resources**

### **Understanding the AI Strategy**
1. **Technical Analysis**: Learn RSI, MACD, Bollinger Bands
2. **Sentiment Analysis**: News impact on market movements
3. **Risk Management**: Position sizing and portfolio theory
4. **Machine Learning**: Feature engineering for trading

### **Recommended Reading**
- "Algorithmic Trading" by Ernie Chan
- "Machine Learning for Asset Managers" by Marcos López de Prado
- "Technical Analysis of the Financial Markets" by John Murphy

### **Online Resources**
- [QuantConnect](https://www.quantconnect.com/) - Algorithm development
- [Alpha Architect](https://alphaarchitect.com/) - Quantitative research
- [Towards Data Science](https://towardsdatascience.com/) - ML/AI articles

---

## 📝 **Contributing & Development**

### **Development Setup**
```bash
# Clone for development
git clone <repo-url>
cd autonomous-trading-ai

# Install development dependencies  
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Code formatting
black src/
flake8 src/
```

### **Project Structure**
```
autonomous-trading-ai/
├── src/
│   ├── analysis/          # AI scoring & technical analysis
│   ├── trading/           # Trade execution & logging
│   ├── dashboard/         # Web interface
│   ├── backtesting/       # Strategy testing
│   └── utils/             # Configuration & utilities
├── config/                # Configuration files
├── data/                  # SQLite database & exports
├── models/                # ML model storage  
├── tests/                 # Unit tests
└── requirements.txt       # Python dependencies
```

---

## ⚠️ **Disclaimers**

### **Trading Risks**
- **Past performance does not guarantee future results**
- **All trading involves risk of substantial losses**
- **AI predictions are not investment advice**
- **Start with small amounts and paper trading**
- **Understand the risks before using real money**

### **Regulatory Compliance**
- **Check local regulations** for automated trading
- **Ensure proper licensing** for commercial use
- **Follow broker terms of service** for API usage
- **Maintain proper records** for tax purposes

### **System Limitations**  
- **Relies on external data sources** (API availability)
- **Market conditions change** (strategies may become ineffective)
- **Technical failures possible** (internet, power, etc.)
- **Continuously monitor and adjust** strategy parameters

---

## 📞 **Support & Community**

### **Getting Help**
- Check the troubleshooting section above
- Review logs in `logs/` directory for error details
- Test individual components using demo scripts

### **Feature Requests**
- Advanced ML models (LSTM, Transformer)  
- Additional brokers (Interactive Brokers, TD Ameritrade, E*TRADE)
- Cryptocurrency trading support
- More technical indicators and strategies
- Mobile app/notifications
- Cloud deployment options

---

## 🎉 **Success Stories**

*"The AI scoring system helped me avoid several bad trades during the market volatility. The sentiment analysis caught the negative news before it impacted the stock price."* - Beta User

*"Portfolio mode with risk management gave me confidence to scale up my trading. The dashboard makes monitoring multiple positions effortless."* - Active Trader

---

**Ready to start AI-powered trading? Run `python demo_enhanced_features.py` to see the system in action!** 🚀

---

*Last updated: October 2024 | Version 2.0 | AI-Enhanced*