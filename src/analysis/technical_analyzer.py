"""
Technical Analysis Module
Handles RSI, MACD calculations and market scanning for optimal trading opportunities
"""

import asyncio
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import yfinance as yf
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class TechnicalSignal:
    """Technical analysis signal data structure"""
    symbol: str
    signal_type: str  # 'buy', 'sell', 'hold'
    confidence: float  # 0.0 to 1.0
    rsi_value: Optional[float] = None
    macd_value: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    price: Optional[float] = None
    volume: Optional[int] = None
    timestamp: datetime = datetime.now()

@dataclass
class MarketOpportunity:
    """Market trading opportunity"""
    symbol: str
    asset_type: str  # 'stock' or 'crypto'
    entry_price: float
    target_price: float
    stop_loss: float
    confidence_score: float
    technical_signals: List[TechnicalSignal]
    strategy: str
    expiration: Optional[datetime] = None

class TechnicalAnalyzer:
    """Main technical analysis engine"""
    
    def __init__(self):
        self.rsi_period = 14
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        
    async def initialize(self):
        """Initialize the technical analyzer"""
        logger.info("Initializing Technical Analyzer...")
        # Any async initialization code here
        
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI (Relative Strength Index)"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(self, prices: pd.Series, 
                      fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        exp_fast = prices.ewm(span=fast).mean()
        exp_slow = prices.ewm(span=slow).mean()
        
        macd_line = exp_fast - exp_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    def analyze_symbol(self, symbol: str, period: str = "3mo") -> Optional[TechnicalSignal]:
        """Analyze a single symbol for technical signals"""
        try:
            # Fetch data
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            
            if data.empty:
                logger.warning(f"No data available for {symbol}")
                return None
            
            # Calculate indicators
            closes = data['Close']
            rsi = self.calculate_rsi(closes, self.rsi_period)
            macd_data = self.calculate_macd(closes, self.macd_fast, self.macd_slow, self.macd_signal)
            
            # Get latest values
            latest_rsi = rsi.iloc[-1]
            latest_macd = macd_data['macd'].iloc[-1]
            latest_signal = macd_data['signal'].iloc[-1]
            latest_histogram = macd_data['histogram'].iloc[-1]
            latest_price = closes.iloc[-1]
            latest_volume = data['Volume'].iloc[-1]
            
            # Generate signal
            signal_type, confidence = self._generate_signal(
                latest_rsi, latest_macd, latest_signal, latest_histogram
            )
            
            return TechnicalSignal(
                symbol=symbol,
                signal_type=signal_type,
                confidence=confidence,
                rsi_value=latest_rsi,
                macd_value=latest_macd,
                macd_signal=latest_signal,
                macd_histogram=latest_histogram,
                price=latest_price,
                volume=int(latest_volume)
            )
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return None
    
    def _generate_signal(self, rsi: float, macd: float, signal: float, histogram: float) -> tuple[str, float]:
        """Generate buy/sell/hold signal with confidence score"""
        signals = []
        confidence_factors = []
        
        # RSI signals
        if rsi < 30:  # Oversold
            signals.append('buy')
            confidence_factors.append(0.7)
        elif rsi > 70:  # Overbought
            signals.append('sell')
            confidence_factors.append(0.7)
        
        # MACD signals
        if macd > signal and histogram > 0:  # Bullish crossover
            signals.append('buy')
            confidence_factors.append(0.6)
        elif macd < signal and histogram < 0:  # Bearish crossover
            signals.append('sell')
            confidence_factors.append(0.6)
        
        # Determine final signal
        if not signals:
            return 'hold', 0.3
        
        # Count buy vs sell signals
        buy_signals = signals.count('buy')
        sell_signals = signals.count('sell')
        
        if buy_signals > sell_signals:
            signal_type = 'buy'
        elif sell_signals > buy_signals:
            signal_type = 'sell'
        else:
            signal_type = 'hold'
        
        # Calculate confidence
        confidence = min(sum(confidence_factors) / len(confidence_factors), 1.0)
        
        return signal_type, confidence
    
    async def scan_stocks(self, symbols: Optional[List[str]] = None) -> List[MarketOpportunity]:
        """Scan stocks for trading opportunities"""
        logger.info("Scanning stocks for opportunities...")
        
        # Default stock symbols to scan (popular stocks)
        if symbols is None:
            symbols = [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX',
                'AMD', 'INTC', 'CRM', 'UBER', 'ABNB', 'ROKU', 'PLTR', 'SNOW'
            ]
        
        opportunities = []
        
        for symbol in symbols:
            try:
                signal = self.analyze_symbol(symbol)
                if signal and signal.signal_type in ['buy', 'sell'] and signal.confidence > 0.5:
                    opportunity = self._create_stock_opportunity(signal)
                    if opportunity:
                        opportunities.append(opportunity)
            except Exception as e:
                logger.error(f"Error scanning {symbol}: {e}")
                continue
        
        # Sort by confidence score
        opportunities.sort(key=lambda x: x.confidence_score, reverse=True)
        
        logger.info(f"Found {len(opportunities)} stock opportunities")
        return opportunities[:10]  # Return top 10
    
    async def scan_crypto(self, symbols: Optional[List[str]] = None) -> List[MarketOpportunity]:
        """Scan crypto for trading opportunities"""
        logger.info("Scanning crypto for opportunities...")
        
        # Default crypto symbols to scan
        if symbols is None:
            symbols = [
                'BTC-USD', 'ETH-USD', 'ADA-USD', 'SOL-USD', 'DOT-USD', 
                'AVAX-USD', 'MATIC-USD', 'LINK-USD', 'UNI-USD', 'AAVE-USD'
            ]
        
        opportunities = []
        
        for symbol in symbols:
            try:
                signal = self.analyze_symbol(symbol)
                if signal and signal.signal_type in ['buy', 'sell'] and signal.confidence > 0.4:
                    opportunity = self._create_crypto_opportunity(signal)
                    if opportunity:
                        opportunities.append(opportunity)
            except Exception as e:
                logger.error(f"Error scanning {symbol}: {e}")
                continue
        
        # Sort by confidence score
        opportunities.sort(key=lambda x: x.confidence_score, reverse=True)
        
        logger.info(f"Found {len(opportunities)} crypto opportunities")
        return opportunities[:10]  # Return top 10
    
    def _create_stock_opportunity(self, signal: TechnicalSignal) -> Optional[MarketOpportunity]:
        """Create a stock trading opportunity from technical signal"""
        if not signal.price:
            return None
        
        if signal.signal_type == 'buy':
            target_price = signal.price * 1.15  # 15% target
            stop_loss = signal.price * 0.95     # 5% stop loss
            strategy = "RSI/MACD Momentum Buy"
        elif signal.signal_type == 'sell':
            target_price = signal.price * 0.85  # 15% target (short)
            stop_loss = signal.price * 1.05     # 5% stop loss
            strategy = "RSI/MACD Momentum Sell"
        else:
            return None
        
        return MarketOpportunity(
            symbol=signal.symbol,
            asset_type='stock',
            entry_price=signal.price,
            target_price=target_price,
            stop_loss=stop_loss,
            confidence_score=signal.confidence,
            technical_signals=[signal],
            strategy=strategy
        )
    
    def _create_crypto_opportunity(self, signal: TechnicalSignal) -> Optional[MarketOpportunity]:
        """Create a crypto trading opportunity from technical signal"""
        if not signal.price:
            return None
        
        if signal.signal_type == 'buy':
            target_price = signal.price * 1.20  # 20% target (crypto more volatile)
            stop_loss = signal.price * 0.90     # 10% stop loss
            strategy = "Crypto Momentum Buy"
        elif signal.signal_type == 'sell':
            target_price = signal.price * 0.80  # 20% target (short)
            stop_loss = signal.price * 1.10     # 10% stop loss
            strategy = "Crypto Momentum Sell"
        else:
            return None
        
        return MarketOpportunity(
            symbol=signal.symbol,
            asset_type='crypto',
            entry_price=signal.price,
            target_price=target_price,
            stop_loss=stop_loss,
            confidence_score=signal.confidence,
            technical_signals=[signal],
            strategy=strategy
        )