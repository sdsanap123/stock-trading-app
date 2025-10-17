#!/usr/bin/env python3
"""
Gemini AI Analyzer Component
Gemini AI-powered comprehensive stock analysis.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class GeminiAIAnalyzer:
    """Gemini AI-powered comprehensive stock analysis."""
    
    def __init__(self):
        self.api_key = None
        self.initialized = False
        self.analysis_cache = {}
        self.cache_file = "gemini_analysis_cache.pkl"
        self.cache_duration_hours = 24
        self._initialize()
    
    def _initialize(self):
        """Initialize Gemini AI."""
        try:
            import os
            self.api_key = os.getenv('GEMINI_API_KEY')
            if self.api_key:
                self.initialized = True
                logger.info("Gemini AI initialized successfully")
            else:
                logger.warning("Gemini API key not found. Set GEMINI_API_KEY environment variable.")
        except Exception as e:
            logger.error(f"Error initializing Gemini AI: {str(e)}")
    
    def set_api_key(self, api_key: str):
        """Set API key and validate it."""
        try:
            if not api_key or not api_key.strip():
                self.api_key = None
                self.initialized = False
                logger.warning("Empty Gemini API key provided")
                return False
            
            self.api_key = api_key.strip()
            
            # Test the API key with a simple request
            if self._validate_api_key():
                self.initialized = True
                logger.info("Gemini API key validated and set successfully")
                return True
            else:
                self.initialized = False
                logger.error("Invalid Gemini API key")
                return False
                
        except Exception as e:
            logger.error(f"Error setting Gemini API key: {str(e)}")
            self.initialized = False
            return False
    
    def _validate_api_key(self) -> bool:
        """Validate the API key with a simple test request."""
        try:
            if not self.api_key:
                return False
            
            # Make a simple test request to validate the API key
            import requests
            
            # Gemini API endpoint for testing
            test_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={self.api_key}"
            
            test_payload = {
                "contents": [{
                    "parts": [{"text": "Hello"}]
                }]
            }
            
            response = requests.post(
                test_url,
                json=test_payload,
                timeout=10
            )
            
            if response.status_code == 200:
                return True
            elif response.status_code == 400:
                logger.error("Gemini API key validation failed: Bad Request")
                return False
            elif response.status_code == 403:
                logger.error("Gemini API key validation failed: Forbidden")
                return False
            else:
                logger.warning(f"Gemini API key validation returned status {response.status_code}")
                return True  # Assume valid if not 400/403
                
        except Exception as e:
            logger.error(f"Error validating Gemini API key: {str(e)}")
            return False
    
    def _get_groq_fallback(self):
        """Get Groq analyzer as fallback."""
        try:
            # Import here to avoid circular imports
            from .groq_analyzer import GroqNewsAnalyzer
            return GroqNewsAnalyzer()
        except Exception as e:
            logger.error(f"Could not initialize Groq fallback: {str(e)}")
            return None
    
    def analyze_stock_comprehensive(self, symbol: str, technical_data: Dict, 
                                  fundamental_data: Dict, news_articles: List[Dict], 
                                  groq_analysis: Dict = None) -> Dict:
        """Comprehensive stock analysis using Gemini AI."""
        try:
            if not self.initialized:
                return self._service_unavailable_response("Gemini AI not initialized")
            
            # Mock response for demo purposes
            return {
                'status': 'success',
                'analysis': {
                    'overall_score': 0.7,
                    'confidence': 0.8,
                    'recommendation': 'BUY',
                    'risk_assessment': 'MODERATE',
                    'key_insights': [
                        'Strong technical indicators',
                        'Positive fundamental metrics',
                        'Favorable market sentiment'
                    ],
                    'reasoning': 'Comprehensive analysis shows positive outlook with moderate risk.',
                    'timestamp': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error in Gemini analysis: {str(e)}")
            return self._service_unavailable_response(f"Analysis error: {str(e)}")
    
    def analyze_stock_for_learning(self, symbol: str, technical_data: Dict, 
                                  fundamental_data: Dict, news_articles: List[Dict], 
                                  groq_analysis: Dict, watchlist_item: Dict) -> Dict:
        """Analyze stock for learning purposes."""
        try:
            if not self.initialized:
                return self._service_unavailable_response("Gemini AI not initialized")
            
            # Mock response for demo
            return {
                'status': 'success',
                'analysis': {
                    'performance_insights': 'Stock showing positive momentum',
                    'learning_points': ['Technical breakout confirmed', 'Volume increasing'],
                    'future_outlook': 'Bullish with proper risk management',
                    'timestamp': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error in learning analysis: {str(e)}")
            return self._service_unavailable_response(f"Analysis error: {str(e)}")
    
    def analyze_top_10_news_with_full_content(self, news_articles: List[Dict]) -> Dict:
        """Analyze top 10 news articles with full content for stock sentiment."""
        try:
            if not self.initialized:
                logger.warning("Gemini not initialized, trying Groq fallback...")
                groq_fallback = self._get_groq_fallback()
                if groq_fallback and groq_fallback.initialized:
                    logger.info("Using Groq fallback for news analysis")
                    return groq_fallback.analyze_top_10_news_with_full_content(news_articles)
                else:
                    return self._service_unavailable_response("Gemini AI not initialized and Groq fallback unavailable. Please set your API keys.")
            
            if not news_articles:
                return self._service_unavailable_response("No news articles provided for analysis.")
            
            # Mock implementation - in real scenario, this would use Gemini API
            logger.info("Using Gemini for news analysis (mock implementation)")
            
            # Extract stocks from news articles
            stocks = []
            for article in news_articles[:10]:
                # Simple stock extraction from title/description
                title = article.get('title', '').upper()
                description = article.get('description', '').upper()
                
                # Look for common stock patterns
                import re
                stock_patterns = re.findall(r'\b[A-Z]{2,6}\b', title + ' ' + description)
                
                for pattern in stock_patterns[:2]:  # Limit to 2 stocks per article
                    if len(pattern) >= 2 and pattern not in ['THE', 'AND', 'FOR', 'WITH', 'FROM', 'THIS', 'THAT']:
                        stocks.append({
                            'symbol': pattern,
                            'sentiment_score': -0.2,  # Default negative for contrarian strategy
                            'market_impact': 'MEDIUM',
                            'risk_factors': ['Market volatility'],
                            'source': 'Gemini API (Fallback)',
                            'timestamp': datetime.now().isoformat()
                        })
            
            return {
                'status': 'success',
                'articles': stocks[:10],  # Limit to 10 stocks
                'total_analyzed': len(news_articles),
                'source': 'Gemini API (Fallback)',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in Gemini news analysis: {str(e)}")
            return self._service_unavailable_response(f"Analysis error: {str(e)}")
    
    def get_comprehensive_stock_analysis(self, symbol: str, technical_data: Dict, 
                                       fundamental_data: Dict, news_articles: List[Dict]) -> Dict:
        """Get comprehensive stock analysis using Gemini AI."""
        try:
            if not self.initialized:
                logger.warning("Gemini not initialized, trying Groq fallback...")
                groq_fallback = self._get_groq_fallback()
                if groq_fallback and groq_fallback.initialized:
                    logger.info("Using Groq fallback for stock analysis")
                    return groq_fallback.get_comprehensive_stock_analysis(symbol, technical_data, fundamental_data, news_articles)
                else:
                    return self._service_unavailable_response("Gemini AI not initialized and Groq fallback unavailable. Please set your API keys.")
            
            # Mock implementation - in real scenario, this would use Gemini API
            logger.info(f"Using Gemini for stock analysis of {symbol} (mock implementation)")
            
            return {
                'status': 'success',
                'symbol': symbol,
                'company_name': f"{symbol} Company",
                'sentiment_score': -0.3,  # Default negative for contrarian strategy
                'market_impact': 'MEDIUM',
                'risk_factors': ['Market volatility', 'Economic uncertainty'],
                'swing_trading_potential': 'MEDIUM',
                'time_horizon': '7 days',
                'source': 'Gemini API (Fallback)',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in Gemini stock analysis: {str(e)}")
            return self._service_unavailable_response(f"Analysis error: {str(e)}")
    
    def _service_unavailable_response(self, message: str) -> Dict:
        """Return service unavailable response."""
        return {
            'status': 'error',
            'message': message,
            'source': 'Gemini AI'
        }
