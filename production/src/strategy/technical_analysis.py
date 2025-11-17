#!/usr/bin/env python3
"""
Technical Analysis Module
Implements RSI, MACD, volume analysis, and candlestick patterns for trading signals.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import logging

class SignalType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class TrendDirection(Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"

@dataclass
class TechnicalSignal:
    """Technical analysis signal result"""
    symbol: str
    signal_type: SignalType
    strength: float  # 0-1, 1 being strongest
    price: float
    rsi: float
    macd_signal: str
    volume_surge: bool
    momentum_score: float
    candlestick_pattern: str
    trend_direction: TrendDirection
    confidence: float
    reasons: List[str]

class TechnicalAnalyzer:
    """Advanced technical analysis for trading signals"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        except Exception as e:
            self.logger.error(f"RSI calculation error: {e}")
            return pd.Series([50] * len(prices))
    
    def calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """Calculate MACD indicator"""
        try:
            ema_fast = prices.ewm(span=fast).mean()
            ema_slow = prices.ewm(span=slow).mean()
            
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal).mean()
            histogram = macd_line - signal_line
            
            return {
                'macd': macd_line,
                'signal': signal_line,
                'histogram': histogram
            }
        except Exception as e:
            self.logger.error(f"MACD calculation error: {e}")
            return {'macd': pd.Series([0] * len(prices)), 
                   'signal': pd.Series([0] * len(prices)), 
                   'histogram': pd.Series([0] * len(prices))}
    
    def calculate_volume_surge(self, volumes: pd.Series, lookback: int = 20) -> pd.Series:
        """Detect volume surges compared to average"""
        try:
            avg_volume = volumes.rolling(window=lookback).mean()
            volume_ratio = volumes / avg_volume
            return volume_ratio > 1.5  # 50% above average
        except Exception as e:
            self.logger.error(f"Volume surge calculation error: {e}")
            return pd.Series([False] * len(volumes))
    
    def calculate_momentum(self, prices: pd.Series, period: int = 20) -> pd.Series:
        """Calculate price momentum"""
        try:
            return (prices / prices.shift(period) - 1) * 100
        except Exception as e:
            self.logger.error(f"Momentum calculation error: {e}")
            return pd.Series([0] * len(prices))
    
    def detect_candlestick_patterns(self, df: pd.DataFrame) -> List[str]:
        """Detect basic candlestick patterns"""
        try:
            patterns = []
            
            if len(df) < 3:
                return patterns
            
            # Get last few candles
            current = df.iloc[-1]
            prev = df.iloc[-2]
            
            # Calculate candle properties
            body_size = abs(current['close'] - current['open'])
            upper_shadow = current['high'] - max(current['close'], current['open'])
            lower_shadow = min(current['close'], current['open']) - current['low']
            
            # Doji pattern
            if body_size < (current['high'] - current['low']) * 0.1:
                patterns.append("DOJI")
            
            # Hammer/Hanging Man
            if (lower_shadow > body_size * 2 and 
                upper_shadow < body_size * 0.5):
                if current['close'] > current['open']:
                    patterns.append("HAMMER")
                else:
                    patterns.append("HANGING_MAN")
            
            # Engulfing patterns
            if len(df) >= 2:
                if (current['close'] > current['open'] and 
                    prev['close'] < prev['open'] and
                    current['close'] > prev['open'] and
                    current['open'] < prev['close']):
                    patterns.append("BULLISH_ENGULFING")
                
                elif (current['close'] < current['open'] and 
                      prev['close'] > prev['open'] and
                      current['close'] < prev['open'] and
                      current['open'] > prev['close']):
                    patterns.append("BEARISH_ENGULFING")
            
            return patterns if patterns else ["NONE"]
            
        except Exception as e:
            self.logger.error(f"Candlestick pattern detection error: {e}")
            return ["NONE"]
    
    def determine_trend(self, prices: pd.Series, short_ma: int = 10, long_ma: int = 20) -> TrendDirection:
        """Determine overall trend direction"""
        try:
            if len(prices) < long_ma:
                return TrendDirection.NEUTRAL
            
            short_sma = prices.rolling(window=short_ma).mean().iloc[-1]
            long_sma = prices.rolling(window=long_ma).mean().iloc[-1]
            
            if short_sma > long_sma * 1.01:  # 1% buffer
                return TrendDirection.BULLISH
            elif short_sma < long_sma * 0.99:
                return TrendDirection.BEARISH
            else:
                return TrendDirection.NEUTRAL
                
        except Exception as e:
            self.logger.error(f"Trend determination error: {e}")
            return TrendDirection.NEUTRAL
    
    def analyze_stock(self, symbol: str, df: pd.DataFrame, config) -> Optional[TechnicalSignal]:
        """Comprehensive technical analysis for a stock"""
        try:
            if len(df) < 10:  # Reduced requirement for testing
                return None
            
            # Calculate all indicators with fallback for limited data
            try:
                rsi = self.calculate_rsi(df['close'])
                macd_data = self.calculate_macd(df['close'])
                volume_surge = self.calculate_volume_surge(df['volume']) if 'volume' in df.columns else pd.Series([False] * len(df))
                momentum = self.calculate_momentum(df['close'], min(config.momentum_lookback, len(df) - 1))
            except Exception as calc_error:
                self.logger.warning(f"Indicator calculation error for {symbol}: {calc_error}")
                # Create fallback simple indicators
                rsi = pd.Series([50] * len(df))  # Neutral RSI
                macd_data = {'macd': pd.Series([0] * len(df)), 'signal': pd.Series([0] * len(df)), 'histogram': pd.Series([0] * len(df))}
                volume_surge = pd.Series([False] * len(df))
                momentum = pd.Series([0] * len(df))
            
            # Get latest values
            current_price = df['close'].iloc[-1]
            current_rsi = rsi.iloc[-1]
            current_macd = macd_data['macd'].iloc[-1]
            current_signal = macd_data['signal'].iloc[-1]
            current_histogram = macd_data['histogram'].iloc[-1]
            current_volume_surge = volume_surge.iloc[-1]
            current_momentum = momentum.iloc[-1]
            
            # Detect patterns
            patterns = self.detect_candlestick_patterns(df)
            trend = self.determine_trend(df['close'])
            
            # Generate trading signal
            signal_type = SignalType.HOLD
            strength = 0.0
            reasons = []
            
            # RSI signals
            if current_rsi < config.rsi_oversold:
                if signal_type != SignalType.SELL:
                    signal_type = SignalType.BUY
                    strength += 0.3
                    reasons.append(f"RSI oversold ({current_rsi:.1f})")
            
            elif current_rsi > config.rsi_overbought:
                if signal_type != SignalType.BUY:
                    signal_type = SignalType.SELL
                    strength += 0.3
                    reasons.append(f"RSI overbought ({current_rsi:.1f})")
            
            # MACD signals
            macd_signal = "NEUTRAL"
            if current_macd > current_signal and macd_data['macd'].iloc[-2] <= macd_data['signal'].iloc[-2]:
                macd_signal = "BULLISH_CROSSOVER"
                if signal_type != SignalType.SELL:
                    signal_type = SignalType.BUY
                    strength += 0.25
                    reasons.append("MACD bullish crossover")
            
            elif current_macd < current_signal and macd_data['macd'].iloc[-2] >= macd_data['signal'].iloc[-2]:
                macd_signal = "BEARISH_CROSSOVER"
                if signal_type != SignalType.BUY:
                    signal_type = SignalType.SELL
                    strength += 0.25
                    reasons.append("MACD bearish crossover")
            
            # Volume confirmation
            if current_volume_surge:
                strength += 0.15
                reasons.append("High volume surge")
            
            # Momentum confirmation
            momentum_score = min(abs(current_momentum) / 5.0, 1.0)  # Normalize to 0-1
            if current_momentum > 2:
                if signal_type == SignalType.BUY:
                    strength += 0.2
                    reasons.append(f"Strong upward momentum ({current_momentum:.1f}%)")
            elif current_momentum < -2:
                if signal_type == SignalType.SELL:
                    strength += 0.2
                    reasons.append(f"Strong downward momentum ({current_momentum:.1f}%)")
            
            # Candlestick pattern confirmation
            bullish_patterns = ["HAMMER", "BULLISH_ENGULFING"]
            bearish_patterns = ["HANGING_MAN", "BEARISH_ENGULFING"]
            
            pattern_str = ", ".join(patterns)
            if any(p in patterns for p in bullish_patterns):
                if signal_type == SignalType.BUY:
                    strength += 0.1
                    reasons.append(f"Bullish pattern: {pattern_str}")
            elif any(p in patterns for p in bearish_patterns):
                if signal_type == SignalType.SELL:
                    strength += 0.1
                    reasons.append(f"Bearish pattern: {pattern_str}")
            
            # Calculate confidence with fallback for low data
            confidence = min(strength, 1.0)
            
            # Fallback: Simple momentum-based signal for weak signals with limited data
            if confidence < 0.3 and len(df) >= 5:
                recent_change = (current_price / df['close'].iloc[0] - 1) * 100
                if abs(recent_change) > 3:  # 3% move threshold
                    signal_type = SignalType.BUY if recent_change > 0 else SignalType.SELL
                    confidence = min(abs(recent_change) / 15, 0.55)  # Cap at 0.55 for simple signals
                    strength = confidence
                    reasons.append(f"Simple momentum: {recent_change:.1f}% move over {len(df)} days")
                    self.logger.info(f"Generated fallback momentum signal for {symbol}: {signal_type} with {confidence:.2f} confidence")
            
            # Price filters
            if current_price < config.min_price or current_price > config.max_price:
                return None
            
            return TechnicalSignal(
                symbol=symbol,
                signal_type=signal_type,
                strength=strength,
                price=current_price,
                rsi=current_rsi,
                macd_signal=macd_signal,
                volume_surge=current_volume_surge,
                momentum_score=momentum_score,
                candlestick_pattern=pattern_str,
                trend_direction=trend,
                confidence=confidence,
                reasons=reasons
            )
            
        except Exception as e:
            self.logger.error(f"Analysis error for {symbol}: {e}")
            return None
    
    def scan_universe(self, data_provider, symbols: List[str], config) -> List[TechnicalSignal]:
        """Scan entire universe for trading signals"""
        signals = []
        
        for symbol in symbols:
            try:
                # Get market data
                df = data_provider.get_bars(symbol, timeframe='1Day', limit=100)
                if df is not None and not df.empty:
                    signal = self.analyze_stock(symbol, df, config)
                    if signal and signal.confidence > 0.4:  # Minimum confidence threshold
                        signals.append(signal)
                        
            except Exception as e:
                self.logger.error(f"Failed to scan {symbol}: {e}")
                continue
        
        # Sort by confidence
        return sorted(signals, key=lambda x: x.confidence, reverse=True)