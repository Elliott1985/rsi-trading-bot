#!/usr/bin/env python3
"""
Sentiment Analysis Module
Analyzes news sentiment to guide trading decisions with weighted scoring.
"""

import requests
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import re
from textblob import TextBlob

@dataclass
class NewsItem:
    """News article data structure"""
    headline: str
    summary: str
    url: str
    source: str
    published_at: datetime
    symbols: List[str]
    sentiment_score: float  # -1 to 1
    relevance_score: float  # 0 to 1

@dataclass
class SentimentAnalysis:
    """Sentiment analysis result"""
    symbol: str
    overall_sentiment: float  # -1 to 1
    news_count: int
    positive_count: int
    negative_count: int
    neutral_count: int
    weighted_sentiment: float
    confidence: float
    recommendation: str  # BULLISH_BIAS, BEARISH_BIAS, SKIP, NEUTRAL
    key_headlines: List[str]

class SentimentAnalyzer:
    """News sentiment analysis for trading signals"""
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.logger = logging.getLogger(__name__)
        self.credentials = config_manager.get_api_credentials()
        
        # Sentiment keywords
        self.bullish_keywords = [
            'beats', 'exceeds', 'strong', 'growth', 'positive', 'upgrade', 'bullish',
            'outperforms', 'rally', 'surge', 'gains', 'profit', 'revenue', 'earnings beat',
            'expansion', 'partnership', 'acquisition', 'innovation', 'breakthrough'
        ]
        
        self.bearish_keywords = [
            'misses', 'disappoints', 'weak', 'decline', 'negative', 'downgrade', 'bearish',
            'underperforms', 'crash', 'plunge', 'losses', 'deficit', 'earnings miss',
            'recession', 'bankruptcy', 'lawsuit', 'investigation', 'scandal', 'warning'
        ]
        
        # High volatility keywords that increase risk
        self.volatility_keywords = [
            'breaking', 'urgent', 'alert', 'investigation', 'lawsuit', 'fda', 'sec',
            'regulation', 'halt', 'suspend', 'emergency', 'crisis', 'scandal'
        ]
    
    def get_alpaca_news(self, symbols: List[str], hours_back: int = 24) -> List[NewsItem]:
        """Fetch news from Alpaca News API"""
        try:
            import alpaca_trade_api as tradeapi
            
            api = tradeapi.REST(
                self.credentials['ALPACA_API_KEY'],
                self.credentials['ALPACA_SECRET_KEY'],
                'https://api.alpaca.markets'
            )
            
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours_back)
            
            # Format dates for Alpaca API (RFC3339 format)
            start_time_str = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
            end_time_str = end_time.strftime('%Y-%m-%dT%H:%M:%SZ')
            
            news_items = []
            
            for symbol in symbols[:10]:  # Limit to avoid rate limits
                try:
                    news = api.get_news(
                        symbol=symbol,
                        start=start_time_str,
                        end=end_time_str,
                        sort='desc',
                        limit=5
                    )
                    
                    for article in news:
                        sentiment_score = self._analyze_text_sentiment(
                            f"{article.headline} {article.summary or ''}"
                        )
                        
                        news_items.append(NewsItem(
                            headline=article.headline,
                            summary=article.summary or '',
                            url=article.url,
                            source=article.source,
                            published_at=article.created_at,
                            symbols=[symbol],
                            sentiment_score=sentiment_score,
                            relevance_score=self._calculate_relevance(article.headline, symbol)
                        ))
                        
                except Exception as e:
                    self.logger.error(f"Failed to get news for {symbol}: {e}")
                    continue
            
            return news_items
            
        except Exception as e:
            self.logger.error(f"Alpaca news fetch error: {e}")
            return []
    
    def get_newsapi_news(self, symbols: List[str], hours_back: int = 24) -> List[NewsItem]:
        """Backup news source using NewsAPI"""
        try:
            api_key = self.credentials.get('NEWSAPI_KEY')
            if not api_key:
                return []
            
            news_items = []
            base_url = "https://newsapi.org/v2/everything"
            
            for symbol in symbols[:5]:  # Limit requests
                query = f"{symbol} OR {symbol.lower()} stock OR {symbol.upper()}"
                
                params = {
                    'q': query,
                    'apiKey': api_key,
                    'language': 'en',
                    'sortBy': 'publishedAt',
                    'pageSize': 5,
                    'from': (datetime.now() - timedelta(hours=hours_back)).isoformat()
                }
                
                response = requests.get(base_url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    
                    for article in data.get('articles', []):
                        if not article.get('title'):
                            continue
                        
                        sentiment_score = self._analyze_text_sentiment(
                            f"{article['title']} {article.get('description', '')}"
                        )
                        
                        news_items.append(NewsItem(
                            headline=article['title'],
                            summary=article.get('description', ''),
                            url=article['url'],
                            source=article['source']['name'],
                            published_at=datetime.fromisoformat(
                                article['publishedAt'].replace('Z', '+00:00')
                            ),
                            symbols=[symbol],
                            sentiment_score=sentiment_score,
                            relevance_score=self._calculate_relevance(article['title'], symbol)
                        ))
                
            return news_items
            
        except Exception as e:
            self.logger.error(f"NewsAPI fetch error: {e}")
            return []
    
    def _analyze_text_sentiment(self, text: str) -> float:
        """Analyze sentiment of text using TextBlob and keywords"""
        try:
            # Clean text
            clean_text = re.sub(r'[^\w\s]', ' ', text.lower())
            
            # TextBlob sentiment (primary)
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            
            # Keyword-based sentiment (secondary)
            bullish_count = sum(1 for keyword in self.bullish_keywords if keyword in clean_text)
            bearish_count = sum(1 for keyword in self.bearish_keywords if keyword in clean_text)
            
            keyword_sentiment = 0
            if bullish_count > bearish_count:
                keyword_sentiment = min(bullish_count * 0.2, 0.5)
            elif bearish_count > bullish_count:
                keyword_sentiment = -min(bearish_count * 0.2, 0.5)
            
            # Combine scores (70% TextBlob, 30% keywords)
            combined_sentiment = (polarity * 0.7) + (keyword_sentiment * 0.3)
            
            # Normalize to -1 to 1
            return max(-1, min(1, combined_sentiment))
            
        except Exception as e:
            self.logger.error(f"Text sentiment analysis error: {e}")
            return 0.0
    
    def _calculate_relevance(self, headline: str, symbol: str) -> float:
        """Calculate how relevant a news item is to the symbol"""
        try:
            text = headline.lower()
            symbol_lower = symbol.lower()
            
            # Direct symbol mentions
            relevance = 0.0
            if symbol_lower in text:
                relevance += 0.6
            
            # Company name variations (simple heuristic)
            if symbol in ['AAPL', 'APPLE'] and 'apple' in text:
                relevance += 0.8
            elif symbol in ['MSFT', 'MICROSOFT'] and 'microsoft' in text:
                relevance += 0.8
            elif symbol in ['GOOGL', 'GOOGLE'] and ('google' in text or 'alphabet' in text):
                relevance += 0.8
            elif symbol in ['AMZN', 'AMAZON'] and 'amazon' in text:
                relevance += 0.8
            elif symbol in ['TSLA', 'TESLA'] and 'tesla' in text:
                relevance += 0.8
            
            # Market-wide impact keywords
            market_keywords = ['market', 'stocks', 'trading', 'wall street', 'nasdaq', 'sp500']
            if any(keyword in text for keyword in market_keywords):
                relevance += 0.3
            
            # Sector-specific relevance
            if symbol in ['XLF', 'JPM', 'BAC'] and ('bank' in text or 'financial' in text):
                relevance += 0.4
            elif symbol in ['XLK', 'NVDA', 'AMD'] and 'tech' in text:
                relevance += 0.4
            
            return min(1.0, relevance)
            
        except Exception as e:
            self.logger.error(f"Relevance calculation error: {e}")
            return 0.3  # Default relevance
    
    def _check_high_volatility_risk(self, news_items: List[NewsItem]) -> bool:
        """Check if news indicates high volatility risk"""
        for item in news_items:
            text = f"{item.headline} {item.summary}".lower()
            if any(keyword in text for keyword in self.volatility_keywords):
                return True
        return False
    
    def analyze_symbol_sentiment(self, symbol: str, news_items: List[NewsItem]) -> SentimentAnalysis:
        """Analyze sentiment for a specific symbol"""
        try:
            # Filter news for this symbol
            symbol_news = [
                item for item in news_items 
                if symbol in item.symbols and item.relevance_score > 0.3
            ]
            
            if not symbol_news:
                return SentimentAnalysis(
                    symbol=symbol,
                    overall_sentiment=0.0,
                    news_count=0,
                    positive_count=0,
                    negative_count=0,
                    neutral_count=0,
                    weighted_sentiment=0.0,
                    confidence=0.0,
                    recommendation="NEUTRAL",
                    key_headlines=[]
                )
            
            # Calculate sentiment statistics
            sentiments = [item.sentiment_score for item in symbol_news]
            relevance_weights = [item.relevance_score for item in symbol_news]
            
            overall_sentiment = sum(sentiments) / len(sentiments)
            
            # Weighted sentiment (by relevance and recency)
            weighted_scores = []
            for i, item in enumerate(symbol_news):
                # Recency weight (newer = higher weight)
                hours_ago = (datetime.now() - item.published_at.replace(tzinfo=None)).total_seconds() / 3600
                recency_weight = max(0.1, 1.0 - (hours_ago / 24))  # Decay over 24 hours
                
                weight = item.relevance_score * recency_weight
                weighted_scores.append(item.sentiment_score * weight)
            
            weighted_sentiment = sum(weighted_scores) / len(weighted_scores) if weighted_scores else 0.0
            
            # Count sentiment types
            positive_count = sum(1 for s in sentiments if s > 0.1)
            negative_count = sum(1 for s in sentiments if s < -0.1)
            neutral_count = len(sentiments) - positive_count - negative_count
            
            # Calculate confidence
            confidence = min(len(symbol_news) / 3, 1.0) * 0.7  # More news = higher confidence
            if len(symbol_news) >= 2:
                sentiment_consistency = 1.0 - (np.std(sentiments) / 2.0)  # Lower variance = higher confidence
                confidence += sentiment_consistency * 0.3
            
            # Generate recommendation
            config = self.config.trading_config
            high_volatility = self._check_high_volatility_risk(symbol_news)
            
            recommendation = "NEUTRAL"
            
            if high_volatility and abs(weighted_sentiment) > 0.6:
                recommendation = "SKIP"  # Too risky
            elif weighted_sentiment < config.sentiment_skip_threshold:
                recommendation = "SKIP"  # Very negative
            elif weighted_sentiment > config.sentiment_bias_threshold:
                recommendation = "BULLISH_BIAS"
            elif weighted_sentiment < -config.sentiment_bias_threshold:
                recommendation = "BEARISH_BIAS"
            
            # Get key headlines
            key_headlines = [
                item.headline for item in sorted(
                    symbol_news, 
                    key=lambda x: x.relevance_score * abs(x.sentiment_score), 
                    reverse=True
                )[:3]
            ]
            
            return SentimentAnalysis(
                symbol=symbol,
                overall_sentiment=overall_sentiment,
                news_count=len(symbol_news),
                positive_count=positive_count,
                negative_count=negative_count,
                neutral_count=neutral_count,
                weighted_sentiment=weighted_sentiment,
                confidence=confidence,
                recommendation=recommendation,
                key_headlines=key_headlines
            )
            
        except Exception as e:
            self.logger.error(f"Symbol sentiment analysis error for {symbol}: {e}")
            return SentimentAnalysis(
                symbol=symbol,
                overall_sentiment=0.0,
                news_count=0,
                positive_count=0,
                negative_count=0,
                neutral_count=0,
                weighted_sentiment=0.0,
                confidence=0.0,
                recommendation="NEUTRAL",
                key_headlines=[]
            )
    
    def get_market_sentiment(self, symbols: List[str]) -> Dict[str, SentimentAnalysis]:
        """Get sentiment analysis for multiple symbols"""
        try:
            # Fetch news from primary source (Alpaca)
            news_items = self.get_alpaca_news(symbols, hours_back=24)
            
            # Fallback to NewsAPI if no news found
            if len(news_items) < 5:
                backup_news = self.get_newsapi_news(symbols, hours_back=24)
                news_items.extend(backup_news)
            
            self.logger.info(f"Fetched {len(news_items)} news items for sentiment analysis")
            
            # Analyze each symbol
            sentiment_results = {}
            for symbol in symbols:
                sentiment_results[symbol] = self.analyze_symbol_sentiment(symbol, news_items)
            
            return sentiment_results
            
        except Exception as e:
            self.logger.error(f"Market sentiment analysis error: {e}")
            # Return neutral sentiment for all symbols
            return {
                symbol: SentimentAnalysis(
                    symbol=symbol,
                    overall_sentiment=0.0,
                    news_count=0,
                    positive_count=0,
                    negative_count=0,
                    neutral_count=0,
                    weighted_sentiment=0.0,
                    confidence=0.0,
                    recommendation="NEUTRAL",
                    key_headlines=[]
                ) for symbol in symbols
            }