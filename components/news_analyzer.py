#!/usr/bin/env python3
"""
News Analyzer Component
News analysis and sentiment calculation with Indian stock filtering.
"""

import os
import csv
import time
import requests
import feedparser
from textblob import TextBlob
import logging
from typing import Dict, List, Set
from datetime import datetime, timedelta
import re
from bs4 import BeautifulSoup

# Get the directory of the current file
current_dir = os.path.dirname(os.path.abspath(__file__))
# Path to the EQUITY_L.csv file (assuming it's in the parent directory)
EQUITY_CSV_PATH = os.path.join(current_dir, '..', 'EQUITY_L.csv')

logger = logging.getLogger(__name__)

class NewsAnalyzer:
    """News analysis and sentiment calculation."""
    
    def __init__(self):
        # Use only Indian stock market RSS feeds
        self.news_sources = [
            'https://in.investing.com/rss/news_25.rss',      # Indian Stock Market News
            'https://in.investing.com/rss/news_1062.rss',    # Indian Economy News
            'https://in.investing.com/rss/news_356.rss',     # Indian Corporate News
            'https://in.investing.com/rss/news_462.rss',     # Indian Banking News
            'https://in.investing.com/rss/news_477.rss',     # Indian IPO News
            'https://in.investing.com/rss/news_14.rss'       # Indian Market Analysis
        ]
        
        # Set a user agent to prevent 403 Forbidden errors
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        feedparser.USER_AGENT = self.headers['User-Agent']
        
        # Terms that indicate non-Indian market news
        self.exclude_terms = [
            # US markets
            'wall street', 'nasdaq', 'nyse', 'dow jones', 's&p 500', 's&p500',
            'federal reserve', 'fed rate', 'fomc', 'usd', 'dollar index',
            'treasury yields', 'us inflation', 'us cpi', 'us jobs report',
            
            # European markets
            'euro', 'eurozone', 'ecb', 'european central bank', 'frankfurt',
            'dax', 'cac', 'ftse', 'london', 'paris', 'frankfurt', 'european union',
            'brexit', 'boe', 'bank of england', 'ecb meeting', 'euro stoxx',
            
            # Asian markets (excluding India)
            'hong kong', 'hang seng', 'nikkei', 'shanghai', 'shenzhen', 'tokyo',
            'japan', 'china', 'beijing', 'shanghai composite', 'csi 300',
            'taiwan', 'south korea', 'kospi', 'kosdaq', 'australia', 'asx',
            'singapore', 'straits times', 'jakarta', 'indonesia', 'thailand',
            'malaysia', 'philippines', 'vietnam',
            
            # Other regions
            'mexico', 'brazil', 'russia', 'ukraine', 'middle east', 'dubai',
            'saudi arabia', 'uae', 'qatar', 'africa', 'south africa', 'jse',
            'canada', 'tsx', 'toronto', 'latin america', 'argentina', 'chile',
            
            # Generic terms that often appear in non-Indian context
            'futures', 'pre-market', 'premarket', 'after hours', 'fed chair',
            'treasury secretary', 'white house', 'washington', 'london', 'uk',
            'europe', 'asia', 'pacific', 'new york', 'chicago', 'chicago fed',
            'us stocks', 'american stocks', 'european stocks', 'asian stocks',
            'global markets', 'international markets'
        ]
        
        # Terms that indicate Indian market news (must include at least one of these)
        self.india_indicators = [
            # Stock exchanges and indices
            'nse', 'bse', 'nifty', 'sensex', 'nifty 50', 'sensex 30',
            'nifty bank', 'bank nifty', 'nifty it', 'nifty auto',
            'nifty pharma', 'nifty psu bank', 'nifty metal', 'nifty realty',
            'nifty midcap', 'nifty smallcap', 'nifty 500', 'nifty next 50',
            'bombay stock exchange', 'national stock exchange',
            
            # Indian market terms
            'indian market', 'indian stock market', 'indian shares',
            'indian equities', 'indian stocks', 'indian investors',
            'indian economy', 'rbi', 'reserve bank of india',
            'sebi', 'securities and exchange board of india',
            'finance ministry', 'union budget', 'gst council', 'gst rates',
            'direct tax', 'indirect tax', 'fdi', 'fii', 'dii',
            'foreign institutional investors', 'domestic institutional investors',
            
            # Common Indian company name suffixes
            'ltd', 'limited', '& co', '& co.', '& company', 'industries',
            'corporation', 'labs', 'pharmaceuticals', 'technologies',
            'consultancy', 'solutions', 'services', 'enterprises',
            
            # Common Indian cities and financial centers
            'mumbai', 'delhi', 'bangalore', 'bengaluru', 'chennai', 'kolkata',
            'hyderabad', 'pune', 'ahmedabad', 'gurgaon', 'noida', 'gurugram',
            'maharastra', 'karnataka', 'tamil nadu', 'west bengal', 'delhi ncr'
        ]
        
        # Load Indian stock symbols
        self.indian_stocks = self._load_indian_stock_symbols()
        logger.info(f"News Analyzer initialized with {len(self.indian_stocks)} Indian stock symbols")
        
        # Cache for storing recommendations
        self._recommendations_cache = None
        self._last_update_time = None
        self._cache_duration = 3600  # 1 hour cache duration
    
    def _load_indian_stock_symbols(self) -> Set[str]:
        """Load Indian stock symbols from EQUITY_L.csv"""
        stocks = set()
        try:
            with open(EQUITY_CSV_PATH, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    # Add both symbol and company name for better matching
                    symbol = row.get('SYMBOL', '').strip()
                    company_name = row.get('NAME OF COMPANY', '').strip()
                    if symbol:
                        stocks.add(symbol.upper())
                    # Add first word of company name for better matching
                    first_word = company_name.split()[0].upper()
                    if len(first_word) > 2:  # Only add if it's a meaningful word
                        stocks.add(first_word)
            logger.info(f"Loaded {len(stocks)} stock symbols and company names")
        except Exception as e:
            logger.error(f"Error loading stock symbols: {str(e)}")
        return stocks
    
    def _is_relevant_news(self, text: str) -> bool:
        """Check if the text is relevant Indian market news with strict filtering"""
        if not text or len(text.strip()) < 20:  # Skip very short texts
            return False
            
        text_lower = text.lower()
        text_upper = text.upper()
        
        # Skip if contains any non-Indian market terms
        for term in self.exclude_terms:
            if term in text_lower:
                return False
        
        # Must contain at least one Indian market indicator
        has_india_indicator = any(
            re.search(r'\b' + re.escape(term) + r'\b', text_lower)
            for term in self.india_indicators
        )
        
        # Must contain at least one Indian stock symbol (3+ characters to avoid false positives)
        has_indian_stock = any(
            len(stock) >= 3 and 
            re.search(r'\b' + re.escape(stock) + r'\b', text_upper)
            for stock in self.indian_stocks
        )
        
        # Must contain at least one of the required indicators
        if not (has_india_indicator or has_indian_stock):
            return False
            
        # Additional checks for false positives
        if self._is_false_positive(text_lower):
            return False
            
        return True
        
    def _is_false_positive(self, text_lower: str) -> bool:
        """Check for common false positives in news text"""
        # Common patterns that might slip through initial filters
        false_positives = [
            # Common words that might match stock symbols
            r'\b(?:the|and|for|with|from|this|that|have|has|had|will|would)\b',
            
            # Common abbreviations that might match stock symbols
            r'\b(?:it|its|me|my|we|us|our|you|your|they|them|their)\b',
            
            # Common words in financial news that aren't specific to India
            r'\b(?:market|stock|stocks|share|shares|trading|investor|investors|price|prices|index|indices)\b',
            
            # Common verbs that might match stock symbols
            r'\b(?:has|have|had|was|were|are|is|be|being|been|do|does|did|will|would|should|could|can|may|might|must)\b',
            
            # Common prepositions and articles
            r'\b(?:in|on|at|by|for|of|to|with|about|as|into|like|through|after|over|between|out|against|during|before|above|below|from|up|down|in|out|on|off|over|under|again|further|then|once|here|there|when|where|why|how|all|any|both|each|few|more|most|other|some|such|no|nor|not|only|own|same|so|than|too|very|s|t|can|will|just|don|should|now|d|ll|m|o|re|ve|y|ain|aren|could|didn|doesn|hadn|hasn|haven|isn|ma|mightn|mustn|needn|shan|shouldn|wasn|weren|won|wouldn)\b'
        ]
        
        # If the text only contains common words, it's likely not relevant
        common_word_ratio = sum(
            bool(re.search(pattern, text_lower, re.IGNORECASE))
            for pattern in false_positives
        ) / max(1, len(text_lower.split()))
        
        return common_word_ratio > 0.7  # If more than 70% of words are common, likely not relevant
    
    def fetch_news(self, force_refresh: bool = False) -> List[Dict]:
        """Fetch and filter news related to Indian stocks with caching."""
        # Return cached results if they exist and are fresh
        current_time = time.time()
        if (not force_refresh and self._recommendations_cache and 
            self._last_update_time and 
            (current_time - self._last_update_time) < self._cache_duration):
            logger.info("Returning cached news articles")
            return self._recommendations_cache
            
        articles = []
        
        for source in self.news_sources:
            try:
                # Add a small delay between requests to avoid rate limiting
                time.sleep(1)
                
                # Parse the feed with custom headers
                feed = feedparser.parse(source, request_headers=self.headers)
                
                # Skip if no entries found
                if not feed.entries:
                    logger.debug(f"No entries found in {source}")
                    continue
                    
                for entry in feed.entries[:15]:  # Check more entries to find relevant ones
                    try:
                        # Get and clean the content
                        title = entry.get('title', '').strip()
                        description = entry.get('summary', entry.get('description', ''))
                        description = re.sub(r'<[^>]+>', '', description).strip()  # Remove HTML tags
                        
                        # Skip if title or description is too short
                        if len(title) < 10 or len(description) < 20:
                            continue
                            
                        # Combine title and description for better matching
                        content = f"{title} {description}"
                        
                        # Skip if not relevant Indian market news
                        if not self._is_relevant_news(content):
                            continue
                        
                        # Extract mentioned stocks (only those with length > 3 to avoid false positives)
                        mentioned_stocks = []
                        content_upper = content.upper()
                        for stock in self.indian_stocks:
                            if len(stock) > 3 and re.search(r'\b' + re.escape(stock) + r'\b', content_upper):
                                mentioned_stocks.append(stock)
                        
                        # Skip if no stocks were mentioned (shouldn't happen due to _is_relevant_news check)
                        if not mentioned_stocks:
                            continue
                        
                        # Clean up the title (remove source names, etc.)
                        clean_title = re.sub(r'\s*-\s*\w+(\.\w+)*\s*$', '', title)
                        
                        articles.append({
                            'title': clean_title,
                            'description': description,
                            'url': entry.get('link', ''),
                            'publishedAt': entry.get('published', ''),
                            'source': source.split('/')[-1].split('.')[0],  # Just get the source name
                            'stocks': mentioned_stocks[:5]  # Limit to top 5 mentioned stocks
                        })
                        
                        # Break if we have enough articles
                        if len(articles) >= 20:  # Limit to 20 articles max
                            break
                            
                    except Exception as e:
                        logger.debug(f"Skipping entry due to error: {str(e)}")
                        continue
                
                if len(articles) >= 20:  # Stop if we have enough articles
                    break
                        
            except Exception as e:
                logger.warning(f"Error fetching from {source}: {str(e)}")
                continue
        
        # Sort articles by published date (newest first)
        articles.sort(key=lambda x: x.get('publishedAt', ''), reverse=True)
        
        # Update cache
        self._recommendations_cache = articles
        self._last_update_time = current_time
        
        logger.info(f"Fetched {len(articles)} relevant Indian market news articles")
        return articles
    
    def fetch_all_news_articles(self) -> List[Dict]:
        """Fetch all news articles from RSS feeds."""
        try:
            all_articles = []
            
            # Fetch from all RSS sources
            for source in self.news_sources:
                try:
                    feed = feedparser.parse(source)
                    for entry in feed.entries:  # Get all articles from each source
                        article = {
                            'title': entry.get('title', ''),
                            'description': entry.get('summary', ''),
                            'url': entry.get('link', ''),
                            'publishedAt': entry.get('published', ''),
                            'source': source,
                            'full_content': ''
                        }
                        all_articles.append(article)
                        
                except Exception as e:
                    logger.warning(f"Error fetching from {source}: {str(e)}")
            
            logger.info(f"Fetched {len(all_articles)} total articles from RSS feeds")
            return all_articles
            
        except Exception as e:
            logger.error(f"Error fetching news articles: {str(e)}")
            return []
    
    def filter_indian_news_by_headline(self, articles: List[Dict]) -> List[Dict]:
        """Filter articles by Indian stock market keywords in headlines and content."""
        try:
            # Get comprehensive NSE stock list for more specific filtering
            nse_stocks = self.get_comprehensive_nse_stocks_list()
            nse_stocks_set = set(nse_stocks)
            
            # Indian stock market specific keywords
            indian_stock_keywords = [
                'NSE', 'BSE', 'BOMBAY STOCK EXCHANGE', 'NATIONAL STOCK EXCHANGE',
                'SENSEX', 'NIFTY', 'NIFTY 50', 'NIFTY NEXT 50',
                'SEBI', 'RBI', 'RESERVE BANK', 'SECURITIES AND EXCHANGE BOARD',
                'UNION BUDGET', 'FISCAL DEFICIT', 'GST', 'GOODS AND SERVICES TAX',
                'FDI', 'FOREIGN DIRECT INVESTMENT', 'FII', 'FOREIGN INSTITUTIONAL INVESTMENT',
                'IPO', 'INITIAL PUBLIC OFFERING', 'QIP', 'QUALIFIED INSTITUTIONAL PLACEMENT',
                'MERGER', 'ACQUISITION', 'TAKEOVER', 'JOINT VENTURE',
                'QUARTERLY RESULTS', 'ANNUAL RESULTS', 'EARNINGS', 'DIVIDEND', 'BONUS',
                'STOCK SPLIT', 'RIGHTS ISSUE', 'BONUS SHARES'
            ]
            
            # Major Indian company names and sectors
            indian_companies = [
                'RELIANCE', 'TATA', 'ADANI', 'HDFC', 'ICICI', 'SBI', 'INFOSYS', 'TCS', 'WIPRO', 'HCL',
                'BHARTI', 'MARUTI', 'BAJAJ', 'MAHINDRA', 'HERO', 'EICHER', 'ASHOK LEYLAND', 'TVS',
                'SUN PHARMA', 'DR REDDY', 'CIPLA', 'LUPIN', 'BIOCON', 'DIVIS LAB', 'AUROBINDO',
                'ITC', 'HUL', 'NESTLE', 'BRITANNIA', 'DABUR', 'GODREJ', 'MARICO', 'COLPAL',
                'ONGC', 'IOC', 'BPCL', 'HPCL', 'GAIL', 'COAL INDIA', 'NTPC', 'POWERGRID',
                'TATA STEEL', 'JSW STEEL', 'HINDALCO', 'VEDANTA', 'SAIL', 'NMDC',
                'LT', 'NCC', 'KEC', 'IRCON', 'RVNL', 'BEML', 'TITAGARH',
                'BEL', 'HAL', 'BDL', 'MIDHANI', 'BHARAT FORGE',
                'APOLLO HOSPITALS', 'FORTIS', 'MAX HEALTH', 'NARAYANA HRUDAYALAYA',
                'DLF', 'GODREJ PROPERTIES', 'BRIGADE', 'SOBHA', 'PRESTIGE',
                'ZEEL', 'SUN TV', 'NETWORK18', 'TV TODAY', 'JAGRAN',
                'INDIGO', 'SPICEJET', 'JET AIRWAYS',
                'BATA', 'TITAN', 'PC JEWELLER', 'KALYAN JEWELLERS',
                'VOLTAS', 'BLUE STAR', 'WHIRLPOOL', 'CROMPTON', 'HAVELLS',
                'ASIAN PAINTS', 'BERGER PAINTS', 'KANSAI NEROLAC', 'AKZO NOBEL',
                'ULTRATECH', 'SHREE CEMENT', 'RAMCO CEMENT', 'HEIDELBERG',
                'BAJAJ FINANCE', 'BAJAJ FINSERV', 'CHOLAMANDALAM', 'LIC HOUSING',
                'MOTILAL OSWAL', 'ANGEL BROKING', 'ZERODHA', 'UPSTOX'
            ]
            
            filtered_articles = []
            
            for article in articles:
                title = article.get('title', '').upper()
                description = article.get('description', '').upper()
                content = f"{title} {description}"
                
                # Check for NSE stock symbols in title/description
                has_nse_stock = any(stock in content for stock in nse_stocks_set)
                
                # Check for Indian stock market keywords
                has_stock_keywords = any(keyword in content for keyword in indian_stock_keywords)
                
                # Check for major Indian companies
                has_indian_company = any(company in content for company in indian_companies)
                
                # Must have at least one of these criteria
                if has_nse_stock or has_stock_keywords or has_indian_company:
                    article['is_india_related'] = True
                    article['filter_reason'] = []
                    if has_nse_stock:
                        article['filter_reason'].append('NSE Stock')
                    if has_stock_keywords:
                        article['filter_reason'].append('Stock Keywords')
                    if has_indian_company:
                        article['filter_reason'].append('Indian Company')
                    
                    filtered_articles.append(article)
                    logger.debug(f"Indian stock article: {article.get('title', '')[:50]}... - {article['filter_reason']}")
            
            logger.info(f"Filtered {len(filtered_articles)} Indian stock-related articles from {len(articles)} total articles")
            return filtered_articles
            
        except Exception as e:
            logger.error(f"Error filtering Indian news: {str(e)}")
            return articles
    
    def fetch_top_10_news_with_content(self) -> List[Dict]:
        """Fetch at least 10 Indian news articles with full content for Groq analysis."""
        try:
            # Step 1: Fetch all articles from RSS feeds
            all_articles = self.fetch_all_news_articles()
            
            if not all_articles:
                logger.warning("No articles fetched from RSS feeds")
                return []
            
            # Step 2: Filter by India-related keywords in headlines
            indian_articles = self.filter_indian_news_by_headline(all_articles)
            
            # Step 3: If we don't have at least 10 Indian articles, try more aggressive filtering
            if len(indian_articles) < 10:
                logger.info(f"Only found {len(indian_articles)} Indian articles, trying more aggressive filtering...")
                indian_articles = self._aggressive_indian_filtering(all_articles)
                logger.info(f"After aggressive filtering: {len(indian_articles)} Indian articles")
            
            # Step 4: If still not enough, try alternative sources or expand search
            if len(indian_articles) < 10:
                logger.info("Still not enough articles, trying alternative filtering methods...")
                indian_articles = self._alternative_indian_filtering(all_articles)
                logger.info(f"After alternative filtering: {len(indian_articles)} Indian articles")
            
            if not indian_articles:
                logger.warning("No India-related articles found after all filtering attempts")
                return []
            
            # Step 5: Fetch full content for filtered articles
            for article in indian_articles:
                try:
                    full_content = self._fetch_article_content(article.get('url', ''))
                    
                    # If full content is empty (due to 403 or other errors), use description as fallback
                    if not full_content or len(full_content.strip()) < 50:
                        description = article.get('description', '')
                        if description and len(description.strip()) > 20:
                            # Enhance description with title for better analysis
                            title = article.get('title', '')
                            enhanced_content = f"{title}. {description}"
                            article['full_content'] = enhanced_content
                            article['content_source'] = 'description_fallback'
                            logger.info(f"Using enhanced description as fallback for {article.get('title', '')[:50]}...")
                        else:
                            article['full_content'] = article.get('title', '')
                            article['content_source'] = 'title_only'
                            logger.warning(f"Using title only for {article.get('title', '')[:50]}...")
                    else:
                        article['full_content'] = full_content
                        article['content_source'] = 'full_content'
                        logger.info(f"Successfully fetched full content for {article.get('title', '')[:50]}...")
                        
                except Exception as e:
                    logger.warning(f"Could not fetch full content for {article.get('url', '')}: {str(e)}")
                    article['full_content'] = article.get('description', '')
            
            # Step 6: Sort by published date (newest first) and take top articles
            indian_articles.sort(key=lambda x: x.get('publishedAt', ''), reverse=True)
            # Take at least 10, but up to 15 for better analysis
            top_articles = indian_articles[:15]
            
            logger.info(f"Fetched {len(top_articles)} Indian news articles with full content for Groq analysis")
            return top_articles
            
        except Exception as e:
            logger.error(f"Error fetching Indian news: {str(e)}")
            return []
    
    def _filter_indian_stock_news(self, articles: List[Dict]) -> List[Dict]:
        """Filter news articles to only include those related to Indian stocks."""
        try:
            nse_stocks = self.get_comprehensive_nse_stocks_list()
            filtered_articles = []
            
            # Indian market keywords to ensure relevance
            indian_market_keywords = [
                'INDIA', 'INDIAN', 'NSE', 'BSE', 'BOMBAY STOCK EXCHANGE', 'NATIONAL STOCK EXCHANGE',
                'SENSEX', 'NIFTY', 'MUMBAI', 'DELHI', 'BENGALURU', 'CHENNAI', 'KOLKATA', 'HYDERABAD',
                'RUPEES', 'INR', '₹', 'CRORES', 'LAKHS', 'CRORE', 'LAKH',
                'SEBI', 'RBI', 'RESERVE BANK', 'SECURITIES AND EXCHANGE BOARD',
                'GST', 'GOODS AND SERVICES TAX', 'DIRECT TAX', 'INDIRECT TAX',
                'UNION BUDGET', 'FISCAL DEFICIT', 'CURRENT ACCOUNT DEFICIT',
                'FDI', 'FOREIGN DIRECT INVESTMENT', 'FII', 'FOREIGN INSTITUTIONAL INVESTMENT',
                'IPO', 'INITIAL PUBLIC OFFERING', 'QIP', 'QUALIFIED INSTITUTIONAL PLACEMENT',
                'MERGER', 'ACQUISITION', 'TAKEOVER', 'JOINT VENTURE',
                'QUARTERLY RESULTS', 'ANNUAL RESULTS', 'EARNINGS', 'PROFIT', 'LOSS',
                'DIVIDEND', 'BONUS', 'STOCK SPLIT', 'RIGHTS ISSUE'
            ]
            
            for article in articles:
                # Check if article mentions any NSE stock
                text = f"{article.get('title', '')} {article.get('description', '')} {article.get('full_content', '')}".upper()
                
                # First check if article is India-related
                is_india_related = any(keyword in text for keyword in indian_market_keywords)
                
                if not is_india_related:
                    continue  # Skip non-India related articles
                
                # Look for stock symbols in the text
                mentioned_stocks = []
                for stock in nse_stocks:
                    if stock in text:
                        mentioned_stocks.append(stock)
                
                # Also check for common company name patterns
                company_patterns = [
                    'RELIANCE', 'TATA', 'ADANI', 'HDFC', 'ICICI', 'SBI', 'INFOSYS', 'TCS', 'WIPRO', 'HCL',
                    'BHARTI', 'MARUTI', 'BAJAJ', 'MAHINDRA', 'HERO', 'EICHER', 'ASHOK LEYLAND', 'TVS',
                    'SUN PHARMA', 'DR REDDY', 'CIPLA', 'LUPIN', 'BIOCON', 'DIVIS LAB', 'AUROBINDO',
                    'ITC', 'HUL', 'NESTLE', 'BRITANNIA', 'DABUR', 'GODREJ', 'MARICO', 'COLPAL',
                    'ONGC', 'IOC', 'BPCL', 'HPCL', 'GAIL', 'COAL INDIA', 'NTPC', 'POWERGRID',
                    'TATA STEEL', 'JSW STEEL', 'HINDALCO', 'VEDANTA', 'SAIL', 'NMDC',
                    'LT', 'NCC', 'KEC', 'IRCON', 'RVNL', 'BEML', 'TITAGARH',
                    'BEL', 'HAL', 'BDL', 'MIDHANI', 'BHARAT FORGE',
                    'APOLLO HOSPITALS', 'FORTIS', 'MAX HEALTH', 'NARAYANA HRUDAYALAYA',
                    'DLF', 'GODREJ PROPERTIES', 'BRIGADE', 'SOBHA', 'PRESTIGE',
                    'ZEEL', 'SUN TV', 'NETWORK18', 'TV TODAY', 'JAGRAN',
                    'INDIGO', 'SPICEJET', 'JET AIRWAYS',
                    'BATA', 'TITAN', 'PC JEWELLER', 'KALYAN JEWELLERS',
                    'VOLTAS', 'BLUE STAR', 'WHIRLPOOL', 'CROMPTON', 'HAVELLS',
                    'ASIAN PAINTS', 'BERGER PAINTS', 'KANSAI NEROLAC', 'AKZO NOBEL',
                    'ULTRATECH', 'SHREE CEMENT', 'RAMCO CEMENT', 'HEIDELBERG',
                    'BAJAJ FINANCE', 'BAJAJ FINSERV', 'CHOLAMANDALAM', 'LIC HOUSING',
                    'MOTILAL OSWAL', 'ANGEL BROKING', 'ZERODHA', 'UPSTOX'
                ]
                
                for pattern in company_patterns:
                    if pattern in text:
                        mentioned_stocks.append(pattern.replace(' ', ''))
                
                # If article mentions any Indian stock OR is India-related, include it
                if mentioned_stocks or is_india_related:
                    article['mentioned_stocks'] = list(set(mentioned_stocks)) if mentioned_stocks else []
                    article['is_india_related'] = is_india_related
                    filtered_articles.append(article)
                    logger.debug(f"Article '{article.get('title', '')[:50]}...' - India related: {is_india_related}, Stocks: {mentioned_stocks[:3]}")
            
            logger.info(f"Filtered {len(filtered_articles)} articles related to Indian stocks from {len(articles)} total articles")
            return filtered_articles
            
        except Exception as e:
            logger.error(f"Error filtering Indian stock news: {str(e)}")
            return articles  # Return all articles if filtering fails
    
    def test_rss_feeds(self) -> Dict:
        """Test RSS feeds to see what content they provide."""
        try:
            feed_results = {}
            
            for source in self.news_sources:
                try:
                    feed = feedparser.parse(source)
                    articles = []
                    
                    for entry in feed.entries[:3]:  # Get first 3 articles
                        article = {
                            'title': entry.get('title', ''),
                            'description': entry.get('summary', ''),
                            'url': entry.get('link', ''),
                            'publishedAt': entry.get('published', '')
                        }
                        articles.append(article)
                    
                    feed_results[source] = {
                        'status': 'success',
                        'article_count': len(feed.entries),
                        'sample_articles': articles
                    }
                    
                except Exception as e:
                    feed_results[source] = {
                        'status': 'error',
                        'error': str(e)
                    }
            
            return feed_results
            
        except Exception as e:
            logger.error(f"Error testing RSS feeds: {str(e)}")
            return {'error': str(e)}
    
    def _fetch_article_content(self, url: str) -> str:
        """Fetch full article content from URL with enhanced headers and error handling."""
        try:
            # Multiple user agents to rotate and avoid detection
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
            ]
            
            # Enhanced headers to mimic a real browser and avoid 403 errors
            headers = {
                'User-Agent': user_agents[hash(url) % len(user_agents)],  # Rotate user agents
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
                'Referer': 'https://www.google.com/',
                'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"'
            }
            
            # Create session with retry strategy
            session = requests.Session()
            session.headers.update(headers)
            
            # Add retry adapter
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry
            
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["HEAD", "GET", "OPTIONS"]
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("http://", adapter)
            session.mount("https://", adapter)
            
            # Try with different approaches
            for attempt in range(2):
                try:
                    if attempt == 0:
                        # First attempt: direct request
                        response = session.get(url, timeout=20, allow_redirects=True)
                    else:
                        # Second attempt: with different headers for investing.com specifically
                        if 'investing.com' in url:
                            investing_headers = headers.copy()
                            investing_headers.update({
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                                'Referer': 'https://in.investing.com/',
                                'Origin': 'https://in.investing.com'
                            })
                            session.headers.update(investing_headers)
                        response = session.get(url, timeout=20, allow_redirects=True)
                    
                    # Handle 403 Forbidden specifically
                    if response.status_code == 403:
                        logger.warning(f"403 Forbidden when fetching {url} (attempt {attempt + 1}) - using description as fallback")
                        if attempt == 0:
                            continue  # Try second attempt
                        else:
                            return ""  # Return empty string, will use description as fallback
                    
                    # Handle other HTTP errors
                    if response.status_code >= 400:
                        logger.warning(f"HTTP {response.status_code} when fetching {url} (attempt {attempt + 1})")
                        if attempt == 0:
                            continue  # Try second attempt
                        else:
                            return ""
                    
                    # Success - parse content
                    response.raise_for_status()
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Try to find article content in common containers
                    content_selectors = [
                        '.article-content',
                        '.article-body',
                        '.content',
                        '.post-content',
                        '.entry-content',
                        '[data-test="article-content"]',
                        '.article-text',
                        '.articlePage',
                        '.article-wrapper',
                        '.article__content',
                        '.article-content-wrapper',
                        '.post-body',
                        '.entry-body',
                        '.story-body',
                        '.article-main-content'
                    ]
                    
                    content = ""
                    for selector in content_selectors:
                        elements = soup.select(selector)
                        if elements:
                            content = ' '.join([elem.get_text(strip=True) for elem in elements])
                            if len(content) > 100:  # Ensure we got meaningful content
                                break
                    
                    # If no specific content found, try to get all paragraph text
                    if not content or len(content) < 100:
                        paragraphs = soup.find_all('p')
                        content = ' '.join([p.get_text(strip=True) for p in paragraphs])
                    
                    # Clean up the content
                    content = re.sub(r'\s+', ' ', content)  # Replace multiple spaces with single space
                    content = content[:5000]  # Limit to 5000 characters
                    
                    if len(content) > 50:  # Only return if we got meaningful content
                        logger.info(f"Successfully fetched content for {url} ({len(content)} characters)")
                        return content
                    else:
                        logger.warning(f"Minimal content fetched for {url} - using description as fallback")
                        return ""
                        
                except requests.exceptions.Timeout:
                    logger.warning(f"Timeout when fetching {url} (attempt {attempt + 1})")
                    if attempt == 0:
                        continue
                    else:
                        return ""
                except requests.exceptions.ConnectionError:
                    logger.warning(f"Connection error when fetching {url} (attempt {attempt + 1})")
                    if attempt == 0:
                        continue
                    else:
                        return ""
            
            # If we get here, all attempts failed
            logger.warning(f"All attempts failed for {url} - using description as fallback")
            return ""
            
        except Exception as e:
            logger.warning(f"Unexpected error when fetching {url}: {str(e)}")
            return ""
    
    def analyze_news_sentiment(self, articles: List[Dict]) -> float:
        """Analyze sentiment of news articles."""
        try:
            if not articles:
                return 0.0
            
            sentiments = []
            for article in articles:
                text = f"{article.get('title', '')} {article.get('description', '')}"
                if text:
                    blob = TextBlob(text)
                    sentiments.append(blob.sentiment.polarity)
            
            if sentiments:
                avg_sentiment = sum(sentiments) / len(sentiments)
                return avg_sentiment
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}")
            return 0.0
    
    def get_comprehensive_nse_stocks_list(self) -> List[str]:
        """Get comprehensive list of all NSE stock symbols."""
        return [
            '20MICRONS', '21STCENMGM', '360ONE', '3IINFO-RE', '3IINFOLTD', '3MINDIA', '3PLAND', '5PAISA', '63MOONS',
            'A2ZINFRA', 'AAATECH', 'AADHARHFC', 'AAKASH', 'AAREYDRUGS', 'AARON', 'AARTECH', 'AARTIDRUGS', 'AARTIIND',
            'AARTIPHARM', 'AARTISURF', 'AARVI', 'AAVAS', 'ABAN', 'ABB', 'ABBOTINDIA', 'ABCAPITAL', 'ABCOTS', 'ABDL',
            'ABFRL', 'ABINFRA', 'ABLBL', 'ABMINTLLTD', 'ABREL', 'ABSLAMC', 'ACC', 'ACCELYA', 'ACCURACY', 'ACE',
            'ACEINTEG', 'ACI', 'ACL', 'ACLGATI', 'ACMESOLAR', 'ACUTAAS', 'ADANIENSOL', 'ADANIENT', 'ADANIGREEN',
            'ADANIPORTS', 'ADANIPOWER', 'ADFFOODS', 'ADL', 'ADOR', 'ADROITINFO', 'ADSL', 'ADVANCE', 'ADVANIHOTR',
            'ADVENZYMES', 'AEGISLOG', 'AEGISVOPAK', 'AEROENTER', 'AEROFLEX', 'AERONEU', 'AETHER', 'AFCONS', 'AFFLE',
            'AFFORDABLE', 'AFIL', 'AFSL', 'AGARIND', 'AGARWALEYE', 'AGI', 'AGIIL', 'AGRITECH', 'AGROPHOS', 'AGSTRA',
            'AHCL', 'AHLADA', 'AHLEAST', 'AHLUCONT', 'AIAENG', 'AIIL', 'AIRAN', 'AIROLAM', 'AJANTPHARM', 'AJAXENGG',
            'AJMERA', 'AJOONI', 'AKASH', 'AKG', 'AKI', 'AKSHAR', 'AKSHARCHEM', 'AKSHOPTFBR', 'AKUMS', 'AKZOINDIA',
            'ALANKIT', 'ALBERTDAVD', 'ALEMBICLTD', 'ALICON', 'ALIVUS', 'ALKALI', 'ALKEM', 'ALKYLAMINE', 'ALLCARGO',
            'ALLDIGI', 'ALLTIME', 'ALMONDZ', 'ALOKINDS', 'ALPA', 'ALPHAGEO', 'ALPSINDUS', 'AMANTA', 'AMBER', 'AMBICAAGAR',
            'AMBIKCO', 'AMBUJACEM', 'AMDIND', 'AMJLAND', 'AMNPLST', 'AMRUTANJAN', 'ANANDRATHI', 'ANANTRAJ', 'ANDHRAPAP',
            'ANDHRSUGAR', 'ANGELONE', 'ANIKINDS', 'ANKITMETAL', 'ANMOL', 'ANSALAPI', 'ANTELOPUS', 'ANTGRAPHIC', 'ANTHEM',
            'ANUHPHR', 'ANUP', 'ANURAS', 'APARINDS', 'APCL', 'APCOTEXIND', 'APEX', 'APLAPOLLO', 'APLLTD', 'APOLLO',
            'APOLLOHOSP', 'APOLLOPIPE', 'APOLLOTYRE', 'APOLSINHOT', 'APTECHT', 'APTUS', 'ARCHIDPLY', 'ARCHIES', 'ARE&M',
            'ARENTERP', 'ARFIN', 'ARIES', 'ARIHANTCAP', 'ARIHANTSUP', 'ARISINFRA', 'ARKADE', 'ARMANFIN', 'AROGRANITE',
            'ARROWGREEN', 'ARSSIYA', 'ARSSBL', 'ARTEMISMED', 'ARTNIRMAN', 'ARVEE', 'ARVIND', 'ARVINDFASN', 'ARVSMART',
            'ASAHIINDIA', 'ASAHISONG', 'ASAL', 'ASALCBR', 'ASHAPURMIN', 'ASHIANA', 'ASHIMASYN', 'ASHOKA', 'ASHOKAMET',
            'ASHOKLEY', 'ASIANENE', 'ASIANHOTNR', 'ASIANPAINT', 'ASIANTILES', 'ASKAUTOLTD', 'ASMS', 'ASPINWALL', 'ASTEC',
            'ASTERDM', 'ASTRAL', 'ASTRAMICRO', 'ASTRAZEN', 'ASTRON', 'ATALREAL', 'ATAM', 'ATGL', 'ATHERENERG', 'ATL',
            'ATLANTAA', 'ATLANTAELE', 'ATLASCYCLE', 'ATUL', 'ATULAUTO', 'AUBANK', 'AURIONPRO', 'AUROPHARMA', 'AURUM',
            'AUSOMENT', 'AUTOAXLES', 'AUTOIND', 'AVADHSUGAR', 'AVALON', 'AVANTEL', 'AVANTIFEED', 'AVG', 'AVL', 'AVONMORE',
            'AVROIND', 'AVTNPL', 'AWFIS', 'AWHCL', 'AWL', 'AXISBANK', 'AXISCADES', 'AXITA', 'AYMSYNTEX', 'AZAD',
            'BAFNAPH', 'BAGFILMS', 'BAIDFIN', 'BAJAJ-AUTO', 'BAJAJCON', 'BAJAJELEC', 'BAJAJFINSV', 'BAJAJHCARE', 'BAJAJHFL',
            'BAJAJHIND', 'BAJAJHLDNG', 'BAJAJINDEF', 'BAJEL', 'BAJFINANCE', 'BALAJEE', 'BALAJITELE', 'BALAMINES', 'BALAXI',
            'BALKRISHNA', 'BALKRISIND', 'BALMLAWRIE', 'BALPHARMA', 'BALRAMCHIN', 'BALUFORGE', 'BANARBEADS', 'BANARISUG',
            'BANCOINDIA', 'BANDHANBNK', 'BANG', 'BANKA', 'BANKBARODA', 'BANKINDIA', 'BANSALWIRE', 'BANSWRAS', 'BASF',
            'BASML', 'BATAINDIA', 'BAYERCROP', 'BBL', 'BBOX', 'BBTC', 'BBTCL', 'BCG', 'BCLIND', 'BCONCEPTS', 'BDL',
            'BEARDSELL', 'BECTORFOOD', 'BEDMUTHA', 'BEL', 'BELLACASA', 'BELRISE', 'BEML', 'BEPL', 'BERGEPAINT', 'BESTAGRO',
            'BFINVEST', 'BFUTILITIE', 'BGLOBAL', 'BGRENERGY', 'BHAGCHEM', 'BHAGERIA', 'BHAGYANGR', 'BHANDARI', 'BHARATFORG',
            'BHARATGEAR', 'BHARATRAS', 'BHARATSE', 'BHARATWIRE', 'BHARTIARTL', 'BHARTIHEXA', 'BHEL', 'BIGBLOC', 'BIKAJI',
            'BIL', 'BILVYAPAR', 'BIOCON', 'BIOFILCHEM', 'BIRLACABLE', 'BIRLACORPN', 'BIRLAMONEY', 'BIRLANU', 'BLACKBUCK',
            'BLAL', 'BLBLIMITED', 'BLISSGVS', 'BLKASHYAP', 'BLS', 'BLSE', 'BLUECHIP', 'BLUECOAST', 'BLUEDART', 'BLUEJET',
            'BLUESTARCO', 'BLUESTONE', 'BLUSPRING', 'BMWVENTLTD', 'BODALCHEM', 'BOHRAIND', 'BOMDYEING', 'BORANA', 'BOROLTD',
            'BORORENEW', 'BOROSCI', 'BOSCHLTD', 'BPCL', 'BPL', 'BRIGADE', 'BRIGHOTEL', 'BRITANNIA', 'BRNL', 'BROOKS',
            'BSE', 'BSHSL', 'BSL', 'BSOFT', 'BTML', 'BUTTERFLY', 'BVCL', 'BYKE', 'CALSOFT', 'CAMLINFINE', 'CAMPUS',
            'CAMS', 'CANBK', 'CANFINHOME', 'CANTABIL', 'CAPACITE', 'CAPITALSFB', 'CAPLIPOINT', 'CAPTRUST', 'CARBORUNIV',
            'CARERATING', 'CARRARO', 'CARTRADE', 'CARYSIL', 'CASTROLIND', 'CCCL', 'CCHHL', 'CCL', 'CDSL', 'CEATLTD',
            'CEIGALL', 'CELEBRITY', 'CELLO', 'CEMPRO', 'CENTENKA', 'CENTEXT', 'CENTRALBK', 'CENTRUM', 'CENTUM', 'CENTURYPLY',
            'CERA', 'CEREBRAINT', 'CESC', 'CEWATER', 'CGCL', 'CGPOWER', 'CHALET', 'CHAMBLFERT', 'CHEMBOND', 'CHEMBONDCH',
            'CHEMCON', 'CHEMFAB', 'CHEMPLASTS', 'CHENNPETRO', 'CHEVIOT', 'CHOICEIN', 'CHOLAFIN', 'CHOLAHLDNG', 'CIEINDIA',
            'CIFL', 'CIGNITITEC', 'CINELINE', 'CINEVISTA', 'CIPLA', 'CLEAN', 'CLEDUCATE', 'CLSEL', 'CMICABLES', 'CMSINFO',
            'COALINDIA', 'COASTCORP', 'COCHINSHIP', 'COFFEEDAY', 'COFORGE', 'COHANCE', 'COLPAL', 'COMPINFO', 'COMPUSOFT',
            'COMSYN', 'CONCOR', 'CONCORDBIO', 'CONFIPET', 'CONSOFINVT', 'CONTROLPR', 'CORALFINAC', 'CORDSCABLE', 'COROMANDEL',
            'COSMOFIRST', 'COUNCODOS', 'CPCAP', 'CPEDU', 'CPPLUS', 'CRAFTSMAN', 'CREATIVE', 'CREATIVEYE', 'CREDITACC',
            'CREST', 'CRISIL', 'CRIZAC', 'CROMPTON', 'CROWN', 'CSBBANK', 'CSLFINANCE', 'CTE', 'CUB', 'CUBEXTUB', 'CUMMINSIND',
            'CUPID', 'CURAA', 'CYBERMEDIA', 'CYBERTECH', 'CYIENT', 'CYIENTDLM', 'DABUR', 'DALBHARAT', 'DALMIASUG', 'DAMCAPITAL',
            'DAMODARIND', 'DANGEE', 'DATAMATICS', 'DATAPATTNS', 'DAVANGERE', 'DBCORP', 'DBEIL', 'DBL', 'DBOL', 'DBREALTY',
            'DBSTOCKBRO', 'DCAL', 'DCBBANK', 'DCI', 'DCM', 'DCMFINSERV', 'DCMNVL', 'DCMSHRIRAM', 'DCMSRIND', 'DCW',
            'DCXINDIA', 'DDEVPLSTIK', 'DECCANCE', 'DEEDEV', 'DEEPAKFERT', 'DEEPAKNTR', 'DEEPINDS', 'DELHIVERY', 'DELPHIFX',
            'DELTACORP', 'DELTAMAGNT', 'DEN', 'DENORA', 'DENTA', 'DEVIT', 'DEVX', 'DEVYANI', 'DGCONTENT', 'DHAMPURSUG',
            'DHANBANK', 'DHANI', 'DHANUKA', 'DHARAN', 'DHARMAJ', 'DHRUV', 'DHUNINV', 'DIACABS', 'DIAMINESQ', 'DIAMONDYD',
            'DICIND', 'DIFFNKG', 'DIGIDRIVE', 'DIGISPICE', 'DIGITIDE', 'DIGJAMLMTD', 'DIL', 'DISHTV', 'DIVGIITTS', 'DIVISLAB',
            'DIXON', 'DJML', 'DLF', 'DLINKINDIA', 'DMART', 'DMCC', 'DNAMEDIA', 'DODLA', 'DOLATALGO', 'DOLLAR', 'DOLPHIN',
            'DOMS', 'DONEAR', 'DPABHUSHAN', 'DPSCLTD', 'DPWIRES', 'DRCSYSTEMS', 'DREAMFOLKS', 'DREDGECORP', 'DRREDDY',
            'DSSL', 'DTIL', 'DUCON', 'DVL', 'DWARKESH', 'DYCL', 'DYNAMATECH', 'DYNPRO', 'E2E', 'EASEMYTRIP', 'EASTSILK',
            'EBGNG', 'ECLERX', 'ECOSMOBLTY', 'EDELWEISS', 'EDUCOMP', 'EFCIL', 'EICHERMOT', 'EIDPARRY', 'EIEL', 'EIFFL',
            'EIHAHOTELS', 'EIHOTEL', 'EIMCOELECO', 'EKC', 'ELDEHSG', 'ELECON', 'ELECTCAST', 'ELECTHERM', 'ELGIEQUIP',
            'ELGIRUBCO', 'ELIN', 'ELLEN', 'EMAMILTD', 'EMAMIPAP', 'EMAMIREAL', 'EMBDL', 'EMCURE', 'EMIL', 'EMKAY',
            'EMMBI', 'EMSLIMITED', 'EMUDHRA', 'ENDURANCE', 'ENERGYDEV', 'ENGINERSIN', 'ENIL', 'ENRIN', 'ENTERO', 'EPACK',
            'EPACKPEB', 'EPIGRAL', 'EPL', 'EQUIPPP', 'EQUITASBNK', 'ERIS', 'ESABINDIA', 'ESAFSFB', 'ESCORTS', 'ESSARSHPNG',
            'ESSENTIA', 'ESTER', 'ETERNAL', 'ETHOSLTD', 'EUREKAFORB', 'EUROBOND', 'EUROPRATIK', 'EUROTEXIND', 'EVEREADY',
            'EVERESTIND', 'EXCEL', 'EXCELINDUS', 'EXICOM', 'EXIDEIND', 'EXPLEOSOL', 'EXXARO', 'FABTECH', 'FACT', 'FAIRCHEMOR',
            'FAZE3Q', 'FCL', 'FCONSUMER', 'FCSSOFT', 'FDC', 'FEDERALBNK', 'FEDFINA', 'FEL', 'FELDVR', 'FIBERWEB', 'FIEMIND',
            'FILATEX', 'FILATFASH', 'FINCABLES', 'FINEORG', 'FINKURVE', 'FINOPB', 'FINPIPE', 'FIRSTCRY', 'FISCHER', 'FIVESTAR',
            'FLAIR', 'FLEXITUFF', 'FLFL', 'FLUOROCHEM', 'FMGOETZE', 'FMNL', 'FOCUS', 'FOODSIN', 'FORCEMOT', 'FORTIS',
            'FOSECOIND', 'FSC', 'FSL', 'FUSION', 'GABRIEL', 'GAEL', 'GAIL', 'GALAPREC', 'GALAXYSURF', 'GALLANTT', 'GANDHAR',
            'GANDHITUBE', 'GANECOS', 'GANESHBE', 'GANESHCP', 'GANESHHOU', 'GANGAFORGE', 'GANGESSECU', 'GARFIBRES', 'GARUDA',
            'GATECH', 'GATECHDVR', 'GATEWAY', 'GAYAHWS', 'GAYAPROJ', 'GCSL', 'GEECEE', 'GEEKAYWIRE', 'GEMAROMA', 'GENCON',
            'GENESYS', 'GENSOL', 'GENUSPAPER', 'GENUSPOWER', 'GEOJITFSL', 'GESHIP', 'GFLLIMITED', 'GFSTEELS', 'GHCL',
            'GHCLTEXTIL', 'GICHSGFIN', 'GICRE', 'GILLANDERS', 'GILLETTE', 'GINNIFILA', 'GIPCL', 'GKENERGY', 'GKWLIMITED',
            'GLAND', 'GLAXO', 'GLENMARK', 'GLFL', 'GLOBAL', 'GLOBALE', 'GLOBALVECT', 'GLOBE', 'GLOBECIVIL', 'GLOBUSSPR',
            'GLOSTERLTD', 'GLOTTIS', 'GMBREW', 'GMDCLTD', 'GMMPFAUDLR', 'GMRAIRPORT', 'GMRP&UI', 'GNA', 'GNFC', 'GOACARBON',
            'GOCLCORP', 'GOCOLORS', 'GODAVARIB', 'GODFRYPHLP', 'GODHA', 'GODIGIT', 'GODREJAGRO', 'GODREJCP', 'GODREJIND',
            'GODREJPROP', 'GOENKA', 'GOKEX', 'GOKUL', 'GOKULAGRO', 'GOLDENTOBC', 'GOLDIAM', 'GOLDTECH', 'GOODLUCK', 'GOPAL',
            'GOYALALUM', 'GPIL', 'GPPL', 'GPTHEALTH', 'GPTINFRA', 'GRANULES', 'GRAPHITE', 'GRASIM', 'GRAVITA', 'GREAVESCOT',
            'GREENLAM', 'GREENPANEL', 'GREENPLY', 'GREENPOWER', 'GRINDWELL', 'GRINFRA', 'GRMOVER', 'GROBTEA', 'GRPLTD',
            'GRSE', 'GRWRHITECH', 'GSFC', 'GSLSU', 'GSPL', 'GSS', 'GTECJAINX', 'GTL', 'GTLINFRA', 'GTPL', 'GUFICBIO',
            'GUJALKALI', 'GUJAPOLLO', 'GUJGASLTD', 'GUJRAFFIA', 'GUJTHEM', 'GULFOILLUB', 'GULFPETRO', 'GULPOLY', 'GVKPIL',
            'GVPIL', 'GVPTECH', 'GVT&D', 'HAL', 'HAPPSTMNDS', 'HAPPYFORGE', 'HARDWYN', 'HARIOMPIPE', 'HARRMALAYA', 'HARSHA',
            'HATHWAY', 'HATSUN', 'HAVELLS', 'HAVISHA', 'HBLENGINE', 'HBSL', 'HCC', 'HCG', 'HCL-INSYS', 'HCLTECH', 'HDBFS',
            'HDFCAMC', 'HDFCBANK', 'HDFCLIFE', 'HDIL', 'HEADSUP', 'HECPROJECT', 'HEG', 'HEIDELBERG', 'HEMIPROP', 'HERANBA',
            'HERCULES', 'HERITGFOOD', 'HEROMOTOCO', 'HESTERBIO', 'HEUBACHIND', 'HEXATRADEX', 'HEXT', 'HFCL', 'HGINFRA', 'HGM',
            'HGS', 'HIKAL', 'HILINFRA', 'HILTON', 'HIMATSEIDE', 'HINDALCO', 'HINDCOMPOS', 'HINDCON', 'HINDCOPPER', 'HINDOILEXP',
            'HINDPETRO', 'HINDUNILVR', 'HINDWAREAP', 'HINDZINC', 'HIRECT', 'HISARMETAL', 'HITECH', 'HITECHCORP', 'HITECHGEAR',
            'HLEGLAS', 'HLVLTD', 'HMAAGRO', 'HMT', 'HMVL', 'HNDFDS', 'HOMEFIRST', 'HONASA', 'HONAUT', 'HONDAPOWER', 'HPAL',
            'HPIL', 'HPL', 'HSCL', 'HTMEDIA', 'HUBTOWN', 'HUDCO', 'HUHTAMAKI', 'HYBRIDFIN', 'HYUNDAI', 'ICDSLTD', 'ICEMAKE',
            'ICICIBANK', 'ICICIGI', 'ICICIPRULI', 'ICIL', 'ICRA', 'IDBI', 'IDEA', 'IDEAFORGE', 'IDFCFIRSTB', 'IEL', 'IEX',
            'IFBAGRO', 'IFBIND', 'IFCI', 'IFGLEXPOR', 'IGARASHI', 'IGCL', 'IGIL', 'IGL', 'IGPL', 'IIFL', 'IIFLCAPS', 'IITL',
            'IKIO', 'IKS', 'IL&FSENGG', 'IL&FSTRANS', 'IMAGICAA', 'IMFA', 'IMPAL', 'IMPEXFERRO', 'INCREDIBLE', 'INDBANK',
            'INDGN', 'INDHOTEL', 'INDIACEM', 'INDIAGLYCO', 'INDIAMART', 'INDIANB', 'INDIANCARD', 'INDIANHUME', 'INDIASHLTR',
            'INDIGO', 'INDIGOPNTS', 'INDIQUBE', 'INDNIPPON', 'INDOAMIN', 'INDOBORAX', 'INDOCO', 'INDOFARM', 'INDORAMA',
            'INDOSTAR', 'INDOTECH', 'INDOTHAI', 'INDOUS', 'INDOWIND', 'INDRAMEDCO', 'INDSWFTLAB', 'INDTERRAIN', 'INDUSINDBK',
            'INDUSTOWER', 'INFIBEAM', 'INFOBEAN', 'INFOMEDIA', 'INFY', 'INGERRAND', 'INNOVACAP', 'INNOVANA', 'INOXGREEN',
            'INOXINDIA', 'INOXWIND', 'INSECTICID', 'INSPIRISYS', 'INTELLECT', 'INTENTECH', 'INTERARCH', 'INTLCONV', 'INVENTURE',
            'IOB', 'IOC', 'IOLCP', 'IONEXCHANG', 'IPCALAB', 'IPL', 'IRB', 'IRCON', 'IRCTC', 'IREDA', 'IRFC', 'IRIS',
            'IRISDOREME', 'IRMENERGY', 'ISFT', 'ISGEC', 'ISHANCH', 'ITC', 'ITCHOTELS', 'ITDC', 'ITI', 'IVALUE', 'IVC',
            'IVP', 'IXIGO', 'IZMO', 'J&KBANK', 'JAGRAN', 'JAGSNPHARM', 'JAIBALAJI', 'JAICORPLTD', 'JAINREC', 'JAIPURKURT',
            'JAMNAAUTO', 'JARO', 'JASH', 'JAYAGROGN', 'JAYBARMARU', 'JAYNECOIND', 'JAYSREETEA', 'JBCHEPHARM', 'JBMA',
            'JCHAC', 'JETFREIGHT', 'JGCHEM', 'JHS', 'JINDALPHOT', 'JINDALPOLY', 'JINDALSAW', 'JINDALSTEL', 'JINDRILL',
            'JINDWORLD', 'JIOFIN', 'JISLDVREQS', 'JISLJALEQS', 'JITFINFRA', 'JKCEMENT', 'JKIL', 'JKIPL', 'JKLAKSHMI',
            'JKPAPER', 'JKTYRE', 'JLHL', 'JMA', 'JMFINANCIL', 'JNKINDIA', 'JOCIL', 'JPASSOCIAT', 'JPOLYINVST', 'JPPOWER',
            'JSFB', 'JSL', 'JSLL', 'JSWCEMENT', 'JSWENERGY', 'JSWHL', 'JSWINFRA', 'JSWSTEEL', 'JTEKTINDIA', 'JTLIND',
            'JUBLCPL', 'JUBLFOOD', 'JUBLINGREA', 'JUBLPHARMA', 'JUNIPER', 'JUSTDIAL', 'JWL', 'JYOTHYLAB', 'JYOTICNC',
            'JYOTISTRUC', 'KABRAEXTRU', 'KAJARIACER', 'KAKATCEM', 'KALAMANDIR', 'KALPATARU', 'KALYANI', 'KALYANIFRG',
            'KALYANKJIL', 'KAMATHOTEL', 'KAMDHENU', 'KAMOPAINTS', 'KANANIIND', 'KANORICHEM', 'KANPRPLA', 'KANSAINER',
            'KAPSTON', 'KARMAENG', 'KARURVYSYA', 'KAUSHALYA', 'KAVDEFENCE', 'KAYA', 'KAYNES', 'KCP', 'KCPSUGIND', 'KDDL',
            'KEC', 'KECL', 'KEEPLEARN', 'KEI', 'KELLTONTEC', 'KERNEX', 'KESORAMIND', 'KEYFINSERV', 'KFINTECH', 'KHADIM',
            'KHAICHEM', 'KHAITANLTD', 'KHANDSE', 'KICL', 'KILITCH', 'KIMS', 'KINGFA', 'KIOCL', 'KIRIINDUS', 'KIRLOSBROS',
            'KIRLOSENG', 'KIRLOSIND', 'KIRLPNU', 'KITEX', 'KKCL', 'KMEW', 'KMSUGAR', 'KNRCON', 'KOHINOOR', 'KOKUYOCMLN',
            'KOLTEPATIL', 'KOPRAN', 'KOTAKBANK', 'KOTARISUG', 'KOTHARIPET', 'KOTHARIPRO', 'KPEL', 'KPIGREEN', 'KPIL',
            'KPITTECH', 'KPRMILL', 'KRBL', 'KREBSBIO', 'KRIDHANINF', 'KRISHANA', 'KRISHIVAL', 'KRITI', 'KRITIKA', 'KRITINUT',
            'KRN', 'KRONOX', 'KROSS', 'KRSNAA', 'KRYSTAL', 'KSB', 'KSCL', 'KSHITIJPOL', 'KSL', 'KSOLVES', 'KTKBANK',
            'KUANTUM', 'LAGNAM', 'LAKPRE', 'LAL', 'LALPATHLAB', 'LAMBODHARA', 'LANCORHOL', 'LANDMARK', 'LAOPALA', 'LASA',
            'LATENTVIEW', 'LATTEYS', 'LAURUSLABS', 'LAXMICOT', 'LAXMIDENTL', 'LAXMIINDIA', 'LCCINFOTEC', 'LEMONTREE',
            'LEXUS', 'LFIC', 'LGBBROSLTD', 'LGHL', 'LIBAS', 'LIBERTSHOE', 'LICHSGFIN', 'LICI', 'LIKHITHA', 'LINC',
            'LINCOLN', 'LINDEINDIA', 'LLOYDSENGG', 'LLOYDSENT', 'LLOYDSME', 'LMW', 'LODHA', 'LOKESHMACH', 'LORDSCHLO',
            'LOTUSDEV', 'LOTUSEYE', 'LOVABLE', 'LOYALTEX', 'LPDC', 'LT', 'LTF', 'LTFOODS', 'LTIM', 'LTTS', 'LUMAXIND',
            'LUMAXTECH', 'LUPIN', 'LUXIND', 'LXCHEM', 'LYKALABS', 'LYPSAGEMS', 'M&M', 'M&MFIN', 'MAANALU', 'MACPOWER',
            'MADHAV', 'MADHUCON', 'MADRASFERT', 'MAGADSUGAR', 'MAGNUM', 'MAHABANK', 'MAHAPEXLTD', 'MAHASTEEL', 'MAHEPC',
            'MAHESHWARI', 'MAHLIFE', 'MAHLOG', 'MAHSCOOTER', 'MAHSEAMLES', 'MAITHANALL', 'MALLCOM', 'MALUPAPER', 'MAMATA',
            'MANAKALUCO', 'MANAKCOAT', 'MANAKSIA', 'MANAKSTEEL', 'MANALIPETC', 'MANAPPURAM', 'MANBA', 'MANCREDIT', 'MANGALAM',
            'MANGCHEFER', 'MANGLMCEM', 'MANINDS', 'MANINFRA', 'MANKIND', 'MANOMAY', 'MANORAMA', 'MANORG', 'MANUGRAPH',
            'MANYAVAR', 'MAPMYINDIA', 'MARALOVER', 'MARATHON', 'MARICO', 'MARINE', 'MARKOLINES', 'MARKSANS', 'MARSHALL',
            'MARUTI', 'MASFIN', 'MASKINVEST', 'MASTEK', 'MASTERTR', 'MATRIMONY', 'MAWANASUG', 'MAXESTATES', 'MAXHEALTH',
            'MAXIND', 'MAYURUNIQ', 'MAZDA', 'MAZDOCK', 'MBAPL', 'MBEL', 'MBLINFRA', 'MCL', 'MCLEODRUSS', 'MCLOUD', 'MCX',
            'MEDANTA', 'MEDIASSIST', 'MEDICAMEQ', 'MEDICO', 'MEDPLUS', 'MEGASOFT', 'MEGASTAR', 'MEIL', 'MENONBE', 'MEP',
            'METROBRAND', 'METROPOLIS', 'MFML', 'MFSL', 'MGEL', 'MGL', 'MHRXMIRU', 'MHRIL', 'MICEL', 'MIDHANI', 'MINDACORP',
            'MINDTECK', 'MIRCELECTR', 'MIRZAINT', 'MITCON', 'MITTAL', 'MKPL', 'MMFL', 'MMP', 'MMTC', 'MOBIKWIK', 'MODIRUBBER',
            'MODISONLTD', 'MODTHREAD', 'MOHITIND', 'MOIL', 'MOKSH', 'MOL', 'MOLDTECH', 'MOLDTKPAC', 'MONARCH', 'MONTECARLO',
            'MORARJEE', 'MOREPENLAB', 'MOSCHIP', 'MOTHERSON', 'MOTILALOFS', 'MOTISONS', 'MOTOGENFIN', 'MPHASIS', 'MPSLTD',
            'MRF', 'MRPL', 'MSPL', 'MSTCLTD', 'MSUMI', 'MTARTECH', 'MTEDUCARE', 'MTNL', 'MUFIN', 'MUFTI', 'MUKANDLTD',
            'MUKKA', 'MUKTAARTS', 'MUNJALAU', 'MUNJALSHOW', 'MURUDCERA', 'MUTHOOTCAP', 'MUTHOOTFIN', 'MUTHOOTMF', 'MVGJL',
            'MWL', 'NACLIND', 'NAGAFERT', 'NAGREEKCAP', 'NAGREEKEXP', 'NAHARCAP', 'NAHARINDUS', 'NAHARPOLY', 'NAHARPING',
            'NAM-INDIA', 'NARMADA', 'NATCAPSUQ', 'NATCOPHARM', 'NATHBIOGEN', 'NATIONALUM', 'NAUKRI', 'NAVA', 'NAVINFLUOR',
            'NAVKARCORP', 'NAVKARURB', 'NAVNETEDUL', 'NAZARA', 'NBCC', 'NBIFIN', 'NCC', 'NCLIND', 'NDGL', 'NDL', 'NDLVENTURE',
            'NDRAUTO', 'NDTV', 'NECCLTD', 'NECLIFE', 'NELCAST', 'NELCO', 'NEOGEN', 'NESCO', 'NESTLEIND', 'NETWEB',
            'NETWORK18', 'NEULANDLAB', 'NEWGEN', 'NEXTMEDIA', 'NFL', 'NGIL', 'NGLFINE', 'NH', 'NHPC', 'NIACL', 'NIBE',
            'NIBL', 'NIITLTD', 'NIITMTS', 'NILAINFRA', 'NILASPACES', 'NILKAMAL', 'NINSYS', 'NIPPOBATRY', 'NIRAJ', 'NIRAJISPAT',
            'NITCO', 'NITINSPIN', 'NITIRAJ', 'NIVABUPA', 'NKIND', 'NLCINDIA', 'NMDC', 'NOCIL', 'NOIDATOLL', 'NORBTEAEXP',
            'NORTHARC', 'NOVAAGRI', 'NPST', 'NRAIL', 'NRBBEARING', 'NRL', 'NSIL', 'NSLNISP', 'NTPC', 'NTPCGREEN', 'NUCLEUS',
            'NURECA', 'NUVAMA', 'NUVOCO', 'NYKAA', 'OAL', 'OBCL', 'OBEROIRLTY', 'OCCLLTD', 'ODIGMA', 'OFSS', 'OIL',
            'OILCOUNTUB', 'OLAELEC', 'OLECTRA', 'OMAXAUTO', 'OMAXE', 'OMFREIGHT', 'OMINFRAL', 'OMKARCHEM', 'ONELIFECAP',
            'ONEPOINT', 'ONESOURCE', 'ONGC', 'ONMOBILE', 'ONWARDTEC', 'OPTIEMUS', 'ORBTEXP', 'ORCHASP', 'ORCHPHARMA',
            'ORICONENT', 'ORIENTALTL', 'ORIENTBELL', 'ORIENTCEM', 'ORIENTCER', 'ORIENTELEC', 'ORIENTHOT', 'ORIENTLTD',
            'ORIENTPPR', 'ORIENTTECH', 'ORISSAMINE', 'ORTEL', 'ORTINGLOBE', 'OSIAHYPER', 'OSWALAGRO', 'OSWALGREEN',
            'OSWALPUMPS', 'OSWALSEEDS', 'PACEDIGITK', 'PAGEIND', 'PAISALO', 'PAKKA', 'PALASHSECU', 'PALREDTEC', 'PANACEABIO',
            'PANACHE', 'PANAMAPET', 'PANSARI', 'PAR', 'PARACABLES', 'PARADEEP', 'PARAGMILK', 'PARAS', 'PARASPETRO',
            'PARKHOTELS', 'PARSVNATH', 'PASHUPATI', 'PASUPTAC', 'PATANJALI', 'PATELENG', 'PATELRMART', 'PATINTLOG', 'PAVNAIND',
            'PAYTM', 'PCBL', 'PCJEWELLER', 'PDMJEPAPER', 'PDSL', 'PEARLPOLY', 'PENIND', 'PENINLAND', 'PERSISTENT', 'PETRONET',
            'PFC', 'PFIZER', 'PFOCUS', 'PFS', 'PGEL', 'PGHH', 'PGHL', 'PGIL', 'PHOENIXLTD', 'PICCADIL', 'PIDILITIND', 'PIGL',
            'PIIND', 'PILANIINVS', 'PILITA', 'PIONEEREMB', 'PITTIENG', 'PIXTRANS', 'PKTEA', 'PLASTIBLEN', 'PLATIND',
            'PLAZACABLE', 'PNB', 'PNBGILTS', 'PNBHOUSING', 'PNC', 'PNCINFRA', 'PNGJL', 'POCL', 'PODDARMENT', 'POKARNA',
            'POLICYBZR', 'POLYCAB', 'POLYMED', 'POLYPLEX', 'PONNIERODE', 'POONAWALLA', 'POWERGRID', 'POWERINDIA', 'POWERMECH',
            'PPAP', 'PPL', 'PPLPHARMA', 'PRABHA', 'PRAENG', 'PRAJIND', 'PRAKASH', 'PRAKASHSTL', 'PRAXIS', 'PRECAM', 'PRECOT',
            'PRECWIRE', 'PREMEXPLN', 'PREMIER', 'PREMIERENE', 'PREMIERPOL', 'PRESTIGE', 'PRICOLLTD', 'PRIMESECU', 'PRIMO',
            'PRINCEPIPE', 'PRITI', 'PRITIKAUTO', 'PRIVISCL', 'PROSTARM', 'PROTEAN', 'PROZONER', 'PRSMJOHNSN', 'PRUDENT',
            'PRUDMOULI', 'PSB', 'PSPPROJECT', 'PTC', 'PTCIL', 'PTL', 'PUNJABCHEM', 'PURVA', 'PVP', 'PVRINOX', 'PVSL',
            'PYRAMID', 'QPOWER', 'QUADFUTURE', 'QUESS', 'QUICKHEAL', 'QUINTEGRA', 'RACE', 'RACLGEAR', 'RADAAN', 'RADHIKAJWE',
            'RADIANTCMS', 'RADICO', 'RADIOCITY', 'RAILTEL', 'RAIN', 'RAINBOW', 'RAJESHEXPO', 'RAJMET', 'RAJOOENG', 'RAJRATAN',
            'RAJRILTD', 'RAJSREESUG', 'RAJTV', 'RAJVIR', 'RALLIS', 'RAMANEWS', 'RAMAPHO', 'RAMASTEEL', 'RAMCOCEM', 'RAMCOIND',
            'RAMCOSYS', 'RAMKY', 'RAMRAT', 'RANASUG', 'RANEHOLDIN', 'RATEGAIN', 'RATNAMANI', 'RATNAVEER', 'RAYMOND',
            'RAYMONDLSL', 'RAYMONDREL', 'RBA', 'RBLBANK', 'RBZJEWEL', 'RCF', 'RCOM', 'RECLTD', 'REDINGTON', 'REDTAPE',
            'REFEX', 'REGAAL', 'REGENCERAM', 'RELAXO', 'RELCHEMQ', 'RELIABLE', 'RELIANCE', 'RELIGARE', 'RELINFRA', 'RELTD',
            'REMSONSIND', 'RENUKA', 'REPCOHOME', 'REPL', 'REPRO', 'RESPONIND', 'RETAIL', 'RGL', 'RHETAN', 'RHFL', 'RHIM',
            'RHL', 'RICOAUTO', 'RIIL', 'RISHABH', 'RITCO', 'RITES', 'RKDL', 'RKEC', 'RKFORGE', 'RKSWAMY', 'RMDRIP', 'RML',
            'RNBDENIMS', 'ROHLTD', 'ROLEXRINGS', 'ROLLT', 'ROLTA', 'ROML', 'ROSSARI', 'ROSSELLIND', 'ROSSTECH', 'ROTO',
            'ROUTE', 'RPEL', 'RPGLIFE', 'RPOWER', 'RPPINFRA', 'RPPL', 'RPSGVENT', 'RPTECH', 'RRKABEL', 'RSSOFTWARE', 'RSWM',
            'RSYSTEMS', 'RTNINDIA', 'RTNPOWER', 'RUBFILA', 'RUBYMILLS', 'RUCHINFRA', 'RUCHIRA', 'RUPA', 'RUSHIL', 'RUSTOMJEE',
            'RVHL', 'RVNL', 'RVTH', 'S&SPOWER', 'SAATVIKGL', 'SABEVENTS', 'SABTNL', 'SADBHAV', 'SADBHIN', 'SADHNANIQ',
            'SAFARI', 'SAGARDEEP', 'SAGCEM', 'SAGILITY', 'SAHYADRI', 'SAIL', 'SAILIFE', 'SAKAR', 'SAKHTISUG', 'SAKSOFT',
            'SAKUMA', 'SALASAR', 'SALONA', 'SALSTEEL', 'SALZERELEC', 'SAMBHAAV', 'SAMBHV', 'SAMHI', 'SAMMAANCAP', 'SAMPANN',
            'SANATHAN', 'SANCO', 'SANDESH', 'SANDHAR', 'SANDUMA', 'SANGAMIND', 'SANGHIIND', 'SANGHVIMOV', 'SANGINITA',
            'SANOFI', 'SANOFICONR', 'SANSERA', 'SANSTAR', 'SANWARIA', 'SAPPHIRE', 'SARDAEN', 'SAREGAMA', 'SARLAPOLY',
            'SARVESHWAR', 'SASKEN', 'SASTASUNDR', 'SATIA', 'SATIN', 'SAURASHCEM', 'SBC', 'SBCL', 'SBFC', 'SBGLP', 'SBICARD',
            'SBILIFE', 'SBIN', 'SCHAEFFLER', 'SCHAND', 'SCHNEIDER', 'SCI', 'SCILAL', 'SCODATUBES', 'SCPL', 'SDBL', 'SEAMECLTD',
            'SECMARK', 'SECURKLOUD', 'SEJALLTD', 'SELMC', 'SEMAC', 'SENCO', 'SENORES', 'SEPC', 'SEQUENT', 'SERVOTECH',
            'SESHAPAPER', 'SETCO', 'SETUINFRA', 'SEYAIND', 'SFL', 'SGFIN', 'SGIL', 'SGL', 'SGLTL', 'SGMART', 'SHAH',
            'SHAHALLOYS', 'SHAILY', 'SHAKTIPUMP', 'SHALBY', 'SHALPAINTS', 'SHANKARA', 'SHANTI', 'SHANTIGEAR', 'SHANTIGOLD',
            'SHARDACROP', 'SHARDAMOTR', 'SHAREINDIA', 'SHEKHAWATI', 'SHEMAROO', 'SHILPAMED', 'SHIVALIK', 'SHIVAMAUTO',
            'SHIVAMILLS', 'SHIVATEX', 'SHK', 'SHOPERSTOP', 'SHRADHA', 'SHREDIGCEM', 'SHREECEM', 'SHREEJISPG', 'SHREEPUSHK',
            'SHREERAMA', 'SHRENIK', 'SHREYANIND', 'SHRINGARMS', 'SHRIPISTON', 'SHRIRAMFIN', 'SHRIRAMPPS', 'SHYAMCENT',
            'SHYAMMETL', 'SHYAMTEL', 'SICALLOG', 'SIEMENS', 'SIGACHI', 'SIGIND', 'SIGMA', 'SIGNATURE', 'SIGNPOST', 'SIKKO',
            'SIL', 'SILGO', 'SILINV', 'SILLYMONKS', 'SILVERTUC', 'SIMBHALS', 'SIMPLEXINF', 'SINCLAIR', 'SINDHUTRAD',
            'SINTERCOM', 'SIRCA', 'SIS', 'SITINET', 'SIYSIL', 'SJS', 'SJVN', 'SKFINDIA', 'SKIL', 'SKIPPER', 'SKMEGGPROD',
            'SKYGOLD', 'SMARTLINK', 'SMARTWORKS', 'SMCGLOBAL', 'SMLISUZU', 'SMLT', 'SMSLIFE', 'SMSPHARMA', 'SNOWMAN', 'SOBHA',
            'SOFTTECH', 'SOLARA', 'SOLARINDS', 'SOLARWORLD', 'SOLEX', 'SOMANYCERA', 'SOMATEX', 'SOMICONVEY', 'SONACOMS',
            'SONAMLTD', 'SONATSOFTW', 'SOTL', 'SOUTHBANK', 'SOUTHWEST', 'SPAL', 'SPANDANA', 'SPARC', 'SPCENET', 'SPECIALITY',
            'SPECTRUM', 'SPENCERS', 'SPIC', 'SPLIL', 'SPLPETRO', 'SPMLINFRA', 'SPORTKING', 'SRD', 'SREEL', 'SRF', 'SRGHFL',
            'SRHHYPOLTD', 'SRM', 'SRPL', 'SSDL', 'SSWL', 'STALLION', 'STANLEY', 'STAR', 'STARCEMENT', 'STARHEALTH',
            'STARPAPER', 'STARTECK', 'STCINDIA', 'STEELCAS', 'STEELCITY', 'STEELXIND', 'STEL', 'STERTOOLS', 'STLNETWORK',
            'STLTECH', 'STOVEKRAFT', 'STYL', 'STYLAMIND', 'STYLEBAAZA', 'STYRENIX', 'SUBEXLTD', 'SUBROS', 'SUDARSCHEM',
            'SUKHJITS', 'SULA', 'SUMEETINDS', 'SUMICHEM', 'SUMIT', 'SUMMITSEC', 'SUNCLAY', 'SUNDARAM', 'SUNDARMFIN',
            'SUNDARMHLD', 'SUNDRMBRAK', 'SUNDRMFAST', 'SUNDROP', 'SUNFLAG', 'SUNPHARMA', 'SUNTECK', 'SUNTV', 'SUPERHOUSE',
            'SUPERSPIN', 'SUPRAJIT', 'SUPREME', 'SUPREMEENG', 'SUPREMEIND', 'SUPREMEINF', 'SUPRIYA', 'SURAJEST', 'SURAJLTD',
            'SURAKSHA', 'SURANASOL', 'SURANAT&P', 'SURYALAXMI', 'SURYAROSNI', 'SURYODAY', 'SUTLEJTEX', 'SUULD', 'SUVEN',
            'SUVIDHAA', 'SUYOG', 'SUZLON', 'SVLL', 'SVPGLOB', 'SWANCORP', 'SWANDEF', 'SWARAJENG', 'SWELECTES', 'SWIGGY',
            'SWSOLAR', 'SYMPHONY', 'SYNCOMF', 'SYNGENE', 'SYRMA', 'SYSTMTXC', 'TAINWALCHM', 'TAJGVK', 'TAKE', 'TALBROAUTO',
            'TANLA', 'TARACHAND', 'TARAPUR', 'TARC', 'TARIL', 'TARMAT', 'TARSONS', 'TASTYBITE', 'TATACAP', 'TATACHEM',
            'TATACOMM', 'TATACONSUM', 'TATAELXSI', 'TATAINVEST', 'TATAMOTORS', 'TATAPOWER', 'TATASTEEL', 'TATATECH', 'TATVA',
            'TBOTEK', 'TBZ', 'TCI', 'TCIEXP', 'TCIFINANCE', 'TCPLPACK', 'TCS', 'TDPOWERSYS', 'TEAMGTY', 'TEAMLEASE',
            'TECHM', 'TECHNOE', 'TECILCHEM', 'TEGA', 'TEJASNET', 'TEMBO', 'TERASOFT', 'TEXINFRA', 'TEXMOPIPES', 'TEXRAIL',
            'TFCILTD', 'TFL', 'TGBHOTELS', 'THANGAMAYL', 'THEINVEST', 'THEJO', 'THELEELA', 'THEMISMED', 'THERMAX',
            'THOMASCOOK', 'THOMASCOTT', 'THYROCARE', 'TI', 'TICL', 'TIGERLOGS', 'TIIL', 'TIINDIA', 'TIJARIA', 'TIL',
            'TIMETECHNO', 'TIMKEN', 'TINNARUBR', 'TIPSFILMS', 'TIPSMUSIC', 'TIRUMALCHM', 'TIRUPATIFL', 'TITAGARH', 'TITAN',
            'TMB', 'TNPETRO', 'TNPL', 'TNTELE', 'TOKYOPLAST', 'TOLINS', 'TORNTPHARM', 'TORNTPOWER', 'TOTAL', 'TOUCHWOOD',
            'TPHQ', 'TPLPLASTEH', 'TRACXN', 'TRANSRAILL', 'TRANSWORLD', 'TRAVELFOOD', 'TREEHOUSE', 'TREJHARA', 'TREL',
            'TRENT', 'TRF', 'TRIDENT', 'TRIGYN', 'TRITURBINE', 'TRIVENI', 'TRU', 'TRUALT', 'TTKHLTCARE', 'TTKPRESTIG', 'TTL',
            'TTML', 'TVSELECT', 'TVSHLTD', 'TVSMOTOR', 'TVSSCS', 'TVSSRICHAK', 'TVTODAY', 'TVVISION', 'UBL', 'UCAL',
            'UCOBANK', 'UDS', 'UEL', 'UFBL', 'UFLEX', 'UFO', 'UGARSUGAR', 'UGROCAP', 'UJJIVANSFB', 'ULTRACEMCO', 'UMAEXPORTS',
            'UMESLTD', 'UMIYA-MRO', 'UNICHEMLAB', 'UNIDT', 'UNIECOM', 'UNIENTER', 'UNIINFO', 'UNIMECH', 'UNIONBANK',
            'UNIPARTS', 'UNITDSPR', 'UNITECH', 'UNITEDPOLY', 'UNITEDTEA', 'UNIVAFOODS', 'UNIVASTU', 'UNIVCABLES', 'UNIVPHOTO',
            'UNOMINDA', 'UPL', 'URAVIDEF', 'URBANCO', 'URJA', 'USHAMART', 'USK', 'UTIAMC', 'UTKARSHBNK', 'UTTAMSUGAR',
            'UYFINCORP', 'V2RETAIL', 'VADILALIND', 'VAIBHAVGBL', 'VAISHALI', 'VAKRANGEE', 'VALIANTLAB', 'VALIANTORG',
            'VARDHACRLC', 'VARDMNPOLY', 'VARROC', 'VASCONEQ', 'VASWANI', 'VBL', 'VCL', 'VEDL', 'VEEDOL', 'VENKEYS',
            'VENTIVE', 'VENUSPIPES', 'VENUSREM', 'VERANDA', 'VERTOZ', 'VESUVIUS', 'VETO', 'VGL', 'VGUARD', 'VHL', 'VHLTD',
            'VIDHIING', 'VIDAYA', 'VIJIFIN', 'VIKASECO', 'VIKASLIFE', 'VIKRAMSOLR', 'VIKRAN', 'VIMTALABS', 'VINATIORGA',
            'VINCOFE', 'VINDHYATEL', 'VINEETLAB', 'VINNY', 'VINYLINDIA', 'VIPCLOTHNG', 'VIPIND', 'VIPULLTD', 'VIRINCHI',
            'VISAKAIND', 'VISASTEEL', 'VISHNU', 'VISHWARAJ', 'VIVIDHA', 'VLEGOV', 'VLSFINANCE', 'VMART', 'VMM', 'VMSTMT',
            'VOLTAMP', 'VOLTAS', 'VPRPL', 'VRAJ', 'VRLLOG', 'VSSL', 'VSTIND', 'VSTL', 'VSTTILLERS', 'VTL', 'WAAREEENER',
            'WAAREEINDO', 'WAAREERTL', 'WABAG', 'WALCHANNAG', 'WANBURY', 'WCIL', 'WEALTH', 'WEBELSOLAR', 'WEIZMANIND',
            'WEL', 'WELCORP', 'WELENT', 'WELINV', 'WELSPUNLIV', 'WENDT', 'WESTLIFE', 'WEWIN', 'WEWORK', 'WHEELS',
            'WHIRLPOOL', 'WILLAMAGOR', 'WINDLAS', 'WINDMACHIN', 'WINSOME', 'WIPL', 'WIPRO', 'WOCKPHARMA', 'WONDERLA',
            'WORTHPERI', 'WSI', 'WSTCSTPAPR', 'XCHANGING', 'XELPMOC', 'XPROINDIA', 'XTGLOBAL', 'YAARI', 'YASHO', 'YATHARTH',
            'YATRA', 'YESBANK', 'YUKEN', 'ZAGGLE', 'ZEEL', 'ZEELEARN', 'ZEEMEDIA', 'ZENITHEXPO', 'ZENITHSTL', 'ZENSARTECH',
            'ZENTEC', 'ZFCVINDIA', 'ZIMLAB', 'ZODIAC', 'ZODIACLOTH', 'ZOTA', 'ZUARI', 'ZUARIIND', 'ZYDUSLIFE', 'ZYDUSWELL'
        ]
    
    def extract_stocks_from_news(self, articles: List[Dict]) -> List[str]:
        """Extract stock symbols from news articles."""
        try:
            # Get comprehensive NSE stocks list
            nse_stocks = self.get_comprehensive_nse_stocks_list()
            
            found_stocks = set()
            for article in articles:
                text = f"{article.get('title', '')} {article.get('description', '')}".upper()
                for stock in nse_stocks:
                    if stock in text:
                        found_stocks.add(stock)
            
            return list(found_stocks)
            
        except Exception as e:
            logger.error(f"Error extracting stocks: {str(e)}")
            return []
    
    def _aggressive_indian_filtering(self, articles: List[Dict]) -> List[Dict]:
        """More aggressive filtering to find Indian stock-related articles."""
        try:
            # Get comprehensive NSE stock list
            nse_stocks = self.get_comprehensive_nse_stocks_list()
            nse_stocks_set = set(nse_stocks)
            
            # Expanded Indian keywords including more general terms
            expanded_indian_keywords = [
                'INDIA', 'INDIAN', 'NSE', 'BSE', 'BOMBAY STOCK EXCHANGE', 'NATIONAL STOCK EXCHANGE',
                'SENSEX', 'NIFTY', 'MUMBAI', 'DELHI', 'BENGALURU', 'CHENNAI', 'KOLKATA', 'HYDERABAD',
                'RUPEES', 'INR', '₹', 'CRORES', 'LAKHS', 'CRORE', 'LAKH',
                'SEBI', 'RBI', 'RESERVE BANK', 'SECURITIES AND EXCHANGE BOARD',
                'GST', 'GOODS AND SERVICES TAX', 'DIRECT TAX', 'INDIRECT TAX',
                'UNION BUDGET', 'FISCAL DEFICIT', 'CURRENT ACCOUNT DEFICIT',
                'FDI', 'FOREIGN DIRECT INVESTMENT', 'FII', 'FOREIGN INSTITUTIONAL INVESTMENT',
                'IPO', 'INITIAL PUBLIC OFFERING', 'QIP', 'QUALIFIED INSTITUTIONAL PLACEMENT',
                'MERGER', 'ACQUISITION', 'TAKEOVER', 'JOINT VENTURE',
                'QUARTERLY RESULTS', 'ANNUAL RESULTS', 'EARNINGS', 'PROFIT', 'LOSS',
                'DIVIDEND', 'BONUS', 'STOCK SPLIT', 'RIGHTS ISSUE',
                # Add more general business terms
                'COMPANY', 'CORPORATION', 'LIMITED', 'LTD', 'PRIVATE', 'PUBLIC',
                'BUSINESS', 'INDUSTRY', 'SECTOR', 'MARKET', 'TRADING', 'INVESTMENT',
                'SHARE', 'SHARES', 'STOCK', 'STOCKS', 'EQUITY', 'EQUITIES',
                'REVENUE', 'SALES', 'GROWTH', 'EXPANSION', 'DEVELOPMENT',
                'PROJECT', 'CONTRACT', 'AGREEMENT', 'PARTNERSHIP', 'COLLABORATION'
            ]
            
            # Major Indian company names (expanded list)
            expanded_indian_companies = [
                'RELIANCE', 'TATA', 'ADANI', 'HDFC', 'ICICI', 'SBI', 'INFOSYS', 'TCS', 'WIPRO', 'HCL',
                'BHARTI', 'MARUTI', 'BAJAJ', 'MAHINDRA', 'HERO', 'EICHER', 'ASHOK LEYLAND', 'TVS',
                'SUN PHARMA', 'DR REDDY', 'CIPLA', 'LUPIN', 'BIOCON', 'DIVIS LAB', 'AUROBINDO',
                'ITC', 'HUL', 'NESTLE', 'BRITANNIA', 'DABUR', 'GODREJ', 'MARICO', 'COLPAL',
                'ONGC', 'IOC', 'BPCL', 'HPCL', 'GAIL', 'COAL INDIA', 'NTPC', 'POWERGRID',
                'TATA STEEL', 'JSW STEEL', 'HINDALCO', 'VEDANTA', 'SAIL', 'NMDC',
                'LT', 'NCC', 'KEC', 'IRCON', 'RVNL', 'BEML', 'TITAGARH',
                'BEL', 'HAL', 'BDL', 'MIDHANI', 'BHARAT FORGE',
                'APOLLO HOSPITALS', 'FORTIS', 'MAX HEALTH', 'NARAYANA HRUDAYALAYA',
                'DLF', 'GODREJ PROPERTIES', 'BRIGADE', 'SOBHA', 'PRESTIGE',
                'ZEEL', 'SUN TV', 'NETWORK18', 'TV TODAY', 'JAGRAN',
                'INDIGO', 'SPICEJET', 'JET AIRWAYS',
                'BATA', 'TITAN', 'PC JEWELLER', 'KALYAN JEWELLERS',
                'VOLTAS', 'BLUE STAR', 'WHIRLPOOL', 'CROMPTON', 'HAVELLS',
                'ASIAN PAINTS', 'BERGER PAINTS', 'KANSAI NEROLAC', 'AKZO NOBEL',
                'ULTRATECH', 'SHREE CEMENT', 'RAMCO CEMENT', 'HEIDELBERG',
                'BAJAJ FINANCE', 'BAJAJ FINSERV', 'CHOLAMANDALAM', 'LIC HOUSING',
                'MOTILAL OSWAL', 'ANGEL BROKING', 'ZERODHA', 'UPSTOX',
                # Add more companies
                'AXIS BANK', 'KOTAK BANK', 'BANDHAN BANK', 'FEDERAL BANK',
                'TECH MAHINDRA', 'MINDTREE', 'L&T INFOTECH', 'MPHASIS',
                'CADILA', 'GLENMARK', 'TORRENT PHARMA', 'ALKEM LABS',
                'M&M', 'BAJAJ AUTO', 'HERO MOTOCORP', 'EICHER MOTORS',
                'JINDAL STEEL', 'JSPL', 'COAL INDIA', 'NMDC', 'SAIL',
                'ADANI PORTS', 'CONCOR', 'CONTAINER CORP', 'GATEWAY DISTRIPARKS'
            ]
            
            filtered_articles = []
            
            for article in articles:
                title = article.get('title', '').upper()
                description = article.get('description', '').upper()
                content = f"{title} {description}"
                
                # Check for NSE stock symbols in title/description
                has_nse_stock = any(stock in content for stock in nse_stocks_set)
                
                # Check for expanded Indian keywords
                has_indian_keywords = any(keyword in content for keyword in expanded_indian_keywords)
                
                # Check for expanded Indian companies
                has_indian_company = any(company in content for company in expanded_indian_companies)
                
                # More lenient criteria - any one of these is enough
                if has_nse_stock or has_indian_keywords or has_indian_company:
                    article['is_india_related'] = True
                    article['filter_reason'] = []
                    if has_nse_stock:
                        article['filter_reason'].append('NSE Stock')
                    if has_indian_keywords:
                        article['filter_reason'].append('Indian Keywords')
                    if has_indian_company:
                        article['filter_reason'].append('Indian Company')
                    
                    filtered_articles.append(article)
                    logger.debug(f"Aggressive filter - Indian article: {article.get('title', '')[:50]}... - {article['filter_reason']}")
            
            logger.info(f"Aggressive filtering found {len(filtered_articles)} Indian articles from {len(articles)} total articles")
            return filtered_articles
            
        except Exception as e:
            logger.error(f"Error in aggressive Indian filtering: {str(e)}")
            return articles
    
    def _alternative_indian_filtering(self, articles: List[Dict]) -> List[Dict]:
        """Alternative filtering methods to find more Indian articles."""
        try:
            # Even more lenient filtering - look for any business/financial terms
            business_keywords = [
                'STOCK', 'SHARE', 'EQUITY', 'MARKET', 'TRADING', 'INVESTMENT',
                'COMPANY', 'CORPORATION', 'BUSINESS', 'INDUSTRY', 'SECTOR',
                'REVENUE', 'SALES', 'PROFIT', 'LOSS', 'GROWTH', 'EXPANSION',
                'DEAL', 'AGREEMENT', 'CONTRACT', 'PARTNERSHIP', 'MERGER',
                'ACQUISITION', 'IPO', 'LISTING', 'DIVIDEND', 'BONUS',
                'QUARTERLY', 'ANNUAL', 'RESULTS', 'EARNINGS', 'PERFORMANCE',
                'FINANCIAL', 'ECONOMIC', 'BANKING', 'INSURANCE', 'REAL ESTATE',
                'INFRASTRUCTURE', 'POWER', 'TELECOM', 'AUTOMOBILE', 'PHARMA',
                'TECHNOLOGY', 'IT', 'SOFTWARE', 'HARDWARE', 'DIGITAL',
                'RETAIL', 'FMCG', 'CONSUMER', 'MANUFACTURING', 'PRODUCTION'
            ]
            
            # Indian cities and states
            indian_locations = [
                'MUMBAI', 'DELHI', 'BENGALURU', 'CHENNAI', 'KOLKATA', 'HYDERABAD',
                'PUNE', 'AHMEDABAD', 'JAIPUR', 'LUCKNOW', 'KANPUR', 'NAGPUR',
                'INDORE', 'THIRUVANANTHAPURAM', 'BHOPAL', 'VISAKHAPATNAM',
                'PIMPRI', 'PATNA', 'VADODARA', 'GHAZIABAD', 'LUDHIANA',
                'AGRA', 'NASHIK', 'FARIDABAD', 'MEERUT', 'RAJKOT',
                'KALYAN', 'VASANT', 'VARANASI', 'SRINAGAR', 'AURANGABAD',
                'NOIDA', 'SOLAPUR', 'RANCHI', 'MYSORE', 'BHUBANESWAR',
                'COIMBATORE', 'KOCHI', 'RAIPUR', 'JABALPUR', 'GUNTUR',
                'CHANDIGARH', 'TIRUCHIRAPPALLI', 'MADURAI', 'GUWAHATI',
                'GURGAON', 'ALIGARH', 'JODHPUR', 'BAREILLY', 'MORADABAD',
                'MYSURU', 'KARNATAKA', 'TAMIL NADU', 'MAHARASHTRA', 'GUJARAT',
                'WEST BENGAL', 'UTTAR PRADESH', 'BIHAR', 'RAJASTHAN', 'ANDHRA PRADESH'
            ]
            
            filtered_articles = []
            
            for article in articles:
                title = article.get('title', '').upper()
                description = article.get('description', '').upper()
                content = f"{title} {description}"
                
                # Check for business keywords
                has_business_keywords = any(keyword in content for keyword in business_keywords)
                
                # Check for Indian locations
                has_indian_location = any(location in content for location in indian_locations)
                
                # Check for currency symbols or Indian terms
                has_indian_terms = any(term in content for term in ['₹', 'RUPEES', 'INR', 'CRORE', 'LAKH', 'CRORES', 'LAKHS'])
                
                # Very lenient criteria - any business term + any Indian indicator
                if has_business_keywords and (has_indian_location or has_indian_terms):
                    article['is_india_related'] = True
                    article['filter_reason'] = ['Business + Indian Location/Terms']
                    filtered_articles.append(article)
                    logger.debug(f"Alternative filter - Indian article: {article.get('title', '')[:50]}...")
            
            logger.info(f"Alternative filtering found {len(filtered_articles)} Indian articles from {len(articles)} total articles")
            return filtered_articles
            
        except Exception as e:
            logger.error(f"Error in alternative Indian filtering: {str(e)}")
            return articles
