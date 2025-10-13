"""
AI-Powered Trade Scoring Module
Combines technical indicators with sentiment analysis to generate confidence scores
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import joblib
import os
from pathlib import Path
from src.analysis.sentiment_analyzer import SentimentScore
from src.analysis.technical_analyzer import TechnicalSignal
from src.utils.logger import setup_logger

# ML models disabled for compatibility - using manual scoring only
MODELS_AVAILABLE = False

logger = setup_logger(__name__)

@dataclass
class TradeScore:
    """AI-generated trade score with detailed breakdown"""
    symbol: str
    confidence_score: float  # 0.0 to 1.0
    signal_strength: str  # 'weak', 'moderate', 'strong', 'very_strong'
    components: Dict[str, float]  # Individual component scores
    features: Dict[str, float]  # Raw feature values used
    model_prediction: float  # Raw model output
    timestamp: datetime

class AITradeScorer:
    """
    AI TRADE SCORING ENGINE - MODIFY FOR DIFFERENT ML APPROACHES
    
    This module combines multiple data sources into a single confidence score:
    - Technical indicators (RSI, MACD, Bollinger Bands, Volume)
    - News sentiment analysis
    - Market volatility and momentum
    - Historical pattern recognition
    
    CUSTOMIZE: Adjust feature weights, add new features, modify ML model
    """
    
    def __init__(self, model_type: str = 'manual'):
        self.model_type = 'manual'  # Force manual scoring for compatibility
        self.model = None
        self.feature_importance = {}
        self.is_trained = False
        
        # Feature weights for manual scoring when ML model not available
        self.feature_weights = {
            'rsi': 0.25,
            'macd': 0.20,
            'bollinger': 0.15,
            'sentiment': 0.25,
            'volume': 0.15
        }
        
        # Model storage path
        self.model_dir = Path("models")
        self.model_dir.mkdir(exist_ok=True)
        
        # Try to load existing model
        self._load_model()
    
    def calculate_trade_score(self, 
                            symbol: str,
                            technical_signal: TechnicalSignal,
                            sentiment_score: Optional[SentimentScore] = None,
                            volume_data: Optional[Dict] = None,
                            market_data: Optional[Dict] = None) -> TradeScore:
        """
        Calculate comprehensive AI trade score
        
        MAIN SCORING LOGIC - MODIFY FEATURE EXTRACTION HERE:
        
        Args:
            symbol: Stock/crypto symbol
            technical_signal: RSI, MACD, price data
            sentiment_score: News sentiment analysis
            volume_data: Volume trends and patterns
            market_data: Additional market context
            
        Returns:
            TradeScore with confidence 0.0-1.0
        """
        try:
            # Extract features from all inputs
            features = self._extract_features(
                technical_signal, sentiment_score, volume_data, market_data
            )
            
            # Get model prediction or manual calculation
            if self.model and self.is_trained and MODELS_AVAILABLE:
                confidence_score = self._get_ml_prediction(features)
                logger.debug(f"ML model prediction for {symbol}: {confidence_score:.3f}")
            else:
                confidence_score = self._get_manual_score(features)
                logger.debug(f"Manual scoring for {symbol}: {confidence_score:.3f}")
            
            # Classify signal strength based on confidence
            signal_strength = self._classify_signal_strength(confidence_score)
            
            # Break down component contributions
            components = self._calculate_component_scores(features)
            
            return TradeScore(
                symbol=symbol,
                confidence_score=confidence_score,
                signal_strength=signal_strength,
                components=components,
                features=features,
                model_prediction=confidence_score,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error calculating trade score for {symbol}: {e}")
            # Return neutral score on error
            return TradeScore(
                symbol=symbol,
                confidence_score=0.5,
                signal_strength='weak',
                components={},
                features={},
                model_prediction=0.5,
                timestamp=datetime.now()
            )
    
    def _extract_features(self,
                         technical_signal: TechnicalSignal,
                         sentiment_score: Optional[SentimentScore],
                         volume_data: Optional[Dict],
                         market_data: Optional[Dict]) -> Dict[str, float]:
        """
        Extract ML features from all input data
        
        FEATURE ENGINEERING - ADD NEW FEATURES HERE:
        This is where you can add new technical indicators, sentiment metrics, etc.
        """
        features = {}
        
        # === TECHNICAL INDICATOR FEATURES ===
        if technical_signal:
            # RSI features
            features['rsi_value'] = technical_signal.rsi_value or 50.0
            features['rsi_oversold'] = 1.0 if (technical_signal.rsi_value or 50) < 30 else 0.0
            features['rsi_overbought'] = 1.0 if (technical_signal.rsi_value or 50) > 70 else 0.0
            features['rsi_momentum'] = self._calculate_rsi_momentum(technical_signal.rsi_value)
            
            # MACD features
            features['macd_value'] = technical_signal.macd_value or 0.0
            features['macd_signal'] = technical_signal.macd_signal or 0.0
            features['macd_histogram'] = technical_signal.macd_histogram or 0.0
            features['macd_bullish'] = 1.0 if (technical_signal.macd_histogram or 0) > 0 else 0.0
            features['macd_crossover'] = self._detect_macd_crossover(technical_signal)
            
            # Price and volatility features
            features['price'] = technical_signal.price or 0.0
            features['volume'] = float(technical_signal.volume or 0)
            
            # Technical signal confidence
            features['technical_confidence'] = technical_signal.confidence
        
        # === SENTIMENT FEATURES ===
        if sentiment_score:
            features['sentiment_score'] = sentiment_score.overall_sentiment
            features['sentiment_confidence'] = sentiment_score.confidence
            features['sentiment_article_count'] = float(sentiment_score.article_count)
            features['sentiment_bullish'] = 1.0 if sentiment_score.overall_sentiment > 0.1 else 0.0
            features['sentiment_bearish'] = 1.0 if sentiment_score.overall_sentiment < -0.1 else 0.0
            features['sentiment_sources'] = float(len(sentiment_score.sources))
        else:
            # Neutral sentiment when not available
            features.update({
                'sentiment_score': 0.0,
                'sentiment_confidence': 0.0,
                'sentiment_article_count': 0.0,
                'sentiment_bullish': 0.0,
                'sentiment_bearish': 0.0,
                'sentiment_sources': 0.0
            })
        
        # === VOLUME FEATURES ===
        if volume_data:
            features['volume_trend'] = volume_data.get('trend', 0.0)
            features['volume_spike'] = volume_data.get('spike', 0.0)
            features['relative_volume'] = volume_data.get('relative_volume', 1.0)
        else:
            features.update({
                'volume_trend': 0.0,
                'volume_spike': 0.0,
                'relative_volume': 1.0
            })
        
        # === MARKET CONTEXT FEATURES ===
        if market_data:
            features['market_regime'] = market_data.get('regime', 0.0)  # Bull/bear market
            features['volatility_regime'] = market_data.get('volatility', 0.5)
            features['correlation_risk'] = market_data.get('correlation', 0.0)
        else:
            features.update({
                'market_regime': 0.5,  # Neutral
                'volatility_regime': 0.5,
                'correlation_risk': 0.0
            })
        
        # === DERIVED FEATURES ===
        # Alignment features (when multiple indicators agree)
        features['bullish_alignment'] = self._calculate_bullish_alignment(features)
        features['bearish_alignment'] = self._calculate_bearish_alignment(features)
        features['indicator_consensus'] = self._calculate_indicator_consensus(features)
        
        return features
    
    def _get_ml_prediction(self, features: Dict[str, float]) -> float:
        """
        Get prediction from trained ML model
        
        ML MODEL PREDICTION LOGIC:
        - Uses trained LightGBM/XGBoost model
        - Returns probability of successful trade (0-1)
        - Handles missing features gracefully
        """
        try:
            # Convert features to array in correct order
            feature_array = self._features_to_array(features)
            
            if self.model_type == 'lightgbm':
                prediction = self.model.predict([feature_array])[0]
            elif self.model_type == 'xgboost':
                import xgboost as xgb
                dmatrix = xgb.DMatrix([feature_array])
                prediction = self.model.predict(dmatrix)[0]
            else:
                prediction = self._get_manual_score(features)
            
            # Ensure prediction is in [0, 1] range
            return max(0.0, min(1.0, prediction))
            
        except Exception as e:
            logger.error(f"Error getting ML prediction: {e}")
            return self._get_manual_score(features)
    
    def _get_manual_score(self, features: Dict[str, float]) -> float:
        """
        Calculate confidence score using manual rules when ML model not available
        
        MANUAL SCORING RULES - CUSTOMIZE LOGIC HERE:
        - RSI oversold/overbought conditions
        - MACD crossovers and momentum
        - Sentiment alignment with technical signals
        - Volume confirmation
        """
        score_components = []
        
        # RSI component (25% weight)
        rsi_score = self._score_rsi_component(features)
        score_components.append(rsi_score * self.feature_weights['rsi'])
        
        # MACD component (20% weight)
        macd_score = self._score_macd_component(features)
        score_components.append(macd_score * self.feature_weights['macd'])
        
        # Bollinger Bands component (15% weight) - simplified
        bollinger_score = 0.6  # Neutral when not implemented
        score_components.append(bollinger_score * self.feature_weights['bollinger'])
        
        # Sentiment component (25% weight)
        sentiment_score = self._score_sentiment_component(features)
        score_components.append(sentiment_score * self.feature_weights['sentiment'])
        
        # Volume component (15% weight)
        volume_score = self._score_volume_component(features)
        score_components.append(volume_score * self.feature_weights['volume'])
        
        # Calculate weighted average
        total_score = sum(score_components)
        
        # Apply consensus bonus (when multiple indicators align)
        consensus_bonus = features.get('indicator_consensus', 0.0) * 0.1
        total_score += consensus_bonus
        
        # Ensure score is in [0, 1] range
        return max(0.0, min(1.0, total_score))
    
    def _score_rsi_component(self, features: Dict[str, float]) -> float:
        """Score RSI component - MODIFY RSI SCORING LOGIC HERE"""
        rsi = features.get('rsi_value', 50.0)
        
        # Strong signals at extremes
        if rsi < 25 or rsi > 75:
            return 0.9
        # Moderate signals
        elif rsi < 35 or rsi > 65:
            return 0.7
        # Weak signals in neutral zone
        else:
            return 0.3
    
    def _score_macd_component(self, features: Dict[str, float]) -> float:
        """Score MACD component - MODIFY MACD SCORING LOGIC HERE"""
        macd_bullish = features.get('macd_bullish', 0.0)
        macd_crossover = features.get('macd_crossover', 0.0)
        
        if macd_crossover > 0.5:  # Strong crossover signal
            return 0.8
        elif macd_bullish > 0.5:  # Bullish MACD
            return 0.6
        else:  # Bearish or neutral
            return 0.4
    
    def _score_sentiment_component(self, features: Dict[str, float]) -> float:
        """Score sentiment component - MODIFY SENTIMENT SCORING LOGIC HERE"""
        sentiment = features.get('sentiment_score', 0.0)
        confidence = features.get('sentiment_confidence', 0.0)
        
        # Strong positive/negative sentiment with high confidence
        if abs(sentiment) > 0.3 and confidence > 0.7:
            return 0.8
        # Moderate sentiment
        elif abs(sentiment) > 0.1:
            return 0.6
        # Neutral sentiment
        else:
            return 0.5
    
    def _score_volume_component(self, features: Dict[str, float]) -> float:
        """Score volume component - MODIFY VOLUME SCORING LOGIC HERE"""
        relative_volume = features.get('relative_volume', 1.0)
        volume_spike = features.get('volume_spike', 0.0)
        
        # High volume confirmation
        if relative_volume > 2.0 or volume_spike > 0.7:
            return 0.8
        # Above average volume
        elif relative_volume > 1.5:
            return 0.6
        # Normal or low volume
        else:
            return 0.4
    
    def _calculate_rsi_momentum(self, rsi_value: Optional[float]) -> float:
        """Calculate RSI momentum - how close to extreme values"""
        if rsi_value is None:
            return 0.0
        
        # Distance from neutral (50)
        distance_from_neutral = abs(rsi_value - 50) / 50
        return distance_from_neutral
    
    def _detect_macd_crossover(self, technical_signal: TechnicalSignal) -> float:
        """Detect MACD crossover strength"""
        if not technical_signal.macd_value or not technical_signal.macd_signal:
            return 0.0
        
        # Simple crossover detection (would need historical data for proper detection)
        macd_diff = technical_signal.macd_value - technical_signal.macd_signal
        return min(abs(macd_diff) * 10, 1.0)  # Scale the difference
    
    def _calculate_bullish_alignment(self, features: Dict[str, float]) -> float:
        """Calculate how many indicators are bullish"""
        bullish_signals = 0
        total_signals = 0
        
        # RSI bullish (oversold)
        if features.get('rsi_oversold', 0.0) > 0.5:
            bullish_signals += 1
        total_signals += 1
        
        # MACD bullish
        if features.get('macd_bullish', 0.0) > 0.5:
            bullish_signals += 1
        total_signals += 1
        
        # Sentiment bullish
        if features.get('sentiment_bullish', 0.0) > 0.5:
            bullish_signals += 1
        total_signals += 1
        
        return bullish_signals / total_signals if total_signals > 0 else 0.0
    
    def _calculate_bearish_alignment(self, features: Dict[str, float]) -> float:
        """Calculate how many indicators are bearish"""
        bearish_signals = 0
        total_signals = 0
        
        # RSI bearish (overbought)
        if features.get('rsi_overbought', 0.0) > 0.5:
            bearish_signals += 1
        total_signals += 1
        
        # MACD bearish
        if features.get('macd_bullish', 0.0) < 0.5:
            bearish_signals += 1
        total_signals += 1
        
        # Sentiment bearish
        if features.get('sentiment_bearish', 0.0) > 0.5:
            bearish_signals += 1
        total_signals += 1
        
        return bearish_signals / total_signals if total_signals > 0 else 0.0
    
    def _calculate_indicator_consensus(self, features: Dict[str, float]) -> float:
        """Calculate overall indicator consensus strength"""
        bullish = self._calculate_bullish_alignment(features)
        bearish = self._calculate_bearish_alignment(features)
        
        # Strong consensus when most indicators agree
        return max(bullish, bearish)
    
    def _calculate_component_scores(self, features: Dict[str, float]) -> Dict[str, float]:
        """Break down the overall score into component contributions"""
        return {
            'rsi_score': self._score_rsi_component(features),
            'macd_score': self._score_macd_component(features),
            'sentiment_score': self._score_sentiment_component(features),
            'volume_score': self._score_volume_component(features),
            'consensus_score': features.get('indicator_consensus', 0.0)
        }
    
    def _classify_signal_strength(self, confidence_score: float) -> str:
        """
        Classify confidence score into strength categories
        
        SIGNAL STRENGTH THRESHOLDS - MODIFY HERE:
        """
        if confidence_score >= 0.8:
            return 'very_strong'
        elif confidence_score >= 0.7:
            return 'strong' 
        elif confidence_score >= 0.6:
            return 'moderate'
        else:
            return 'weak'
    
    def _features_to_array(self, features: Dict[str, float]) -> List[float]:
        """Convert features dict to array for ML model"""
        # Define expected feature order (would be saved with trained model)
        expected_features = [
            'rsi_value', 'rsi_oversold', 'rsi_overbought', 'rsi_momentum',
            'macd_value', 'macd_signal', 'macd_histogram', 'macd_bullish', 'macd_crossover',
            'sentiment_score', 'sentiment_confidence', 'sentiment_article_count',
            'volume_trend', 'volume_spike', 'relative_volume',
            'bullish_alignment', 'bearish_alignment', 'indicator_consensus'
        ]
        
        return [features.get(feature, 0.0) for feature in expected_features]
    
    def _load_model(self):
        """Load trained ML model if available"""
        model_path = self.model_dir / f"trade_scorer_{self.model_type}.joblib"
        
        if model_path.exists() and MODELS_AVAILABLE:
            try:
                self.model = joblib.load(model_path)
                self.is_trained = True
                logger.info(f"Loaded trained {self.model_type} model from {model_path}")
            except Exception as e:
                logger.warning(f"Failed to load model: {e}")
                self.is_trained = False
        else:
            logger.info(f"No trained model found at {model_path}")
            self.is_trained = False
    
    def save_model(self):
        """Save trained model to disk"""
        if self.model:
            model_path = self.model_dir / f"trade_scorer_{self.model_type}.joblib"
            joblib.dump(self.model, model_path)
            logger.info(f"Saved model to {model_path}")
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from trained model"""
        if not self.model or not self.is_trained:
            return {}
        
        try:
            if self.model_type == 'lightgbm':
                importances = self.model.feature_importances_
            elif self.model_type == 'xgboost':
                importances = self.model.feature_importances_
            else:
                return {}
            
            feature_names = [
                'rsi_value', 'rsi_oversold', 'rsi_overbought', 'rsi_momentum',
                'macd_value', 'macd_signal', 'macd_histogram', 'macd_bullish', 'macd_crossover',
                'sentiment_score', 'sentiment_confidence', 'sentiment_article_count',
                'volume_trend', 'volume_spike', 'relative_volume',
                'bullish_alignment', 'bearish_alignment', 'indicator_consensus'
            ]
            
            return dict(zip(feature_names, importances))
            
        except Exception as e:
            logger.error(f"Error getting feature importance: {e}")
            return {}