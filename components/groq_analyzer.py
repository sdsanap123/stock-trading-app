#!/usr/bin/env python3
"""
Groq News Analyzer Component
Groq AI-powered news analysis.
"""

import requests
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
import time
import random

logger = logging.getLogger(__name__)

class GroqNewsAnalyzer:
    """Groq API-powered news analyzer."""
    
    def __init__(self):
        self.api_key = None
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.initialized = False
        self._initialize()
    
    def _initialize(self):
        """Initialize Groq API."""
        try:
            # Try to get API key from environment or config
            import os
            self.api_key = os.getenv('GROQ_API_KEY')
            if self.api_key:
                self.initialized = True
                logger.info("Groq AI initialized successfully")
            else:
                logger.warning("Groq API key not found. Set GROQ_API_KEY environment variable.")
        except Exception as e:
            logger.error(f"Error initializing Groq AI: {str(e)}")
    
    def set_api_key(self, api_key: str):
        """Set API key and validate it."""
        try:
            if not api_key or not api_key.strip():
                self.api_key = None
                self.initialized = False
                logger.warning("Empty API key provided")
                return False
            
            self.api_key = api_key.strip()
            
            # Test the API key with a simple request
            if self._validate_api_key():
                self.initialized = True
                logger.info("Groq API key validated and set successfully")
                return True
            else:
                self.initialized = False
                logger.error("Invalid Groq API key")
                return False
                
        except Exception as e:
            logger.error(f"Error setting Groq API key: {str(e)}")
            self.initialized = False
            return False
    
    def _validate_api_key(self) -> bool:
        """Validate the API key with a simple test request."""
        try:
            if not self.api_key:
                return False
            
            # Make a simple test request to validate the API key
            import requests
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Simple test payload
            test_payload = {
                "model": "llama-3.1-8b-instant",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10
            }
            
            response = requests.post(
                self.base_url,
                headers=headers,
                json=test_payload,
                timeout=10
            )
            
            if response.status_code == 200:
                return True
            elif response.status_code == 401:
                logger.error("Groq API key validation failed: Unauthorized")
                return False
            else:
                logger.warning(f"Groq API key validation returned status {response.status_code}")
                return True  # Assume valid if not 401
                
        except Exception as e:
            logger.error(f"Error validating Groq API key: {str(e)}")
            return False
    
    def _make_request_with_retry(self, payload: Dict, max_retries: int = 3) -> Optional[Dict]:
        """Make API request with retry logic for rate limiting."""
        for attempt in range(max_retries):
            try:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                response = requests.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:  # Rate limited
                    if attempt < max_retries - 1:
                        # Exponential backoff with jitter
                        wait_time = (2 ** attempt) + random.uniform(0, 1)
                        logger.warning(f"Rate limited, waiting {wait_time:.1f}s before retry {attempt + 1}/{max_retries}")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error("Rate limited after all retries")
                        return None
                elif response.status_code == 401:
                    logger.error("Authentication failed - invalid API key")
                    return None
                else:
                    logger.error(f"API request failed with status {response.status_code}: {response.text}")
                    return None
                    
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"Request timeout, waiting {wait_time:.1f}s before retry {attempt + 1}/{max_retries}")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error("Request timeout after all retries")
                    return None
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"Request error: {str(e)}, waiting {wait_time:.1f}s before retry {attempt + 1}/{max_retries}")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Request failed after all retries: {str(e)}")
                    return None
        
        return None
    
    def _get_gemini_fallback(self):
        """Get Gemini analyzer as fallback."""
        try:
            # Import here to avoid circular imports
            from .gemini_analyzer import GeminiAIAnalyzer
            return GeminiAIAnalyzer()
        except Exception as e:
            logger.error(f"Could not initialize Gemini fallback: {str(e)}")
            return None
    
    def analyze_top_10_news_with_full_content(self, news_articles: List[Dict]) -> Dict:
        """Analyze top 10 news articles with full content for stock sentiment."""
        try:
            if not self.initialized:
                logger.warning("Groq not initialized, trying Gemini fallback...")
                gemini_fallback = self._get_gemini_fallback()
                if gemini_fallback and gemini_fallback.initialized:
                    logger.info("Using Gemini fallback for news analysis")
                    return gemini_fallback.analyze_top_10_news_with_full_content(news_articles)
                else:
                    return self._service_unavailable_response("Groq AI not initialized and Gemini fallback unavailable. Please set your API keys.")
            
            if not news_articles:
                return self._service_unavailable_response("No news articles provided for analysis.")
            
            # Prepare full content for analysis with length limits
            full_content = ""
            for i, article in enumerate(news_articles[:10]):  # Top 10 articles
                # Limit content length to prevent JSON issues
                title = article.get('title', '')[:200]
                content = article.get('full_content', article.get('description', ''))
                if len(content) > 1500:  # Limit content to 1500 characters per article
                    content = content[:1500] + "..."
                
                full_content += f"\n--- ARTICLE {i+1} ---\n"
                full_content += f"Title: {title}\n"
                full_content += f"Published: {article.get('publishedAt', '')}\n"
                full_content += f"Source: {article.get('source', '')}\n"
                full_content += f"Content: {content}\n"
            
            prompt = f"""You are a senior financial analyst specializing in Indian stock markets. Analyze the following news articles and identify stocks with significant sentiment impact and price relevance.

NEWS ARTICLES:
{full_content}

CRITICAL ANALYSIS REQUIREMENTS:
1. RELEVANCE CHECK: Only include articles that are directly relevant to specific NSE-listed Indian stocks
2. PRICE IMPACT ASSESSMENT: Focus on news that can significantly impact stock prices in the next 7 days
3. SWING TRADING FOCUS: Prioritize news suitable for short-term swing trading opportunities

FOCUS ONLY on these high-impact news types:
1. EARNINGS REPORTS - Quarterly results, profit/loss announcements, guidance updates
2. LARGE DEALS - Mergers, acquisitions, partnerships, major contracts (>₹1000 crores)
3. GOVERNMENT DECISIONS - Policy changes, budget allocations, regulatory approvals
4. SECTOR-SPECIFIC IMPACT - Government decisions affecting specific industries
5. MAJOR CORPORATE ACTIONS - Stock splits, bonus issues, dividend announcements
6. REGULATORY CHANGES - SEBI decisions, RBI policies, sector-specific regulations

EXAMPLES of High-Impact Government News:
- Railway budget increase → Positive for IRCON, RVNL, TITAGARH, BEML
- Defense budget allocation → Positive for BEL, HAL, BDL, MIDHANI
- Infrastructure spending → Positive for LT, NCC, KEC, PNC Infratech
- Power sector reforms → Positive for NTPC, POWERGRID, TATAPOWER
- Banking sector policies → Impact on HDFCBANK, ICICIBANK, SBIN, etc.
- Telecom policy changes → Impact on BHARTIARTL, RELIANCE, VODAFONE_IDEA
- Pharma regulations → Impact on SUNPHARMA, DRREDDY, CIPLA, etc.
- FMCG tax changes → Impact on HINDUNILVR, ITC, NESTLEIND, etc.

SKIP these low-impact news types:
- General market commentary
- Analyst price targets
- Routine corporate announcements
- International news without direct Indian impact
- Vague sector outlooks without specific company impact

Respond ONLY with valid JSON in this exact format:
{{
  "stocks": [
    {{
      "symbol": "NSE_SYMBOL",
      "company_name": "Full Company Name",
      "news_summary": "2-3 sentence summary focusing on specific impact and relevance",
      "sentiment_score": -1.0,
      "sentiment_label": "POSITIVE",
      "impact_level": "HIGH",
      "key_factors": ["specific earnings beat", "major deal announcement", "regulatory approval"],
      "price_impact": "UPWARD",
      "confidence": 0.8,
      "news_type": "EARNINGS/DEAL/GOVERNMENT/REGULATORY/OTHER",
      "swing_trading_potential": "HIGH/MEDIUM/LOW",
      "time_horizon": "1-3 days/3-7 days/1-2 weeks"
    }}
  ]
}}

Guidelines:
- sentiment_score: -1.0 (very negative) to 1.0 (very positive)
- sentiment_label: "POSITIVE", "NEGATIVE", or "NEUTRAL"
- impact_level: "HIGH" (significant price impact), "MEDIUM", or "LOW"
- price_impact: "UPWARD", "DOWNWARD", or "NEUTRAL"
- confidence: 0.0 to 1.0 (how confident you are about the impact)
- key_factors: Array of 2-4 specific factors (earnings beat, major deal, regulatory approval, etc.)
- news_type: "EARNINGS", "DEAL", "GOVERNMENT", "REGULATORY", or "OTHER"
- swing_trading_potential: "HIGH" (strong short-term opportunity), "MEDIUM", or "LOW"
- time_horizon: Expected timeframe for price impact
- Use proper JSON escaping for quotes in strings

Focus ONLY on NSE-listed Indian stocks from major sectors:
- Banking & Financial Services (HDFCBANK, ICICIBANK, SBIN, KOTAKBANK, AXISBANK, etc.)
- IT & Technology (TCS, INFY, HCLTECH, WIPRO, TECHM, etc.)
- Pharmaceuticals (SUNPHARMA, DRREDDY, CIPLA, BIOCON, LUPIN, etc.)
- Automobiles (MARUTI, TATAMOTORS, BAJAJ-AUTO, EICHERMOT, HEROMOTOCO, etc.)
- Energy & Oil (RELIANCE, ONGC, BPCL, IOC, ADANIPOWER, etc.)
- Metals & Mining (TATASTEEL, HINDALCO, JSWSTEEL, SAIL, VEDL, etc.)
- FMCG (HINDUNILVR, ITC, NESTLEIND, BRITANNIA, DABUR, etc.)
- Infrastructure (LT, ADANIPORTS, POWERGRID, NTPC, IRCON, etc.)

CRITICAL: Only use valid NSE stock symbols. Do NOT use:
- US stock symbols (like SCHW, CM, MAN)
- Delisted stocks
- Invalid symbols
- Symbols with suffixes (.NS, .BO, etc.)

Government-Sensitive Stocks for Swing Trading:
- Railway: IRCON, RVNL, TITAGARH, BEML, TEXRAIL
- Defense: BEL, HAL, BDL, MIDHANI, BHARATFORG
- Infrastructure: NCC, KEC, PNC Infratech, GMR Infra, GVK Power
- Power: NTPC, POWERGRID, TATAPOWER, ADANIPOWER, TORRENT
- PSU Banks: SBIN, PNB, BOI, CANBK, UNIONBANK
- Oil PSUs: ONGC, IOC, BPCL, HPCL, GAIL
- Telecom: BHARTIARTL, RELIANCE, VODAFONE_IDEA

Provide analysis for the most impactful news affecting NSE-listed Indian stocks suitable for 7-day swing trading."""

            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # Use currently available models (desktop app models were decommissioned)
            models_to_try = [
                "llama-3.1-8b-instant",     # Primary working model
                "llama-3.3-70b-versatile",  # Alternative if available
                "llama-3.1-70b-versatile"   # Fallback if available
            ]
            
            # Try up to 3 times with different models
            for attempt in range(3):
                response = self._try_models_request(models_to_try, headers, prompt, timeout=60)
                
                if response is not None and response.status_code == 200:
                    result = response.json()
                    content = result['choices'][0]['message']['content']
                    
                    # Try to fix common JSON issues
                    fixed_content = self._fix_json_response(content)
                    
                    try:
                        news_data = json.loads(fixed_content)
                        formatted_news = []
                        
                        # Handle both object format (with 'stocks' key) and array format
                        if isinstance(news_data, dict) and 'stocks' in news_data:
                            stocks_list = news_data.get('stocks', [])
                        elif isinstance(news_data, list):
                            stocks_list = news_data
                        else:
                            stocks_list = []
                        
                        for stock in stocks_list:
                            if isinstance(stock, dict):
                                symbol = stock.get('symbol', 'UNKNOWN')
                                
                                # Clean and validate symbol
                                clean_symbol = symbol.split('.')[0].upper() if symbol else 'UNKNOWN'
                                
                                # Skip invalid symbols
                                if clean_symbol in ['UNKNOWN', 'SCHW', 'CM', 'MAN'] or len(clean_symbol) < 2:
                                    logger.warning(f"Skipping invalid stock symbol: {symbol}")
                                    continue
                                
                                formatted_news.append({
                                    'symbol': clean_symbol,
                                    'company_name': stock.get('company_name', 'Unknown Company'),
                                    'news_summary': stock.get('news_summary', 'No summary available'),
                                    'sentiment_score': float(stock.get('sentiment_score', 0)),
                                    'sentiment_label': stock.get('sentiment_label', 'NEUTRAL'),
                                    'impact_level': stock.get('impact_level', 'LOW'),
                                    'key_factors': stock.get('key_factors', []),
                                    'price_impact': stock.get('price_impact', 'NEUTRAL'),
                                    'confidence': float(stock.get('confidence', 0.5)),
                                    'news_type': stock.get('news_type', 'OTHER'),
                                    'swing_trading_potential': stock.get('swing_trading_potential', 'MEDIUM'),
                                    'time_horizon': stock.get('time_horizon', '3-7 days'),
                                    'published': datetime.now().isoformat()
                                })
                        
                        logger.info(f"✅ Successfully analyzed {len(formatted_news)} stocks from top 10 news via Groq AI (attempt {attempt + 1})")
                        return {
                            'status': 'success',
                            'articles': formatted_news,
                            'source': 'Groq API (Top 10 News Analysis)',
                            'timestamp': datetime.now().isoformat()
                        }
                        
                    except json.JSONDecodeError as e:
                        logger.warning(f"JSON decode error (attempt {attempt + 1}): {str(e)}")
                        if attempt < 2:  # Try again with different model
                            continue
                        else:
                            logger.error(f"All attempts failed to parse JSON: {str(e)}")
                            return self._service_unavailable_response(f"Invalid JSON response from Groq API: {str(e)}")
                elif response is not None:
                    logger.warning(f"Groq API error (attempt {attempt + 1}): {response.status_code}")
                    if attempt < 2:
                        continue
                else:
                    logger.warning(f"All models failed (attempt {attempt + 1})")
                    if attempt < 2:
                        continue
            
            # If we get here, all attempts failed - try Gemini fallback
            logger.error("All attempts failed to get valid response from Groq, trying Gemini fallback...")
            gemini_fallback = self._get_gemini_fallback()
            if gemini_fallback and gemini_fallback.initialized:
                logger.info("Using Gemini fallback for news analysis")
                return gemini_fallback.analyze_top_10_news_with_full_content(news_articles)
            else:
                return self._service_unavailable_response("All Groq AI models are currently unavailable and Gemini fallback unavailable. Please check your API keys and try again later.")
            
        except requests.exceptions.Timeout:
            logger.error("Groq API request timed out")
            return self._service_unavailable_response("Groq API request timed out")
        except requests.exceptions.RequestException as e:
            logger.error(f"Groq API request error: {str(e)}")
            return self._service_unavailable_response(f"Groq API request error: {str(e)}")
        except Exception as e:
            logger.error(f"Error in Groq analysis: {str(e)}")
            return self._service_unavailable_response(f"Analysis error: {str(e)}")
    
    def fetch_and_analyze_indian_stock_news(self) -> Dict:
        """Fetch and analyze Indian stock news."""
        try:
            if not self.initialized:
                return self._service_unavailable_response("Groq AI not initialized. Please set your GROQ_API_KEY.")
            
            # Real Groq API call
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            prompt = """You are a financial analyst. Analyze the top 10 most significant stock-related news from India focusing on NSE-listed equity stocks. 

IMPORTANT: Respond ONLY with valid JSON. Do not include any explanatory text, markdown formatting, or code blocks. Just return the raw JSON.

Required JSON format (respond with exactly this structure):
{
  "stocks": [
    {
      "symbol": "NSE_SYMBOL",
      "company_name": "Full Company Name",
      "news_summary": "2-3 sentence summary of the news",
      "sentiment_score": -1.0,
      "sentiment_label": "POSITIVE",
      "impact_level": "HIGH",
      "key_factors": ["factor1", "factor2", "factor3"],
      "price_impact": "UPWARD",
      "confidence": 0.8
    }
  ]
}

Guidelines:
- sentiment_score: Use decimal numbers between -1.0 and 1.0
- sentiment_label: Use only "POSITIVE", "NEGATIVE", or "NEUTRAL"
- impact_level: Use only "HIGH", "MEDIUM", or "LOW"
- price_impact: Use only "UPWARD", "DOWNWARD", or "NEUTRAL"
- confidence: Use decimal numbers between 0.0 and 1.0
- key_factors: Array of strings, maximum 5 items
- Use proper JSON escaping for quotes in strings

Focus on NSE equity stocks from major sectors:
- Banking & Financial Services (HDFCBANK, ICICIBANK, SBIN, KOTAKBANK, AXISBANK, etc.)
- IT & Technology (TCS, INFY, HCLTECH, WIPRO, TECHM, etc.)
- Pharmaceuticals (SUNPHARMA, DRREDDY, CIPLA, BIOCON, LUPIN, etc.)
- Automobiles (MARUTI, TATAMOTORS, BAJAJ-AUTO, EICHERMOT, HEROMOTOCO, etc.)
- Energy & Oil (RELIANCE, ONGC, BPCL, IOC, ADANIPOWER, etc.)
- Metals & Mining (TATASTEEL, HINDALCO, JSWSTEEL, SAIL, VEDL, etc.)
- FMCG (HINDUNILVR, ITC, NESTLEIND, BRITANNIA, DABUR, etc.)
- Infrastructure (LT, ADANIPORTS, POWERGRID, NTPC, IRCON, etc.)

Provide analysis for the most impactful news affecting NSE-listed Indian stocks today."""

            # Try different models in order of preference (matching original app)
            models_to_try = [
                "llama-3.1-8b-instant",    # Only model to use
                "mixtral-8x7b-32768",      # Alternative high-performance model
                "gemma-7b-it"              # Google's model
            ]
            
            # Use the first available model
            model = models_to_try[0]
            
            data = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 4000
            }
            
            # Try the request with fallback models
            response = self._try_models_request(models_to_try, headers, prompt, timeout=30)
            
            if response is not None and response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # Parse JSON response
                try:
                    news_data = json.loads(content)
                    formatted_news = []
                    
                    # Handle both object format (with 'stocks' key) and array format
                    if isinstance(news_data, dict) and 'stocks' in news_data:
                        stocks_list = news_data.get('stocks', [])
                    elif isinstance(news_data, list):
                        stocks_list = news_data
                    else:
                        stocks_list = []
                    
                    for stock in stocks_list:
                        if isinstance(stock, dict):
                            formatted_news.append({
                                'symbol': stock.get('symbol', 'UNKNOWN'),
                                'company_name': stock.get('company_name', 'Unknown Company'),
                                'news_summary': stock.get('news_summary', 'No summary available'),
                                'sentiment_score': float(stock.get('sentiment_score', 0)),
                                'sentiment_label': stock.get('sentiment_label', 'NEUTRAL'),
                                'impact_level': stock.get('impact_level', 'LOW'),
                                'key_factors': stock.get('key_factors', []),
                                'price_impact': stock.get('price_impact', 'NEUTRAL'),
                                'confidence': float(stock.get('confidence', 0.5)),
                                'published': datetime.now().isoformat()
                            })
                    
                    logger.info(f"✅ Successfully analyzed {len(formatted_news)} Indian stocks via Groq AI")
                    return {
                        'status': 'success',
                        'articles': formatted_news,
                        'source': 'Groq API',
                        'timestamp': datetime.now().isoformat()
                    }
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing Groq response: {str(e)}")
                    return self._service_unavailable_response(f"Invalid JSON response from Groq API: {str(e)}")
            elif response is not None:
                logger.error(f"Groq API error: {response.status_code} - {response.text}")
                return self._service_unavailable_response(f"Groq API error: {response.status_code}")
            else:
                logger.error("All Groq models failed - no response received")
                return self._service_unavailable_response("All Groq AI models are currently unavailable. Please check your API key and try again later.")
            
        except requests.exceptions.Timeout:
            logger.error("Groq API request timed out")
            return self._service_unavailable_response("Groq API request timed out")
        except requests.exceptions.RequestException as e:
            logger.error(f"Groq API request error: {str(e)}")
            return self._service_unavailable_response(f"Groq API request error: {str(e)}")
        except Exception as e:
            logger.error(f"Error in Groq analysis: {str(e)}")
            return self._service_unavailable_response(f"Analysis error: {str(e)}")
    
    def get_comprehensive_stock_analysis(self, stock_symbol: str, technical_data: Dict, 
                                       fundamental_data: Dict, news_articles: List[Dict]) -> Dict:
        """Get comprehensive stock analysis using Groq AI with all data sources."""
        try:
            if not self.initialized:
                return self._service_unavailable_response("Groq AI not initialized. Please set your GROQ_API_KEY.")
            
            # Format all data for comprehensive analysis
            technical_summary = self._format_technical_data_for_groq(technical_data)
            fundamental_summary = self._format_fundamental_data_for_groq(fundamental_data)
            news_summary = self._format_news_data_for_groq(news_articles)
            
            prompt = f"""You are a senior financial analyst. Provide a comprehensive analysis of {stock_symbol} considering all available data.

TECHNICAL ANALYSIS:
{technical_summary}

FUNDAMENTAL ANALYSIS:
{fundamental_summary}

NEWS SENTIMENT:
{news_summary}

Provide a comprehensive analysis in JSON format:
{{
  "overall_score": 0.0 to 1.0,
  "recommendation": "BUY/SELL/HOLD",
  "confidence": 0.0 to 1.0,
  "reasoning": "Detailed reasoning for the recommendation",
  "key_factors": ["factor1", "factor2", "factor3"],
  "risk_assessment": "LOW/MEDIUM/HIGH",
  "time_horizon": "SHORT/MEDIUM/LONG",
  "price_target": "Expected price range",
  "stop_loss": "Risk management level",
  "technical_insights": "Technical analysis summary",
  "fundamental_insights": "Fundamental analysis summary",
  "sentiment_insights": "News sentiment summary",
  "market_outlook": "Overall market perspective"
}}

Focus on:
1. Integration of all data sources
2. Risk-reward assessment
3. Market timing considerations
4. Technical and fundamental alignment
5. News sentiment impact
6. Actionable insights for swing trading

Provide only valid JSON response."""

            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # Use currently available models (desktop app models were decommissioned)
            models_to_try = [
                "llama-3.1-8b-instant",     # Primary working model
                "llama-3.3-70b-versatile",  # Alternative if available
                "llama-3.1-70b-versatile"   # Fallback if available
            ]
            
            response = self._try_models_request(models_to_try, headers, prompt, timeout=30)
            
            if response is not None and response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                try:
                    # Try to fix the JSON response first
                    fixed_content = self._fix_json_response(content)
                    analysis_data = json.loads(fixed_content)
                    return {
                        'status': 'success',
                        'overall_score': float(analysis_data.get('overall_score', 0.5)),
                        'recommendation': analysis_data.get('recommendation', 'HOLD'),
                        'confidence': float(analysis_data.get('confidence', 0.5)),
                        'reasoning': analysis_data.get('reasoning', 'No reasoning provided'),
                        'key_factors': analysis_data.get('key_factors', []),
                        'risk_assessment': analysis_data.get('risk_assessment', 'MEDIUM'),
                        'time_horizon': analysis_data.get('time_horizon', 'MEDIUM'),
                        'price_target': analysis_data.get('price_target', 'N/A'),
                        'stop_loss': analysis_data.get('stop_loss', 'N/A'),
                        'technical_insights': analysis_data.get('technical_insights', 'No technical insights'),
                        'fundamental_insights': analysis_data.get('fundamental_insights', 'No fundamental insights'),
                        'sentiment_insights': analysis_data.get('sentiment_insights', 'No sentiment insights'),
                        'market_outlook': analysis_data.get('market_outlook', 'No market outlook'),
                        'source': 'Groq API',
                        'timestamp': datetime.now().isoformat()
                    }
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing comprehensive Groq response: {str(e)}")
                    return self._service_unavailable_response(f"Invalid JSON response: {str(e)}")
            elif response is not None:
                logger.error(f"Groq API error for comprehensive analysis: {response.status_code}")
                return self._service_unavailable_response(f"Groq API error: {response.status_code}")
            else:
                logger.error("All Groq models failed for comprehensive analysis - no response received")
                return self._service_unavailable_response("All available Groq models are currently unavailable. Please try again later.")
            
        except requests.exceptions.Timeout:
            logger.error("Groq API request timed out for comprehensive analysis")
            return self._service_unavailable_response("Groq API request timed out")
        except requests.exceptions.RequestException as e:
            logger.error(f"Groq API request error for comprehensive analysis: {str(e)}")
            return self._service_unavailable_response(f"Groq API request error: {str(e)}")
        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {str(e)}")
            return self._service_unavailable_response(f"Analysis error: {str(e)}")
    
    def get_stock_specific_analysis(self, news_articles: List[Dict], stock_symbol: str) -> Dict:
        """Get stock-specific analysis."""
        try:
            if not self.initialized:
                return self._service_unavailable_response("Groq AI not initialized. Please set your GROQ_API_KEY.")
            
            # Filter news articles for this specific stock
            stock_news = []
            for article in news_articles:
                title = article.get('title', '').upper()
                description = article.get('description', '').upper()
                if stock_symbol.upper() in title or stock_symbol.upper() in description:
                    stock_news.append(article)
            
            if not stock_news:
                return {
                    'status': 'success',
                    'sentiment_score': 0.0,
                    'confidence': 0.3,
                    'key_insights': ['No specific news found for this stock'],
                    'source': 'Groq API',
                    'message': f'No news articles found for {stock_symbol}'
                }
            
            # Create prompt for stock-specific analysis
            news_text = ""
            for article in stock_news[:5]:  # Limit to 5 most relevant articles
                news_text += f"Title: {article.get('title', '')}\n"
                news_text += f"Description: {article.get('description', '')}\n\n"
            
            prompt = f"""Analyze the following news articles for {stock_symbol} and provide sentiment analysis.

News Articles:
{news_text}

Respond ONLY with valid JSON in this exact format:
{{
  "sentiment_score": -1.0,
  "confidence": 0.8,
  "key_insights": ["insight1", "insight2", "insight3"],
  "market_impact": "HIGH",
  "risk_factors": ["risk1", "risk2"]
}}

Guidelines:
- sentiment_score: -1.0 (very negative) to 1.0 (very positive)
- confidence: 0.0 to 1.0
- key_insights: Array of 2-4 key insights
- market_impact: "HIGH", "MEDIUM", or "LOW"
- risk_factors: Array of potential risks (optional)"""

            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # Use currently available models (desktop app models were decommissioned)
            models_to_try = [
                "llama-3.1-8b-instant",     # Primary working model
                "llama-3.3-70b-versatile",  # Alternative if available
                "llama-3.1-70b-versatile"   # Fallback if available
            ]
            
            response = self._try_models_request(models_to_try, headers, prompt, timeout=15)
            
            if response is not None and response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                try:
                    # Try to fix the JSON response first
                    fixed_content = self._fix_json_response(content)
                    analysis_data = json.loads(fixed_content)
                    return {
                        'status': 'success',
                        'sentiment_score': float(analysis_data.get('sentiment_score', 0)),
                        'confidence': float(analysis_data.get('confidence', 0.5)),
                        'key_insights': analysis_data.get('key_insights', []),
                        'market_impact': analysis_data.get('market_impact', 'MEDIUM'),
                        'risk_factors': analysis_data.get('risk_factors', []),
                        'source': 'Groq API',
                        'timestamp': datetime.now().isoformat()
                    }
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing stock-specific Groq response: {str(e)}")
                    return self._service_unavailable_response(f"Invalid JSON response: {str(e)}")
            elif response is not None:
                logger.error(f"Groq API error for stock analysis: {response.status_code}")
                return self._service_unavailable_response(f"Groq API error: {response.status_code}")
            else:
                logger.error("All Groq models failed for stock analysis - trying Gemini fallback...")
                gemini_fallback = self._get_gemini_fallback()
                if gemini_fallback and gemini_fallback.initialized:
                    logger.info("Using Gemini fallback for stock analysis")
                    return gemini_fallback.get_comprehensive_stock_analysis(symbol, technical_data, fundamental_data, news_articles)
                else:
                    return self._service_unavailable_response("All available Groq models are currently unavailable and Gemini fallback unavailable. Please try again later.")
            
        except requests.exceptions.Timeout:
            logger.error("Groq API request timed out for stock analysis")
            return self._service_unavailable_response("Groq API request timed out")
        except requests.exceptions.RequestException as e:
            logger.error(f"Groq API request error for stock analysis: {str(e)}")
            return self._service_unavailable_response(f"Groq API request error: {str(e)}")
        except Exception as e:
            logger.error(f"Error in stock-specific analysis: {str(e)}")
            return self._service_unavailable_response(f"Analysis error: {str(e)}")
    
    def _try_models_request(self, models_to_try: List[str], headers: Dict, prompt: str, timeout: int = 30) -> Optional[requests.Response]:
        """Try different models until one works."""
        failed_models = []
        
        for model in models_to_try:
            try:
                data = {
                    "model": model,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.3,
                    "max_tokens": 4000
                }
                
                # Use retry logic for this request
                response_data = self._make_request_with_retry(data)
                
                if response_data:
                    logger.info(f"✅ Successfully used model: {model}")
                    # Create a mock response object with the data
                    class MockResponse:
                        def __init__(self, data):
                            self.status_code = 200
                            self.json_data = data
                        def json(self):
                            return self.json_data
                        @property
                        def text(self):
                            return json.dumps(self.json_data)
                    return MockResponse(response_data)
                else:
                    # Request failed after retries, try next model
                    error_msg = f"Model {model} failed after retries"
                    failed_models.append(error_msg)
                    logger.warning(f"⚠️ {error_msg}, trying next...")
                    continue
                    
            except requests.exceptions.Timeout:
                error_msg = f"Model {model} timed out"
                failed_models.append(error_msg)
                logger.warning(f"⚠️ {error_msg}, trying next...")
                continue
            except requests.exceptions.RequestException as e:
                error_msg = f"Model {model} request error: {str(e)}"
                failed_models.append(error_msg)
                logger.warning(f"⚠️ {error_msg}, trying next...")
                continue
        
        logger.error(f"❌ All models failed. Failed models: {', '.join(failed_models)}")
        return None
    
    def _format_technical_data_for_groq(self, technical_data: Dict) -> str:
        """Format technical data for Groq comprehensive analysis."""
        if not technical_data:
            return "No technical data available"
        
        formatted = []
        formatted.append(f"Current Price: ₹{technical_data.get('current_price', 'N/A')}")
        formatted.append(f"RSI (14): {technical_data.get('rsi', 'N/A')}")
        formatted.append(f"MACD: {technical_data.get('macd', 'N/A')}")
        formatted.append(f"Stochastic K: {technical_data.get('stochastic_k', 'N/A')}")
        formatted.append(f"Williams %R: {technical_data.get('williams_r', 'N/A')}")
        formatted.append(f"Bollinger Bands: Upper={technical_data.get('bb_upper', 'N/A')}, Middle={technical_data.get('bb_middle', 'N/A')}, Lower={technical_data.get('bb_lower', 'N/A')}")
        formatted.append(f"Moving Averages: SMA 10={technical_data.get('sma_10', 'N/A')}, SMA 20={technical_data.get('sma_20', 'N/A')}, SMA 50={technical_data.get('sma_50', 'N/A')}")
        formatted.append(f"Volume Ratio (20-day): {technical_data.get('volume_ratio_20', 'N/A')}")
        formatted.append(f"Price Changes: 1D={technical_data.get('price_change_1d', 'N/A')}%, 5D={technical_data.get('price_change_5d', 'N/A')}%, 20D={technical_data.get('price_change_20d', 'N/A')}%")
        formatted.append(f"Trend Analysis: Short={technical_data.get('trend_short', 'N/A')}, Medium={technical_data.get('trend_medium', 'N/A')}, Long={technical_data.get('trend_long', 'N/A')}")
        formatted.append(f"Technical Score: {technical_data.get('technical_score', 'N/A')}")
        
        return "\n".join(formatted)
    
    def _format_fundamental_data_for_groq(self, fundamental_data: Dict) -> str:
        """Format fundamental data for Groq comprehensive analysis."""
        if not fundamental_data:
            return "No fundamental data available"
        
        formatted = []
        
        # Check if we have detailed fundamental analysis
        if 'ratings' in fundamental_data and 'metrics' in fundamental_data:
            # Detailed analysis from FundamentalAnalyzer
            ratings = fundamental_data.get('ratings', {})
            metrics = fundamental_data.get('metrics', {})
            raw_data = fundamental_data.get('raw_data', {})
            
            formatted.append(f"Overall Fundamental Score: {fundamental_data.get('score', 0):.2f}")
            formatted.append(f"Valuation Rating: {ratings.get('valuation', 'N/A')} (Score: {metrics.get('valuation_score', 0):.2f})")
            formatted.append(f"Profitability Rating: {ratings.get('profitability', 'N/A')} (Score: {metrics.get('profitability_score', 0):.2f})")
            formatted.append(f"Growth Rating: {ratings.get('growth', 'N/A')} (Score: {metrics.get('growth_score', 0):.2f})")
            formatted.append(f"Financial Health Rating: {ratings.get('financial_health', 'N/A')} (Score: {metrics.get('health_score', 0):.2f})")
            formatted.append(f"Efficiency Rating: {ratings.get('efficiency', 'N/A')} (Score: {metrics.get('efficiency_score', 0):.2f})")
            
            # Key ratios
            formatted.append(f"P/E Ratio: {raw_data.get('pe_ratio', 'N/A')}")
            formatted.append(f"P/B Ratio: {raw_data.get('pb_ratio', 'N/A')}")
            formatted.append(f"ROE: {raw_data.get('roe', 'N/A')}%")
            formatted.append(f"ROA: {raw_data.get('roa', 'N/A')}%")
            formatted.append(f"Debt/Equity: {raw_data.get('debt_equity', 'N/A')}")
            formatted.append(f"Current Ratio: {raw_data.get('current_ratio', 'N/A')}")
        else:
            # Basic fundamental data
            formatted.append(f"P/E Ratio: {fundamental_data.get('pe_ratio', 'N/A')}")
            formatted.append(f"P/B Ratio: {fundamental_data.get('pb_ratio', 'N/A')}")
            formatted.append(f"ROE: {fundamental_data.get('roe', 'N/A')}")
            formatted.append(f"ROA: {fundamental_data.get('roa', 'N/A')}")
            formatted.append(f"Debt/Equity: {fundamental_data.get('debt_equity', 'N/A')}")
            formatted.append(f"Current Ratio: {fundamental_data.get('current_ratio', 'N/A')}")
            formatted.append(f"Score: {fundamental_data.get('score', 'N/A')}")
        
        return "\n".join(formatted)
    
    def _format_news_data_for_groq(self, news_articles: List[Dict]) -> str:
        """Format news data for Groq comprehensive analysis."""
        if not news_articles:
            return "No news data available"
        
        formatted = []
        formatted.append(f"Total News Articles: {len(news_articles)}")
        
        for i, article in enumerate(news_articles[:5]):  # Limit to top 5 articles
            title = article.get('title', 'No title')
            description = article.get('description', 'No description')
            sentiment = article.get('sentiment_score', 0)
            formatted.append(f"Article {i+1}: {title}")
            formatted.append(f"  Description: {description[:100]}...")
            formatted.append(f"  Sentiment: {sentiment:.2f}")
        
        return "\n".join(formatted)
    
    def _service_unavailable_response(self, message: str) -> Dict:
        """Return service unavailable response."""
        return {
            'status': 'error',
            'message': message,
            'source': 'Groq AI'
        }
    
    def _fix_json_response(self, content: str) -> str:
        """Try to fix common JSON issues in Groq responses."""
        try:
            # First, try to extract JSON from code blocks
            if '```' in content:
                # Look for JSON code blocks
                if '```json' in content:
                    start_marker = '```json'
                    end_marker = '```'
                elif '```' in content:
                    # Generic code block
                    start_marker = '```'
                    end_marker = '```'
                else:
                    start_marker = None
                    end_marker = None
                
                if start_marker and end_marker:
                    start_idx = content.find(start_marker)
                    if start_idx >= 0:
                        start_idx += len(start_marker)
                        end_idx = content.find(end_marker, start_idx)
                        if end_idx > start_idx:
                            content = content[start_idx:end_idx].strip()
            
            # Remove any text before the first {
            start_idx = content.find('{')
            if start_idx > 0:
                content = content[start_idx:]
            
            # Remove any text after the last }
            end_idx = content.rfind('}')
            if end_idx > 0:
                content = content[:end_idx + 1]
            
            # Try to fix unterminated strings by finding the last complete object
            if content.count('{') > content.count('}'):
                # Find the last complete object
                brace_count = 0
                last_complete_idx = -1
                for i, char in enumerate(content):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            last_complete_idx = i
                
                if last_complete_idx > 0:
                    content = content[:last_complete_idx + 1]
            
            # Try to fix unterminated strings by truncating at the last complete quote
            if content.count('"') % 2 != 0:
                # Find the last complete string
                quote_count = 0
                last_complete_quote = -1
                for i, char in enumerate(content):
                    if char == '"' and (i == 0 or content[i-1] != '\\'):
                        quote_count += 1
                        if quote_count % 2 == 0:
                            last_complete_quote = i
                
                if last_complete_quote > 0:
                    # Find the next } after the last complete quote
                    next_brace = content.find('}', last_complete_quote)
                    if next_brace > 0:
                        content = content[:next_brace + 1]
            
            return content
            
        except Exception as e:
            logger.warning(f"Error fixing JSON response: {str(e)}")
            return content
