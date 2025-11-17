# 🤖 Autonomous Trading Bot

A fully autonomous trading bot that uses advanced technical analysis, sentiment analysis, and risk management to execute live trades through Alpaca Markets.

## ⚠️ Important Warning

**This bot trades with REAL MONEY using live Alpaca API keys. Use at your own risk. Trading involves significant financial risk and you can lose money.**

## 🚀 Features

### 🎯 Core Trading Logic
- **Technical Analysis**: RSI, MACD, volume analysis, candlestick patterns
- **Sentiment Analysis**: News sentiment from Alpaca and NewsAPI
- **Pre-market Scanning**: Identifies high momentum opportunities
- **Autonomous Execution**: Automatically places and manages trades
- **Risk Management**: Dynamic stop-loss, take-profit, and position sizing

### 💰 Capital Management
- **Dynamic Allocation**: Uses configurable percentage of available balance
- **Position Sizing**: Calculates optimal position size based on risk
- **Daily Loss Limits**: Prevents excessive losses in a single day
- **Portfolio Limits**: Maximum number of concurrent positions

### 📊 Monitoring & Analytics
- **Web Dashboard**: Real-time portfolio and performance monitoring
- **Trade Logging**: Complete CSV logs of all trades
- **Performance Metrics**: Win rate, profit factor, Sharpe ratio, drawdown
- **Symbol Rankings**: Tracks which stocks perform best
- **Strategy Analysis**: Identifies most effective trading signals

### 🛡️ Risk Management
- **Stop Losses**: Automatic stop-loss orders on every trade
- **Trailing Stops**: Protect profits with trailing stop-loss
- **Position Limits**: Maximum exposure per position and total portfolio
- **Validation**: Multiple checks before executing any trade

## 🏗️ Architecture

```
production/
├── src/                      # Source code
│   ├── api/                  # Alpaca API client
│   ├── strategy/             # Trading strategies and analysis
│   ├── utils/               # Configuration, logging, risk management
│   ├── dashboard/           # Web dashboard
│   └── main_bot.py         # Main bot orchestrator
├── config/                  # Configuration files
├── logs/                   # Trade and performance logs
├── data/                   # Risk metrics and historical data
└── run_bot.py             # Startup script
```

## 📋 Prerequisites

1. **Alpaca Account**: Live trading account with API access
2. **Python 3.8+**: Latest Python installation
3. **Funding**: Your Alpaca account must be funded for trading

## ⚙️ Installation

1. **Clone and navigate to production directory**:
   ```bash
   cd /Users/homebase/projects/autonomous-trading-ai/production
   ```

2. **Install dependencies**:
   ```bash
   pip3 install alpaca-trade-api pandas numpy textblob flask requests
   ```

3. **Verify your API keys** are in the parent directory:
   ```bash
   cat ../api_keys.env
   ```

## 🔧 Configuration

The bot uses `config/trading_config.json` for all settings:

### Key Settings:
- **Capital Allocation**: `use_percentage` (default: 100%)
- **Risk Management**: `stop_loss_percent` (default: 5%), `take_profit_percent` (default: 15%)
- **Position Limits**: `max_positions` (default: 5), `max_daily_loss` (default: $200)
- **Strategy Parameters**: RSI thresholds, volume requirements, price ranges

## 🚀 Usage

### Start the Trading Bot
```bash
python3 run_bot.py --mode bot
```

### Start the Web Dashboard
```bash
python3 run_bot.py --mode dashboard
```
Then open http://localhost:5000 in your browser.

### Skip Pre-flight Checks (Advanced)
```bash
python3 run_bot.py --skip-checks
```

## 📊 Dashboard Features

The web dashboard provides:
- **Real-time Portfolio**: Current value, buying power, positions
- **Performance Metrics**: Win rate, P&L, Sharpe ratio, drawdown
- **Active Positions**: Current holdings with unrealized P&L
- **Recent Orders**: Trade history and order status
- **Configuration**: Ability to adjust trading parameters

## 🔍 How It Works

### 1. Market Scanning
- Scans pre-configured universe of liquid stocks
- Applies technical analysis (RSI, MACD, volume, patterns)
- Analyzes news sentiment from multiple sources
- Combines signals with confidence scoring

### 2. Trade Execution
- Validates trades against risk parameters
- Calculates optimal position size
- Places market orders with automatic stop-losses
- Tracks positions for exit conditions

### 3. Risk Management
- Monitors all positions continuously
- Applies trailing stops on profitable trades
- Enforces daily loss limits and position limits
- Records all trades for performance analysis

### 4. Learning & Adaptation
- Tracks performance by symbol and strategy
- Identifies best-performing setups
- Adjusts confidence based on historical success
- Provides recommendations for strategy improvement

## 📈 Performance Tracking

All trading data is logged to CSV files:
- **`logs/trades.csv`**: Complete trade history
- **`logs/performance.csv`**: Daily performance metrics
- **`logs/debug.log`**: Bot operation logs

## ⚠️ Risk Considerations

1. **Start Small**: Begin with minimal funding to test the system
2. **Monitor Closely**: Watch the bot's performance, especially initially
3. **Market Conditions**: Performance varies with market volatility
4. **No Guarantees**: Past performance doesn't predict future results
5. **Kill Switch**: Always be ready to stop the bot if needed

## 🛠️ Customization

### Adding New Strategies
Add new analysis methods to `src/strategy/technical_analysis.py`

### Modifying Risk Parameters
Edit `config/trading_config.json` or use the web dashboard

### Adding New Data Sources
Extend `src/strategy/sentiment_analysis.py` for additional news sources

## 🔧 Troubleshooting

### Common Issues:

**"Configuration validation failed"**
- Check that `config/trading_config.json` exists and is valid

**"Alpaca connection failed"**
- Verify API keys are correct and account is approved
- Ensure account has sufficient funding

**"No trading opportunities found"**
- Normal during low-volatility periods
- Check if market is open and scan universe is appropriate

**"Daily loss limit reached"**
- Bot will stop trading to prevent further losses
- Adjust `max_daily_loss` in configuration if needed

## 🎛️ Advanced Usage

### Running Multiple Strategies
The modular design allows running different strategies simultaneously by modifying the scan universe and parameters.

### Backtesting
Use the logging system to analyze historical performance and optimize parameters.

### Notifications
Placeholder hooks exist for SMS/email alerts - implement as needed.

## 📚 Educational Use

This bot serves as a comprehensive example of:
- Professional trading system architecture
- Risk management implementation
- Real-time data processing and decision making
- Performance tracking and analysis

## 🤝 Support

This is a production trading system. Ensure you understand the code and risks before using with real money.

## 📄 License

Use at your own risk. No warranties provided.

---

**Remember: Only invest what you can afford to lose. Trading is risky and this bot does not guarantee profits.**