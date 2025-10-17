#!/usr/bin/env python3
"""
Equity Loader Component
Loads stock symbols from EQUITY.csv file for analysis and filtering.
"""

import pandas as pd
import logging
import os
from typing import List, Dict, Set

logger = logging.getLogger(__name__)

class EquityLoader:
    """Loads and manages stock symbols from EQUITY.csv file."""
    
    def __init__(self, equity_file: str = "EQUITY.csv"):
        """Initialize equity loader."""
        self.equity_file = equity_file
        self.stock_symbols = set()
        self.stock_data = {}
        self.load_equity_data()
        logger.info(f"EquityLoader initialized with {len(self.stock_symbols)} stocks")
    
    def load_equity_data(self):
        """Load stock symbols and data from EQUITY.csv file."""
        try:
            if not os.path.exists(self.equity_file):
                logger.error(f"EQUITY.csv file not found at {self.equity_file}")
                return
            
            # Read the CSV file
            df = pd.read_csv(self.equity_file)
            
            # Extract stock symbols and company names
            for _, row in df.iterrows():
                symbol = row.get('SYMBOL', '').strip()
                company_name = row.get('NAME OF COMPANY', '').strip()
                series = row.get(' SERIES', '').strip()
                
                if symbol and series == 'EQ':  # Only include equity series
                    self.stock_symbols.add(symbol)
                    self.stock_data[symbol] = {
                        'symbol': symbol,
                        'company_name': company_name,
                        'series': series,
                        'date_of_listing': row.get(' DATE OF LISTING', ''),
                        'paid_up_value': row.get(' PAID UP VALUE', ''),
                        'market_lot': row.get(' MARKET LOT', ''),
                        'isin_number': row.get(' ISIN NUMBER', ''),
                        'face_value': row.get(' FACE VALUE', '')
                    }
            
            logger.info(f"Loaded {len(self.stock_symbols)} equity stocks from {self.equity_file}")
            
        except Exception as e:
            logger.error(f"Error loading equity data: {str(e)}")
    
    def get_stock_symbols(self) -> Set[str]:
        """Get all stock symbols."""
        return self.stock_symbols.copy()
    
    def get_stock_data(self, symbol: str) -> Dict:
        """Get data for a specific stock symbol."""
        return self.stock_data.get(symbol, {})
    
    def get_company_name(self, symbol: str) -> str:
        """Get company name for a stock symbol."""
        stock_data = self.get_stock_data(symbol)
        return stock_data.get('company_name', symbol)
    
    def is_valid_stock(self, symbol: str) -> bool:
        """Check if a stock symbol is valid (exists in EQUITY.csv)."""
        return symbol in self.stock_symbols
    
    def validate_stock_symbols(self, symbols: List[str]) -> List[str]:
        """Validate and filter stock symbols against EQUITY.csv."""
        valid_symbols = []
        for symbol in symbols:
            if self.is_valid_stock(symbol):
                valid_symbols.append(symbol)
            else:
                logger.debug(f"Invalid stock symbol: {symbol}")
        
        logger.info(f"Validated {len(valid_symbols)} out of {len(symbols)} symbols")
        return valid_symbols
    
    def get_top_stocks(self, limit: int = 100) -> List[str]:
        """Get top N stocks by market cap or other criteria."""
        # For now, return first N stocks alphabetically
        # In a real implementation, you might want to sort by market cap
        sorted_symbols = sorted(list(self.stock_symbols))
        return sorted_symbols[:limit]
    
    def search_stocks(self, query: str) -> List[Dict]:
        """Search stocks by symbol or company name."""
        results = []
        query_lower = query.lower()
        
        for symbol, data in self.stock_data.items():
            if (query_lower in symbol.lower() or 
                query_lower in data.get('company_name', '').lower()):
                results.append(data)
        
        return results
    
    def get_stock_count(self) -> int:
        """Get total number of stocks."""
        return len(self.stock_symbols)
