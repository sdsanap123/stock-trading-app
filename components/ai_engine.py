#!/usr/bin/env python3
"""
AI Recommendation Engine Component
AI-powered recommendation engine with contrarian analysis capabilities.
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class AIRecommendationEngine:
    """AI-powered recommendation engine with contrarian analysis capabilities."""
    
    def __init__(self):
        self.learning_data = []
        self.performance_history = []
        self.recommendation_tracker = None
        
        # Initialize fundamental analyzer
        try:
            from .fundamental_analyzer import FundamentalAnalyzer
            self.fundamental_analyzer = FundamentalAnalyzer()
            logger.info("Fundamental analyzer initialized successfully")
        except ImportError as e:
            logger.warning(f"Could not import fundamental analyzer: {str(e)}")
            self.fundamental_analyzer = None
        except Exception as e:
            logger.warning(f"Fundamental analyzer initialization failed: {str(e)}")
            self.fundamental_analyzer = None
        
        self.fundamental_ratings = {}
        logger.info("AI Recommendation Engine initialized with contrarian analysis capabilities")
    
    def set_fundamental_analyzer(self, fundamental_analyzer):
        """Set the fundamental analyzer instance."""
        self.fundamental_analyzer = fundamental_analyzer
        if fundamental_analyzer:
            logger.info("Fundamental analyzer set successfully")
        else:
            logger.warning("Fundamental analyzer set to None")
    
    def generate_ai_recommendation(self, stock_data: Dict, technical_analysis: Dict, 
                                 news_sentiment: float, catalysts: List[str], groq_analysis: Dict = None, 
                                 gemini_analysis: Dict = None) -> Dict:
        """Generate AI-powered recommendation with new criteria: negative sentiment + bearish technical indicators."""
        try:
            # New criteria: Recommend stocks with negative sentiment and bearish technical indicators
            # This is for contrarian/oversold opportunities
            
            # Check if all required data is available
            if not self._validate_required_data(technical_analysis, groq_analysis, news_sentiment, stock_data):
                return {
                    'action': 'SKIP',
                    'confidence': 0,
                    'reasoning': 'Missing required data (news, technical, or fundamental analysis)',
                    'target_price': 0,
                    'stop_loss': 0,
                    'technical_data': technical_analysis,
                    'fundamental_data': stock_data,
                    'groq_analysis': groq_analysis,
                    'gemini_analysis': gemini_analysis
                }
            
            # Check negative sentiment requirement
            sentiment_negative = self._check_negative_sentiment(news_sentiment, groq_analysis)
            if not sentiment_negative:
                return {
                    'action': 'SKIP',
                    'confidence': 0,
                    'reasoning': 'Sentiment not negative enough for contrarian opportunity',
                    'target_price': 0,
                    'stop_loss': 0,
                    'technical_data': technical_analysis,
                    'fundamental_data': stock_data,
                    'groq_analysis': groq_analysis,
                    'gemini_analysis': gemini_analysis
                }
            
            # Check bearish technical indicators (3-4 out of 4 should be bearish, 1 neutral)
            technical_bearish_count, technical_neutral_count = self._count_bearish_indicators(technical_analysis)
            
            if technical_bearish_count < 3 or (technical_bearish_count + technical_neutral_count) < 4:
                return {
                    'action': 'SKIP',
                    'confidence': 0,
                    'reasoning': f'Insufficient bearish technical indicators ({technical_bearish_count} bearish, {technical_neutral_count} neutral)',
                    'target_price': 0,
                    'stop_loss': 0,
                    'technical_data': technical_analysis,
                    'fundamental_data': stock_data,
                    'groq_analysis': groq_analysis,
                    'gemini_analysis': gemini_analysis
                }
            
            # Calculate AI score based on new criteria
            ai_score = self._calculate_contrarian_score(technical_analysis, groq_analysis, news_sentiment)
            
            # Determine recommendation based on contrarian score
            if ai_score >= 0.6:  # High contrarian opportunity
                action = 'BUY'
                confidence = min(95, ai_score * 100)
            elif ai_score >= 0.4:  # Medium contrarian opportunity
                action = 'BUY'
                confidence = min(85, ai_score * 100)
            else:
                action = 'SKIP'
                confidence = 0
            
            # Calculate target price and stop loss for BUY recommendations
            current_price = technical_analysis.get('current_price', 0)
            if current_price > 0 and action == 'BUY':
                # Contrarian strategy: Higher upside potential for oversold stocks
                target_price = current_price * (1 + (ai_score * 0.4))  # Up to 40% upside
                stop_loss = current_price * (1 - 0.12)  # 12% stop loss for contrarian plays
            else:
                target_price = 0
                stop_loss = 0
            
            # Generate reasoning for contrarian recommendation
            reasoning = self._generate_contrarian_reasoning(
                technical_analysis, groq_analysis, news_sentiment, 
                technical_bearish_count, technical_neutral_count, ai_score, action, confidence
            )
            
            # Create recommendation result
            recommendation = {
                'action': action,
                'confidence': confidence,
                'reasoning': reasoning,
                        'target_price': target_price,
                        'stop_loss': stop_loss,
                        'technical_data': technical_analysis,
                'fundamental_data': stock_data,
                        'groq_analysis': groq_analysis,
                        'gemini_analysis': gemini_analysis,
                'contrarian_score': ai_score,
                'bearish_indicators': technical_bearish_count,
                'neutral_indicators': technical_neutral_count
                    }
            
            return recommendation
            
        except Exception as e:
            logger.error(f"Error generating AI recommendation: {str(e)}")
            return {
                'action': 'SKIP',
                'confidence': 0,
                'reasoning': f'Error in analysis: {str(e)}',
                'target_price': 0,
                'stop_loss': 0,
                'technical_data': technical_analysis,
                'fundamental_data': stock_data,
                'groq_analysis': groq_analysis,
                'gemini_analysis': gemini_analysis
            }
    
    def _validate_required_data(self, technical_analysis: Dict, groq_analysis: Dict, news_sentiment: float, fundamental_data: Dict = None) -> bool:
        """Validate that all required data is available."""
        try:
            # Check technical analysis - must have all key indicators
            if not technical_analysis:
                logger.warning("Technical analysis data missing")
                return False
            
            required_technical_fields = ['current_price', 'rsi', 'macd', 'sma_20', 'volume_ratio_20']
            for field in required_technical_fields:
                if field not in technical_analysis or technical_analysis[field] is None:
                    logger.warning(f"Technical analysis missing required field: {field}")
                    return False
            
            # Check news sentiment
            if news_sentiment is None:
                logger.warning("News sentiment data missing")
                return False
            
            # Check Groq analysis
            if not groq_analysis or groq_analysis.get('status') != 'success':
                logger.warning("Groq analysis data missing or failed")
                return False
            
            # Check fundamental data if provided
            if fundamental_data is not None:
                # Check if we have at least some fundamental data
                available_fields = []
                for field in ['pe_ratio', 'pb_ratio', 'market_cap', 'current_price']:
                    if field in fundamental_data and fundamental_data[field] is not None:
                        available_fields.append(field)
                
                if not available_fields:
                    logger.warning("No fundamental data available for analysis")
                    return False
                
                # Log what data we have
                logger.info(f"Fundamental data available: {available_fields}")
                
                # Check for missing critical fields and warn but don't fail
                missing_critical = []
                for field in ['pe_ratio', 'pb_ratio']:
                    if field not in fundamental_data or fundamental_data[field] is None:
                        missing_critical.append(field)
                
                if missing_critical:
                    logger.warning(f"Missing critical fundamental fields: {missing_critical} - proceeding with available data")
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating required data: {str(e)}")
            return False
    
    def _check_negative_sentiment(self, news_sentiment: float, groq_analysis: Dict) -> bool:
        """Check if sentiment is negative enough for contrarian opportunity."""
        try:
            # Check news sentiment (should be negative)
            if news_sentiment > -0.1:  # Not negative enough
                return False
            
            # Check Groq sentiment
            if groq_analysis and groq_analysis.get('status') == 'success':
                groq_sentiment = groq_analysis.get('sentiment_score', 0)
                if groq_sentiment > -0.2:  # Not negative enough
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking negative sentiment: {str(e)}")
            return False
    
    def _count_bearish_indicators(self, technical_analysis: Dict) -> tuple:
        """Count bearish and neutral technical indicators."""
        try:
            bearish_count = 0
            neutral_count = 0
            
            # RSI - bearish if > 70, neutral if 50-70
            rsi = technical_analysis.get('rsi', 50)
            if rsi > 70:
                bearish_count += 1
            elif 50 <= rsi <= 70:
                neutral_count += 1
            
            # MACD - bearish if negative, neutral if near zero
            macd = technical_analysis.get('macd', 0)
            if macd < -0.01:
                bearish_count += 1
            elif -0.01 <= macd <= 0.01:
                neutral_count += 1
            
            # Price vs SMA - bearish if below SMA, neutral if near SMA
            current_price = technical_analysis.get('current_price', 0)
            sma_20 = technical_analysis.get('sma_20', 0)
            if current_price > 0 and sma_20 > 0:
                price_vs_sma = (current_price - sma_20) / sma_20
                if price_vs_sma < -0.02:  # 2% below SMA
                    bearish_count += 1
                elif -0.02 <= price_vs_sma <= 0.02:  # Within 2% of SMA
                    neutral_count += 1
            
            # Volume - bearish if low volume, neutral if average
            volume_ratio = technical_analysis.get('volume_ratio_20', 1)
            if volume_ratio < 0.8:  # Low volume
                bearish_count += 1
            elif 0.8 <= volume_ratio <= 1.2:  # Average volume
                neutral_count += 1
            
            return bearish_count, neutral_count
            
        except Exception as e:
            logger.error(f"Error counting bearish indicators: {str(e)}")
            return 0, 0
    
    def _calculate_contrarian_score(self, technical_analysis: Dict, groq_analysis: Dict, news_sentiment: float) -> float:
        """Calculate contrarian opportunity score."""
        try:
            score = 0.0
            
            # Sentiment component (40% weight) - more negative = higher score
            sentiment_score = abs(news_sentiment)  # Convert negative to positive
            if groq_analysis and groq_analysis.get('status') == 'success':
                groq_sentiment = abs(groq_analysis.get('sentiment_score', 0))
                sentiment_score = max(sentiment_score, groq_sentiment)
            score += sentiment_score * 0.4
            
            # Technical oversold component (35% weight)
            technical_score = 0
            rsi = technical_analysis.get('rsi', 50)
            if rsi > 70:  # Overbought - good for contrarian
                technical_score += 0.3
            elif rsi > 60:
                technical_score += 0.2
            
            # Price below SMA
            current_price = technical_analysis.get('current_price', 0)
            sma_20 = technical_analysis.get('sma_20', 0)
            if current_price > 0 and sma_20 > 0:
                price_vs_sma = (current_price - sma_20) / sma_20
                if price_vs_sma < -0.05:  # 5% below SMA
                    technical_score += 0.3
                elif price_vs_sma < -0.02:  # 2% below SMA
                    technical_score += 0.2
            
            # Low volume (contrarian signal)
            volume_ratio = technical_analysis.get('volume_ratio_20', 1)
            if volume_ratio < 0.7:
                technical_score += 0.2
            elif volume_ratio < 0.9:
                technical_score += 0.1
            
            score += min(technical_score, 1.0) * 0.35
            
            # Market conditions (25% weight)
            market_score = 0.5  # Base score
            # Add volatility component
            atr = technical_analysis.get('atr', 0)
            if atr > 0:
                # Higher volatility = higher contrarian opportunity
                market_score += 0.3
            
            score += market_score * 0.25
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating contrarian score: {str(e)}")
            return 0.0
    
    def _generate_contrarian_reasoning(self, technical_analysis: Dict, groq_analysis: Dict, 
                                     news_sentiment: float, bearish_count: int, neutral_count: int,
                                     ai_score: float, action: str, confidence: float) -> str:
        """Generate reasoning for contrarian recommendation."""
        try:
            reasoning_parts = []
            
            # Sentiment analysis
            reasoning_parts.append(f"📰 **Negative Sentiment Detected**: News sentiment at {news_sentiment:.3f}")
            if groq_analysis and groq_analysis.get('status') == 'success':
                groq_sentiment = groq_analysis.get('sentiment_score', 0)
                reasoning_parts.append(f"🤖 **AI Analysis**: Groq sentiment at {groq_sentiment:.3f}")
            
            # Technical analysis
            reasoning_parts.append(f"📊 **Technical Indicators**: {bearish_count} bearish, {neutral_count} neutral out of 4 indicators")
            
            # Specific technical details
            rsi = technical_analysis.get('rsi', 50)
            reasoning_parts.append(f"• RSI: {rsi:.1f} ({'Overbought' if rsi > 70 else 'Neutral' if rsi > 50 else 'Oversold'})")
            
            current_price = technical_analysis.get('current_price', 0)
            sma_20 = technical_analysis.get('sma_20', 0)
            if current_price > 0 and sma_20 > 0:
                price_vs_sma = (current_price - sma_20) / sma_20 * 100
                reasoning_parts.append(f"• Price vs SMA20: {price_vs_sma:+.1f}%")
            
            # Contrarian opportunity
            reasoning_parts.append(f"🎯 **Contrarian Opportunity**: Score {ai_score:.2f} - Oversold conditions with negative sentiment")
            reasoning_parts.append(f"💡 **Strategy**: Buy the dip on oversold conditions for potential reversal")
            
            return "\n\n".join(reasoning_parts)
            
        except Exception as e:
            logger.error(f"Error generating contrarian reasoning: {str(e)}")
            return f"Contrarian analysis completed with score {ai_score:.2f}"