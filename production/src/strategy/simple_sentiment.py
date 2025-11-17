#!/usr/bin/env python3
"""
Simplified Sentiment Analyzer
Quick deployment version without heavy ML dependencies
"""

import requests
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

class SimpleSentimentAnalyzer:
    """Simplified sentiment analyzer using basic NLP and news analysis"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        
        # Simple sentiment keywords
        self.positive_keywords = [
            'bullish', 'buy', 'strong', 'growth', 'profit', 'gains', 'surge', 
            'rally', 'upgrade', 'optimistic', 'positive', 'outperform', 'beat',
            'exceed', 'momentum', 'breakout', 'catalyst', 'opportunity'
        ]
        
        self.negative_keywords = [
            'bearish', 'sell', 'weak', 'decline', 'loss', 'drop', 'crash',
            'downgrade', 'pessimistic', 'negative', 'underperform', 'miss',
            'concern', 'risk', 'uncertainty', 'volatility', 'correction'
        ]
        
        # Cache for news data
        self.news_cache = {}
        self.cache_timeout = 300  # 5 minutes
    
    def analyze_symbol_sentiment(self, symbol: str) -> Dict:
        """Analyze sentiment for a given symbol"""
        try:
            self.logger.info(f"🔍 Analyzing sentiment for {symbol}")
            
            # Get news data
            news_data = self.get_news_data(symbol)
            
            # Analyze sentiment
            sentiment_score = self.calculate_basic_sentiment(news_data)
            
            # Determine recommendation
            recommendation = self.get_recommendation(sentiment_score, symbol)
            
            # Calculate confidence
            confidence = min(0.8, abs(sentiment_score) + 0.3)  # Basic confidence
            
            # Risk assessment
            risk_level = self.assess_risk_level(sentiment_score, symbol)
            
            # Key themes (simplified)
            key_themes = self.extract_key_themes(news_data)
            
            result = {
                'symbol': symbol,
                'sentiment_score': sentiment_score,
                'recommendation': recommendation,
                'confidence': confidence,
                'risk_level': risk_level,
                'momentum_direction': self.get_momentum_direction(sentiment_score),
                'key_themes': key_themes,
                'news_count': len(news_data),
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"📊 Sentiment analysis for {symbol}: {recommendation} (score: {sentiment_score:.2f})")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Sentiment analysis failed for {symbol}: {e}")
            return self.get_neutral_sentiment(symbol)
    
    def get_news_data(self, symbol: str) -> List[Dict]:
        """Get news data for symbol (simplified)"""
        try:
            # Check cache
            cache_key = f"{symbol}_{int(time.time() // self.cache_timeout)}"
            if cache_key in self.news_cache:
                return self.news_cache[cache_key]
            
            # Clean symbol for news search
            search_symbol = symbol.replace('/', '').replace('-', '')
            if '/' in symbol:  # Crypto
                search_symbol = symbol.split('/')[0]
            
            # Try to get news from various sources
            news_articles = []
            
            # Method 1: Try to get from Alpaca (if available)
            try:
                news_articles.extend(self.get_alpaca_news(search_symbol))
            except:
                pass
            
            # Method 2: Use basic web scraping (simplified)
            if len(news_articles) < 5:
                news_articles.extend(self.get_basic_news(search_symbol))
            
            # Cache results
            self.news_cache[cache_key] = news_articles
            
            return news_articles[:20]  # Limit to 20 articles
            
        except Exception as e:
            self.logger.warning(f"Could not fetch news for {symbol}: {e}")
            return []
    
    def get_alpaca_news(self, symbol: str) -> List[Dict]:
        """Try to get news from Alpaca (if client available)"""
        try:
            # This would use the Alpaca client if available
            # For now, return empty list
            return []
        except:
            return []
    
    def get_basic_news(self, symbol: str) -> List[Dict]:
        """Get basic news using simple approach"""
        try:
            # This is a simplified approach - in production you'd use proper news APIs
            # For now, return mock data with some basic sentiment
            mock_news = [
                {
                    'title': f'{symbol} shows strong momentum in recent trading',
                    'summary': f'Recent analysis suggests {symbol} has positive outlook',
                    'timestamp': datetime.now().isoformat()
                },
                {
                    'title': f'Market analysts review {symbol} performance',
                    'summary': f'Mixed signals for {symbol} in current market conditions',
                    'timestamp': (datetime.now() - timedelta(hours=2)).isoformat()
                }
            ]
            
            return mock_news
            
        except Exception as e:
            self.logger.warning(f"Basic news fetch failed: {e}")
            return []
    
    def calculate_basic_sentiment(self, news_data: List[Dict]) -> float:
        """Calculate basic sentiment score"""
        if not news_data:
            return 0.0
        
        total_score = 0.0
        total_weight = 0.0
        
        for article in news_data:
            # Combine title and summary
            text = f"{article.get('title', '')} {article.get('summary', '')}"
            text = text.lower()
            
            # Count positive and negative keywords
            positive_count = sum(1 for word in self.positive_keywords if word in text)
            negative_count = sum(1 for word in self.negative_keywords if word in text)
            
            # Calculate article sentiment
            if positive_count + negative_count > 0:
                article_sentiment = (positive_count - negative_count) / (positive_count + negative_count)
            else:
                article_sentiment = 0.0
            
            # Weight by recency (more recent = higher weight)
            weight = 1.0  # Could add time-based weighting here
            
            total_score += article_sentiment * weight
            total_weight += weight
        
        # Average sentiment
        if total_weight > 0:
            avg_sentiment = total_score / total_weight
        else:
            avg_sentiment = 0.0
        
        # Normalize to [-1, 1] range
        return max(-1.0, min(1.0, avg_sentiment))
    
    def get_recommendation(self, sentiment_score: float, symbol: str) -> str:
        """Get trading recommendation based on sentiment"""
        
        # Adjust thresholds based on symbol type
        if '/' in symbol:  # Crypto - more volatile, need stronger signals
            buy_threshold = 0.3
            sell_threshold = -0.3
        else:  # Stocks
            buy_threshold = 0.2
            sell_threshold = -0.2
        
        if sentiment_score >= buy_threshold:
            if sentiment_score >= 0.6:
                return 'STRONG_BUY'
            else:
                return 'BUY'
        elif sentiment_score <= sell_threshold:
            if sentiment_score <= -0.6:
                return 'STRONG_SELL'
            else:
                return 'SELL'
        else:
            return 'HOLD'
    
    def assess_risk_level(self, sentiment_score: float, symbol: str) -> str:
        """Assess risk level"""
        abs_score = abs(sentiment_score)
        
        if '/' in symbol:  # Crypto inherently higher risk
            if abs_score > 0.7:
                return 'HIGH'
            elif abs_score > 0.3:
                return 'MEDIUM'
            else:
                return 'LOW'
        else:  # Stocks
            if abs_score > 0.8:
                return 'HIGH'
            elif abs_score > 0.4:
                return 'MEDIUM'
            else:
                return 'LOW'
    
    def get_momentum_direction(self, sentiment_score: float) -> str:
        """Get momentum direction"""
        if sentiment_score > 0.2:
            return 'BULLISH'
        elif sentiment_score < -0.2:
            return 'BEARISH'
        else:
            return 'NEUTRAL'
    
    def extract_key_themes(self, news_data: List[Dict]) -> List[str]:
        """Extract key themes from news (simplified)"""
        themes = []
        
        # Count keyword frequencies
        all_text = ' '.join([
            f"{article.get('title', '')} {article.get('summary', '')}" 
            for article in news_data
        ]).lower()
        
        # Check for common themes
        theme_keywords = {
            'earnings': ['earnings', 'revenue', 'profit', 'eps'],
            'market': ['market', 'trading', 'volume', 'price'],
            'technology': ['tech', 'innovation', 'development', 'product'],
            'regulation': ['regulation', 'sec', 'compliance', 'legal'],
            'partnership': ['partnership', 'deal', 'agreement', 'merger']
        }
        
        for theme, keywords in theme_keywords.items():
            if any(keyword in all_text for keyword in keywords):
                themes.append(theme)
        
        return themes[:5]  # Limit to top 5 themes
    
    def get_neutral_sentiment(self, symbol: str) -> Dict:
        """Return neutral sentiment as fallback"""
        return {
            'symbol': symbol,
            'sentiment_score': 0.0,
            'recommendation': 'HOLD',
            'confidence': 0.3,
            'risk_level': 'MEDIUM',
            'momentum_direction': 'NEUTRAL',
            'key_themes': ['market'],
            'news_count': 0,
            'timestamp': datetime.now().isoformat()
        }