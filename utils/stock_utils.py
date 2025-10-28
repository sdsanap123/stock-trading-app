import pandas as pd
import os
from typing import Optional, Dict, Any
import yfinance as yf
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variable to store the equity data
equity_df = None

def load_equity_data() -> pd.DataFrame:
    """
    Load the EQUITY_L.csv file into a pandas DataFrame.
    """
    global equity_df
    if equity_df is None:
        try:
            file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'EQUITY_L.csv')
            equity_df = pd.read_csv(file_path)
            logger.info(f"Loaded EQUITY_L.csv with {len(equity_df)} entries")
        except Exception as e:
            logger.error(f"Error loading EQUITY_L.csv: {str(e)}")
            equity_df = pd.DataFrame(columns=['SYMBOL', 'NAME OF COMPANY'])
    return equity_df

def find_stock_symbol(company_name: str) -> Optional[str]:
    """
    Find stock symbol by company name in EQUITY_L.csv.
    
    Args:
        company_name: The name of the company to search for
        
    Returns:
        str: The stock symbol if found, None otherwise
    """
    try:
        df = load_equity_data()
        if df.empty:
            return None
            
        # Case-insensitive search in company names
        matches = df[df['NAME OF COMPANY'].str.contains(company_name, case=False, na=False)]
        
        if not matches.empty:
            return matches.iloc[0]['SYMBOL']
            
    except Exception as e:
        logger.error(f"Error finding stock symbol for {company_name}: {str(e)}")
        
    return None

def get_stock_data(symbol: str, company_name: str = None) -> Optional[Dict[str, Any]]:
    """
    Get stock data from yfinance with fallback to symbol lookup.
    
    Args:
        symbol: The stock symbol to fetch data for
        company_name: Optional company name for fallback lookup
        
    Returns:
        Dict containing stock data or None if not found
    """
    try:
        # First try with the given symbol
        stock = yf.Ticker(f"{symbol}.NS")
        info = stock.info
        
        # If we don't get valid data, try with company name lookup
        if not info or 'symbol' not in info:
            if company_name:
                alt_symbol = find_stock_symbol(company_name)
                if alt_symbol and alt_symbol != symbol:
                    logger.info(f"Trying alternative symbol {alt_symbol} for {company_name}")
                    stock = yf.Ticker(f"{alt_symbol}.NS")
                    info = stock.info
                    
                    if info and 'symbol' in info:
                        return {
                            'symbol': alt_symbol,
                            'company_name': info.get('shortName', company_name),
                            'current_price': info.get('currentPrice', info.get('regularMarketPrice')),
                            'sector': info.get('sector', ''),
                            'market_cap': info.get('marketCap'),
                            'pe_ratio': info.get('trailingPE'),
                            'volume': info.get('volume')
                        }
        
        # If we have valid data, return it
        if info and 'symbol' in info:
            return {
                'symbol': symbol,
                'company_name': info.get('shortName', company_name or symbol),
                'current_price': info.get('currentPrice', info.get('regularMarketPrice')),
                'sector': info.get('sector', ''),
                'market_cap': info.get('marketCap'),
                'pe_ratio': info.get('trailingPE'),
                'volume': info.get('volume')
            }
            
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {str(e)}")
        
    return None
