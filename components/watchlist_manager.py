#!/usr/bin/env python3
"""
Watchlist Manager Component
Watchlist management functionality.
"""

import logging
from typing import Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)

class WatchlistManager:
    """Watchlist management functionality."""
    
    def __init__(self):
        self.watchlist = []
        logger.info("Watchlist Manager initialized")
    
    def add_to_watchlist(self, stock_data: Dict) -> bool:
        """Add stock to watchlist."""
        try:
            # Check if already exists
            for item in self.watchlist:
                if item.get('symbol') == stock_data.get('symbol'):
                    return False
            
            # Add to watchlist
            watchlist_item = {
                'symbol': stock_data.get('symbol'),
                'entry_price': stock_data.get('current_price', 0),
                'current_price': stock_data.get('current_price', 0),
                'target_price': stock_data.get('target_price', 0),
                'stop_loss': stock_data.get('stop_loss', 0),
                'recommendation': stock_data.get('recommendation', 'HOLD'),
                'confidence': stock_data.get('confidence', 0),
                'added_date': datetime.now().isoformat(),
                'status': 'ACTIVE'
            }
            
            self.watchlist.append(watchlist_item)
            logger.info(f"Added {stock_data.get('symbol')} to watchlist")
            return True
            
        except Exception as e:
            logger.error(f"Error adding to watchlist: {str(e)}")
            return False
    
    def remove_from_watchlist(self, symbol: str) -> bool:
        """Remove stock from watchlist."""
        try:
            for i, item in enumerate(self.watchlist):
                if item.get('symbol') == symbol:
                    self.watchlist.pop(i)
                    logger.info(f"Removed {symbol} from watchlist")
                    return True
            return False
            
        except Exception as e:
            logger.error(f"Error removing from watchlist: {str(e)}")
            return False
    
    def get_watchlist(self) -> List[Dict]:
        """Get current watchlist."""
        return self.watchlist.copy()
    
    def update_watchlist_item(self, symbol: str, updates: Dict) -> bool:
        """Update watchlist item."""
        try:
            for item in self.watchlist:
                if item.get('symbol') == symbol:
                    item.update(updates)
                    item['last_updated'] = datetime.now().isoformat()
                    logger.info(f"Updated {symbol} in watchlist")
                    return True
            return False
            
        except Exception as e:
            logger.error(f"Error updating watchlist item: {str(e)}")
            return False
