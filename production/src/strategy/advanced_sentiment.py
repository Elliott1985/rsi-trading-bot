#!/usr/bin/env python3
"""
Advanced Sentiment Analysis
Enhanced news sentiment analysis for trading decisions using financial NLP.
"""

import requests
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from textblob import TextBlob
import re

class AdvancedSentimentAnalyzer:
    """Advanced sentiment analysis for trading decisions"""
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.logger = logging.getLogger(__name__)
        self.credentials = config_manager.get_api_credentials()
        
        # Financial keywords with weights
        self.financial_keywords = {
            'bullish': ['bullish', 'rally', 'surge', 'gains', 'growth', 'breakout', 'momentum', 
                       'outperform', 'upgrade', 'buy', 'strong', 'positive', 'rising', 'bull'],
            'bearish': ['bearish', 'crash', 'plunge', 'decline', 'drop', 'fall', 'weakness',
                       'underperform', 'downgrade', 'sell', 'negative', 'falling', 'bear'],
            'volatility': ['volatile', 'uncertainty', 'risk', 'unstable', 'swing', 'fluctuate',
                          'turbulent', 'erratic', 'wild', 'choppy'],
            'momentum': ['momentum', 'acceleration', 'velocity', 'trend', 'direction', 'force',
                        'strength', 'power', 'drive', 'push']
        }
        
        # Crypto-specific keywords
        self.crypto_keywords = {
            'adoption': ['adoption', 'institutional', 'etf', 'mainstream', 'regulation', 'legal'],
            'technical': ['blockchain', 'defi', 'smart contract', 'validator', 'staking', 'yield'],
            'market': ['halving', 'mining', 'hash rate', 'whale', 'hodl', 'fomo', 'fud']
        }
        
        # AMD-specific keywords
        self.amd_keywords = {
            'products': ['ryzen', 'epyc', 'radeon', 'instinct', 'zen', 'rdna', 'cpu', 'gpu'],
            'business': ['datacenter', 'gaming', 'ai', 'machine learning', 'cloud', 'server'],
            'competition': ['intel', 'nvidia', 'market share', 'performance', 'benchmark']
        }
    
    def analyze_symbol_sentiment(self, symbol: str, hours_back: int = 24) -> Dict:
        """Comprehensive sentiment analysis for a specific symbol"""
        try:
            # Get news for the symbol
            news_items = self._fetch_symbol_news(symbol, hours_back)
            
            if not news_items:
                return self._default_sentiment_result(symbol)
            
            # Analyze each news item
            sentiment_scores = []
            risk_indicators = []
            momentum_indicators = []
            
            for item in news_items:
                analysis = self._analyze_news_item(item, symbol)
                sentiment_scores.append(analysis['sentiment'])
                risk_indicators.append(analysis['risk_score'])
                momentum_indicators.append(analysis['momentum_score'])
            
            # Calculate weighted sentiment
            weighted_sentiment = self._calculate_weighted_sentiment(
                sentiment_scores, news_items
            )
            
            # Risk assessment
            avg_risk = sum(risk_indicators) / len(risk_indicators)
            risk_level = self._determine_risk_level(avg_risk, weighted_sentiment)
            
            # Momentum assessment
            avg_momentum = sum(momentum_indicators) / len(momentum_indicators)
            momentum_direction = self._determine_momentum(avg_momentum, weighted_sentiment)
            
            # Trading recommendation
            recommendation = self._generate_trading_recommendation(
                symbol, weighted_sentiment, risk_level, momentum_direction
            )
            
            return {
                'symbol': symbol,
                'sentiment_score': weighted_sentiment,
                'risk_level': risk_level,
                'momentum_direction': momentum_direction,
                'recommendation': recommendation,
                'news_count': len(news_items),
                'confidence': min(len(news_items) / 5, 1.0),  # Higher confidence with more news
                'key_themes': self._extract_key_themes(news_items, symbol),
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Sentiment analysis failed for {symbol}: {e}")
            return self._default_sentiment_result(symbol)
    
    def _fetch_symbol_news(self, symbol: str, hours_back: int) -> List[Dict]:
        """Fetch news items for a symbol"""
        news_items = []
        
        try:
            # Try Alpaca news first
            alpaca_news = self._get_alpaca_news(symbol, hours_back)
            news_items.extend(alpaca_news)
            
            # Fallback to other sources if needed
            if len(news_items) < 3:
                external_news = self._get_external_news(symbol, hours_back)
                news_items.extend(external_news)
            
        except Exception as e:
            self.logger.error(f"Failed to fetch news for {symbol}: {e}")
        
        return news_items[:10]  # Limit to most recent 10 items
    
    def _get_alpaca_news(self, symbol: str, hours_back: int) -> List[Dict]:
        """Get news from Alpaca"""
        try:
            import alpaca_trade_api as tradeapi
            
            api = tradeapi.REST(
                self.credentials['ALPACA_API_KEY'],
                self.credentials['ALPACA_SECRET_KEY'],
                'https://api.alpaca.markets'
            )
            
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours_back)
            
            # Clean symbol for Alpaca (remove /USD if crypto)
            clean_symbol = symbol.replace('/USD', '') if '/' in symbol else symbol
            
            news = api.get_news(
                symbols=clean_symbol,
                start=start_time,
                end=end_time,
                sort='desc',
                limit=10
            )
            
            return [
                {
                    'headline': article.headline,
                    'content': article.summary or '',
                    'source': article.source,
                    'published_at': article.created_at,
                    'url': article.url
                }
                for article in news
            ]
            
        except Exception as e:
            self.logger.error(f"Alpaca news fetch failed for {symbol}: {e}")
            return []
    
    def _get_external_news(self, symbol: str, hours_back: int) -> List[Dict]:
        """Get news from external sources"""
        try:
            # This would integrate with NewsAPI, Reddit, Twitter, etc.
            # For now, return empty list
            return []
            
        except Exception as e:
            self.logger.error(f"External news fetch failed for {symbol}: {e}")
            return []
    
    def _analyze_news_item(self, news_item: Dict, symbol: str) -> Dict:
        """Analyze individual news item"""
        try:
            text = f"{news_item['headline']} {news_item['content']}".lower()
            
            # Basic sentiment using TextBlob
            blob = TextBlob(text)
            base_sentiment = blob.sentiment.polarity
            
            # Enhanced financial sentiment
            financial_sentiment = self._calculate_financial_sentiment(text, symbol)
            
            # Risk indicators
            risk_score = self._calculate_risk_score(text)
            
            # Momentum indicators
            momentum_score = self._calculate_momentum_score(text)
            
            # Combine sentiments (70% financial, 30% base)
            combined_sentiment = (financial_sentiment * 0.7) + (base_sentiment * 0.3)
            
            return {
                'sentiment': combined_sentiment,
                'risk_score': risk_score,
                'momentum_score': momentum_score,
                'relevance': self._calculate_relevance(text, symbol)
            }
            
        except Exception as e:
            self.logger.error(f"News item analysis failed: {e}")
            return {'sentiment': 0, 'risk_score': 0.5, 'momentum_score': 0, 'relevance': 0.5}
    
    def _calculate_financial_sentiment(self, text: str, symbol: str) -> float:
        """Calculate sentiment using financial keywords"""
        sentiment_score = 0
        word_count = 0
        
        # General financial keywords
        for word in self.financial_keywords['bullish']:
            count = text.count(word)
            sentiment_score += count * 0.5
            word_count += count
            
        for word in self.financial_keywords['bearish']:
            count = text.count(word)
            sentiment_score -= count * 0.5
            word_count += count
        
        # Symbol-specific keywords
        if '/' in symbol:  # Crypto
            for category, keywords in self.crypto_keywords.items():
                for word in keywords:
                    if word in text:
                        # Positive weight for adoption and technical progress
                        weight = 0.3 if category in ['adoption', 'technical'] else 0.1
                        sentiment_score += weight
                        word_count += 1
        
        elif symbol == 'AMD':  # AMD specific
            for category, keywords in self.amd_keywords.items():
                for word in keywords:
                    if word in text:
                        # Positive for products and business, neutral for competition
                        weight = 0.3 if category in ['products', 'business'] else 0
                        sentiment_score += weight
                        word_count += 1
        
        # Normalize to -1 to 1
        if word_count > 0:
            return max(-1, min(1, sentiment_score / max(word_count, 1)))
        else:
            return 0
    
    def _calculate_risk_score(self, text: str) -> float:
        """Calculate risk level from 0 (low) to 1 (high)"""
        risk_indicators = 0
        total_indicators = 0
        
        # High risk keywords
        high_risk_words = ['crash', 'plunge', 'volatile', 'uncertain', 'risk', 'danger', 
                          'warning', 'concern', 'problem', 'issue', 'trouble']
        
        for word in high_risk_words:
            if word in text:
                risk_indicators += 1
            total_indicators += 1
        
        # Volatility keywords
        for word in self.financial_keywords['volatility']:
            if word in text:
                risk_indicators += 0.5
            total_indicators += 1
        
        return min(risk_indicators / max(total_indicators, 1), 1.0)
    
    def _calculate_momentum_score(self, text: str) -> float:
        """Calculate momentum score from -1 (negative) to 1 (positive)"""
        momentum_score = 0
        
        for word in self.financial_keywords['momentum']:
            if word in text:
                momentum_score += 0.2
        
        # Direction indicators
        positive_momentum = ['accelerating', 'increasing', 'growing', 'rising', 'climbing']
        negative_momentum = ['decelerating', 'decreasing', 'slowing', 'falling', 'dropping']
        
        for word in positive_momentum:
            if word in text:
                momentum_score += 0.3
                
        for word in negative_momentum:
            if word in text:
                momentum_score -= 0.3
        
        return max(-1, min(1, momentum_score))
    
    def _calculate_relevance(self, text: str, symbol: str) -> float:
        """Calculate how relevant the news is to the symbol"""
        relevance = 0
        
        # Direct symbol mention
        clean_symbol = symbol.replace('/USD', '') if '/' in symbol else symbol
        if clean_symbol.lower() in text:
            relevance += 0.6
        
        # Company/crypto name variations
        if symbol == 'AMD' and ('advanced micro devices' in text or 'amd' in text):
            relevance += 0.8
        elif symbol == 'SOL/USD' and ('solana' in text or 'sol' in text):
            relevance += 0.8
        
        # Industry keywords
        if '/' in symbol:  # Crypto
            crypto_general = ['cryptocurrency', 'crypto', 'bitcoin', 'blockchain', 'defi']
            for word in crypto_general:
                if word in text:
                    relevance += 0.2
                    break
        else:  # Stock
            if symbol == 'AMD':
                tech_keywords = ['semiconductor', 'chip', 'processor', 'gaming', 'datacenter']
                for word in tech_keywords:
                    if word in text:
                        relevance += 0.3
                        break
        
        return min(relevance, 1.0)
    
    def _calculate_weighted_sentiment(self, scores: List[float], news_items: List[Dict]) -> float:
        """Calculate weighted sentiment based on recency and relevance"""
        if not scores:
            return 0
        
        weighted_scores = []
        total_weight = 0
        
        for i, score in enumerate(scores):
            # Recency weight (newer = higher weight)
            try:
                pub_time = news_items[i]['published_at']
                if isinstance(pub_time, str):
                    pub_time = datetime.fromisoformat(pub_time.replace('Z', '+00:00'))
                
                hours_ago = (datetime.now(pub_time.tzinfo) - pub_time).total_seconds() / 3600
                recency_weight = max(0.1, 1.0 - (hours_ago / 24))
            except:
                recency_weight = 0.5
            
            # Apply weight
            weighted_scores.append(score * recency_weight)
            total_weight += recency_weight
        
        return sum(weighted_scores) / total_weight if total_weight > 0 else 0
    
    def _determine_risk_level(self, risk_score: float, sentiment: float) -> str:
        """Determine overall risk level"""
        if risk_score > 0.7 or abs(sentiment) > 0.8:
            return "HIGH"
        elif risk_score > 0.4 or abs(sentiment) > 0.5:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _determine_momentum(self, momentum_score: float, sentiment: float) -> str:
        """Determine momentum direction"""
        combined = (momentum_score + sentiment) / 2
        
        if combined > 0.3:
            return "BULLISH"
        elif combined < -0.3:
            return "BEARISH"
        else:
            return "NEUTRAL"
    
    def _generate_trading_recommendation(self, symbol: str, sentiment: float, 
                                       risk_level: str, momentum: str) -> str:
        """Generate trading recommendation"""
        
        # Skip high-risk scenarios
        if risk_level == "HIGH" and abs(sentiment) > 0.6:
            return "SKIP_HIGH_RISK"
        
        # Strong signals
        if sentiment > 0.5 and momentum == "BULLISH" and risk_level != "HIGH":
            return "STRONG_BUY"
        elif sentiment < -0.5 and momentum == "BEARISH" and risk_level != "HIGH":
            return "STRONG_SELL"
        
        # Moderate signals
        elif sentiment > 0.3 and momentum in ["BULLISH", "NEUTRAL"]:
            return "BUY"
        elif sentiment < -0.3 and momentum in ["BEARISH", "NEUTRAL"]:
            return "SELL"
        
        # Neutral/hold
        else:
            return "HOLD"
    
    def _extract_key_themes(self, news_items: List[Dict], symbol: str) -> List[str]:
        """Extract key themes from news"""
        themes = []
        all_text = " ".join([item['headline'] + " " + item['content'] for item in news_items]).lower()
        
        # Check for major themes
        if 'earnings' in all_text or 'revenue' in all_text:
            themes.append("EARNINGS")
        if 'partnership' in all_text or 'deal' in all_text:
            themes.append("PARTNERSHIPS")
        if 'regulation' in all_text or 'legal' in all_text:
            themes.append("REGULATORY")
        if 'upgrade' in all_text or 'downgrade' in all_text:
            themes.append("ANALYST_RATING")
        
        # Symbol-specific themes
        if symbol == 'AMD':
            if any(word in all_text for word in ['ryzen', 'epyc', 'gpu', 'cpu']):
                themes.append("PRODUCT_NEWS")
            if 'datacenter' in all_text or 'server' in all_text:
                themes.append("DATACENTER")
        
        elif symbol == 'SOL/USD':
            if 'defi' in all_text or 'nft' in all_text:
                themes.append("ECOSYSTEM")
            if 'staking' in all_text or 'validator' in all_text:
                themes.append("NETWORK")
        
        return themes[:3]  # Return top 3 themes
    
    def _default_sentiment_result(self, symbol: str) -> Dict:
        """Return default sentiment result when analysis fails"""
        return {
            'symbol': symbol,
            'sentiment_score': 0.0,
            'risk_level': "MEDIUM",
            'momentum_direction': "NEUTRAL",
            'recommendation': "HOLD",
            'news_count': 0,
            'confidence': 0.0,
            'key_themes': [],
            'analysis_timestamp': datetime.now().isoformat()
        }