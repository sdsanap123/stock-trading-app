#!/usr/bin/env python3
"""
Cache Manager Component
Manages caching for articles and stock analysis to avoid redundant processing.
"""

import json
import pickle
import hashlib
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)

class CacheManager:
    """Manages caching for articles and stock analysis with smart relevance tracking."""
    
    def __init__(self, cache_dir: str = "cache"):
        """Initialize cache manager."""
        self.cache_dir = cache_dir
        self.articles_cache_file = os.path.join(cache_dir, "articles_cache.pkl")
        self.stocks_cache_file = os.path.join(cache_dir, "stocks_cache.pkl")
        self.analysis_cache_file = os.path.join(cache_dir, "analysis_cache.pkl")
        self.recommendations_cache_file = os.path.join(cache_dir, "recommendations_cache.pkl")
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
        
        # Load existing caches
        self.articles_cache = self._load_cache(self.articles_cache_file)
        self.stocks_cache = self._load_cache(self.stocks_cache_file)
        self.analysis_cache = self._load_cache(self.analysis_cache_file)
        self.recommendations_cache = self._load_cache(self.recommendations_cache_file)
        
        # Cache expiration times (in hours)
        self.articles_cache_hours = 168  # Articles cache for 7 days (168 hours)
        self.stocks_cache_hours = 168    # Stock analysis cache for 7 days (168 hours)
        self.analysis_cache_hours = 168  # Groq analysis cache for 7 days (168 hours)
        self.recommendations_cache_hours = 168  # Recommendations cache for 7 days (168 hours)
        
        logger.info("Smart Cache Manager initialized successfully")
    
    def _load_cache(self, cache_file: str) -> Dict:
        """Load cache from file."""
        try:
            if os.path.exists(cache_file):
                with open(cache_file, 'rb') as f:
                    cache = pickle.load(f)
                    logger.info(f"Loaded cache from {cache_file}")
                    return cache
        except Exception as e:
            logger.warning(f"Could not load cache from {cache_file}: {str(e)}")
        
        return {}
    
    def _save_cache(self, cache: Dict, cache_file: str):
        """Save cache to file."""
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(cache, f)
                logger.info(f"Saved cache to {cache_file}")
        except Exception as e:
            logger.error(f"Could not save cache to {cache_file}: {str(e)}")
    
    def _generate_cache_key(self, data: Any) -> str:
        """Generate a cache key from data."""
        try:
            # Convert data to string and create hash
            data_str = json.dumps(data, sort_keys=True, default=str)
            return hashlib.md5(data_str.encode()).hexdigest()
        except Exception as e:
            logger.warning(f"Could not generate cache key: {str(e)}")
            return str(hash(str(data)))
    
    def _is_cache_valid(self, timestamp: str, cache_hours: int) -> bool:
        """Check if cache entry is still valid."""
        try:
            cache_time = datetime.fromisoformat(timestamp)
            expiry_time = cache_time + timedelta(hours=cache_hours)
            return datetime.now() < expiry_time
        except Exception as e:
            logger.warning(f"Could not check cache validity: {str(e)}")
            return False
    
    def _clean_expired_cache(self, cache: Dict, cache_hours: int) -> Dict:
        """Remove expired entries from cache."""
        cleaned_cache = {}
        for key, value in cache.items():
            if isinstance(value, dict) and 'timestamp' in value:
                if self._is_cache_valid(value['timestamp'], cache_hours):
                    cleaned_cache[key] = value
            else:
                # Keep entries without timestamp (legacy entries)
                cleaned_cache[key] = value
        
        return cleaned_cache
    
    def cache_articles(self, articles: List[Dict]) -> List[Dict]:
        """Cache articles and return only new ones."""
        try:
            # Clean expired cache entries
            self.articles_cache = self._clean_expired_cache(self.articles_cache, self.articles_cache_hours)
            
            new_articles = []
            current_time = datetime.now().isoformat()
            
            for article in articles:
                # Create cache key from article URL and title
                cache_key = self._generate_cache_key({
                    'url': article.get('url', ''),
                    'title': article.get('title', '')
                })
                
                if cache_key not in self.articles_cache:
                    # New article - add to cache and include in new articles
                    self.articles_cache[cache_key] = {
                        'article': article,
                        'timestamp': current_time
                    }
                    new_articles.append(article)
                    logger.debug(f"Cached new article: {article.get('title', '')[:50]}...")
                else:
                    logger.debug(f"Article already cached: {article.get('title', '')[:50]}...")
            
            # Save updated cache
            self._save_cache(self.articles_cache, self.articles_cache_file)
            
            logger.info(f"Cached {len(new_articles)} new articles out of {len(articles)} total articles")
            return new_articles
            
        except Exception as e:
            logger.error(f"Error caching articles: {str(e)}")
            return articles  # Return all articles if caching fails
    
    def cache_stock_analysis(self, symbol: str, analysis_data: Dict) -> bool:
        """Cache stock analysis data."""
        try:
            # Clean expired cache entries
            self.stocks_cache = self._clean_expired_cache(self.stocks_cache, self.stocks_cache_hours)
            
            cache_key = f"stock_{symbol.upper()}"
            current_time = datetime.now().isoformat()
            
            self.stocks_cache[cache_key] = {
                'analysis': analysis_data,
                'timestamp': current_time
            }
            
            # Save updated cache
            self._save_cache(self.stocks_cache, self.stocks_cache_file)
            
            logger.info(f"Cached analysis for stock: {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Error caching stock analysis for {symbol}: {str(e)}")
            return False
    
    def get_cached_stock_analysis(self, symbol: str) -> Optional[Dict]:
        """Get cached stock analysis if available and valid."""
        try:
            cache_key = f"stock_{symbol.upper()}"
            
            if cache_key in self.stocks_cache:
                cache_entry = self.stocks_cache[cache_key]
                
                if isinstance(cache_entry, dict) and 'timestamp' in cache_entry:
                    if self._is_cache_valid(cache_entry['timestamp'], self.stocks_cache_hours):
                        logger.info(f"Retrieved cached analysis for stock: {symbol}")
                        return cache_entry['analysis']
                    else:
                        # Remove expired entry
                        del self.stocks_cache[cache_key]
                        self._save_cache(self.stocks_cache, self.stocks_cache_file)
                        logger.info(f"Removed expired cache for stock: {symbol}")
                else:
                    # Legacy entry without timestamp
                    logger.info(f"Retrieved legacy cached analysis for stock: {symbol}")
                    return cache_entry
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving cached stock analysis for {symbol}: {str(e)}")
            return None
    
    def cache_groq_analysis(self, analysis_key: str, analysis_data: Dict) -> bool:
        """Cache Groq analysis data."""
        try:
            # Clean expired cache entries
            self.analysis_cache = self._clean_expired_cache(self.analysis_cache, self.analysis_cache_hours)
            
            current_time = datetime.now().isoformat()
            
            self.analysis_cache[analysis_key] = {
                'analysis': analysis_data,
                'timestamp': current_time
            }
            
            # Save updated cache
            self._save_cache(self.analysis_cache, self.analysis_cache_file)
            
            logger.info(f"Cached Groq analysis: {analysis_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error caching Groq analysis {analysis_key}: {str(e)}")
            return False
    
    def get_cached_groq_analysis(self, analysis_key: str) -> Optional[Dict]:
        """Get cached Groq analysis if available and valid."""
        try:
            if analysis_key in self.analysis_cache:
                cache_entry = self.analysis_cache[analysis_key]
                
                if isinstance(cache_entry, dict) and 'timestamp' in cache_entry:
                    if self._is_cache_valid(cache_entry['timestamp'], self.analysis_cache_hours):
                        logger.info(f"Retrieved cached Groq analysis: {analysis_key}")
                        return cache_entry['analysis']
                    else:
                        # Remove expired entry
                        del self.analysis_cache[analysis_key]
                        self._save_cache(self.analysis_cache, self.analysis_cache_file)
                        logger.info(f"Removed expired Groq cache: {analysis_key}")
                else:
                    # Legacy entry without timestamp
                    logger.info(f"Retrieved legacy cached Groq analysis: {analysis_key}")
                    return cache_entry
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving cached Groq analysis {analysis_key}: {str(e)}")
            return None
    
    def is_stock_in_watchlist(self, symbol: str, watchlist: List[Dict]) -> bool:
        """Check if stock is already in watchlist."""
        try:
            symbol_upper = symbol.upper()
            for item in watchlist:
                if item.get('symbol', '').upper() == symbol_upper:
                    return True
            return False
        except Exception as e:
            logger.error(f"Error checking watchlist for {symbol}: {str(e)}")
            return False
    
    def filter_watchlist_stocks(self, stocks: List[Dict], watchlist: List[Dict], 
                               allow_negative_news: bool = True) -> List[Dict]:
        """Filter out stocks already in watchlist unless there's very negative news."""
        try:
            filtered_stocks = []
            
            for stock in stocks:
                symbol = stock.get('symbol', '')
                
                if not self.is_stock_in_watchlist(symbol, watchlist):
                    # Stock not in watchlist - include it
                    filtered_stocks.append(stock)
                elif allow_negative_news:
                    # Stock is in watchlist - only include if very negative news
                    sentiment_score = stock.get('sentiment_score', 0)
                    sentiment_label = stock.get('sentiment_label', 'NEUTRAL')
                    
                    # Only include if very negative (sentiment score < -0.7 or NEGATIVE with high impact)
                    if (sentiment_score < -0.7 or 
                        (sentiment_label == 'NEGATIVE' and stock.get('impact_level') == 'HIGH')):
                        stock['watchlist_override'] = True
                        stock['override_reason'] = 'Very negative news - potential sell signal'
                        filtered_stocks.append(stock)
                        logger.info(f"Including {symbol} from watchlist due to very negative news")
                    else:
                        logger.info(f"Excluding {symbol} from recommendations - already in watchlist")
                else:
                    logger.info(f"Excluding {symbol} from recommendations - already in watchlist")
            
            logger.info(f"Filtered {len(filtered_stocks)} stocks from {len(stocks)} (removed {len(stocks) - len(filtered_stocks)} watchlist stocks)")
            return filtered_stocks
            
        except Exception as e:
            logger.error(f"Error filtering watchlist stocks: {str(e)}")
            return stocks  # Return all stocks if filtering fails
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        try:
            # Clean all caches first
            self.articles_cache = self._clean_expired_cache(self.articles_cache, self.articles_cache_hours)
            self.stocks_cache = self._clean_expired_cache(self.stocks_cache, self.stocks_cache_hours)
            self.analysis_cache = self._clean_expired_cache(self.analysis_cache, self.analysis_cache_hours)
            self.recommendations_cache = self._clean_expired_cache(self.recommendations_cache, self.recommendations_cache_hours)
            
            # Count recommendation changes
            changes_count = 0
            for cache_entry in self.recommendations_cache.values():
                if isinstance(cache_entry, dict) and 'recommendation' in cache_entry:
                    if cache_entry['recommendation'].get('change_detected', False):
                        changes_count += 1
            
            return {
                'articles': len(self.articles_cache),
                'stocks': len(self.stocks_cache),
                'analysis': len(self.analysis_cache),
                'recommendations': len(self.recommendations_cache),
                'recommendation_changes': changes_count,
                'articles_cache_hours': self.articles_cache_hours,
                'stocks_cache_hours': self.stocks_cache_hours,
                'analysis_cache_hours': self.analysis_cache_hours,
                'recommendations_cache_hours': self.recommendations_cache_hours,
                'cache_dir': self.cache_dir
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {str(e)}")
            return {}
    
    def cache_recommendation(self, symbol: str, recommendation: Dict) -> Dict:
        """Cache recommendation and detect changes."""
        try:
            # Clean expired cache entries
            self.recommendations_cache = self._clean_expired_cache(self.recommendations_cache, self.recommendations_cache_hours)
            
            cache_key = f"rec_{symbol.upper()}"
            current_time = datetime.now().isoformat()
            
            # Check if we have a previous recommendation
            previous_rec = None
            if cache_key in self.recommendations_cache:
                cache_entry = self.recommendations_cache[cache_key]
                if isinstance(cache_entry, dict) and 'recommendation' in cache_entry:
                    previous_rec = cache_entry['recommendation']
            
            # Detect changes
            change_detected = False
            change_type = None
            change_details = {}
            
            if previous_rec:
                # Compare key recommendation fields
                prev_action = previous_rec.get('action', 'HOLD')
                prev_confidence = previous_rec.get('confidence', 0)
                prev_target = previous_rec.get('target_price', 0)
                prev_stop_loss = previous_rec.get('stop_loss', 0)
                
                curr_action = recommendation.get('action', 'HOLD')
                curr_confidence = recommendation.get('confidence', 0)
                curr_target = recommendation.get('target_price', 0)
                curr_stop_loss = recommendation.get('stop_loss', 0)
                
                # Check for significant changes
                if prev_action != curr_action:
                    change_detected = True
                    change_type = 'action_change'
                    change_details = {
                        'previous_action': prev_action,
                        'current_action': curr_action,
                        'change': f"{prev_action} → {curr_action}"
                    }
                elif abs(prev_confidence - curr_confidence) > 10:  # 10% confidence change
                    change_detected = True
                    change_type = 'confidence_change'
                    change_details = {
                        'previous_confidence': prev_confidence,
                        'current_confidence': curr_confidence,
                        'change': f"{prev_confidence:.1f}% → {curr_confidence:.1f}%"
                    }
                elif abs(prev_target - curr_target) / prev_target > 0.05:  # 5% target change
                    change_detected = True
                    change_type = 'target_change'
                    change_details = {
                        'previous_target': prev_target,
                        'current_target': curr_target,
                        'change': f"₹{prev_target:.2f} → ₹{curr_target:.2f}"
                    }
                elif abs(prev_stop_loss - curr_stop_loss) / prev_stop_loss > 0.05:  # 5% stop loss change
                    change_detected = True
                    change_type = 'stop_loss_change'
                    change_details = {
                        'previous_stop_loss': prev_stop_loss,
                        'current_stop_loss': curr_stop_loss,
                        'change': f"₹{prev_stop_loss:.2f} → ₹{curr_stop_loss:.2f}"
                    }
            
            # Add change tracking to recommendation
            recommendation['change_detected'] = change_detected
            recommendation['change_type'] = change_type
            recommendation['change_details'] = change_details
            recommendation['last_updated'] = current_time
            
            # Cache the recommendation
            self.recommendations_cache[cache_key] = {
                'recommendation': recommendation,
                'timestamp': current_time,
                'change_history': self._get_change_history(cache_key, change_detected, change_type, change_details)
            }
            
            # Save updated cache
            self._save_cache(self.recommendations_cache, self.recommendations_cache_file)
            
            if change_detected:
                logger.info(f"Recommendation change detected for {symbol}: {change_type}")
            else:
                logger.info(f"Cached recommendation for {symbol} (no changes)")
            
            return recommendation
            
        except Exception as e:
            logger.error(f"Error caching recommendation for {symbol}: {str(e)}")
            return recommendation
    
    def get_cached_recommendation(self, symbol: str) -> Optional[Dict]:
        """Get cached recommendation if available and valid."""
        try:
            cache_key = f"rec_{symbol.upper()}"
            
            if cache_key in self.recommendations_cache:
                cache_entry = self.recommendations_cache[cache_key]
                
                if isinstance(cache_entry, dict) and 'timestamp' in cache_entry:
                    if self._is_cache_valid(cache_entry['timestamp'], self.recommendations_cache_hours):
                        logger.info(f"Retrieved cached recommendation for {symbol}")
                        return cache_entry['recommendation']
                    else:
                        # Remove expired entry
                        del self.recommendations_cache[cache_key]
                        self._save_cache(self.recommendations_cache, self.recommendations_cache_file)
                        logger.info(f"Removed expired recommendation cache for {symbol}")
                else:
                    # Legacy entry without timestamp
                    logger.info(f"Retrieved legacy cached recommendation for {symbol}")
                    return cache_entry
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving cached recommendation for {symbol}: {str(e)}")
            return None
    
    def _get_change_history(self, cache_key: str, change_detected: bool, change_type: str, change_details: Dict) -> List[Dict]:
        """Get or create change history for a stock."""
        try:
            if cache_key in self.recommendations_cache:
                existing_entry = self.recommendations_cache[cache_key]
                if isinstance(existing_entry, dict) and 'change_history' in existing_entry:
                    change_history = existing_entry['change_history']
                else:
                    change_history = []
            else:
                change_history = []
            
            # Add new change if detected
            if change_detected:
                change_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'change_type': change_type,
                    'change_details': change_details
                })
                
                # Keep only last 10 changes
                if len(change_history) > 10:
                    change_history = change_history[-10:]
            
            return change_history
            
        except Exception as e:
            logger.error(f"Error managing change history for {cache_key}: {str(e)}")
            return []
    
    def is_stock_relevant_for_caching(self, symbol: str, recommendation: Dict, news_impact: str = 'MEDIUM') -> bool:
        """Determine if a stock is relevant enough to cache."""
        try:
            # Only cache BUY recommendations
            if recommendation.get('action') != 'BUY':
                return False
            
            # Cache based on confidence level
            confidence = recommendation.get('confidence', 0)
            if confidence < 40:  # Only cache recommendations with at least 40% confidence
                return False
            
            # Cache based on news impact
            if news_impact == 'HIGH':
                return True
            elif news_impact == 'MEDIUM' and confidence >= 60:
                return True
            elif news_impact == 'LOW' and confidence >= 80:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking relevance for {symbol}: {str(e)}")
            return False
    
    def get_recommendation_changes(self, symbol: str = None) -> Dict:
        """Get all recommendation changes or changes for a specific symbol."""
        try:
            changes = {}
            
            for cache_key, cache_entry in self.recommendations_cache.items():
                if isinstance(cache_entry, dict) and 'recommendation' in cache_entry:
                    rec = cache_entry['recommendation']
                    stock_symbol = cache_key.replace('rec_', '')
                    
                    if symbol is None or stock_symbol.upper() == symbol.upper():
                        if rec.get('change_detected', False):
                            changes[stock_symbol] = {
                                'change_type': rec.get('change_type'),
                                'change_details': rec.get('change_details'),
                                'last_updated': rec.get('last_updated'),
                                'current_recommendation': rec
                            }
            
            return changes
            
        except Exception as e:
            logger.error(f"Error getting recommendation changes: {str(e)}")
            return {}
    
    def clear_cache(self, cache_type: str = 'safe'):
        """Clear cache entries. Default 'safe' mode only clears news and analysis cache."""
        try:
            cleared_items = []
            
            # Default 'safe' mode only clears news and analysis cache
            if cache_type == 'safe':
                cache_type = 'news_analysis'
            
            if cache_type in ['all', 'news_analysis', 'articles']:
                self.articles_cache = {}
                self._save_cache(self.articles_cache, self.articles_cache_file)
                cleared_items.append("articles")
                logger.info("Cleared articles cache")
            
            if cache_type in ['all', 'news_analysis', 'stocks']:
                self.stocks_cache = {}
                self._save_cache(self.stocks_cache, self.stocks_cache_file)
                cleared_items.append("stocks")
                logger.info("Cleared stocks cache")
            
            if cache_type in ['all', 'news_analysis', 'analysis']:
                self.analysis_cache = {}
                self._save_cache(self.analysis_cache, self.analysis_cache_file)
                cleared_items.append("analysis")
                logger.info("Cleared analysis cache")
            
            # Only clear recommendations if explicitly requested
            if cache_type in ['all', 'recommendations']:
                self.recommendations_cache = {}
                self._save_cache(self.recommendations_cache, self.recommendations_cache_file)
                cleared_items.append("recommendations")
                logger.info("Cleared recommendations cache")
            
            # Clear any additional cache files only for 'all'
            if cache_type == 'all':
                self._clear_additional_cache_files()
                cleared_items.append("additional files")
            
            return {
                'success': True,
                'cleared_items': cleared_items,
                'message': f"Successfully cleared: {', '.join(cleared_items)}"
            }
                
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return {
                'success': False,
                'message': f"Error clearing cache: {str(e)}"
            }
    
    def _clear_additional_cache_files(self):
        """Clear additional cache files that might exist."""
        try:
            import os
            import glob
            
            # Clear any .pkl files in cache directory
            cache_dir = "cache"
            if os.path.exists(cache_dir):
                pkl_files = glob.glob(os.path.join(cache_dir, "*.pkl"))
                for pkl_file in pkl_files:
                    try:
                        os.remove(pkl_file)
                        logger.info(f"Removed cache file: {pkl_file}")
                    except Exception as e:
                        logger.warning(f"Could not remove {pkl_file}: {str(e)}")
            
            # Clear any temporary cache files
            temp_files = glob.glob("*.tmp")
            for temp_file in temp_files:
                try:
                    os.remove(temp_file)
                    logger.info(f"Removed temp file: {temp_file}")
                except Exception as e:
                    logger.warning(f"Could not remove {temp_file}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error clearing additional cache files: {str(e)}")
