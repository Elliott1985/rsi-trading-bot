# Autonomous Trading AI 🤖📈

A fully autonomous trading assistant that connects to E*TRADE and Crypto.com accounts to analyze markets, identify optimal trades, and execute trades based on technical indicators and AI-driven strategies.

## Features

### Phase 1: Market Analysis & Recommendations
- ✅ RSI and MACD technical analysis
- ✅ Pre-market scanning for stocks and crypto
- ✅ Budget-based trade suggestions
- ✅ Options strategies (calls/puts) with entry/exit recommendations
- ✅ Real-time market data integration

### Phase 2: Trade Management (Coming Soon)
- 🔄 Real-time trade tracking
- 🔄 Automated exit signals based on technical indicators
- 🔄 Portfolio risk management
- 🔄 News sentiment analysis integration

### Phase 3: Full Automation (Future)
- ⏳ E*TRADE API integration for automated stock/options trading
- ⏳ Crypto.com API integration for automated crypto trading
- ⏳ Fully autonomous trading with preset risk parameters
- ⏳ Advanced machine learning trade optimization

## Project Structure

```
autonomous-trading-ai/
├── app.py                      # Main application entry point
├── requirements.txt            # Python dependencies
├── config/                     # Configuration files
│   ├── trading_config.yaml    # Trading parameters
│   └── api_keys.env           # API credentials (git-ignored)
├── src/
│   ├── analysis/              # Technical analysis modules
│   │   ├── technical_analyzer.py
│   │   ├── rsi_analyzer.py
│   │   └── macd_analyzer.py
│   ├── trading/               # Trading strategy modules
│   │   ├── portfolio_manager.py
│   │   ├── options_strategies.py
│   │   └── crypto_strategies.py
│   ├── brokers/               # Broker API integrations
│   │   ├── etrade_client.py
│   │   └── crypto_com_client.py
│   ├── notifications/         # Alert and notification systems
│   │   └── notifier.py
│   └── utils/                 # Utilities and helpers
│       ├── config.py
│       ├── logger.py
│       └── market_data.py
├── tests/                     # Unit and integration tests
├── logs/                      # Application logs
└── docs/                      # Documentation
```

## Quick Start

### 1. Environment Setup
```bash
# Clone and navigate to project
cd autonomous-trading-ai

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration
```bash
# Copy example config
cp config/trading_config.example.yaml config/trading_config.yaml

# Set up API keys (create this file)
touch config/api_keys.env
```

Add your API keys to `config/api_keys.env`:
```env
# Market Data
ALPHA_VANTAGE_API_KEY=your_key_here
FINNHUB_API_KEY=your_key_here

# Brokers (for future phases)
ETRADE_CLIENT_KEY=your_key_here
ETRADE_CLIENT_SECRET=your_key_here
CRYPTO_COM_API_KEY=your_key_here
CRYPTO_COM_SECRET=your_key_here

# Notifications
SLACK_WEBHOOK_URL=your_webhook_here
TWILIO_SID=your_sid_here
TWILIO_AUTH_TOKEN=your_token_here
```

### 3. Run the Bot
```bash
# Run market scan
python app.py scan

# Analyze trades with budget
python app.py analyze --budget 1000 --profit-goal 15

# Monitor existing positions (coming soon)
python app.py monitor
```

## Technical Analysis Features

### RSI (Relative Strength Index)
- Identifies overbought/oversold conditions
- Configurable periods (default: 14)
- Generates buy/sell signals

### MACD (Moving Average Convergence Divergence)
- Trend following momentum indicator
- Signal line crossovers for entry/exit
- Histogram analysis for momentum shifts

### Pre-Market Scanning
- Scans top gainers/losers
- Volume analysis
- Gap analysis for breakout opportunities

## Trading Strategies

### Options Strategies
- **Momentum Calls**: Based on RSI oversold + MACD bullish crossover
- **Momentum Puts**: Based on RSI overbought + MACD bearish crossover
- **Straddles**: For high volatility plays
- **Iron Condors**: For range-bound markets

### Crypto Strategies
- **Trend Following**: Multi-timeframe analysis
- **Mean Reversion**: RSI-based entries
- **Breakout Trading**: Volume + momentum confirmation

## Risk Management
- Position sizing based on portfolio percentage
- Stop-loss and take-profit automation
- Maximum daily loss limits
- Correlation analysis to avoid over-concentration

## Development

### Running Tests
```bash
pytest tests/ -v
```

### Code Formatting
```bash
black src/ tests/
flake8 src/ tests/
```

### Type Checking
```bash
mypy src/
```

## Roadmap

- [x] **Phase 1**: Technical analysis and recommendations
- [ ] **Phase 2**: Paper trading and backtesting
- [ ] **Phase 3**: Live trading integration
- [ ] **Phase 4**: Machine learning optimization
- [ ] **Phase 5**: Multi-account management

## Disclaimer

⚠️ **Important**: This software is for educational and research purposes. Trading involves significant risk of financial loss. Always:
- Test strategies thoroughly before using real money
- Never risk more than you can afford to lose  
- Understand the risks of algorithmic trading
- Comply with all applicable regulations

## License

This project is private and proprietary. All rights reserved.