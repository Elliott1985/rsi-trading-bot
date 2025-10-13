"""
Advanced Technical Indicators Module
Implements EMA crossovers, ATR, VWAP, Choppiness Index, and multi-timeframe analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import yfinance as yf
from datetime import datetime, timedelta
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class AdvancedIndicators:
    """Container for advanced technical indicators"""
    ema_fast: Optional[pd.Series] = None
    ema_slow: Optional[pd.Series] = None
    ema_crossover: Optional[str] = None  # 'bullish', 'bearish', 'neutral'
    atr: Optional[pd.Series] = None
    atr_stop_loss: Optional[float] = None
    vwap: Optional[pd.Series] = None
    vwap_signal: Optional[str] = None  # 'above', 'below', 'neutral'
    choppiness: Optional[pd.Series] = None
    is_choppy: Optional[bool] = None
    multi_timeframe_bias: Optional[str] = None  # 'bullish', 'bearish', 'neutral'
    bollinger_bands: Optional[Dict[str, pd.Series]] = None
    volume_profile: Optional[Dict] = None

class AdvancedIndicatorsCalculator:
    """
    ADVANCED TECHNICAL INDICATORS - ADD NEW INDICATORS HERE
    
    This module provides sophisticated technical analysis beyond basic RSI/MACD:
    - EMA Crossovers (9/21, 5/20, custom periods)
    - ATR for dynamic stop losses
    - VWAP for intraday bias
    - Choppiness Index to avoid sideways markets
    - Multi-timeframe confirmation
    - Bollinger Bands with squeeze detection
    - Volume Profile analysis
    
    CUSTOMIZE: Add new indicators, modify parameters, adjust timeframes
    """
    
    def __init__(self):
        self.ema_fast_default = 9
        self.ema_slow_default = 21
        self.atr_period_default = 14
        self.atr_multiplier_default = 2.0
        self.choppiness_period_default = 14
        self.choppiness_threshold_default = 61.8
    
    def calculate_all_indicators(self, 
                               symbol: str,
                               period: str = '3mo',
                               ema_fast: int = 9,
                               ema_slow: int = 21,
                               atr_period: int = 14,
                               atr_multiplier: float = 2.0) -> Optional[AdvancedIndicators]:
        """
        Calculate all advanced indicators for a symbol
        
        MAIN CALCULATION ENTRY POINT - MODIFY TO ADD NEW INDICATORS:
        
        Args:
            symbol: Stock/crypto symbol
            period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            ema_fast: Fast EMA period
            ema_slow: Slow EMA period  
            atr_period: ATR calculation period
            atr_multiplier: ATR multiplier for stop loss
            
        Returns:
            AdvancedIndicators object with all calculated values
        """
        try:
            # Fetch market data
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            
            if data.empty:
                logger.warning(f"No data available for {symbol}")
                return None
            
            # Calculate all indicators
            indicators = AdvancedIndicators()
            
            # EMA Crossovers
            indicators.ema_fast = self.calculate_ema(data['Close'], ema_fast)
            indicators.ema_slow = self.calculate_ema(data['Close'], ema_slow)
            indicators.ema_crossover = self.detect_ema_crossover(
                indicators.ema_fast, indicators.ema_slow
            )
            
            # ATR and dynamic stop loss
            indicators.atr = self.calculate_atr(data, atr_period)
            indicators.atr_stop_loss = self.calculate_atr_stop_loss(
                data['Close'].iloc[-1], indicators.atr.iloc[-1], atr_multiplier
            )
            
            # VWAP
            indicators.vwap = self.calculate_vwap(data)
            indicators.vwap_signal = self.get_vwap_signal(data['Close'], indicators.vwap)
            
            # Choppiness Index
            indicators.choppiness = self.calculate_choppiness_index(data, self.choppiness_period_default)
            indicators.is_choppy = self.is_market_choppy(indicators.choppiness)
            
            # Bollinger Bands with squeeze detection
            indicators.bollinger_bands = self.calculate_bollinger_bands_advanced(data['Close'])
            
            # Volume Profile
            indicators.volume_profile = self.calculate_volume_profile(data)
            
            # Multi-timeframe analysis (if enabled)
            indicators.multi_timeframe_bias = self.get_multi_timeframe_bias(symbol)
            
            logger.debug(f"Calculated advanced indicators for {symbol}")
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating advanced indicators for {symbol}: {e}")
            return None
    
    def calculate_ema(self, prices: pd.Series, period: int) -> pd.Series:
        """
        Calculate Exponential Moving Average
        
        EMA CALCULATION - MODIFY FOR DIFFERENT SMOOTHING:
        - More responsive than SMA
        - Good for trend following
        - Popular periods: 5, 9, 12, 21, 50, 200
        """
        return prices.ewm(span=period, adjust=False).mean()
    
    def detect_ema_crossover(self, ema_fast: pd.Series, ema_slow: pd.Series) -> str:
        """
        Detect EMA crossover signals
        
        CROSSOVER DETECTION LOGIC - MODIFY FOR SENSITIVITY:
        - Bullish: Fast EMA crosses above Slow EMA
        - Bearish: Fast EMA crosses below Slow EMA  
        - Uses last few periods to confirm trend
        """
        if len(ema_fast) < 3 or len(ema_slow) < 3:
            return 'neutral'
        
        # Current and previous values
        fast_current = ema_fast.iloc[-1]
        fast_prev = ema_fast.iloc[-2]
        slow_current = ema_slow.iloc[-1]
        slow_prev = ema_slow.iloc[-2]
        
        # Crossover detection
        if fast_prev <= slow_prev and fast_current > slow_current:
            return 'bullish'
        elif fast_prev >= slow_prev and fast_current < slow_current:
            return 'bearish'
        elif fast_current > slow_current:
            return 'bullish_trend'  # Above but no recent cross
        elif fast_current < slow_current:
            return 'bearish_trend'  # Below but no recent cross
        else:
            return 'neutral'
    
    def calculate_atr(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calculate Average True Range (ATR)
        
        ATR CALCULATION - MEASURES VOLATILITY:
        - High ATR = High volatility
        - Low ATR = Low volatility
        - Used for position sizing and stop losses
        """
        high = data['High']
        low = data['Low']
        close = data['Close']
        
        # Calculate True Range components
        tr1 = high - low  # Current high - current low
        tr2 = abs(high - close.shift(1))  # Current high - previous close
        tr3 = abs(low - close.shift(1))   # Current low - previous close
        
        # True Range is the maximum of the three
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # ATR is the moving average of True Range
        atr = true_range.ewm(span=period, adjust=False).mean()
        
        return atr
    
    def calculate_atr_stop_loss(self, current_price: float, current_atr: float, multiplier: float = 2.0) -> float:
        """
        Calculate dynamic stop loss using ATR
        
        ATR STOP LOSS LOGIC - MODIFY MULTIPLIER FOR RISK:
        - Multiplier 1.0 = Tight stops (more trades, more whipsaws)
        - Multiplier 2.0 = Balanced (default)
        - Multiplier 3.0 = Loose stops (fewer trades, ride trends)
        """
        return current_price - (current_atr * multiplier)
    
    def calculate_vwap(self, data: pd.DataFrame) -> pd.Series:
        """
        Calculate Volume Weighted Average Price (VWAP)
        
        VWAP CALCULATION - INTRADAY BIAS INDICATOR:
        - Price above VWAP = Bullish bias
        - Price below VWAP = Bearish bias
        - Institutional trading benchmark
        """
        typical_price = (data['High'] + data['Low'] + data['Close']) / 3
        volume = data['Volume']
        
        # Cumulative sums
        cum_vol = volume.cumsum()
        cum_price_vol = (typical_price * volume).cumsum()
        
        # VWAP calculation
        vwap = cum_price_vol / cum_vol
        
        return vwap
    
    def get_vwap_signal(self, prices: pd.Series, vwap: pd.Series) -> str:
        """
        Determine VWAP signal
        
        VWAP SIGNAL LOGIC - MODIFY FOR SENSITIVITY:
        """
        if len(prices) < 1 or len(vwap) < 1:
            return 'neutral'
        
        current_price = prices.iloc[-1]
        current_vwap = vwap.iloc[-1]
        
        # Price relative to VWAP
        if current_price > current_vwap * 1.002:  # 0.2% above
            return 'bullish'
        elif current_price < current_vwap * 0.998:  # 0.2% below
            return 'bearish'
        else:
            return 'neutral'
    
    def calculate_choppiness_index(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calculate Choppiness Index
        
        CHOPPINESS INDEX - MEASURES MARKET DIRECTION:
        - Values 0-100
        - Above 61.8 = Choppy/sideways market (avoid trading)
        - Below 38.2 = Trending market (good for trading)
        - Between = Neutral
        """
        high = data['High']
        low = data['Low']
        close = data['Close']
        
        # True Range calculation
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # ATR for period
        atr_sum = true_range.rolling(window=period).sum()
        
        # High-Low range for period
        high_max = high.rolling(window=period).max()
        low_min = low.rolling(window=period).min()
        range_sum = high_max - low_min
        
        # Choppiness Index calculation
        choppiness = 100 * np.log10(atr_sum / range_sum) / np.log10(period)
        
        return choppiness
    
    def is_market_choppy(self, choppiness: pd.Series, threshold: float = 61.8) -> bool:
        """
        Determine if market is in choppy/sideways mode
        
        CHOPPINESS THRESHOLD - MODIFY FOR TRADING STYLE:
        - Conservative: 50.0 (avoid more potential chop)
        - Balanced: 61.8 (default, golden ratio)
        - Aggressive: 70.0 (trade through more chop)
        """
        if len(choppiness) < 1:
            return False
        
        current_choppiness = choppiness.iloc[-1]
        return current_choppiness > threshold
    
    def calculate_bollinger_bands_advanced(self, prices: pd.Series, period: int = 20, std_dev: float = 2.0) -> Dict[str, pd.Series]:
        """
        Calculate Bollinger Bands with squeeze detection
        
        BOLLINGER BANDS - VOLATILITY AND MEAN REVERSION:
        - Upper/Lower bands show volatility
        - Squeeze = Bands contracting (low volatility, breakout coming)
        - Expansion = Bands expanding (high volatility, trend in motion)
        """
        # Moving average (middle band)
        middle = prices.rolling(window=period).mean()
        
        # Standard deviation
        std = prices.rolling(window=period).std()
        
        # Upper and lower bands
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        
        # Band width (for squeeze detection)
        band_width = (upper - lower) / middle
        
        # Squeeze detection (when bands are contracting)
        squeeze_threshold = band_width.rolling(window=20).mean()
        is_squeeze = band_width < squeeze_threshold * 0.8
        
        return {
            'upper': upper,
            'middle': middle,
            'lower': lower,
            'band_width': band_width,
            'is_squeeze': is_squeeze
        }
    
    def calculate_volume_profile(self, data: pd.DataFrame) -> Dict:
        """
        Calculate basic volume profile analysis
        
        VOLUME PROFILE - WHERE MOST TRADING OCCURRED:
        - High volume areas = Support/Resistance
        - Low volume areas = Price likely to move through quickly
        - POC (Point of Control) = Highest volume price level
        """
        try:
            # Create price bins
            price_range = data['High'].max() - data['Low'].min()
            num_bins = 50
            bin_size = price_range / num_bins
            
            # Calculate volume at each price level
            volume_profile = {}
            poc_price = 0.0
            poc_volume = 0
            
            for i, row in data.iterrows():
                typical_price = (row['High'] + row['Low'] + row['Close']) / 3
                bin_level = int((typical_price - data['Low'].min()) / bin_size)
                
                if bin_level in volume_profile:
                    volume_profile[bin_level] += row['Volume']
                else:
                    volume_profile[bin_level] = row['Volume']
                
                # Track Point of Control (highest volume)
                if volume_profile[bin_level] > poc_volume:
                    poc_volume = volume_profile[bin_level]
                    poc_price = data['Low'].min() + (bin_level * bin_size)
            
            return {
                'poc_price': poc_price,
                'poc_volume': poc_volume,
                'volume_distribution': volume_profile,
                'total_volume': data['Volume'].sum()
            }
            
        except Exception as e:
            logger.error(f"Error calculating volume profile: {e}")
            return {'poc_price': 0.0, 'poc_volume': 0, 'volume_distribution': {}, 'total_volume': 0}
    
    def get_multi_timeframe_bias(self, symbol: str) -> str:
        """
        Get multi-timeframe trend bias
        
        MULTI-TIMEFRAME ANALYSIS - CONFIRM TRADES ACROSS TIMEFRAMES:
        - Daily trend for overall direction
        - Shorter timeframe for entry timing
        - Alignment = Stronger signals
        """
        try:
            # Get daily data for longer-term trend
            ticker = yf.Ticker(symbol)
            daily_data = ticker.history(period='3mo', interval='1d')
            
            if daily_data.empty:
                return 'neutral'
            
            # Calculate trend on daily timeframe
            daily_ema_fast = self.calculate_ema(daily_data['Close'], 9)
            daily_ema_slow = self.calculate_ema(daily_data['Close'], 21)
            daily_trend = self.detect_ema_crossover(daily_ema_fast, daily_ema_slow)
            
            # For intraday confirmation, we'd need intraday data
            # For now, return the daily bias
            if 'bullish' in daily_trend:
                return 'bullish'
            elif 'bearish' in daily_trend:
                return 'bearish'
            else:
                return 'neutral'
                
        except Exception as e:
            logger.debug(f"Multi-timeframe analysis failed for {symbol}: {e}")
            return 'neutral'
    
    def get_indicator_summary(self, indicators: AdvancedIndicators) -> Dict[str, str]:
        """
        Get human-readable summary of all indicators
        
        INDICATOR SUMMARY - MODIFY FOR DIFFERENT INTERPRETATIONS:
        """
        summary = {}
        
        if indicators.ema_crossover:
            summary['EMA_Trend'] = indicators.ema_crossover
        
        if indicators.vwap_signal:
            summary['VWAP_Bias'] = indicators.vwap_signal
        
        if indicators.is_choppy is not None:
            summary['Market_Condition'] = 'Choppy' if indicators.is_choppy else 'Trending'
        
        if indicators.multi_timeframe_bias:
            summary['Higher_TF_Bias'] = indicators.multi_timeframe_bias
        
        if indicators.bollinger_bands and 'is_squeeze' in indicators.bollinger_bands:
            is_squeeze = indicators.bollinger_bands['is_squeeze'].iloc[-1] if len(indicators.bollinger_bands['is_squeeze']) > 0 else False
            summary['Bollinger_State'] = 'Squeeze' if is_squeeze else 'Expansion'
        
        return summary
    
    def calculate_composite_signal(self, indicators: AdvancedIndicators) -> Tuple[str, float]:
        """
        Calculate composite signal strength from all indicators
        
        COMPOSITE SIGNAL LOGIC - MODIFY WEIGHTS FOR DIFFERENT STRATEGIES:
        - EMA crossover: 30% weight
        - VWAP bias: 25% weight  
        - Choppiness filter: 20% weight (reduces signal if choppy)
        - Multi-timeframe: 25% weight
        """
        signals = []
        weights = []
        
        # EMA crossover signal (30% weight)
        if indicators.ema_crossover:
            if 'bullish' in indicators.ema_crossover:
                signals.append(1.0)
            elif 'bearish' in indicators.ema_crossover:
                signals.append(-1.0)
            else:
                signals.append(0.0)
            weights.append(0.30)
        
        # VWAP signal (25% weight)
        if indicators.vwap_signal:
            if indicators.vwap_signal == 'bullish':
                signals.append(0.8)
            elif indicators.vwap_signal == 'bearish':
                signals.append(-0.8)
            else:
                signals.append(0.0)
            weights.append(0.25)
        
        # Multi-timeframe bias (25% weight)
        if indicators.multi_timeframe_bias:
            if indicators.multi_timeframe_bias == 'bullish':
                signals.append(0.7)
            elif indicators.multi_timeframe_bias == 'bearish':
                signals.append(-0.7)
            else:
                signals.append(0.0)
            weights.append(0.25)
        
        # Choppiness filter (20% weight - reduces signal strength if choppy)
        chop_weight = 0.20
        if indicators.is_choppy:
            # Reduce all signals if market is choppy
            signals = [s * 0.5 for s in signals]  # Reduce signal strength by 50%
        weights.append(chop_weight)
        
        if not signals:
            return 'neutral', 0.0
        
        # Calculate weighted average
        weighted_signal = sum(s * w for s, w in zip(signals, weights)) / sum(weights)
        
        # Classify signal
        if weighted_signal > 0.3:
            signal_type = 'bullish'
        elif weighted_signal < -0.3:
            signal_type = 'bearish'
        else:
            signal_type = 'neutral'
        
        # Signal strength (0.0 to 1.0)
        signal_strength = min(abs(weighted_signal), 1.0)
        
        return signal_type, signal_strength