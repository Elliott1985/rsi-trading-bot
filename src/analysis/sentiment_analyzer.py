"""
News Sentiment Analysis Module
Analyzes news sentiment using NewsAPI, Finnhub, and other sources
"""

import asyncio
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import requests
from newsapi import NewsApiClient
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class SentimentScore:
    """Sentiment analysis result"""
    symbol: str
    overall_sentiment: float  # -1.0 to +1.0
    confidence: float  # 0.0 to 1.0
    article_count: int
    sources: List[str]
    timestamp: datetime
    details: Dict[str, float]  # Individual component scores

class SentimentAnalyzer:
    """
    SENTIMENT ANALYSIS ENGINE - MODIFY FOR DIFFERENT SENTIMENT SOURCES
    
    This module fetches and analyzes news sentiment for stocks/crypto:
    - NewsAPI: General news sentiment
    - Finnhub: Financial news focus  
    - VADER: Social media style sentiment
    - TextBlob: Academic sentiment analysis
    
    CUSTOMIZE: Add new news sources, adjust sentiment weights, modify thresholds
    """
    
    def __init__(self):
        self.newsapi_key = os.getenv('NEWSAPI_KEY')
        self.finnhub_key = os.getenv('FINNHUB_API_KEY')
        
        # Initialize sentiment analyzers
        self.vader = SentimentIntensityAnalyzer()
        
        # Initialize news clients
        if self.newsapi_key and self.newsapi_key != 'your_newsapi_key_here':
            self.newsapi = NewsApiClient(api_key=self.newsapi_key)
        else:
            self.newsapi = None
            logger.warning("NewsAPI key not configured - using alternative sources")
    
    async def get_sentiment_score(self, symbol: str, lookback_hours: int = 24) -> Optional[SentimentScore]:
        """
        Get comprehensive sentiment score for a symbol
        
        MAIN SENTIMENT SCORING LOGIC - MODIFY WEIGHTS HERE:
        - NewsAPI weight: 40%
        - Finnhub weight: 40% 
        - Volume/mention weight: 20%
        
        Args:
            symbol: Stock/crypto symbol (e.g., 'AAPL', 'BTC')
            lookback_hours: How many hours back to analyze news
            
        Returns:
            SentimentScore object with overall sentiment (-1 to +1)
        """
        try:
            logger.info(f"Analyzing sentiment for {symbol}")
            
            # Fetch news from multiple sources
            newsapi_data = await self._fetch_newsapi_sentiment(symbol, lookback_hours)
            finnhub_data = await self._fetch_finnhub_sentiment(symbol, lookback_hours)
            
            # Combine sentiment scores
            sentiment_scores = []
            sources = []
            total_articles = 0
            
            if newsapi_data:
                sentiment_scores.append(newsapi_data[0] * 0.4)  # 40% weight for NewsAPI
                sources.append('newsapi')
                total_articles += newsapi_data[1]
                
            if finnhub_data:
                sentiment_scores.append(finnhub_data[0] * 0.4)  # 40% weight for Finnhub
                sources.append('finnhub')
                total_articles += finnhub_data[1]
            
            # Calculate mention volume sentiment (20% weight)
            if total_articles > 0:
                # More mentions generally indicate more interest/volatility
                mention_score = min(total_articles / 50.0, 1.0) * 0.2
                sentiment_scores.append(mention_score)
                sources.append('volume')
            
            if not sentiment_scores:
                logger.warning(f"No sentiment data available for {symbol}")
                return None
            
            # Calculate overall sentiment
            overall_sentiment = sum(sentiment_scores)
            overall_sentiment = max(-1.0, min(1.0, overall_sentiment))  # Clamp to [-1, 1]
            
            # Calculate confidence based on data availability and consistency
            confidence = self._calculate_confidence(sentiment_scores, total_articles)
            
            return SentimentScore(
                symbol=symbol,
                overall_sentiment=overall_sentiment,
                confidence=confidence,
                article_count=total_articles,
                sources=sources,
                timestamp=datetime.now(),
                details={
                    'newsapi': newsapi_data[0] if newsapi_data else 0.0,
                    'finnhub': finnhub_data[0] if finnhub_data else 0.0,
                    'mention_volume': mention_score if 'volume' in sources else 0.0
                }
            )
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment for {symbol}: {e}")
            return None
    
    async def _fetch_newsapi_sentiment(self, symbol: str, lookback_hours: int) -> Optional[Tuple[float, int]]:
        """
        Fetch sentiment from NewsAPI
        
        NEWSAPI SENTIMENT LOGIC:
        - Searches for company name + stock symbol
        - Analyzes headlines and descriptions
        - Uses VADER sentiment analysis
        
        Returns: (sentiment_score, article_count) or None
        """
        if not self.newsapi:
            return None
            
        try:
            # Get company name mapping for better search
            company_name = self._get_company_name(symbol)
            search_query = f'{company_name} OR {symbol}'
            
            # Fetch recent news
            from_date = datetime.now() - timedelta(hours=lookback_hours)
            
            news_response = self.newsapi.get_everything(
                q=search_query,
                from_param=from_date.isoformat(),
                language='en',
                sort_by='relevancy',
                page_size=50
            )
            
            articles = news_response.get('articles', [])
            if not articles:
                return None
            
            # Analyze sentiment of headlines and descriptions
            sentiments = []
            for article in articles:
                text = f"{article.get('title', '')} {article.get('description', '')}"
                if text.strip():
                    # Use VADER sentiment
                    vader_score = self.vader.polarity_scores(text)
                    # Convert compound score (-1 to 1) to our scale
                    sentiments.append(vader_score['compound'])
            
            if not sentiments:
                return None
            
            # Calculate average sentiment
            avg_sentiment = sum(sentiments) / len(sentiments)
            
            logger.debug(f"NewsAPI sentiment for {symbol}: {avg_sentiment:.3f} from {len(articles)} articles")
            return (avg_sentiment, len(articles))
            
        except Exception as e:
            logger.error(f"Error fetching NewsAPI sentiment for {symbol}: {e}")
            return None
    
    async def _fetch_finnhub_sentiment(self, symbol: str, lookback_hours: int) -> Optional[Tuple[float, int]]:
        """
        Fetch sentiment from Finnhub financial news
        
        FINNHUB SENTIMENT LOGIC:
        - Uses financial-specific news
        - Focuses on earnings, analyst reports, etc.
        - Generally more accurate for financial sentiment
        
        Returns: (sentiment_score, article_count) or None
        """
        if not self.finnhub_key or self.finnhub_key == 'your_finnhub_key_here':
            return None
            
        try:
            # Finnhub news endpoint
            from_date = datetime.now() - timedelta(hours=lookback_hours)
            to_date = datetime.now()
            
            url = f"https://finnhub.io/api/v1/company-news"
            params = {
                'symbol': symbol,
                'from': from_date.strftime('%Y-%m-%d'),
                'to': to_date.strftime('%Y-%m-%d'),
                'token': self.finnhub_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            news_data = response.json()
            
            if not news_data:
                return None
            
            # Analyze sentiment of headlines and summaries
            sentiments = []
            for article in news_data[:25]:  # Limit to 25 most recent
                text = f"{article.get('headline', '')} {article.get('summary', '')}"
                if text.strip():
                    # Use TextBlob for financial text
                    blob = TextBlob(text)
                    # TextBlob polarity is -1 to 1, perfect for our scale
                    sentiments.append(blob.sentiment.polarity)
            
            if not sentiments:
                return None
            
            # Calculate weighted average (more recent articles get higher weight)
            weights = [1.0 / (i + 1) for i in range(len(sentiments))]
            weighted_sentiment = sum(s * w for s, w in zip(sentiments, weights)) / sum(weights)
            
            logger.debug(f"Finnhub sentiment for {symbol}: {weighted_sentiment:.3f} from {len(news_data)} articles")
            return (weighted_sentiment, len(news_data))
            
        except Exception as e:
            logger.error(f"Error fetching Finnhub sentiment for {symbol}: {e}")
            return None
    
    def _get_company_name(self, symbol: str) -> str:
        """
        Map stock symbol to company name for better news search
        
        COMPANY NAME MAPPING - ADD MORE SYMBOLS HERE:
        This helps get more relevant news results
        """
        company_map = {
            'AAPL': 'Apple Inc',
            'MSFT': 'Microsoft Corporation',
            'GOOGL': 'Google Alphabet',
            'AMZN': 'Amazon',
            'TSLA': 'Tesla',
            'META': 'Meta Facebook',
            'NVDA': 'NVIDIA',
            'NFLX': 'Netflix',
            'AMD': 'Advanced Micro Devices',
            'INTC': 'Intel',
            'CRM': 'Salesforce',
            'UBER': 'Uber',
            'ABNB': 'Airbnb',
            'ROKU': 'Roku',
            'PLTR': 'Palantir',
            'SNOW': 'Snowflake',
            # Crypto mappings
            'BTC-USD': 'Bitcoin',
            'ETH-USD': 'Ethereum',
            'ADA-USD': 'Cardano',
            'SOL-USD': 'Solana',
            'DOT-USD': 'Polkadot',
            'AVAX-USD': 'Avalanche',
            'LINK-USD': 'Chainlink',
            'AAVE-USD': 'Aave'
        }
        
        return company_map.get(symbol, symbol)
    
    def _calculate_confidence(self, sentiment_scores: List[float], article_count: int) -> float:
        """
        Calculate confidence in sentiment analysis
        
        CONFIDENCE CALCULATION LOGIC:
        - More articles = higher confidence
        - Consistent sentiment across sources = higher confidence
        - Multiple data sources = higher confidence
        """
        if not sentiment_scores:
            return 0.0
        
        # Base confidence from article count
        article_confidence = min(article_count / 20.0, 1.0)  # Max confidence at 20+ articles
        
        # Consistency confidence (lower variance = higher confidence)
        if len(sentiment_scores) > 1:
            variance = sum((s - sum(sentiment_scores) / len(sentiment_scores)) ** 2 for s in sentiment_scores)
            variance /= len(sentiment_scores)
            consistency_confidence = max(0.0, 1.0 - variance)
        else:
            consistency_confidence = 0.5  # Medium confidence for single source
        
        # Source diversity confidence
        source_confidence = min(len(sentiment_scores) / 3.0, 1.0)  # Max at 3+ sources
        
        # Combine confidence factors
        overall_confidence = (article_confidence * 0.4 + 
                            consistency_confidence * 0.4 + 
                            source_confidence * 0.2)
        
        return min(1.0, overall_confidence)
    
    async def batch_sentiment_analysis(self, symbols: List[str], lookback_hours: int = 24) -> Dict[str, SentimentScore]:
        """
        Analyze sentiment for multiple symbols in batch
        
        BATCH PROCESSING:
        - Processes multiple symbols concurrently
        - Includes rate limiting to avoid API limits
        - Returns dict mapping symbol -> SentimentScore
        """
        logger.info(f"Starting batch sentiment analysis for {len(symbols)} symbols")
        
        # Process in batches to avoid API rate limits
        batch_size = 5
        results = {}
        
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i + batch_size]
            
            # Process batch concurrently
            tasks = [self.get_sentiment_score(symbol, lookback_hours) for symbol in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Collect results
            for symbol, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Error processing {symbol}: {result}")
                elif result:
                    results[symbol] = result
            
            # Rate limiting delay
            if i + batch_size < len(symbols):
                await asyncio.sleep(2)  # 2 second delay between batches
        
        logger.info(f"Completed batch sentiment analysis: {len(results)}/{len(symbols)} successful")
        return results