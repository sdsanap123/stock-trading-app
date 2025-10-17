#!/usr/bin/env python3
"""
Performance Learning Component
Learns from recommendation performance to improve future recommendations.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
import os

logger = logging.getLogger(__name__)

class PerformanceLearning:
    """Learns from recommendation performance to improve future recommendations."""
    
    def __init__(self):
        self.learning_data_file = "data/performance_learning.json"
        self.learning_data = {
            'recommendations': [],
            'performance_metrics': {},
            'learning_rules': {},
            'last_updated': None
        }
        self.load_learning_data()
        logger.info("Performance Learning initialized")
    
    def load_learning_data(self):
        """Load learning data from file."""
        try:
            if os.path.exists(self.learning_data_file):
                with open(self.learning_data_file, 'r') as f:
                    self.learning_data = json.load(f)
                logger.info(f"Loaded {len(self.learning_data.get('recommendations', []))} learning records")
            else:
                self.learning_data = {
                    'recommendations': [],
                    'performance_metrics': {},
                    'learning_rules': {},
                    'last_updated': None
                }
        except Exception as e:
            logger.error(f"Error loading learning data: {str(e)}")
            self.learning_data = {
                'recommendations': [],
                'performance_metrics': {},
                'learning_rules': {},
                'last_updated': None
            }
    
    def save_learning_data(self):
        """Save learning data to file."""
        try:
            os.makedirs(os.path.dirname(self.learning_data_file), exist_ok=True)
            self.learning_data['last_updated'] = datetime.now().isoformat()
            with open(self.learning_data_file, 'w') as f:
                json.dump(self.learning_data, f, indent=2)
            logger.info("Saved learning data")
        except Exception as e:
            logger.error(f"Error saving learning data: {str(e)}")
    
    def record_recommendation(self, symbol: str, recommendation: Dict, 
                            technical_data: Dict, fundamental_data: Dict,
                            news_sentiment: float, groq_analysis: Dict) -> str:
        """Record a recommendation for future performance tracking."""
        try:
            recommendation_id = f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            learning_record = {
                'id': recommendation_id,
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'recommendation': recommendation,
                'technical_data': technical_data,
                'fundamental_data': fundamental_data,
                'news_sentiment': news_sentiment,
                'groq_analysis': groq_analysis,
                'performance_data': {
                    'entry_price': technical_data.get('current_price', 0),
                    'target_price': recommendation.get('target_price', 0),
                    'stop_loss': recommendation.get('stop_loss', 0),
                    'confidence': recommendation.get('confidence', 0),
                    'action': recommendation.get('action', 'HOLD')
                },
                'outcome': {
                    'status': 'PENDING',  # PENDING, SUCCESS, FAILURE, STOP_LOSS
                    'final_price': 0,
                    'performance_percent': 0,
                    'days_held': 0,
                    'target_hit': False,
                    'stop_loss_hit': False,
                    'analyzed_date': None
                }
            }
            
            self.learning_data['recommendations'].append(learning_record)
            self.save_learning_data()
            
            logger.info(f"Recorded recommendation for learning: {symbol}")
            return recommendation_id
            
        except Exception as e:
            logger.error(f"Error recording recommendation: {str(e)}")
            return ""
    
    def analyze_performance(self, symbol: str, current_price: float, 
                          days_held: int = 7) -> Dict:
        """Analyze performance of a recommendation after specified days."""
        try:
            # Find the most recent recommendation for this symbol
            recent_recommendations = [
                rec for rec in self.learning_data['recommendations']
                if rec['symbol'] == symbol and rec['outcome']['status'] == 'PENDING'
            ]
            
            if not recent_recommendations:
                return {'success': False, 'message': 'No pending recommendations found'}
            
            # Get the most recent recommendation
            recommendation = max(recent_recommendations, key=lambda x: x['timestamp'])
            
            # Calculate performance
            entry_price = recommendation['performance_data']['entry_price']
            target_price = recommendation['performance_data']['target_price']
            stop_loss = recommendation['performance_data']['stop_loss']
            action = recommendation['performance_data']['action']
            
            if entry_price <= 0:
                return {'success': False, 'message': 'Invalid entry price'}
            
            # Calculate performance percentage
            performance_percent = ((current_price - entry_price) / entry_price) * 100
            
            # Determine outcome
            outcome = {
                'status': 'PENDING',
                'final_price': current_price,
                'performance_percent': performance_percent,
                'days_held': days_held,
                'target_hit': False,
                'stop_loss_hit': False,
                'analyzed_date': datetime.now().isoformat()
            }
            
            if action == 'BUY':
                if current_price >= target_price:
                    outcome['status'] = 'SUCCESS'
                    outcome['target_hit'] = True
                elif current_price <= stop_loss:
                    outcome['status'] = 'STOP_LOSS'
                    outcome['stop_loss_hit'] = True
                elif performance_percent > 0:
                    outcome['status'] = 'SUCCESS'
                else:
                    outcome['status'] = 'FAILURE'
            elif action == 'SELL':
                if current_price <= target_price:
                    outcome['status'] = 'SUCCESS'
                    outcome['target_hit'] = True
                elif current_price >= stop_loss:
                    outcome['status'] = 'STOP_LOSS'
                    outcome['stop_loss_hit'] = True
                elif performance_percent < 0:
                    outcome['status'] = 'SUCCESS'
                else:
                    outcome['status'] = 'FAILURE'
            
            # Update recommendation record
            recommendation['outcome'] = outcome
            self.save_learning_data()
            
            # Update performance metrics
            self._update_performance_metrics(recommendation)
            
            logger.info(f"Analyzed performance for {symbol}: {outcome['status']} ({performance_percent:.2f}%)")
            
            return {
                'success': True,
                'symbol': symbol,
                'outcome': outcome,
                'recommendation': recommendation
            }
            
        except Exception as e:
            logger.error(f"Error analyzing performance for {symbol}: {str(e)}")
            return {'success': False, 'message': str(e)}
    
    def _update_performance_metrics(self, recommendation: Dict):
        """Update overall performance metrics."""
        try:
            symbol = recommendation['symbol']
            outcome = recommendation['outcome']
            performance_data = recommendation['performance_data']
            
            # Initialize metrics for symbol if not exists
            if symbol not in self.learning_data['performance_metrics']:
                self.learning_data['performance_metrics'][symbol] = {
                    'total_recommendations': 0,
                    'successful_recommendations': 0,
                    'failed_recommendations': 0,
                    'stop_loss_hits': 0,
                    'target_hits': 0,
                    'avg_performance_percent': 0,
                    'avg_confidence': 0,
                    'success_rate': 0
                }
            
            metrics = self.learning_data['performance_metrics'][symbol]
            metrics['total_recommendations'] += 1
            
            if outcome['status'] == 'SUCCESS':
                metrics['successful_recommendations'] += 1
            elif outcome['status'] == 'FAILURE':
                metrics['failed_recommendations'] += 1
            
            if outcome['stop_loss_hit']:
                metrics['stop_loss_hits'] += 1
            
            if outcome['target_hit']:
                metrics['target_hits'] += 1
            
            # Calculate averages
            if metrics['total_recommendations'] > 0:
                metrics['success_rate'] = (metrics['successful_recommendations'] / metrics['total_recommendations']) * 100
            
            # Update learning rules based on performance
            self._update_learning_rules(recommendation)
            
        except Exception as e:
            logger.error(f"Error updating performance metrics: {str(e)}")
    
    def _update_learning_rules(self, recommendation: Dict):
        """Update learning rules based on recommendation performance."""
        try:
            outcome = recommendation['outcome']
            technical_data = recommendation['technical_data']
            groq_analysis = recommendation['groq_analysis']
            
            # Learn from successful recommendations
            if outcome['status'] == 'SUCCESS':
                # Extract successful patterns
                success_patterns = {
                    'rsi_range': technical_data.get('rsi', 50),
                    'macd_signal': technical_data.get('macd', 0),
                    'volume_ratio': technical_data.get('volume_ratio_20', 1),
                    'sentiment_score': groq_analysis.get('sentiment_score', 0) if groq_analysis else 0,
                    'confidence_threshold': recommendation['performance_data']['confidence']
                }
                
                # Store successful patterns
                if 'successful_patterns' not in self.learning_data['learning_rules']:
                    self.learning_data['learning_rules']['successful_patterns'] = []
                
                self.learning_data['learning_rules']['successful_patterns'].append(success_patterns)
                
                # Keep only recent patterns (last 50)
                if len(self.learning_data['learning_rules']['successful_patterns']) > 50:
                    self.learning_data['learning_rules']['successful_patterns'] = \
                        self.learning_data['learning_rules']['successful_patterns'][-50:]
            
            # Learn from failed recommendations
            elif outcome['status'] == 'FAILURE':
                # Extract failed patterns to avoid
                failure_patterns = {
                    'rsi_range': technical_data.get('rsi', 50),
                    'macd_signal': technical_data.get('macd', 0),
                    'volume_ratio': technical_data.get('volume_ratio_20', 1),
                    'sentiment_score': groq_analysis.get('sentiment_score', 0) if groq_analysis else 0,
                    'confidence_threshold': recommendation['performance_data']['confidence']
                }
                
                # Store failed patterns
                if 'failed_patterns' not in self.learning_data['learning_rules']:
                    self.learning_data['learning_rules']['failed_patterns'] = []
                
                self.learning_data['learning_rules']['failed_patterns'].append(failure_patterns)
                
                # Keep only recent patterns (last 50)
                if len(self.learning_data['learning_rules']['failed_patterns']) > 50:
                    self.learning_data['learning_rules']['failed_patterns'] = \
                        self.learning_data['learning_rules']['failed_patterns'][-50:]
            
        except Exception as e:
            logger.error(f"Error updating learning rules: {str(e)}")
    
    def get_learning_insights(self) -> Dict:
        """Get insights from learning data."""
        try:
            insights = {
                'total_recommendations': len(self.learning_data['recommendations']),
                'successful_recommendations': 0,
                'failed_recommendations': 0,
                'overall_success_rate': 0,
                'top_performing_stocks': [],
                'learning_rules_count': len(self.learning_data.get('learning_rules', {})),
                'last_updated': self.learning_data.get('last_updated')
            }
            
            # Calculate overall metrics
            for rec in self.learning_data['recommendations']:
                if rec['outcome']['status'] == 'SUCCESS':
                    insights['successful_recommendations'] += 1
                elif rec['outcome']['status'] == 'FAILURE':
                    insights['failed_recommendations'] += 1
            
            if insights['total_recommendations'] > 0:
                insights['overall_success_rate'] = (insights['successful_recommendations'] / insights['total_recommendations']) * 100
            
            # Get top performing stocks
            stock_performance = {}
            for symbol, metrics in self.learning_data['performance_metrics'].items():
                if metrics['total_recommendations'] >= 3:  # Minimum 3 recommendations
                    stock_performance[symbol] = metrics['success_rate']
            
            insights['top_performing_stocks'] = sorted(
                stock_performance.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10]
            
            return insights
            
        except Exception as e:
            logger.error(f"Error getting learning insights: {str(e)}")
            return {
                'total_recommendations': 0,
                'successful_recommendations': 0,
                'failed_recommendations': 0,
                'overall_success_rate': 0,
                'top_performing_stocks': [],
                'learning_rules_count': 0,
                'last_updated': None
            }
    
    def apply_learning_to_recommendation(self, symbol: str, technical_data: Dict, 
                                       groq_analysis: Dict, base_recommendation: Dict) -> Dict:
        """Apply learning insights to improve a recommendation."""
        try:
            # Get historical performance for this symbol
            symbol_metrics = self.learning_data['performance_metrics'].get(symbol, {})
            
            # Get learning rules
            successful_patterns = self.learning_data['learning_rules'].get('successful_patterns', [])
            failed_patterns = self.learning_data['learning_rules'].get('failed_patterns', [])
            
            # Adjust recommendation based on learning
            adjusted_recommendation = base_recommendation.copy()
            
            # Adjust confidence based on historical performance
            if symbol_metrics.get('success_rate', 0) > 70:
                # High success rate - increase confidence
                adjusted_recommendation['confidence'] = min(95, adjusted_recommendation['confidence'] * 1.1)
            elif symbol_metrics.get('success_rate', 0) < 30:
                # Low success rate - decrease confidence
                adjusted_recommendation['confidence'] = max(10, adjusted_recommendation['confidence'] * 0.9)
            
            # Adjust target and stop loss based on historical performance
            if symbol_metrics.get('target_hits', 0) > symbol_metrics.get('stop_loss_hits', 0):
                # More target hits than stop losses - can be more aggressive
                if adjusted_recommendation['action'] == 'BUY':
                    adjusted_recommendation['target_price'] *= 1.05  # 5% higher target
            else:
                # More stop losses than target hits - be more conservative
                if adjusted_recommendation['action'] == 'BUY':
                    adjusted_recommendation['stop_loss'] *= 0.95  # 5% tighter stop loss
            
            # Add learning insights to reasoning
            learning_insight = f"📚 Learning: {symbol} has {symbol_metrics.get('success_rate', 0):.1f}% success rate"
            if 'reasoning' in adjusted_recommendation:
                adjusted_recommendation['reasoning'] += f"\n\n{learning_insight}"
            else:
                adjusted_recommendation['reasoning'] = learning_insight
            
            return adjusted_recommendation
            
        except Exception as e:
            logger.error(f"Error applying learning to recommendation: {str(e)}")
            return base_recommendation
