#!/usr/bin/env python3
"""
Fundamental Analyzer Component
Fundamental analysis for stocks using financial data.
"""

import yfinance as yf
import pandas as pd
import numpy as np
import logging
import time
import random
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class FundamentalAnalyzer:
    """Fundamental analysis for stocks."""
    
    def __init__(self):
        self.request_delay = 1.5  # Base delay between requests (longer than technical)
        self.max_retries = 3
        self.last_request_time = 0
        logger.info("Fundamental Analyzer initialized")
    
    def _fetch_financial_data_with_retry(self, symbol: str, max_retries: int = 3) -> Optional[Dict]:
        """Fetch financial data with retry logic for rate limiting."""
        for attempt in range(max_retries):
            try:
                # Add delay to prevent rate limiting
                current_time = time.time()
                time_since_last_request = current_time - self.last_request_time
                if time_since_last_request < self.request_delay:
                    sleep_time = self.request_delay - time_since_last_request + random.uniform(0, 0.5)
                    logger.debug(f"Rate limiting delay: {sleep_time:.2f}s")
                    time.sleep(sleep_time)
                
                self.last_request_time = time.time()
                
                # Fetch financial data
                ticker = yf.Ticker(symbol)
                info = ticker.info
                
                if not info or len(info) < 5:  # Basic check for valid data
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) + random.uniform(0, 1)
                        logger.warning(f"No financial data for {symbol}, waiting {wait_time:.1f}s before retry {attempt + 1}/{max_retries}")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"No financial data available for {symbol} after {max_retries} attempts")
                        return None
                
                return info
                
            except Exception as e:
                error_msg = str(e).lower()
                if 'rate limited' in error_msg or 'too many requests' in error_msg:
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) + random.uniform(1, 3)
                        logger.warning(f"Rate limited for {symbol}, waiting {wait_time:.1f}s before retry {attempt + 1}/{max_retries}")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"Rate limited for {symbol} after {max_retries} attempts")
                        return None
                elif 'delisted' in error_msg or 'no price data' in error_msg:
                    logger.warning(f"Stock {symbol} appears to be delisted or has no financial data")
                    return None
                else:
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) + random.uniform(0, 1)
                        logger.warning(f"Error fetching financial data for {symbol}: {str(e)}, waiting {wait_time:.1f}s before retry {attempt + 1}/{max_retries}")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"Error fetching financial data for {symbol} after {max_retries} attempts: {str(e)}")
                        return None
        
        return None
    
    def is_stock_valid(self, symbol: str) -> bool:
        """Check if a stock is valid and has data available with multiple validation checks."""
        try:
            # Multiple validation checks to prevent false positives
            ticker = yf.Ticker(symbol)
            
            # Check 1: Try to get basic info first
            try:
                info = ticker.info
                if info and len(info) > 5:
                    # If we have basic info, the stock likely exists
                    logger.debug(f"Stock {symbol} has basic info available")
            except Exception as e:
                logger.debug(f"Could not get basic info for {symbol}: {str(e)}")
            
            # Check 2: Try different time periods for price data
            periods_to_try = ['1d', '5d', '1mo', '3mo']
            hist = None
            
            for period in periods_to_try:
                try:
                    hist = ticker.history(period=period)
                    if not hist.empty and len(hist) > 0:
                        logger.debug(f"Stock {symbol} has price data for period {period}")
                        break
                except Exception as e:
                    logger.debug(f"Could not get {period} data for {symbol}: {str(e)}")
                    continue
            
            # Check 3: If no price data, try to get current price
            if hist is None or hist.empty:
                try:
                    # Try to get current price
                    current_price = ticker.history(period='1d', interval='1m')
                    if not current_price.empty:
                        logger.debug(f"Stock {symbol} has current price data")
                        return True
                except Exception as e:
                    logger.debug(f"Could not get current price for {symbol}: {str(e)}")
            
            # Check 4: Validate the data we got
            if hist is not None and not hist.empty:
                # Check if we have recent data (within last 30 days)
                latest_date = hist.index[-1]
                # Handle timezone-aware vs timezone-naive datetime comparison
                now = pd.Timestamp.now()
                if latest_date.tz is not None and now.tz is None:
                    now = now.tz_localize('UTC')
                elif latest_date.tz is None and now.tz is not None:
                    latest_date = latest_date.tz_localize('UTC')
                days_old = (now - latest_date).days
                
                if days_old > 30:
                    logger.warning(f"Stock {symbol} data is {days_old} days old, might be delisted")
                    return False
                
                # Check if price data looks reasonable
                if 'Close' in hist.columns:
                    latest_price = hist['Close'].iloc[-1]
                    if latest_price <= 0 or pd.isna(latest_price):
                        logger.warning(f"Stock {symbol} has invalid price data")
                        return False
                
                logger.debug(f"Stock {symbol} validation passed")
                return True
            
            # Check 5: If all else fails, try a different approach
            try:
                # Try to get just the ticker info without price data
                ticker_info = ticker.info
                if ticker_info and 'symbol' in ticker_info:
                    logger.debug(f"Stock {symbol} exists but has no recent price data")
                    return True
            except Exception as e:
                logger.debug(f"Final check failed for {symbol}: {str(e)}")
            
            # Only mark as invalid if we've exhausted all checks
            logger.warning(f"Stock {symbol} failed all validation checks")
            return False
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # Be more specific about what constitutes a delisted stock
            delisted_indicators = [
                'delisted',
                'no longer trading',
                'suspended',
                'bankruptcy',
                'ceased trading'
            ]
            
            if any(indicator in error_msg for indicator in delisted_indicators):
                logger.warning(f"Stock {symbol} appears to be delisted: {str(e)}")
                return False
            else:
                # For other errors, don't assume delisted - might be temporary
                logger.warning(f"Error validating stock {symbol}: {str(e)} - treating as valid")
                return True  # Give benefit of doubt
    
    def get_financial_data(self, symbol: str) -> Optional[Dict]:
        """Get financial data for a stock."""
        try:
            # Get company info with retry logic
            info = self._fetch_financial_data_with_retry(symbol)
            
            if not info:
                logger.warning(f"No financial data available for {symbol}")
                return None
            
            # Get financial statements (with additional delay)
            time.sleep(0.5)  # Additional delay for financial statements
            ticker = yf.Ticker(symbol)
            financials = ticker.financials
            balance_sheet = ticker.balance_sheet
            cashflow = ticker.cashflow
            
            # Check if we have any financial data
            has_financial_data = not financials.empty or not balance_sheet.empty
            
            # If no financial statements but we have basic info, still proceed
            if not has_financial_data and not info:
                logger.warning(f"No financial data available for {symbol}")
                return None
            
            # Extract key financial metrics
            financial_data = {
                'symbol': symbol,
                'company_name': info.get('longName', 'Unknown'),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'market_cap': self._get_market_cap(info),
                'enterprise_value': info.get('enterpriseValue'),
                'pe_ratio': self._get_pe_ratio(info),
                'forward_pe': info.get('forwardPE'),
                'peg_ratio': info.get('pegRatio'),
                'pb_ratio': info.get('priceToBook'),
                'ps_ratio': info.get('priceToSalesTrailing12Months'),
                'dividend_yield': info.get('dividendYield'),
                'dividend_rate': info.get('dividendRate'),
                'payout_ratio': info.get('payoutRatio'),
                'beta': info.get('beta'),
                '52_week_high': info.get('fiftyTwoWeekHigh'),
                '52_week_low': info.get('fiftyTwoWeekLow'),
                'current_price': info.get('currentPrice'),
                'target_price': info.get('targetMeanPrice'),
                'recommendation': info.get('recommendationKey'),
                'analyst_count': info.get('numberOfAnalystOpinions'),
                'revenue_growth': info.get('revenueGrowth'),
                'earnings_growth': info.get('earningsGrowth'),
                'profit_margins': info.get('profitMargins'),
                'operating_margins': info.get('operatingMargins'),
                'gross_margins': info.get('grossMargins'),
                'return_on_equity': info.get('returnOnEquity'),
                'return_on_assets': info.get('returnOnAssets'),
                'debt_to_equity': info.get('debtToEquity'),
                'current_ratio': info.get('currentRatio'),
                'quick_ratio': info.get('quickRatio'),
                'cash_per_share': info.get('totalCashPerShare'),
                'book_value': info.get('bookValue'),
                'price_to_book': info.get('priceToBook'),
                'enterprise_to_revenue': info.get('enterpriseToRevenue'),
                'enterprise_to_ebitda': info.get('enterpriseToEbitda'),
                'earnings_quarterly_growth': info.get('earningsQuarterlyGrowth'),
                'revenue_quarterly_growth': info.get('revenueQuarterlyGrowth'),
                'held_percent_insiders': info.get('heldPercentInsiders'),
                'held_percent_institutions': info.get('heldPercentInstitutions'),
                'float_shares': info.get('floatShares'),
                'shares_outstanding': info.get('sharesOutstanding'),
                'shares_short': info.get('sharesShort'),
                'short_ratio': info.get('shortRatio'),
                'short_percent_of_float': info.get('shortPercentOfFloat'),
                'implied_shares_outstanding': info.get('impliedSharesOutstanding'),
                'last_split_date': info.get('lastSplitDate', None),
                'last_split_factor': info.get('lastSplitFactor', None),
                'last_dividend_date': info.get('lastDividendDate', None),
                'last_dividend_value': info.get('lastDividendValue'),
                'ex_dividend_date': info.get('exDividendDate', None),
                'next_dividend_date': info.get('nextDividendDate', None),
                'next_earnings_date': info.get('nextEarningsDate', None),
                'currency': info.get('currency', 'USD'),
                'exchange': info.get('exchange', 'NSE'),
                'timezone': info.get('timezone', 'Asia/Kolkata'),
                'timestamp': pd.Timestamp.now().isoformat()
            }
            
            # Add financial statement data if available
            if not financials.empty:
                try:
                    # Get latest year data
                    latest_year = financials.columns[0]
                    financial_data.update({
                        'total_revenue': financials.loc['Total Revenue', latest_year] if 'Total Revenue' in financials.index else 0,
                        'gross_profit': financials.loc['Gross Profit', latest_year] if 'Gross Profit' in financials.index else 0,
                        'operating_income': financials.loc['Operating Income', latest_year] if 'Operating Income' in financials.index else 0,
                        'net_income': financials.loc['Net Income', latest_year] if 'Net Income' in financials.index else 0,
                        'ebitda': financials.loc['EBITDA', latest_year] if 'EBITDA' in financials.index else 0,
                        'ebit': financials.loc['EBIT', latest_year] if 'EBIT' in financials.index else 0,
                        'research_development': financials.loc['Research Development', latest_year] if 'Research Development' in financials.index else 0,
                        'selling_general_administrative': financials.loc['Selling General Administrative', latest_year] if 'Selling General Administrative' in financials.index else 0,
                        'total_operating_expenses': financials.loc['Total Operating Expenses', latest_year] if 'Total Operating Expenses' in financials.index else 0,
                        'interest_expense': financials.loc['Interest Expense', latest_year] if 'Interest Expense' in financials.index else 0,
                        'income_before_tax': financials.loc['Income Before Tax', latest_year] if 'Income Before Tax' in financials.index else 0,
                        'income_tax_expense': financials.loc['Income Tax Expense', latest_year] if 'Income Tax Expense' in financials.index else 0,
                        'net_income_common': financials.loc['Net Income Common Stockholders', latest_year] if 'Net Income Common Stockholders' in financials.index else 0,
                        'diluted_eps': financials.loc['Diluted EPS', latest_year] if 'Diluted EPS' in financials.index else 0,
                        'basic_eps': financials.loc['Basic EPS', latest_year] if 'Basic EPS' in financials.index else 0,
                        'weighted_average_shares': financials.loc['Weighted Average Shares', latest_year] if 'Weighted Average Shares' in financials.index else 0,
                        'weighted_average_shares_diluted': financials.loc['Weighted Average Shares Diluted', latest_year] if 'Weighted Average Shares Diluted' in financials.index else 0
                    })
                except Exception as e:
                    logger.warning(f"Error extracting financials data: {str(e)}")
            
            if not balance_sheet.empty:
                try:
                    # Get latest year data
                    latest_year = balance_sheet.columns[0]
                    financial_data.update({
                        'total_cash': balance_sheet.loc['Total Cash', latest_year] if 'Total Cash' in balance_sheet.index else 0,
                        'total_cash_per_share': balance_sheet.loc['Total Cash Per Share', latest_year] if 'Total Cash Per Share' in balance_sheet.index else 0,
                        'total_debt': balance_sheet.loc['Total Debt', latest_year] if 'Total Debt' in balance_sheet.index else 0,
                        'total_debt_per_equity': balance_sheet.loc['Total Debt/Equity', latest_year] if 'Total Debt/Equity' in balance_sheet.index else 0,
                        'current_assets': balance_sheet.loc['Current Assets', latest_year] if 'Current Assets' in balance_sheet.index else 0,
                        'total_assets': balance_sheet.loc['Total Assets', latest_year] if 'Total Assets' in balance_sheet.index else 0,
                        'current_liabilities': balance_sheet.loc['Current Liabilities', latest_year] if 'Current Liabilities' in balance_sheet.index else 0,
                        'total_liabilities': balance_sheet.loc['Total Liabilities', latest_year] if 'Total Liabilities' in balance_sheet.index else 0,
                        'total_stockholder_equity': balance_sheet.loc['Total Stockholder Equity', latest_year] if 'Total Stockholder Equity' in balance_sheet.index else 0,
                        'retained_earnings': balance_sheet.loc['Retained Earnings', latest_year] if 'Retained Earnings' in balance_sheet.index else 0,
                        'common_stock': balance_sheet.loc['Common Stock', latest_year] if 'Common Stock' in balance_sheet.index else 0,
                        'treasury_stock': balance_sheet.loc['Treasury Stock', latest_year] if 'Treasury Stock' in balance_sheet.index else 0,
                        'capital_surplus': balance_sheet.loc['Capital Surplus', latest_year] if 'Capital Surplus' in balance_sheet.index else 0,
                        'other_stockholder_equity': balance_sheet.loc['Other Stockholder Equity', latest_year] if 'Other Stockholder Equity' in balance_sheet.index else 0,
                        'goodwill': balance_sheet.loc['Goodwill', latest_year] if 'Goodwill' in balance_sheet.index else 0,
                        'intangible_assets': balance_sheet.loc['Intangible Assets', latest_year] if 'Intangible Assets' in balance_sheet.index else 0,
                        'net_tangible_assets': balance_sheet.loc['Net Tangible Assets', latest_year] if 'Net Tangible Assets' in balance_sheet.index else 0,
                        'working_capital': balance_sheet.loc['Working Capital', latest_year] if 'Working Capital' in balance_sheet.index else 0,
                        'invested_capital': balance_sheet.loc['Invested Capital', latest_year] if 'Invested Capital' in balance_sheet.index else 0,
                        'tangible_book_value': balance_sheet.loc['Tangible Book Value', latest_year] if 'Tangible Book Value' in balance_sheet.index else 0,
                        'total_capitalization': balance_sheet.loc['Total Capitalization', latest_year] if 'Total Capitalization' in balance_sheet.index else 0,
                        'common_stock_shares_outstanding': balance_sheet.loc['Common Stock Shares Outstanding', latest_year] if 'Common Stock Shares Outstanding' in balance_sheet.index else 0,
                        'net_income': balance_sheet.loc['Net Income', latest_year] if 'Net Income' in balance_sheet.index else 0,
                        'net_income_common': balance_sheet.loc['Net Income Common Stockholders', latest_year] if 'Net Income Common Stockholders' in balance_sheet.index else 0,
                        'net_income_common_stockholders': balance_sheet.loc['Net Income Common Stockholders', latest_year] if 'Net Income Common Stockholders' in balance_sheet.index else 0,
                        'net_income_common_stockholders_attributable': balance_sheet.loc['Net Income Common Stockholders Attributable', latest_year] if 'Net Income Common Stockholders Attributable' in balance_sheet.index else 0,
                        'net_income_common_stockholders_attributable_to_parent': balance_sheet.loc['Net Income Common Stockholders Attributable To Parent', latest_year] if 'Net Income Common Stockholders Attributable To Parent' in balance_sheet.index else 0,
                        'net_income_common_stockholders_attributable_to_parent_common': balance_sheet.loc['Net Income Common Stockholders Attributable To Parent Common', latest_year] if 'Net Income Common Stockholders Attributable To Parent Common' in balance_sheet.index else 0,
                        'net_income_common_stockholders_attributable_to_parent_common_basic': balance_sheet.loc['Net Income Common Stockholders Attributable To Parent Common Basic', latest_year] if 'Net Income Common Stockholders Attributable To Parent Common Basic' in balance_sheet.index else 0,
                        'net_income_common_stockholders_attributable_to_parent_common_diluted': balance_sheet.loc['Net Income Common Stockholders Attributable To Parent Common Diluted', latest_year] if 'Net Income Common Stockholders Attributable To Parent Common Diluted' in balance_sheet.index else 0,
                        'net_income_common_stockholders_attributable_to_parent_common_diluted_eps': balance_sheet.loc['Net Income Common Stockholders Attributable To Parent Common Diluted EPS', latest_year] if 'Net Income Common Stockholders Attributable To Parent Common Diluted EPS' in balance_sheet.index else 0,
                        'net_income_common_stockholders_attributable_to_parent_common_diluted_eps_basic': balance_sheet.loc['Net Income Common Stockholders Attributable To Parent Common Diluted EPS Basic', latest_year] if 'Net Income Common Stockholders Attributable To Parent Common Diluted EPS Basic' in balance_sheet.index else 0,
                        'net_income_common_stockholders_attributable_to_parent_common_diluted_eps_diluted': balance_sheet.loc['Net Income Common Stockholders Attributable To Parent Common Diluted EPS Diluted', latest_year] if 'Net Income Common Stockholders Attributable To Parent Common Diluted EPS Diluted' in balance_sheet.index else 0
                    })
                except Exception as e:
                    logger.warning(f"Error extracting balance sheet data: {str(e)}")
            
            return financial_data
            
        except Exception as e:
            logger.error(f"Error getting financial data for {symbol}: {str(e)}")
            return None
    
    def _get_market_cap(self, info: Dict) -> Optional[float]:
        """Get market cap with fallback calculation. Returns None if data not available."""
        try:
            # Try different field names for market cap
            market_cap = info.get('marketCap')
            if market_cap is not None and market_cap > 0:
                return market_cap
            
            # Try alternative field names
            market_cap = info.get('market_cap')
            if market_cap is not None and market_cap > 0:
                return market_cap
            
            # Try to calculate from shares outstanding and current price
            shares_outstanding = info.get('sharesOutstanding')
            current_price = info.get('currentPrice')
            
            if shares_outstanding is not None and current_price is not None and shares_outstanding > 0 and current_price > 0:
                calculated_market_cap = shares_outstanding * current_price
                logger.info(f"Calculated market cap: {calculated_market_cap:,.0f} (shares: {shares_outstanding:,.0f} * price: {current_price:.2f})")
                return calculated_market_cap
            
            # Try to calculate from float shares and current price
            float_shares = info.get('floatShares')
            if float_shares is not None and current_price is not None and float_shares > 0 and current_price > 0:
                calculated_market_cap = float_shares * current_price
                logger.info(f"Calculated market cap from float shares: {calculated_market_cap:,.0f}")
                return calculated_market_cap
            
            # If all else fails, return None to indicate missing data
            logger.debug("Could not determine market cap from available data")
            return None
            
        except Exception as e:
            logger.error(f"Error calculating market cap: {str(e)}")
            return None
    
    def _get_pe_ratio(self, info: Dict) -> Optional[float]:
        """Get P/E ratio with fallback calculation. Returns None if data not available."""
        try:
            # Try different field names for P/E ratio
            pe_ratio = info.get('trailingPE')
            if pe_ratio is not None and pe_ratio > 0:
                return pe_ratio
            
            # Try alternative field names
            pe_ratio = info.get('forwardPE')
            if pe_ratio is not None and pe_ratio > 0:
                return pe_ratio
            
            pe_ratio = info.get('pe_ratio')
            if pe_ratio is not None and pe_ratio > 0:
                return pe_ratio
            
            # Try to calculate from current price and earnings per share
            current_price = info.get('currentPrice')
            eps = info.get('trailingEps')
            
            if current_price is not None and eps is not None and current_price > 0 and eps > 0:
                calculated_pe = current_price / eps
                logger.info(f"Calculated P/E ratio: {calculated_pe:.2f} (price: {current_price:.2f} / eps: {eps:.2f})")
                return calculated_pe
            
            # Try alternative EPS field
            eps = info.get('forwardEps')
            if current_price is not None and eps is not None and current_price > 0 and eps > 0:
                calculated_pe = current_price / eps
                logger.info(f"Calculated P/E ratio from forward EPS: {calculated_pe:.2f}")
                return calculated_pe
            
            # If all else fails, return None to indicate missing data
            logger.debug("Could not determine P/E ratio from available data")
            return None
            
        except Exception as e:
            logger.error(f"Error calculating P/E ratio: {str(e)}")
            return None
    
    def calculate_fundamental_score(self, financial_data: Dict) -> Dict:
        """Calculate fundamental score based on financial metrics."""
        try:
            if not financial_data:
                return {'score': 0.0, 'ratings': {}}
            
            score = 0.0
            ratings = {}
            
            # Valuation Metrics (25% weight)
            valuation_score = 0.0
            
            # P/E Ratio
            pe_ratio = financial_data.get('pe_ratio', 0)
            if pe_ratio > 0:
                if pe_ratio < 15:
                    valuation_score += 0.8
                    ratings['P/E Ratio'] = 'Excellent (< 15)'
                elif pe_ratio < 25:
                    valuation_score += 0.6
                    ratings['P/E Ratio'] = 'Good (15-25)'
                elif pe_ratio < 35:
                    valuation_score += 0.4
                    ratings['P/E Ratio'] = 'Fair (25-35)'
                else:
                    valuation_score += 0.2
                    ratings['P/E Ratio'] = 'Expensive (> 35)'
            else:
                ratings['P/E Ratio'] = 'N/A'
            
            # P/B Ratio
            pb_ratio = financial_data.get('pb_ratio', 0)
            if pb_ratio > 0:
                if pb_ratio < 1.5:
                    valuation_score += 0.8
                    ratings['P/B Ratio'] = 'Excellent (< 1.5)'
                elif pb_ratio < 3:
                    valuation_score += 0.6
                    ratings['P/B Ratio'] = 'Good (1.5-3)'
                elif pb_ratio < 5:
                    valuation_score += 0.4
                    ratings['P/B Ratio'] = 'Fair (3-5)'
                else:
                    valuation_score += 0.2
                    ratings['P/B Ratio'] = 'Expensive (> 5)'
            else:
                ratings['P/B Ratio'] = 'N/A'
            
            # P/S Ratio
            ps_ratio = financial_data.get('ps_ratio', 0)
            if ps_ratio > 0:
                if ps_ratio < 2:
                    valuation_score += 0.8
                    ratings['P/S Ratio'] = 'Excellent (< 2)'
                elif ps_ratio < 5:
                    valuation_score += 0.6
                    ratings['P/S Ratio'] = 'Good (2-5)'
                elif ps_ratio < 10:
                    valuation_score += 0.4
                    ratings['P/S Ratio'] = 'Fair (5-10)'
                else:
                    valuation_score += 0.2
                    ratings['P/S Ratio'] = 'Expensive (> 10)'
            else:
                ratings['P/S Ratio'] = 'N/A'
            
            valuation_score = min(valuation_score, 1.0)
            score += valuation_score * 0.25
            
            # Profitability Metrics (30% weight)
            profitability_score = 0.0
            
            # ROE
            roe = financial_data.get('return_on_equity', 0)
            if roe > 0:
                if roe > 20:
                    profitability_score += 0.8
                    ratings['ROE'] = 'Excellent (> 20%)'
                elif roe > 15:
                    profitability_score += 0.6
                    ratings['ROE'] = 'Good (15-20%)'
                elif roe > 10:
                    profitability_score += 0.4
                    ratings['ROE'] = 'Fair (10-15%)'
                else:
                    profitability_score += 0.2
                    ratings['ROE'] = 'Poor (< 10%)'
            else:
                ratings['ROE'] = 'N/A'
            
            # ROA
            roa = financial_data.get('return_on_assets', 0)
            if roa > 0:
                if roa > 10:
                    profitability_score += 0.8
                    ratings['ROA'] = 'Excellent (> 10%)'
                elif roa > 5:
                    profitability_score += 0.6
                    ratings['ROA'] = 'Good (5-10%)'
                elif roa > 2:
                    profitability_score += 0.4
                    ratings['ROA'] = 'Fair (2-5%)'
                else:
                    profitability_score += 0.2
                    ratings['ROA'] = 'Poor (< 2%)'
            else:
                ratings['ROA'] = 'N/A'
            
            # Profit Margins
            profit_margins = financial_data.get('profit_margins', 0)
            if profit_margins > 0:
                if profit_margins > 15:
                    profitability_score += 0.8
                    ratings['Profit Margins'] = 'Excellent (> 15%)'
                elif profit_margins > 10:
                    profitability_score += 0.6
                    ratings['Profit Margins'] = 'Good (10-15%)'
                elif profit_margins > 5:
                    profitability_score += 0.4
                    ratings['Profit Margins'] = 'Fair (5-10%)'
                else:
                    profitability_score += 0.2
                    ratings['Profit Margins'] = 'Poor (< 5%)'
            else:
                ratings['Profit Margins'] = 'N/A'
            
            profitability_score = min(profitability_score, 1.0)
            score += profitability_score * 0.30
            
            # Growth Metrics (20% weight)
            growth_score = 0.0
            
            # Revenue Growth
            revenue_growth = financial_data.get('revenue_growth', 0)
            if revenue_growth > 0:
                if revenue_growth > 20:
                    growth_score += 0.8
                    ratings['Revenue Growth'] = 'Excellent (> 20%)'
                elif revenue_growth > 10:
                    growth_score += 0.6
                    ratings['Revenue Growth'] = 'Good (10-20%)'
                elif revenue_growth > 5:
                    growth_score += 0.4
                    ratings['Revenue Growth'] = 'Fair (5-10%)'
                else:
                    growth_score += 0.2
                    ratings['Revenue Growth'] = 'Poor (< 5%)'
            else:
                ratings['Revenue Growth'] = 'N/A'
            
            # Earnings Growth
            earnings_growth = financial_data.get('earnings_growth', 0)
            if earnings_growth > 0:
                if earnings_growth > 20:
                    growth_score += 0.8
                    ratings['Earnings Growth'] = 'Excellent (> 20%)'
                elif earnings_growth > 10:
                    growth_score += 0.6
                    ratings['Earnings Growth'] = 'Good (10-20%)'
                elif earnings_growth > 5:
                    growth_score += 0.4
                    ratings['Earnings Growth'] = 'Fair (5-10%)'
                else:
                    growth_score += 0.2
                    ratings['Earnings Growth'] = 'Poor (< 5%)'
            else:
                ratings['Earnings Growth'] = 'N/A'
            
            growth_score = min(growth_score, 1.0)
            score += growth_score * 0.20
            
            # Financial Health Metrics (25% weight)
            health_score = 0.0
            
            # Debt to Equity
            debt_to_equity = financial_data.get('debt_to_equity', 0)
            if debt_to_equity > 0:
                if debt_to_equity < 0.3:
                    health_score += 0.8
                    ratings['Debt/Equity'] = 'Excellent (< 0.3)'
                elif debt_to_equity < 0.6:
                    health_score += 0.6
                    ratings['Debt/Equity'] = 'Good (0.3-0.6)'
                elif debt_to_equity < 1.0:
                    health_score += 0.4
                    ratings['Debt/Equity'] = 'Fair (0.6-1.0)'
                else:
                    health_score += 0.2
                    ratings['Debt/Equity'] = 'Poor (> 1.0)'
            else:
                ratings['Debt/Equity'] = 'N/A'
            
            # Current Ratio
            current_ratio = financial_data.get('current_ratio', 0)
            if current_ratio > 0:
                if current_ratio > 2:
                    health_score += 0.8
                    ratings['Current Ratio'] = 'Excellent (> 2)'
                elif current_ratio > 1.5:
                    health_score += 0.6
                    ratings['Current Ratio'] = 'Good (1.5-2)'
                elif current_ratio > 1:
                    health_score += 0.4
                    ratings['Current Ratio'] = 'Fair (1-1.5)'
                else:
                    health_score += 0.2
                    ratings['Current Ratio'] = 'Poor (< 1)'
            else:
                ratings['Current Ratio'] = 'N/A'
            
            health_score = min(health_score, 1.0)
            score += health_score * 0.25
            
            # Ensure score is between 0 and 1
            score = max(0, min(1, score))
            
            return {
                'score': score,
                'ratings': ratings,
                'valuation_score': valuation_score,
                'profitability_score': profitability_score,
                'growth_score': growth_score,
                'health_score': health_score,
                'timestamp': pd.Timestamp.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating fundamental score: {str(e)}")
            return {'score': 0.0, 'ratings': {}}
