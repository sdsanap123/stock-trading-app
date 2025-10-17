#!/usr/bin/env python3
"""
Portfolio Manager Component
Handles Excel portfolio uploads and portfolio analysis.
"""

import pandas as pd
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)

class PortfolioManager:
    """Manages portfolio data from Excel uploads and provides analysis."""
    
    def __init__(self):
        self.portfolio_data = []
        self.portfolio_file = "data/portfolio.json"
        self.load_portfolio()
        logger.info("Portfolio Manager initialized")
    
    def load_portfolio(self):
        """Load portfolio data from file."""
        try:
            if os.path.exists(self.portfolio_file):
                import json
                with open(self.portfolio_file, 'r') as f:
                    self.portfolio_data = json.load(f)
                logger.info(f"Loaded {len(self.portfolio_data)} portfolio items")
            else:
                self.portfolio_data = []
        except Exception as e:
            logger.error(f"Error loading portfolio: {str(e)}")
            self.portfolio_data = []
    
    def save_portfolio(self):
        """Save portfolio data to file."""
        try:
            import json
            os.makedirs(os.path.dirname(self.portfolio_file), exist_ok=True)
            with open(self.portfolio_file, 'w') as f:
                json.dump(self.portfolio_data, f, indent=2)
            logger.info(f"Saved {len(self.portfolio_data)} portfolio items")
        except Exception as e:
            logger.error(f"Error saving portfolio: {str(e)}")
    
    def upload_excel_portfolio(self, uploaded_file) -> Dict:
        """Upload and process Excel portfolio file."""
        try:
            # Read Excel file
            df = pd.read_excel(uploaded_file)
            
            # Validate required columns
            required_columns = ['Scrip Name', 'Free Qty', 'Rate', 'Valuation']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                return {
                    'success': False,
                    'message': f"Missing required columns: {', '.join(missing_columns)}",
                    'data': None
                }
            
            # Process portfolio data
            portfolio_items = []
            for index, row in df.iterrows():
                try:
                    # Get symbol from Scrip Name (remove .NS suffix if present)
                    scrip_name = str(row['Scrip Name']).strip()
                    symbol = scrip_name.replace('.NS', '').replace('.NSE', '')
                    
                    # Calculate current values
                    free_qty = float(row['Free Qty']) if pd.notna(row['Free Qty']) else 0
                    rate = float(row['Rate']) if pd.notna(row['Rate']) else 0
                    valuation = float(row['Valuation']) if pd.notna(row['Valuation']) else 0
                    
                    # Calculate entry price (Rate from Excel)
                    entry_price = rate
                    
                    # Calculate current market value
                    current_market_value = free_qty * entry_price
                    
                    portfolio_item = {
                        'symbol': symbol,
                        'scrip_name': scrip_name,
                        'free_qty': free_qty,
                        'entry_price': entry_price,
                        'current_price': entry_price,  # Will be updated with live data
                        'valuation': valuation,
                        'current_market_value': current_market_value,
                        'date_added': datetime.now().isoformat(),
                        'recommendation': 'HOLD',  # Default recommendation
                        'confidence': 0,
                        'target_price': 0,
                        'stop_loss': 0,
                        'last_analyzed': None,
                        'analysis_count': 0
                    }
                    
                    portfolio_items.append(portfolio_item)
                    
                except Exception as e:
                    logger.warning(f"Error processing row {index}: {str(e)}")
                    continue
            
            # Update portfolio data
            self.portfolio_data = portfolio_items
            self.save_portfolio()
            
            return {
                'success': True,
                'message': f"Successfully uploaded {len(portfolio_items)} portfolio items",
                'data': portfolio_items
            }
            
        except Exception as e:
            logger.error(f"Error uploading Excel portfolio: {str(e)}")
            return {
                'success': False,
                'message': f"Error processing Excel file: {str(e)}",
                'data': None
            }
    
    def get_portfolio(self) -> List[Dict]:
        """Get current portfolio data."""
        return self.portfolio_data
    
    def update_portfolio_prices(self, price_data: Dict[str, float]):
        """Update portfolio with current market prices."""
        try:
            for item in self.portfolio_data:
                symbol = item['symbol']
                if symbol in price_data:
                    old_price = item['current_price']
                    new_price = price_data[symbol]
                    item['current_price'] = new_price
                    item['current_market_value'] = item['free_qty'] * new_price
                    
                    # Calculate P&L
                    if old_price > 0:
                        pnl_percent = ((new_price - old_price) / old_price) * 100
                        item['pnl_percent'] = pnl_percent
                        item['pnl_amount'] = (new_price - old_price) * item['free_qty']
            
            self.save_portfolio()
            logger.info("Updated portfolio prices")
            
        except Exception as e:
            logger.error(f"Error updating portfolio prices: {str(e)}")
    
    def analyze_portfolio_item(self, item: Dict, technical_analysis: Dict, 
                             fundamental_analysis: Dict, news_sentiment: float,
                             groq_analysis: Dict, ai_recommendation: Dict) -> Dict:
        """Analyze a single portfolio item and update recommendation."""
        try:
            # Update analysis data
            item['last_analyzed'] = datetime.now().isoformat()
            item['analysis_count'] = item.get('analysis_count', 0) + 1
            
            # Update recommendation based on AI analysis
            if ai_recommendation and ai_recommendation.get('action'):
                item['recommendation'] = ai_recommendation['action']
                item['confidence'] = ai_recommendation.get('confidence', 0)
                item['target_price'] = ai_recommendation.get('target_price', 0)
                item['stop_loss'] = ai_recommendation.get('stop_loss', 0)
                item['reasoning'] = ai_recommendation.get('reasoning', '')
            
            # Store analysis data
            item['technical_analysis'] = technical_analysis
            item['fundamental_analysis'] = fundamental_analysis
            item['news_sentiment'] = news_sentiment
            item['groq_analysis'] = groq_analysis
            
            return item
            
        except Exception as e:
            logger.error(f"Error analyzing portfolio item {item.get('symbol', 'unknown')}: {str(e)}")
            return item
    
    def get_items_for_analysis(self) -> List[Dict]:
        """Get portfolio items that need analysis (7+ days old or never analyzed)."""
        try:
            items_to_analyze = []
            current_date = datetime.now()
            
            for item in self.portfolio_data:
                date_added = datetime.fromisoformat(item.get('date_added', current_date.isoformat()))
                last_analyzed = item.get('last_analyzed')
                
                # Check if item needs analysis
                needs_analysis = False
                
                if not last_analyzed:
                    # Never analyzed
                    needs_analysis = True
                else:
                    # Check if 7+ days since last analysis
                    last_analysis_date = datetime.fromisoformat(last_analyzed)
                    days_since_analysis = (current_date - last_analysis_date).days
                    if days_since_analysis >= 7:
                        needs_analysis = True
                
                if needs_analysis:
                    items_to_analyze.append(item)
            
            return items_to_analyze
            
        except Exception as e:
            logger.error(f"Error getting items for analysis: {str(e)}")
            return []
    
    def get_portfolio_summary(self) -> Dict:
        """Get portfolio summary statistics."""
        try:
            if not self.portfolio_data:
                return {
                    'total_items': 0,
                    'total_value': 0,
                    'total_pnl': 0,
                    'avg_pnl_percent': 0,
                    'recommendations': {'BUY': 0, 'HOLD': 0, 'SELL': 0}
                }
            
            total_value = sum(item.get('current_market_value', 0) for item in self.portfolio_data)
            total_pnl = sum(item.get('pnl_amount', 0) for item in self.portfolio_data)
            avg_pnl_percent = sum(item.get('pnl_percent', 0) for item in self.portfolio_data) / len(self.portfolio_data)
            
            recommendations = {'BUY': 0, 'HOLD': 0, 'SELL': 0}
            for item in self.portfolio_data:
                rec = item.get('recommendation', 'HOLD')
                if rec in recommendations:
                    recommendations[rec] += 1
            
            return {
                'total_items': len(self.portfolio_data),
                'total_value': total_value,
                'total_pnl': total_pnl,
                'avg_pnl_percent': avg_pnl_percent,
                'recommendations': recommendations
            }
            
        except Exception as e:
            logger.error(f"Error getting portfolio summary: {str(e)}")
            return {
                'total_items': 0,
                'total_value': 0,
                'total_pnl': 0,
                'avg_pnl_percent': 0,
                'recommendations': {'BUY': 0, 'HOLD': 0, 'SELL': 0}
            }
    
    def remove_portfolio_item(self, symbol: str) -> bool:
        """Remove a portfolio item by symbol."""
        try:
            original_count = len(self.portfolio_data)
            self.portfolio_data = [item for item in self.portfolio_data if item.get('symbol') != symbol]
            
            if len(self.portfolio_data) < original_count:
                self.save_portfolio()
                logger.info(f"Removed portfolio item: {symbol}")
                return True
            else:
                logger.warning(f"Portfolio item not found: {symbol}")
                return False
                
        except Exception as e:
            logger.error(f"Error removing portfolio item {symbol}: {str(e)}")
            return False
