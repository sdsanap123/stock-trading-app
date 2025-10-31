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
    Load the EQUITY_L.csv file into a pandas DataFrame with caching.
    
    Returns:
        pd.DataFrame: DataFrame containing equity data with columns like 'SYMBOL', 'NAME OF COMPANY', etc.
    """
    global equity_df
    
    if equity_df is not None and not equity_df.empty:
        return equity_df
    
    try:
        # Try to find EQUITY_L.csv in common locations
        search_paths = [
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'EQUITY_L.csv'),
            'EQUITY_L.csv',
            os.path.join('data', 'EQUITY_L.csv'),
            os.path.join('..', 'EQUITY_L.csv')
        ]
        
        file_path = None
        for path in search_paths:
            if os.path.exists(path):
                file_path = path
                break
        
        if not file_path:
            logger.error("EQUITY_L.csv not found in any of the searched locations")
            return pd.DataFrame(columns=['SYMBOL', 'NAME OF COMPANY'])
        
        # Read the CSV with appropriate encoding
        try:
            equity_df = pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            equity_df = pd.read_csv(file_path, encoding='latin1')
        
        # Standardize column names (strip and uppercase)
        equity_df.columns = equity_df.columns.str.strip().str.upper()
        
        # Ensure required columns exist
        required_columns = ['SYMBOL', 'NAME OF COMPANY']
        for col in required_columns:
            if col not in equity_df.columns:
                logger.error(f"Required column '{col}' not found in EQUITY_L.csv")
                return pd.DataFrame(columns=required_columns)
        
        # Clean the data
        equity_df = equity_df.dropna(subset=['SYMBOL', 'NAME OF COMPANY'], how='all')
        equity_df['SYMBOL'] = equity_df['SYMBOL'].astype(str).str.strip()
        equity_df['NAME OF COMPANY'] = equity_df['NAME OF COMPANY'].astype(str).str.strip()
        
        # Remove duplicates, keeping the first occurrence
        equity_df = equity_df.drop_duplicates(subset=['SYMBOL'], keep='first')
        
        logger.info(f"Successfully loaded {len(equity_df)} equity records from {file_path}")
        
    except Exception as e:
        logger.error(f"Error loading EQUITY_L.csv: {str(e)}")
        equity_df = pd.DataFrame(columns=['SYMBOL', 'NAME OF COMPANY'])
    
    return equity_df

def find_stock_symbol(company_name: str) -> Optional[str]:
    """
    Find stock symbol by company name or symbol in EQUITY_L.csv.
    
    Args:
        company_name: The name or symbol of the company to search for
        
    Returns:
        str: The stock symbol with exchange suffix (e.g., 'RELIANCE.NS') if found, None otherwise
    """
    try:
        if not company_name or not isinstance(company_name, str):
            return None
            
        df = load_equity_data()
        if df.empty:
            return None
        
        # Clean the input
        search_term = company_name.strip().upper()
        
        # Check if input is already a symbol
        symbol_matches = df[df['SYMBOL'].str.upper() == search_term]
        if not symbol_matches.empty:
            symbol = symbol_matches.iloc[0]['SYMBOL']
            return f"{symbol}.NS"  # Add NSE suffix by default
        
        # Check if input is an ISIN
        if 'ISIN' in df.columns:
            isin_matches = df[df['ISIN'].str.upper() == search_term]
            if not isin_matches.empty:
                return f"{isin_matches.iloc[0]['SYMBOL']}.NS"
        
        # Search in company names with flexible matching
        df['SEARCH_TERM'] = df['NAME OF COMPANY'].str.upper().fillna('')
        
        # Try exact match first
        exact_matches = df[df['SEARCH_TERM'] == search_term]
        if not exact_matches.empty:
            return f"{exact_matches.iloc[0]['SYMBOL']}.NS"
        
        # Try contains match
        contains_matches = df[df['SEARCH_TERM'].str.contains(search_term, case=False, na=False)]
        if not contains_matches.empty:
            return f"{contains_matches.iloc[0]['SYMBOL']}.NS"
        
        # Try word-by-word matching for better partial matches
        search_terms = search_term.split()
        if len(search_terms) > 1:
            # Look for rows that contain all search terms
            mask = df['SEARCH_TERM'].notna()
            for term in search_terms:
                mask = mask & df['SEARCH_TERM'].str.contains(term, case=False, na=False)
            
            matches = df[mask]
            if not matches.empty:
                return f"{matches.iloc[0]['SYMBOL']}.NS"
        
        # Try fuzzy matching for more flexible matching
        try:
            from fuzzywuzzy import process
            company_names = df['SEARCH_TERM'].tolist()
            best_match = process.extractOne(search_term, company_names, score_cutoff=70)
            if best_match:
                matched_name = best_match[0]
                symbol = df[df['SEARCH_TERM'] == matched_name].iloc[0]['SYMBOL']
                return f"{symbol}.NS"
        except ImportError:
            logger.debug("fuzzywuzzy not installed, skipping fuzzy matching")
        
        logger.warning(f"No matching symbol found for: {company_name}")
        return None
            
    except Exception as e:
        logger.error(f"Error finding stock symbol for '{company_name}': {str(e)}")
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
