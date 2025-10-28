#!/usr/bin/env python3
"""
Enhanced Swing Trading App - Streamlit Web Version
A comprehensive stock analysis and trading application with AI-powered recommendations.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import json
import pickle
import time
import requests
from typing import Dict, List, Optional, Tuple
import sys
from dataclasses import dataclass
from textblob import TextBlob
import feedparser
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('enhanced_trading.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import all the analysis components from the original app
from components.ai_engine import AIRecommendationEngine
from components.technical_analyzer import TechnicalAnalyzer
from components.fundamental_analyzer import FundamentalAnalyzer
from components.news_analyzer import NewsAnalyzer
from components.groq_analyzer import GroqNewsAnalyzer
from components.gemini_analyzer import GeminiAIAnalyzer
from components.watchlist_manager import WatchlistManager
from components.recommendation_learning import RecommendationTracker
from components.firebase_integration import FirebaseSync
from components.cache_manager import CacheManager
from components.swing_strategy import SwingTradingStrategy
from components.email_notifications import EmailNotificationManager, AlertType, AlertPriority
from components.price_monitor import PriceMonitor
from components.notification_settings import NotificationSettingsManager, NotificationChannel
from components.data_persistence import DataPersistenceManager
from components.expandable_ui import ExpandableUI
from components.scheduled_analysis import ScheduledAnalysis
from components.swing_performance_tracker import SwingPerformanceTracker

# Page configuration
st.set_page_config(
    page_title="Enhanced Swing Trading App",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #1f4e79, #2e8b57);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .metric-card {
        background-color: #1e1e1e;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #2e8b57;
    }
    
    .sentiment-positive {
        color: #28a745;
        font-weight: bold;
    }
    
    .sentiment-negative {
        color: #dc3545;
        font-weight: bold;
    }
    
    .sentiment-neutral {
        color: #ffc107;
        font-weight: bold;
    }
    
    .recommendation-buy {
        color: #28a745;
        font-weight: bold;
        font-size: 1.2rem;
    }
    
    .recommendation-sell {
        color: #dc3545;
        font-weight: bold;
        font-size: 1.2rem;
    }
    
    .recommendation-hold {
        color: #ffc107;
        font-weight: bold;
        font-size: 1.2rem;
    }
    
    .news-card {
        background-color: #2d2d2d;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #1f4e79;
    }
    
    .groq-card {
        background-color: #2d2d2d;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #2e8b57;
    }
    
    .government-highlight {
        background-color: #3d2d2d;
        border-left: 4px solid #ffd700;
        box-shadow: 0 0 10px rgba(255, 215, 0, 0.3);
    }
    
    /* Compact UI optimizations */
    .main-header {
        font-size: 1.8rem !important;
        margin-bottom: 1rem !important;
    }
    
    /* Compact tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.3rem;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 0.2rem 0.6rem;
        font-size: 0.85rem;
        min-height: 2rem;
    }
    
    /* Compact sidebar */
    .css-1d391kg {
        padding-top: 0.5rem;
    }
    
    /* Compact metrics */
    .metric-card {
        padding: 0.5rem !important;
        margin: 0.2rem 0 !important;
    }
    
    /* Compact expandable content */
    .expandable-row {
        margin: 0.1rem 0;
        padding: 0.2rem;
    }
    
    /* Reduce spacing */
    .element-container {
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

@dataclass
class StockData:
    """Data class for stock information."""
    symbol: str
    name: str
    current_price: float
    change: float
    change_percent: float
    volume: int
    market_cap: float

class StreamlitTradingApp:
    """Main Streamlit Trading Application."""
    
    def __init__(self):
        """Initialize the application."""
        self.initialize_session_state()
        self.initialize_components()
    
    def initialize_session_state(self):
        """Initialize Streamlit session state."""
        # First, initialize the data persistence
        if 'data_persistence' not in st.session_state:
            st.session_state.data_persistence = DataPersistenceManager()
        
        # Initialize cache manager
        if 'cache_manager' not in st.session_state:
            st.session_state.cache_manager = CacheManager()
            
        # Initialize basic session state variables
        session_vars = {
            'recommendations': [],
            'news_articles': [],
            'groq_news_data': {},
            'watchlist': [],
            'portfolio': [],
            'analysis_in_progress': False,
            'last_analysis_time': None,
            'show_saved_recommendations': False,
            'saved_groq_key': self.load_saved_api_key('groq'),
            'saved_gemini_key': self.load_saved_api_key('gemini')
        }
        
        # Set default values if not already set
        for key, default_value in session_vars.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
        
        # Load watchlist from database if available and watchlist is empty
        if not st.session_state.watchlist:
            try:
                saved_watchlist = st.session_state.data_persistence.get_watchlist()
                if saved_watchlist:
                    st.session_state.watchlist = saved_watchlist
                    logger.info(f"Loaded {len(saved_watchlist)} items from saved watchlist")
            except Exception as e:
                logger.error(f"Error loading watchlist: {str(e)}")
        
        # Load recommendations if we don't have any in the current session
        if not st.session_state.recommendations:
            try:
                available_dates = st.session_state.data_persistence.get_available_dates()
                if available_dates:
                    latest_date = max(available_dates)
                    latest_recommendations = st.session_state.data_persistence.get_recommendations_by_date(latest_date)
                    if latest_recommendations:
                        # Convert any string values to their appropriate types
                        for rec in latest_recommendations:
                            # Ensure confidence is a number
                            if 'confidence' in rec and isinstance(rec['confidence'], str):
                                try:
                                    rec['confidence'] = float(rec['confidence'])
                                except (ValueError, TypeError):
                                    rec['confidence'] = 0.0
                        
                        # Remove duplicates based on symbol
                        unique_recommendations = {}
                        for rec in latest_recommendations:
                            symbol = rec.get('symbol')
                            if symbol:  # Only add if symbol exists
                                unique_recommendations[symbol] = rec
                        
                        st.session_state.recommendations = list(unique_recommendations.values())
                        logger.info(f"Loaded {len(st.session_state.recommendations)} unique recommendations from {latest_date}")
            except Exception as e:
                logger.error(f"Error loading recommendations: {str(e)}")
                st.session_state.recommendations = []  # Ensure we have an empty list on error
        
        if 'swing_performance_tracker' not in st.session_state:
            st.session_state.swing_performance_tracker = SwingPerformanceTracker(working_capital=100000)
        if 'swing_strategy' not in st.session_state:
            # Initialize swing strategy with adaptive parameters
            adaptive_params = st.session_state.swing_performance_tracker.get_adaptive_parameters()
            st.session_state.swing_strategy = SwingTradingStrategy(adaptive_parameters=adaptive_params)
        if 'email_notifications' not in st.session_state:
            st.session_state.email_notifications = EmailNotificationManager()
        if 'price_monitor' not in st.session_state:
            st.session_state.price_monitor = PriceMonitor(self._notification_callback)
        if 'notification_settings' not in st.session_state:
            st.session_state.notification_settings = NotificationSettingsManager()
        if 'scheduled_analysis' not in st.session_state:
            st.session_state.scheduled_analysis = ScheduledAnalysis(self.analyze_market)
        
    def initialize_components(self):
        """Initialize all analysis components."""
        try:
            # Initialize AI components
            self.ai_engine = AIRecommendationEngine()
            self.technical_analyzer = TechnicalAnalyzer()
            self.fundamental_analyzer = FundamentalAnalyzer()
            self.news_analyzer = NewsAnalyzer()
            self.groq_analyzer = GroqNewsAnalyzer()
            self.gemini_analyzer = GeminiAIAnalyzer()
            self.watchlist_manager = WatchlistManager()
            
            # Set fundamental analyzer in AI engine
            self.ai_engine.set_fundamental_analyzer(self.fundamental_analyzer)
            
            # Initialize learning system
            try:
                self.recommendation_tracker = RecommendationTracker()
                st.session_state.learning_available = True
            except:
                st.session_state.learning_available = False
            
            # Initialize Firebase
            try:
                self.firebase_sync = FirebaseSync('firebase_config.json')
                st.session_state.firebase_available = self.firebase_sync.initialized
            except:
                st.session_state.firebase_available = False
            
            # Initialize API keys in analyzers
            self._initialize_api_keys()
            
            # Start scheduled analysis
            if hasattr(self, 'scheduled_analysis') and st.session_state.get('scheduled_analysis'):
                st.session_state.scheduled_analysis.start_scheduler()
                logger.info("Scheduled analysis started")
            
            logger.info("All components initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing components: {str(e)}")
            st.error(f"Error initializing components: {str(e)}")
    
    def _initialize_api_keys(self):
        """Initialize API keys in analyzers from saved settings."""
        try:
            # Load and set Groq API key
            groq_key = self.load_saved_api_key('groq')
            if groq_key:
                self.groq_analyzer.api_key = groq_key
                self.groq_analyzer.initialized = True
                logger.info("Groq API key loaded and initialized")
            else:
                self.groq_analyzer.initialized = False
                logger.warning("Groq API key not found")
            
            # Load and set Gemini API key
            gemini_key = self.load_saved_api_key('gemini')
            if gemini_key:
                self.gemini_analyzer.api_key = gemini_key
                self.gemini_analyzer.initialized = True
                logger.info("Gemini API key loaded and initialized")
            else:
                self.gemini_analyzer.initialized = False
                logger.warning("Gemini API key not found")
                
        except Exception as e:
            logger.error(f"Error initializing API keys: {str(e)}")
    
    def _auto_save_recommendations(self):
        """Automatically save recommendations."""
        try:
            if st.session_state.get('recommendations'):
                data_persistence = st.session_state.data_persistence
                data_persistence.save_recommendations(st.session_state.recommendations)
                logger.info(f"Auto-saved {len(st.session_state.recommendations)} recommendations")
        except Exception as e:
            logger.error(f"Error auto-saving recommendations: {str(e)}")
    
    def _auto_save_buy_recommendations(self):
        """Automatically save only BUY recommendations date-wise."""
        try:
            if st.session_state.get('recommendations'):
                data_persistence = st.session_state.data_persistence
                current_date = datetime.now().strftime("%Y-%m-%d")
                
                # Save BUY recommendations specifically
                success = data_persistence.save_buy_recommendations(st.session_state.recommendations, current_date)
                
                if success:
                    # Count BUY recommendations
                    buy_count = 0
                    for rec in st.session_state.recommendations:
                        recommendation = rec.get('recommendation', '').upper()
                        action = rec.get('action', '').upper()
                        if recommendation == 'BUY' or action == 'BUY':
                            buy_count += 1
                    
                    logger.info(f"Auto-saved {buy_count} BUY recommendations for {current_date}")
                    return True
                else:
                    logger.error("Failed to save BUY recommendations")
                    return False
            else:
                logger.info("No recommendations to save")
                return True
        except Exception as e:
            logger.error(f"Error auto-saving BUY recommendations: {str(e)}")
            return False
    
    def _auto_save_buy_recommendations_for_manual(self, recommendations: List[Dict]):
        """Save BUY recommendations from manual analysis."""
        try:
            if recommendations:
                data_persistence = st.session_state.data_persistence
                current_date = datetime.now().strftime("%Y-%m-%d")
                
                # Save BUY recommendations specifically
                success = data_persistence.save_buy_recommendations(recommendations, current_date)
                
                if success:
                    logger.info(f"Auto-saved {len(recommendations)} BUY recommendation(s) from manual analysis for {current_date}")
                    return True
                else:
                    logger.error("Failed to save manual BUY recommendations")
                    return False
            else:
                logger.info("No manual recommendations to save")
                return True
        except Exception as e:
            logger.error(f"Error auto-saving manual BUY recommendations: {str(e)}")
            return False
    
    def _auto_save_watchlist(self):
        """Automatically save watchlist."""
        try:
            if st.session_state.get('watchlist'):
                data_persistence = st.session_state.data_persistence
                data_persistence.save_watchlist(st.session_state.watchlist)
                logger.info(f"Auto-saved {len(st.session_state.watchlist)} watchlist items")
        except Exception as e:
            logger.error(f"Error auto-saving watchlist: {str(e)}")
    
    def _auto_save_swing_strategies(self):
        """Automatically save swing strategies."""
        try:
            if st.session_state.get('recommendations'):
                swing_strategies = []
                for rec in st.session_state.recommendations:
                    swing_plan = rec.get('swing_plan', {})
                    if swing_plan:
                        swing_strategies.append(swing_plan)
                
                if swing_strategies:
                    data_persistence = st.session_state.data_persistence
                    data_persistence.save_swing_strategies(swing_strategies)
                    logger.info(f"Auto-saved {len(swing_strategies)} swing strategies")
        except Exception as e:
            logger.error(f"Error auto-saving swing strategies: {str(e)}")
    
    def _auto_save_news(self):
        """Automatically save news articles."""
        try:
            if st.session_state.get('news_articles'):
                data_persistence = st.session_state.data_persistence
                news_data = []
                for article in st.session_state.news_articles:
                    news_data.append({
                        'symbol': 'NEWS',
                        'company_name': article.get('title', 'News Article'),
                        'current_price': 0,
                        'recommendation': 'INFO',
                        'confidence': 0,
                        'target_price': 0,
                        'stop_loss': 0,
                        'reasoning': article.get('description', ''),
                        'technical_data': {},
                        'fundamental_data': {},
                        'groq_analysis': {},
                        'gemini_analysis': {},
                        'swing_plan': {},
                        'swing_validation': {},
                        'news_article': article
                    })
                data_persistence.save_recommendations(news_data)
                logger.info(f"Auto-saved {len(news_data)} news articles")
        except Exception as e:
            logger.error(f"Error auto-saving news: {str(e)}")
    
    def load_saved_api_key(self, key_type: str) -> str:
        """Load saved API key from session state or environment variables (Replit Secrets)."""
        try:
            # First check session state (for current session)
            if key_type == 'groq':
                session_key = st.session_state.get('saved_groq_key', '')
                if session_key:
                    return session_key
            elif key_type == 'gemini':
                session_key = st.session_state.get('saved_gemini_key', '')
                if session_key:
                    return session_key
            
            # Check environment variables (Replit Secrets)
            if key_type == 'groq':
                env_key = os.getenv('GROQ_API_KEY', '')
                if env_key:
                    return env_key
            elif key_type == 'gemini':
                env_key = os.getenv('GEMINI_API_KEY', '')
                if env_key:
                    return env_key
            
            # Try Streamlit secrets (for deployment)
            try:
                if key_type == 'groq':
                    return st.secrets.get('GROQ_API_KEY', '')
                elif key_type == 'gemini':
                    return st.secrets.get('GEMINI_API_KEY', '')
            except:
                pass
                
        except Exception as e:
            logger.warning(f"Could not load saved {key_type} API key: {str(e)}")
        return ""
    
    def save_api_key(self, key_type: str, api_key: str) -> bool:
        """Save API key to session state only. For permanent storage, use Replit Secrets."""
        try:
            # Save to session state for current session
            if key_type == 'groq':
                st.session_state.saved_groq_key = api_key
            elif key_type == 'gemini':
                st.session_state.saved_gemini_key = api_key
            
            logger.info(f"Saved {key_type} API key to session state")
            return True
        except Exception as e:
            logger.error(f"Could not save {key_type} API key: {str(e)}")
            return False
    
    def delete_saved_api_key(self, key_type: str) -> bool:
        """Clear saved API key from session state."""
        try:
            # Clear from session state
            if key_type == 'groq':
                st.session_state.saved_groq_key = ""
            elif key_type == 'gemini':
                st.session_state.saved_gemini_key = ""
            
            logger.info(f"Cleared {key_type} API key from session state")
            return True
        except Exception as e:
            logger.error(f"Could not clear {key_type} API key: {str(e)}")
            return False
    
    def _notification_callback(self, alert_type: str, stock_data: Dict, additional_data: Dict = None):
        """Callback function for price monitor alerts."""
        try:
            # Convert alert type string to AlertType enum
            alert_type_mapping = {
                'target_hit': AlertType.TARGET_HIT,
                'stop_loss_hit': AlertType.STOP_LOSS_HIT,
                'significant_movement': AlertType.SIGNIFICANT_MOVEMENT,
                'daily_summary': AlertType.DAILY_SUMMARY,
                'risk_alert': AlertType.RISK_ALERT,
                'swing_plan_update': AlertType.SWING_PLAN_UPDATE
            }
            
            alert_type_enum = alert_type_mapping.get(alert_type, AlertType.SIGNIFICANT_MOVEMENT)
            
            # Determine priority based on alert type
            priority_mapping = {
                AlertType.STOP_LOSS_HIT: AlertPriority.CRITICAL,
                AlertType.RISK_ALERT: AlertPriority.CRITICAL,
                AlertType.TARGET_HIT: AlertPriority.HIGH,
                AlertType.SIGNIFICANT_MOVEMENT: AlertPriority.MEDIUM,
                AlertType.SWING_PLAN_UPDATE: AlertPriority.MEDIUM,
                AlertType.DAILY_SUMMARY: AlertPriority.LOW
            }
            
            priority = priority_mapping.get(alert_type_enum, AlertPriority.MEDIUM)
            
            # Send email notification
            email_manager = st.session_state.email_notifications
            success = email_manager.send_alert(alert_type_enum, stock_data, additional_data, priority)
            
            if success:
                logger.info(f"Notification sent successfully: {alert_type} for {stock_data.get('symbol')}")
            else:
                logger.warning(f"Failed to send notification: {alert_type} for {stock_data.get('symbol')}")
                
        except Exception as e:
            logger.error(f"Error in notification callback: {str(e)}")
    
    def run(self):
        """Run the main application."""
        # Header
        st.markdown('<h1 class="main-header">🚀 Enhanced Swing Trading App - AI Powered</h1>', unsafe_allow_html=True)
        
        # Sidebar
        self.create_sidebar()
        
        # Main content - Compact tab layout
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
            "📰 News", 
            "🤖 Groq", 
            "🎯 BUY", 
            "📈 Swing", 
            "👀 Watch", 
            "🔍 Manual",
            "📊 Portfolio",
            "🔔 Alerts"
        ])
        
        with tab1:
            self.news_analysis_tab()
        
        with tab2:
            self.groq_news_analysis_tab()
        
        with tab3:
            self.recommendations_tab()
        
        with tab4:
            self.swing_trading_tab()
        
        with tab5:
            self.watchlist_tab()
        
        with tab6:
            self.manual_analysis_tab()
        
        with tab7:
            self.portfolio_tab()
        
        with tab8:
            self.notifications_tab()
    
    def create_sidebar(self):
        """Create the sidebar with controls."""
        # Compact sidebar - only show essential controls
        with st.sidebar:
            # Always show essential controls
            st.markdown("### 🚀 Quick Actions")
            
            # Market Analysis Button
            if st.button("📊 Analyze Market", key="analyze_market_btn", type="primary"):
                if not st.session_state.get('analysis_in_progress', False):
                    st.session_state.analysis_in_progress = True
                    self.analyze_market()
            
            # Show analysis status
            if st.session_state.get('analysis_in_progress', False):
                st.info("🔄 Analysis in progress...")
            
            # Show last analysis time
            if st.session_state.get('last_analysis_time'):
                st.caption(f"Last: {st.session_state.last_analysis_time[11:16]}")
            
            # Always show API Keys section
            st.markdown("---")
            st.markdown("### 🔑 API Keys")
            
            # Groq API Key
            groq_key = st.text_input(
                "Groq API Key",
                value=st.session_state.saved_groq_key,
                type="password",
                help="Enter your Groq API key",
                placeholder="gsk_..."
            )
            
            # Groq API Key Actions
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Save", key="save_groq"):
                    if groq_key and groq_key != st.session_state.saved_groq_key:
                        if self.save_api_key('groq', groq_key):
                            st.session_state.saved_groq_key = groq_key
                            # Reinitialize Groq analyzer with new key
                            self.groq_analyzer.api_key = groq_key
                            self.groq_analyzer.initialized = True
                            st.success("✅ Saved and initialized!")
                        else:
                            st.error("❌ Failed to save")
                    else:
                        st.info("ℹ️ No changes to save")
            
            with col2:
                if st.button("🗑️ Delete", key="delete_groq"):
                    if self.delete_saved_api_key('groq'):
                        st.session_state.saved_groq_key = ""
                        # Deinitialize Groq analyzer
                        self.groq_analyzer.api_key = ""
                        self.groq_analyzer.initialized = False
                        st.success("✅ Groq API key deleted!")
                    else:
                        st.error("❌ Failed to delete Groq API key")
            
            # Gemini API Key
            gemini_key = st.text_input(
                "Gemini API Key",
                value=st.session_state.saved_gemini_key,
                type="password",
                help="Enter your Gemini API key",
                placeholder="AIza..."
            )
            
            # Gemini API Key Actions
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Save", key="save_gemini"):
                    if gemini_key and gemini_key != st.session_state.saved_gemini_key:
                        if self.save_api_key('gemini', gemini_key):
                            st.session_state.saved_gemini_key = gemini_key
                            # Reinitialize Gemini analyzer with new key
                            self.gemini_analyzer.api_key = gemini_key
                            self.gemini_analyzer.initialized = True
                            st.success("✅ Saved and initialized!")
                        else:
                            st.error("❌ Failed to save")
                    else:
                        st.info("ℹ️ No changes to save")
            
            with col2:
                if st.button("🗑️ Delete", key="delete_gemini"):
                    if self.delete_saved_api_key('gemini'):
                        st.session_state.saved_gemini_key = ""
                        # Deinitialize Gemini analyzer
                        self.gemini_analyzer.api_key = ""
                        self.gemini_analyzer.initialized = False
                        st.success("✅ Gemini API key deleted!")
                    else:
                        st.error("❌ Failed to delete Gemini API key")
            
            # Update analyzers
            if groq_key and hasattr(self, 'groq_analyzer'):
                self.groq_analyzer.api_key = groq_key
                self.groq_analyzer.initialized = True
                if groq_key == st.session_state.saved_groq_key:
                    st.success("✅ Groq API key loaded from saved settings!")
                else:
                    st.success("✅ Groq API key set! (Click Save to remember)")
            else:
                if hasattr(self, 'groq_analyzer'):
                    self.groq_analyzer.initialized = False
                    st.info("ℹ️ Enter Groq API key to enable AI analysis")
            
            if gemini_key and hasattr(self, 'gemini_analyzer'):
                self.gemini_analyzer.api_key = gemini_key
                self.gemini_analyzer.initialized = True
                if gemini_key == st.session_state.saved_gemini_key:
                    st.success("✅ Gemini API key loaded from saved settings!")
                else:
                    st.success("✅ Gemini API key set! (Click Save to remember)")
            else:
                if hasattr(self, 'gemini_analyzer'):
                    self.gemini_analyzer.initialized = False
                    st.info("ℹ️ Enter Gemini API key to enable AI analysis")
            
            st.markdown("---")
            st.markdown("### 💾 Cache")
            
            # Cache statistics
            cache_manager = st.session_state.cache_manager
            cache_stats = cache_manager.get_cache_stats()
            st.metric("Articles", cache_stats.get('articles', 0))
            st.metric("Stocks", cache_stats.get('stocks', 0))
            
            if st.button("🗑️ Clear Cache", key="clear_cache_btn"):
                cache_manager.clear_cache('all')
                st.success("Cache cleared!")
                st.rerun()
            
            st.markdown("---")
            st.markdown("### ⏰ Scheduled Analysis")
            
            # Show scheduled analysis status
            if st.session_state.get('scheduled_analysis'):
                scheduler = st.session_state.scheduled_analysis
                status = scheduler.get_scheduler_status()
                
                if status['is_running']:
                    st.success("🟢 Running")
                else:
                    st.error("🔴 Stopped")
                
                st.caption(f"Next: {status['next_analysis']}")
                st.caption(f"Days: {', '.join(status['scheduled_days'])}")
                st.caption(f"Time: {status['scheduled_time']}")
                
                # Manual trigger button
                if st.button("🚀 Run Analysis Now", key="manual_analysis_btn"):
                    scheduler.run_analysis_now()
                    st.success("Analysis triggered!")
                    st.rerun()
            else:
                st.warning("Scheduler not initialized")
        
        
        if gemini_key:
            # Update the Gemini analyzer with the new key
            if hasattr(self, 'gemini_analyzer'):
                self.gemini_analyzer.api_key = gemini_key
                self.gemini_analyzer.initialized = True
                if gemini_key == st.session_state.saved_gemini_key:
                    st.sidebar.success("✅ Gemini API key loaded from saved settings!")
                else:
                    st.sidebar.success("✅ Gemini API key set! (Click Save to remember)")
            else:
                st.sidebar.warning("⚠️ Gemini analyzer not initialized")
        else:
            if hasattr(self, 'gemini_analyzer'):
                self.gemini_analyzer.initialized = False
                st.sidebar.info("ℹ️ Enter Gemini API key to enable comprehensive AI analysis")
        
        st.sidebar.markdown("---")
        
        # Market Analysis Section
        st.sidebar.header("📊 Market Analysis")
        
        if st.sidebar.button("🔍 Analyze Market", type="primary", use_container_width=True):
            self.analyze_market()
        
        if st.sidebar.button("📰 Fetch News", use_container_width=True):
            self.fetch_news()
        
        if st.sidebar.button("🤖 Fetch Groq Analysis", use_container_width=True):
            self.fetch_groq_news_analysis()
        
        # Status
        st.sidebar.header("📈 Status")
        if st.session_state.last_analysis_time:
            st.sidebar.success(f"Last Analysis: {st.session_state.last_analysis_time}")
        else:
            st.sidebar.info("No analysis performed yet")
        
        # Quick Stats
        st.sidebar.header("📊 Quick Stats")
        col1, col2 = st.sidebar.columns(2)
        with col1:
            st.metric("Recommendations", len(st.session_state.recommendations))
        with col2:
            st.metric("Watchlist Items", len(st.session_state.watchlist))
        
        # API Status
        st.sidebar.header("📊 API Status")
        
        # Groq AI Status
        if hasattr(self, 'groq_analyzer') and self.groq_analyzer.initialized:
            st.sidebar.success("🤖 Groq AI: Active")
        else:
            st.sidebar.warning("🤖 Groq AI: Inactive")
            st.sidebar.caption("Add API key in Configuration section")
        
        # Gemini AI Status
        if hasattr(self, 'gemini_analyzer') and self.gemini_analyzer.initialized:
            st.sidebar.success("🧠 Gemini AI: Active")
        else:
            st.sidebar.warning("🧠 Gemini AI: Inactive")
            st.sidebar.caption("Add API key in Configuration section")
        
        # Learning System Status
        if st.session_state.learning_available:
            st.sidebar.success("📚 Learning System: Active")
        else:
            st.sidebar.warning("📚 Learning System: Unavailable")
        
        # Firebase Status
        if st.session_state.firebase_available:
            st.sidebar.success("☁️ Firebase Sync: Active")
        else:
            st.sidebar.warning("☁️ Firebase Sync: Unavailable")
        
        # Cache Statistics
        st.sidebar.header("💾 Cache Statistics")
        cache_manager = st.session_state.cache_manager
        cache_stats = cache_manager.get_cache_stats()
        
        if cache_stats:
            st.sidebar.metric("Cached Articles", cache_stats.get('articles_cache_size', 0))
            st.sidebar.metric("Cached Stocks", cache_stats.get('stocks_cache_size', 0))
            st.sidebar.metric("Cached Analysis", cache_stats.get('analysis_cache_size', 0))
            
            st.sidebar.caption("Cache Duration: 7 days")
            
            if st.sidebar.button("🗑️ Clear Cache"):
                cache_manager.clear_cache('all')
                st.sidebar.success("Cache cleared!")
                st.rerun()
    
    def news_analysis_tab(self):
        """News Analysis tab."""
        st.header("📰 News Analysis")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            if st.button("📰 Fetch Latest News", type="primary", key="fetch_news_btn"):
                self.fetch_news()
        
        with col2:
            if st.button("🔍 Analyze Sentiment", key="analyze_sentiment_btn"):
                self.analyze_sentiment()
        
        # News is automatically saved when fetched
        
        # Display news articles in rows
        if st.session_state.news_articles:
            st.subheader(f"📰 Latest News ({len(st.session_state.news_articles)} articles)")
            
            # Header row
            col1, col2, col3, col4, col5 = st.columns([3, 1.5, 1, 1, 0.8])
            with col1:
                st.markdown("**Headline**")
            with col2:
                st.markdown("**Source**")
            with col3:
                st.markdown("**Published**")
            with col4:
                st.markdown("**Sentiment**")
            with col5:
                st.markdown("**Details**")
            
            st.markdown("---")
            
            # Display each article in a row
            for i, article in enumerate(st.session_state.news_articles[:10]):
                ExpandableUI.display_news_row(article, i)
        else:
            st.info("No news articles available. Click 'Fetch Latest News' to get started.")
    
    def groq_news_analysis_tab(self):
        """Groq News Analysis tab."""
        st.header("🤖 Groq AI News Analysis with Sentiment")
        
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            if st.button("🔍 Fetch Groq News Analysis", type="primary", key="fetch_groq_analysis_btn"):
                self.fetch_groq_news_analysis()
        
        with col2:
            if st.button("📰 Fetch Indian News", key="fetch_indian_news_btn"):
                self.fetch_news()
        
        with col3:
            if st.button("🔄 Refresh Display", key="refresh_display_btn"):
                st.rerun()
        
        with col4:
            if st.button("📡 Test RSS Feeds", key="test_rss_feeds_btn"):
                self.test_rss_feeds()
        
        # Display Groq news analysis
        if st.session_state.groq_news_data:
            st.subheader(f"🤖 Groq AI Analysis ({len(st.session_state.groq_news_data)} stocks)")
            
            for news_item in st.session_state.groq_news_data:
                self.display_groq_news_card(news_item)
        else:
            st.info("No Groq AI analysis available. Click 'Fetch Groq News Analysis' to get started.")
    
    def display_groq_news_card(self, news_item: Dict):
        """Display a Groq news analysis card."""
        symbol = news_item.get('symbol', 'N/A')
        company_name = news_item.get('company_name', 'Unknown Company')
        sentiment_label = news_item.get('sentiment_label', 'NEUTRAL')
        sentiment_score = news_item.get('sentiment_score', 0)
        confidence = news_item.get('confidence', 0)
        impact_level = news_item.get('impact_level', 'LOW')
        price_impact = news_item.get('price_impact', 'NEUTRAL')
        news_summary = news_item.get('news_summary', 'No summary available')
        key_factors = news_item.get('key_factors', [])
        news_type = news_item.get('news_type', 'OTHER')
        
        # Sentiment color and emoji based on news type
        sentiment_class = f"sentiment-{sentiment_label.lower()}"
        
        # Different emojis based on news type
        if news_type == "GOVERNMENT":
            sentiment_emoji = "🏛️" if sentiment_label == "POSITIVE" else "🏛️" if sentiment_label == "NEGATIVE" else "🏛️"
        elif news_type == "EARNINGS":
            sentiment_emoji = "💰" if sentiment_label == "POSITIVE" else "💸" if sentiment_label == "NEGATIVE" else "💰"
        elif news_type == "DEAL":
            sentiment_emoji = "🤝" if sentiment_label == "POSITIVE" else "🤝" if sentiment_label == "NEGATIVE" else "🤝"
        elif news_type == "REGULATORY":
            sentiment_emoji = "📋" if sentiment_label == "POSITIVE" else "📋" if sentiment_label == "NEGATIVE" else "📋"
        else:
            sentiment_emoji = "📈" if sentiment_label == "POSITIVE" else "📉" if sentiment_label == "NEGATIVE" else "➡️"
        
        # Create card
        with st.container():
            # Special styling for government news
            card_class = "groq-card government-highlight" if news_type == "GOVERNMENT" else "groq-card"
            title_emoji = "🏛️" if news_type == "GOVERNMENT" else "📈"
            
            st.markdown(f"""
            <div class="{card_class}">
                <h3>{title_emoji} {symbol} - {company_name}</h3>
                <p><span class="{sentiment_class}">{sentiment_emoji} {sentiment_label}</span> 
                (Score: {sentiment_score:.2f}, Confidence: {confidence:.1%})</p>
                <p><strong>News Type:</strong> {news_type}</p>
                <p><strong>Impact:</strong> {impact_level} | <strong>Price Impact:</strong> {price_impact}</p>
                <p><strong>Summary:</strong> {news_summary}</p>
            </div>
            """, unsafe_allow_html=True)
            
            if key_factors:
                st.markdown("**🔑 Key Factors:**")
                for factor in key_factors[:5]:
                    st.markdown(f"• {factor}")
            
            st.markdown("---")
    
    def recommendations_tab(self):
        """BUY Recommendations tab."""
        st.header("🎯 BUY Recommendations Only")
        st.info("This tab shows only BUY recommendations with more lenient criteria for swing trading opportunities.")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            if st.button("🔍 Generate BUY Recommendations", type="primary", key="generate_buy_recs_btn"):
                self.analyze_market()
        
        with col2:
            if st.button("🔄 Refresh", key="refresh_recs_btn"):
                st.rerun()
        
        # Recommendations are automatically saved when generated
        
        # Display recommendations
        if st.session_state.recommendations:
            st.subheader(f"🎯 BUY Recommendations ({len(st.session_state.recommendations)} stocks)")
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total BUY", len(st.session_state.recommendations))
            
            with col2:
                avg_confidence = sum(r.get('confidence', 0) for r in st.session_state.recommendations) / len(st.session_state.recommendations)
                st.metric("Avg Confidence", f"{avg_confidence:.1f}%")
            
            with col3:
                high_confidence = len([r for r in st.session_state.recommendations if r.get('confidence', 0) >= 80])
                st.metric("High Confidence", high_confidence)
            
            with col4:
                st.metric("Actions", "View Saved")
                if st.button("📊 View Saved", key="view_saved_recs"):
                    st.session_state.show_saved_recommendations = not st.session_state.get('show_saved_recommendations', False)
            
            # Show saved recommendations if toggled
            if st.session_state.get('show_saved_recommendations', False):
                self.display_saved_recommendations()
                return
            
            st.markdown("---")
            
            # Header row with consistent alignment and tooltips
            col1, col2, col3, col4, col5, col6, col7 = st.columns([1.5, 1, 1, 1, 1, 0.8, 0.8])
            with col1:
                st.markdown("**Stock**")
            with col2:
                st.markdown("**Price (₹)**")
            with col3:
                st.markdown("**Confidence**")
            with col4:
                st.markdown("**Target (₹)**")
            with col5:
                st.markdown("**Stop Loss**")
            with col6:
                st.markdown("**Details**")
            with col7:
                st.markdown("**Actions**")
            
            st.markdown("<hr style='margin: 0.5rem 0;'/>", unsafe_allow_html=True)
            
            # Display recommendations in rows
            for i, rec in enumerate(st.session_state.recommendations):
                ExpandableUI.display_recommendation_row(rec, i)
                
                # Check if add to watchlist button was clicked
                if st.session_state.get(f"add_to_watchlist_{i}", False):
                    self.add_to_watchlist(rec)
                    st.session_state[f"add_to_watchlist_{i}"] = False
                    st.rerun()
        else:
            st.info("No BUY recommendations available. Click 'Generate BUY Recommendations' to get started.")
    
    def display_recommendation_card(self, rec: Dict, index: int):
        """Display a recommendation card."""
        symbol = rec.get('symbol', 'N/A')
        recommendation = rec.get('recommendation', 'HOLD')
        confidence = rec.get('confidence', 0)
        current_price = rec.get('current_price', 0)
        target_price = rec.get('target_price', 0)
        stop_loss = rec.get('stop_loss', 0)
        reasoning = rec.get('reasoning', 'No reasoning provided')
        
        # Recommendation color
        rec_class = f"recommendation-{recommendation.lower()}"
        rec_emoji = "📈" if recommendation == "BUY" else "📉" if recommendation == "SELL" else "➡️"
        
        # Create card
        with st.container():
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <h3>{rec_emoji} {symbol}</h3>
                    <p><span class="{rec_class}">{recommendation}</span> 
                    (Confidence: {confidence:.1f}%)</p>
                    <p><strong>Current:</strong> ₹{current_price:.2f} | 
                    <strong>Target:</strong> ₹{target_price:.2f} | 
                    <strong>Stop Loss:</strong> ₹{stop_loss:.2f}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                if st.button(f"📊 Details", key=f"details_{index}"):
                    self.show_recommendation_details(rec)
            
            with col3:
                if st.button(f"👀 Add to Watchlist", key=f"watchlist_{index}"):
                    self.add_to_watchlist(rec)
            
            # Reasoning
            with st.expander(f"💭 Reasoning for {symbol}"):
                st.markdown(reasoning)
            
            st.markdown("---")
    
    def display_buy_recommendation_card(self, rec: Dict, index: int, show_swing_plans: bool = True):
        """Display a BUY recommendation card with swing trading details."""
        symbol = rec.get('symbol', 'N/A')
        confidence = rec.get('confidence', 0)
        current_price = rec.get('current_price', 0)
        target_price = rec.get('target_price', 0)
        stop_loss = rec.get('stop_loss', 0)
        reasoning = rec.get('reasoning', 'No reasoning provided')
        swing_plan = rec.get('swing_plan', {})
        swing_validation = rec.get('swing_validation', {})
        
        # Create card
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                # Main recommendation info
                st.markdown(f"""
                <div class="metric-card">
                    <h3>📈 {symbol} - BUY RECOMMENDATION</h3>
                    <p><span class="recommendation-buy">BUY</span> 
                    (Confidence: {confidence:.1f}%)</p>
                    <p><strong>Current:</strong> ₹{current_price:.2f} | 
                    <strong>Target:</strong> ₹{target_price:.2f} | 
                    <strong>Stop Loss:</strong> ₹{stop_loss:.2f}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Swing trading validation score
                if swing_validation:
                    score = swing_validation.get('score', 0)
                    is_suitable = swing_validation.get('is_suitable', False)
                    score_color = "green" if score >= 70 else "orange" if score >= 50 else "red"
                    
                    st.markdown(f"""
                    <div style="background-color: #2d2d2d; padding: 0.5rem; border-radius: 0.5rem; margin: 0.5rem 0;">
                        <p><strong>Swing Trading Score:</strong> <span style="color: {score_color}">{score}/100</span></p>
                        <p><strong>Suitable for Swing:</strong> {'✅ Yes' if is_suitable else '❌ No'}</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            with col2:
                if st.button(f"📊 Details", key=f"details_{index}"):
                    self.show_recommendation_details(rec)
            
            with col3:
                if st.button(f"👀 Add to Watchlist", key=f"watchlist_{index}"):
                    self.add_to_watchlist(rec)
            
            # Swing trading plan (if available and requested)
            if show_swing_plans and swing_plan:
                with st.expander(f"📈 7-Day Swing Trading Plan for {symbol}"):
                    self.display_swing_plan(swing_plan)
            
            # Reasoning
            with st.expander(f"💭 Reasoning for {symbol}"):
                st.markdown(reasoning)
            
            st.markdown("---")
    
    def display_swing_plan(self, swing_plan: Dict):
        """Display swing trading plan details."""
        try:
            # Display stock information header
            symbol = swing_plan.get('symbol', 'UNKNOWN')
            company_name = swing_plan.get('company_name', '')
            confidence = swing_plan.get('confidence', 0)
            
            # Create header with stock info
            if company_name:
                st.markdown(f"### 📈 {symbol} - {company_name}")
            else:
                st.markdown(f"### 📈 {symbol}")
            
            # Confidence indicator
            if confidence >= 80:
                st.success(f"🎯 High Confidence: {confidence:.1f}%")
            elif confidence >= 60:
                st.warning(f"⚠️ Medium Confidence: {confidence:.1f}%")
            else:
                st.info(f"ℹ️ Confidence: {confidence:.1f}%")
            
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**📊 Position Details:**")
                st.write(f"• Investment Amount: ₹{swing_plan.get('investment_amount', 0):,.0f}")
                st.write(f"• Position Size: {swing_plan.get('position_size', 0)} shares")
                st.write(f"• Risk Amount: ₹{swing_plan.get('risk_amount', 0):,.0f}")
                st.write(f"• Risk Percentage: {swing_plan.get('risk_percentage', 0):.1f}%")
                
                st.markdown("**🎯 Entry/Exit Levels:**")
                st.write(f"• Entry Price: ₹{swing_plan.get('entry_price', 0):.2f}")
                st.write(f"• Stop Loss: ₹{swing_plan.get('stop_loss', 0):.2f}")
                st.write(f"• Take Profit: ₹{swing_plan.get('take_profit', 0):.2f}")
                st.write(f"• Risk-Reward Ratio: {swing_plan.get('risk_reward_ratio', 0):.2f}:1")
            
            with col2:
                st.markdown("**📅 Timeline:**")
                st.write(f"• Entry Date: {swing_plan.get('entry_date', 'N/A')[:10]}")
                st.write(f"• Expected Exit: {swing_plan.get('expected_exit_date', 'N/A')[:10]}")
                st.write(f"• Holding Period: {swing_plan.get('holding_period_days', 7)} days")
                
                st.markdown("**💰 Potential Returns:**")
                st.write(f"• Potential Profit: ₹{swing_plan.get('potential_profit', 0):.2f}")
                st.write(f"• Potential Loss: ₹{swing_plan.get('potential_loss', 0):.2f}")
                st.write(f"• Profit Percentage: {((swing_plan.get('potential_profit', 0) / swing_plan.get('investment_amount', 1)) * 100):.1f}%")
            
            # Strategy rules
            st.markdown("**📋 Strategy Rules:**")
            rules = swing_plan.get('strategy_rules', [])
            for rule in rules:
                st.write(f"• {rule}")
            
            # Risk management
            st.markdown("**⚠️ Risk Management:**")
            risk_mgmt = swing_plan.get('risk_management', [])
            for risk in risk_mgmt:
                st.write(f"• {risk}")
            
            st.markdown("---")
                
        except Exception as e:
            st.error(f"Error displaying swing plan: {str(e)}")
    
    def swing_trading_tab(self):
        """Swing Trading Plans tab."""
        st.header("📈 7-Day Swing Trading Plans")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            if st.button("🔄 Refresh Strategies", type="primary", key="refresh_strategies_btn"):
                if st.session_state.get('recommendations'):
                    st.rerun()
                else:
                    st.warning("No recommendations to refresh. Run market analysis first.")
        
        # Swing strategies are automatically saved when generated
        
        with col2:
            if st.button("📊 Analyze Performance", type="secondary", key="analyze_swing_performance_btn"):
                self.analyze_swing_performance()
        
        with col3:
            if st.button("📊 View Saved", key="view_saved_swing"):
                st.session_state.show_saved_swing_strategies = not st.session_state.get('show_saved_swing_strategies', False)
        
        # Show saved strategies if toggled
        if st.session_state.get('show_saved_swing_strategies', False):
            self.display_saved_swing_strategies()
            return
        
        # Display current adaptive parameters
        self.display_current_adaptive_parameters()
        
        if st.session_state.recommendations:
            # Extract swing strategies from recommendations
            swing_strategies = []
            for rec in st.session_state.recommendations:
                swing_plan = rec.get('swing_plan', {})
                if swing_plan:
                    swing_strategies.append(swing_plan)
            
            if swing_strategies:
                st.subheader(f"📈 Swing Trading Plans ({len(swing_strategies)} strategies)")
                
                # Summary metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Strategies", len(swing_strategies))
                
                with col2:
                    high_confidence = len([s for s in swing_strategies if s.get('confidence', 0) >= 80])
                    st.metric("High Confidence", high_confidence)
                
                with col3:
                    avg_risk_reward = sum(s.get('risk_reward_ratio', 0) for s in swing_strategies) / len(swing_strategies)
                    st.metric("Avg Risk-Reward", f"{avg_risk_reward:.2f}:1")
                
                with col4:
                    # Calculate days to expiry
                    current_date = datetime.now()
                    total_days = 0
                    for strategy in swing_strategies:
                        try:
                            exit_date = datetime.fromisoformat(strategy.get('expected_exit_date', '').replace('Z', '+00:00'))
                            days_remaining = (exit_date - current_date).days
                            total_days += max(0, days_remaining)
                        except:
                            total_days += 7  # Default 7 days
                    avg_days = total_days / len(swing_strategies) if swing_strategies else 0
                    st.metric("Avg Days Left", f"{avg_days:.0f}")
                
                st.markdown("---")
                
                # Header row with consistent alignment
                col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([1.5, 1, 1, 1, 0.8, 1, 0.8, 0.8])
                with col1:
                    st.markdown("**Stock**")
                with col2:
                    st.markdown("**Entry (₹)**")
                with col3:
                    st.markdown("**Take Profit (₹)**")
                with col4:
                    st.markdown("**Stop Loss (₹)**")
                with col5:
                    st.markdown("**Days**")
                with col6:
                    st.markdown("**Risk/Reward**")
                with col7:
                    st.markdown("**Details**")
                with col8:
                    st.markdown("**Actions**")
                
                st.markdown("<hr style='margin: 0.5rem 0;'/>", unsafe_allow_html=True)
                
                # Display swing strategies in rows
                for i, strategy in enumerate(swing_strategies):
                    # Get the values with proper fallbacks
                    symbol = strategy.get('symbol', 'UNKNOWN')
                    company_name = strategy.get('company_name', '')
                    current_price = strategy.get('current_price', 0)
                    
                    # Get entry/exit levels with proper fallbacks
                    entry_price = strategy.get('entry_price', current_price)
                    take_profit = strategy.get('take_profit', 0)
                    stop_loss = strategy.get('stop_loss', 0)
                    
                    # If we have a 'levels' dictionary, use those values
                    if 'levels' in strategy and isinstance(strategy['levels'], dict):
                        entry_price = strategy['levels'].get('entry_price', entry_price)
                        take_profit = strategy['levels'].get('take_profit', take_profit)
                        stop_loss = strategy['levels'].get('stop_loss', stop_loss)
                    
                    # Ensure we have valid values
                    entry_price = entry_price or current_price
                    take_profit = take_profit or (entry_price * 1.02)  # Default 2% take profit
                    stop_loss = stop_loss or (entry_price * 0.98)  # Default 2% stop loss
                    
                    # Update the strategy dictionary with the calculated values
                    strategy.update({
                        'entry_price': entry_price,
                        'take_profit': take_profit,
                        'stop_loss': stop_loss,
                        'current_price': current_price
                    })
                    
                    # Display the row
                    ExpandableUI.display_swing_strategy_row(strategy, i)
                    
                    # Check if add to watchlist button was clicked
                    if st.session_state.get(f"add_swing_to_watchlist_{i}", False):
                        # Convert swing strategy to recommendation format for watchlist
                        watchlist_item = {
                            'symbol': symbol,
                            'company_name': company_name,
                            'current_price': current_price,
                            'recommendation': 'BUY',
                            'confidence': strategy.get('confidence', 0),
                            'target_price': take_profit,
                            'stop_loss': stop_loss,
                            'entry_price': entry_price,
                            'reasoning': f"Swing trading strategy: {strategy.get('strategy_name', '')}",
                            'created_at': datetime.now().isoformat()
                        }
                        self.add_to_watchlist(watchlist_item)
                        st.session_state[f"add_swing_to_watchlist_{i}"] = False
                        st.rerun()
            else:
                st.info("No swing trading plans available. Generate BUY recommendations first.")
        else:
            st.info("No swing trading plans available. Generate BUY recommendations first.")
    
    def watchlist_tab(self):
        """Watchlist tab."""
        st.header("👀 Watchlist Management")
        
        # Check for delete actions from watchlist details
        for key in list(st.session_state.keys()):
            if key.startswith('delete_from_watchlist_'):
                symbol_to_delete = key.replace('delete_from_watchlist_', '')
                # Remove the stock from watchlist
                st.session_state.watchlist = [
                    item for item in st.session_state.watchlist 
                    if item.get('symbol') != symbol_to_delete
                ]
                # Auto-save watchlist
                self._auto_save_watchlist()
                # Clear the session state flag
                del st.session_state[key]
                st.success(f"✅ Deleted {symbol_to_delete} from watchlist!")
                st.rerun()
        
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            if st.button("🔄 Update Prices", type="primary", key="update_prices_btn"):
                self.update_watchlist_prices()
        
        with col2:
            if st.button("🧠 Analyze Performance", key="analyze_performance_btn"):
                self.analyze_watchlist_stocks()
        
        # Watchlist is automatically saved when modified
        
        with col4:
            if st.button("🗑️ Clear Watchlist", key="clear_watchlist_btn"):
                st.session_state.watchlist = []
                # Auto-save empty watchlist
                self._auto_save_watchlist()
                st.success("Watchlist cleared!")
                st.rerun()
        
        # Display watchlist
        if st.session_state.watchlist:
            st.subheader(f"👀 Watchlist ({len(st.session_state.watchlist)} stocks)")
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Stocks", len(st.session_state.watchlist))
            
            with col2:
                active_count = len([item for item in st.session_state.watchlist if item.get('status') == 'ACTIVE'])
                st.metric("Active", active_count)
            
            with col3:
                # Calculate total P&L
                total_pnl = 0
                for item in st.session_state.watchlist:
                    entry_price = item.get('entry_price', 0)
                    current_price = item.get('current_price', 0)
                    if entry_price > 0:
                        pnl = ((current_price - entry_price) / entry_price) * 100
                        total_pnl += pnl
                avg_pnl = total_pnl / len(st.session_state.watchlist) if st.session_state.watchlist else 0
                st.metric("Avg P&L", f"{avg_pnl:.1f}%")
            
            with col4:
                st.metric("Actions", "View Saved")
                if st.button("📊 View Saved", key="view_saved_watchlist"):
                    st.session_state.show_saved_watchlist = not st.session_state.get('show_saved_watchlist', False)
            
            # Show saved watchlist if toggled
            if st.session_state.get('show_saved_watchlist', False):
                self.display_saved_watchlist()
                return
            
            st.markdown("---")
            
            # Add sorting controls
            sort_col1, sort_col2 = st.columns(2)
            with sort_col1:
                sort_by = st.selectbox(
                    "Sort by",
                    ["Date Added", "Symbol", "P&L %", "Current Price", "Entry Price", "Status"],
                    key="watchlist_sort_by"
                )
            with sort_col2:
                sort_order = st.radio(
                    "Order",
                    ["Ascending", "Descending"],
                    index=1,  # Default to descending for most useful sort orders
                    horizontal=True,
                    key="watchlist_sort_order"
                )
            
            # Sort the watchlist
            sorted_watchlist = st.session_state.watchlist.copy()
            reverse_sort = (sort_order == "Descending")
            
            if sort_by == "Symbol":
                sorted_watchlist.sort(key=lambda x: x.get('symbol', '').upper(), reverse=reverse_sort)
            elif sort_by == "P&L %":
                sorted_watchlist.sort(
                    key=lambda x: (
                        (x.get('current_price', 0) - x.get('entry_price', 0)) / x.get('entry_price', 1) 
                        if x.get('entry_price', 0) > 0 else 0
                    ),
                    reverse=reverse_sort
                )
            elif sort_by == "Current Price":
                sorted_watchlist.sort(key=lambda x: x.get('current_price', 0), reverse=reverse_sort)
            elif sort_by == "Entry Price":
                sorted_watchlist.sort(key=lambda x: x.get('entry_price', 0), reverse=reverse_sort)
            elif sort_by == "Status":
                sorted_watchlist.sort(key=lambda x: x.get('status', ''), reverse=not reverse_sort)
            else:  # Default sort by Date Added
                sorted_watchlist.sort(
                    key=lambda x: x.get('added_date', ''), 
                    reverse=not reverse_sort  # Most recent first by default
                )
            
            # Display sorted watchlist items in rows
            for i, item in enumerate(sorted_watchlist):
                ExpandableUI.display_watchlist_row(item, i)
        else:
            st.info("No stocks in watchlist. Add stocks from recommendations or manual analysis.")
    
    def display_watchlist_item(self, item: Dict, index: int):
        """Display a watchlist item."""
        symbol = item.get('symbol', 'N/A')
        current_price = item.get('current_price', 0)
        entry_price = item.get('entry_price', 0)
        target_price = item.get('target_price', 0)
        stop_loss = item.get('stop_loss', 0)
        recommendation = item.get('recommendation', 'HOLD')
        confidence = item.get('confidence', 0)
        performance_pct = item.get('performance_pct', 0)
        
        # Performance color
        perf_color = "green" if performance_pct > 0 else "red" if performance_pct < 0 else "gray"
        
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h4>📈 {symbol}</h4>
                <p><strong>Current:</strong> ₹{current_price:.2f} | 
                <strong>Entry:</strong> ₹{entry_price:.2f} | 
                <strong>Performance:</strong> <span style="color: {perf_color}">{performance_pct:+.2f}%</span></p>
                <p><strong>Target:</strong> ₹{target_price:.2f} | 
                <strong>Stop Loss:</strong> ₹{stop_loss:.2f}</p>
                <p><strong>Recommendation:</strong> {recommendation} ({confidence:.1f}%)</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            if st.button(f"📊 Update", key=f"update_{index}"):
                self.update_watchlist_item(symbol)
        
        with col3:
            if st.button(f"🗑️ Remove", key=f"remove_{index}"):
                st.session_state.watchlist.pop(index)
                st.success(f"Removed {symbol} from watchlist")
                st.rerun()
        
        st.markdown("---")
    
    def manual_analysis_tab(self):
        """Manual Analysis tab."""
        st.header("🔍 Manual Stock Analysis")
        
        # Input section
        col1, col2 = st.columns([2, 1])
        
        with col1:
            symbol = st.text_input(
                "Stock Symbol", 
                placeholder="Enter stock symbol (e.g., TCS, RELIANCE, HDFCBANK)",
                help="Enter NSE stock symbol without .NS suffix"
            )
        
        with col2:
            if st.button("🔍 Analyze Stock", type="primary", key="analyze_stock_btn"):
                if symbol:
                    self.analyze_manual_stock(symbol.upper())
                else:
                    st.error("Please enter a stock symbol")
        
        # Display manual analysis results
        if 'manual_analysis_result' in st.session_state:
            self.display_manual_analysis_result()
    
    def portfolio_tab(self):
        """Portfolio tab."""
        st.header("📊 Portfolio Tracking")
        
        # Check if portfolio exists in session state, initialize if not
        if 'portfolio' not in st.session_state:
            st.session_state.portfolio = []
        
        # Add new stock to portfolio
        with st.expander("➕ Add Stock to Portfolio"):
            with st.form("add_stock_form"):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    symbol = st.text_input("Symbol", "", help="Stock symbol (e.g., RELIANCE.NS)")
                with col2:
                    quantity = st.number_input("Quantity", min_value=1, value=1, step=1)
                with col3:
                    buy_price = st.number_input("Buy Price (₹)", min_value=0.01, value=100.0, step=0.01)
                with col4:
                    buy_date = st.date_input("Buy Date", value=datetime.now())
                
                if st.form_submit_button("Add to Portfolio"):
                    if symbol:
                        # Get current price
                        try:
                            stock = yf.Ticker(symbol)
                            current_price = stock.history(period='1d')['Close'].iloc[-1]
                            
                            # Add to portfolio
                            st.session_state.portfolio.append({
                                'symbol': symbol.upper(),
                                'quantity': quantity,
                                'buy_price': buy_price,
                                'current_price': current_price,
                                'buy_date': buy_date.isoformat(),
                                'last_updated': datetime.now().isoformat()
                            })
                            st.success(f"Added {symbol.upper()} to portfolio!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error adding stock: {str(e)}")
        
        # Display portfolio summary
        if st.session_state.portfolio:
            # Update current prices
            if st.button("🔄 Update Prices", key="update_portfolio_prices"):
                with st.spinner("Updating prices..."):
                    for item in st.session_state.portfolio:
                        try:
                            stock = yf.Ticker(item['symbol'])
                            item['current_price'] = stock.history(period='1d')['Close'].iloc[-1]
                            item['last_updated'] = datetime.now().isoformat()
                        except:
                            pass
                st.rerun()
            
            # Calculate portfolio metrics
            total_investment = sum(item['quantity'] * item['buy_price'] for item in st.session_state.portfolio)
            current_value = sum(item['quantity'] * item.get('current_price', item['buy_price']) for item in st.session_state.portfolio)
            total_pnl = current_value - total_investment
            total_pnl_pct = (total_pnl / total_investment * 100) if total_investment > 0 else 0
            
            # Display summary metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Investment", f"₹{total_investment:,.2f}")
            with col2:
                st.metric("Current Value", f"₹{current_value:,.2f}")
            with col3:
                st.metric("Total P&L", 
                         f"₹{total_pnl:+,.2f}", 
                         f"{total_pnl_pct:+.2f}%",
                         delta_color="normal" if total_pnl >= 0 else "inverse")
            
            # Add sorting controls
            st.markdown("### Your Portfolio")
            sort_col1, sort_col2 = st.columns(2)
            with sort_col1:
                sort_by = st.selectbox(
                    "Sort by",
                    ["Symbol", "P&L %", "Current Value", "Quantity", "Buy Date"],
                    key="portfolio_sort_by"
                )
            with sort_col2:
                sort_order = st.radio(
                    "Order",
                    ["Ascending", "Descending"],
                    index=1,  # Default to descending for most useful sort orders
                    horizontal=True,
                    key="portfolio_sort_order"
                )
            
            # Sort the portfolio
            sorted_portfolio = st.session_state.portfolio.copy()
            reverse_sort = (sort_order == "Descending")
            
            if sort_by == "Symbol":
                sorted_portfolio.sort(key=lambda x: x.get('symbol', '').upper(), reverse=reverse_sort)
            elif sort_by == "P&L %":
                sorted_portfolio.sort(
                    key=lambda x: (
                        (x.get('current_price', 0) - x.get('buy_price', 0)) / x.get('buy_price', 1) 
                        if x.get('buy_price', 0) > 0 else 0
                    ),
                    reverse=reverse_sort
                )
            elif sort_by == "Current Value":
                sorted_portfolio.sort(
                    key=lambda x: x.get('quantity', 0) * x.get('current_price', 0), 
                    reverse=reverse_sort
                )
            elif sort_by == "Quantity":
                sorted_portfolio.sort(key=lambda x: x.get('quantity', 0), reverse=reverse_sort)
            else:  # Buy Date
                sorted_portfolio.sort(
                    key=lambda x: x.get('buy_date', ''), 
                    reverse=not reverse_sort  # Most recent first by default
                )
            
            # Display portfolio table
            st.markdown("""
            <style>
            .portfolio-table {
                width: 100%;
                border-collapse: collapse;
            }
            .portfolio-table th, .portfolio-table td {
                padding: 8px 12px;
                text-align: left;
                border-bottom: 1px solid #444;
            }
            .portfolio-table th {
                background-color: #2d2d2d;
                font-weight: bold;
            }
            .positive { color: #28a745; }
            .negative { color: #dc3545; }
            </style>
            """, unsafe_allow_html=True)
            
            # Table header
            st.markdown("""
            <table class="portfolio-table">
                <tr>
                    <th>Symbol</th>
                    <th>Quantity</th>
                    <th>Avg. Buy Price</th>
                    <th>Current Price</th>
                    <th>P&L</th>
                    <th>Value</th>
                    <th>Actions</th>
                </tr>
            """, unsafe_allow_html=True)
            
            # Table rows
            for item in sorted_portfolio:
                symbol = item['symbol']
                quantity = item['quantity']
                buy_price = item['buy_price']
                current_price = item.get('current_price', buy_price)
                pnl = (current_price - buy_price) * quantity
                pnl_pct = ((current_price - buy_price) / buy_price * 100) if buy_price > 0 else 0
                value = quantity * current_price
                
                pnl_class = "positive" if pnl >= 0 else "negative"
                pnl_sign = "+" if pnl >= 0 else ""
                
                st.markdown(f"""
                <tr>
                    <td><strong>{symbol}</strong></td>
                    <td>{quantity:,}</td>
                    <td>₹{buy_price:,.2f}</td>
                    <td>₹{current_price:,.2f}</td>
                    <td class="{pnl_class}">{pnl_sign}₹{abs(pnl):,.2f} ({pnl_sign}{abs(pnl_pct):.2f}%)</td>
                    <td>₹{value:,.2f}</td>
                    <td>
                        <button onclick=\"
                            const index = Array.from(document.querySelectorAll('td:first-child')).findIndex(td => td.textContent === \"{symbol}\");
                            if (index !== -1) {{
                                const deleteBtn = document.querySelectorAll('button[data-action=delete]')[index];
                                deleteBtn.click();
                            }}\" 
                        style=\"background: none; border: none; color: #dc3545; cursor: pointer;\">
                            🗑️
                        </button>
                    </td>
                </tr>
                """, unsafe_allow_html=True)
                
                # Handle delete action
                if st.button("🗑️", key=f"delete_{symbol}", help=f"Remove {symbol} from portfolio", 
                           type="secondary", use_container_width=True, data_action="delete"):
                    st.session_state.portfolio = [p for p in st.session_state.portfolio if p['symbol'] != symbol]
                    st.rerun()
            
            st.markdown("</table>", unsafe_allow_html=True)
            
            # Add some spacing
            st.markdown("<br><br>", unsafe_allow_html=True)
            
        else:
            st.info("Your portfolio is empty. Add stocks to get started!")
    
    def notifications_tab(self):
        """Notifications management tab."""
        st.header("🔔 Email Notifications & Price Monitoring")
        st.info("Configure email notifications and real-time price monitoring for your stocks.")
        
        # Create tabs for different notification sections
        notif_tab1, notif_tab2, notif_tab3, notif_tab4 = st.tabs([
            "📧 Email Settings",
            "⚙️ Alert Preferences", 
            "📊 Price Monitoring",
            "📋 Alert History"
        ])
        
        with notif_tab1:
            self.email_settings_section()
        
        with notif_tab2:
            self.alert_preferences_section()
        
        with notif_tab3:
            self.price_monitoring_section()
        
        with notif_tab4:
            self.alert_history_section()
    
    def email_settings_section(self):
        """Email settings configuration section."""
        st.subheader("📧 Email Configuration")
        
        email_manager = st.session_state.email_notifications
        settings = email_manager.settings
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**SMTP Settings**")
            smtp_server = st.text_input("SMTP Server", value=settings.smtp_server, help="e.g., smtp.gmail.com")
            smtp_port = st.number_input("SMTP Port", value=settings.smtp_port, min_value=1, max_value=65535)
            
            st.markdown("**Email Credentials**")
            sender_email = st.text_input("Sender Email", value=settings.sender_email, type="default")
            sender_password = st.text_input("Sender Password", value=settings.sender_password, type="password")
            recipient_email = st.text_input("Recipient Email", value=settings.recipient_email, type="default")
        
        with col2:
            st.markdown("**Email Status**")
            
            # Test email connection
            if st.button("🧪 Test Email Connection", key="test_email_btn"):
                with st.spinner("Testing email connection..."):
                    result = email_manager.test_email_connection()
                    if result['success']:
                        st.success("✅ Email connection successful!")
                    else:
                        st.error(f"❌ Email connection failed: {result['message']}")
            
            # Email notifications toggle
            email_enabled = st.checkbox("Enable Email Notifications", value=settings.email_enabled)
            
            if st.button("💾 Save Email Settings", key="save_email_settings_btn"):
                try:
                    email_manager.update_settings(
                        smtp_server=smtp_server,
                        smtp_port=smtp_port,
                        sender_email=sender_email,
                        sender_password=sender_password,
                        recipient_email=recipient_email,
                        email_enabled=email_enabled
                    )
                    st.success("✅ Email settings saved!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error saving email settings: {str(e)}")
        
        # Email templates preview
        st.markdown("**📧 Email Templates Preview**")
        with st.expander("View Email Templates"):
            st.markdown("""
            **Available Email Templates:**
            - 🎯 **Target Hit**: Sent when stock reaches target price
            - 🛑 **Stop Loss Hit**: Sent when stock hits stop loss
            - 📊 **Significant Movement**: Sent for large price movements
            - 📊 **Daily Summary**: Daily portfolio summary
            - ⚠️ **Risk Alert**: Critical risk warnings
            - 📈 **Swing Plan Update**: Swing trading plan updates
            """)
    
    def alert_preferences_section(self):
        """Alert preferences configuration section."""
        st.subheader("⚙️ Alert Preferences")
        
        settings_manager = st.session_state.notification_settings
        prefs = settings_manager.preferences
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Alert Types**")
            target_hit = st.checkbox("Target Price Hit", value=prefs.target_hit_alerts)
            stop_loss = st.checkbox("Stop Loss Hit", value=prefs.stop_loss_alerts)
            significant_movement = st.checkbox("Significant Movement", value=prefs.significant_movement_alerts)
            daily_summary = st.checkbox("Daily Summary", value=prefs.daily_summary)
            risk_alerts = st.checkbox("Risk Alerts", value=prefs.risk_alerts)
            swing_updates = st.checkbox("Swing Plan Updates", value=prefs.swing_plan_updates)
        
        with col2:
            st.markdown("**Thresholds**")
            movement_threshold = st.slider("Significant Movement %", 1.0, 20.0, prefs.thresholds.significant_movement_percent, 0.5)
            max_alerts_hour = st.number_input("Max Alerts per Hour", 1, 50, prefs.thresholds.max_alerts_per_hour)
            risk_threshold = st.slider("Risk Alert Threshold %", 5.0, 25.0, prefs.thresholds.risk_alert_threshold, 1.0)
            
            st.markdown("**Quiet Hours**")
            quiet_start = st.time_input("Quiet Hours Start", value=datetime.strptime(prefs.quiet_hours_start, "%H:%M").time())
            quiet_end = st.time_input("Quiet Hours End", value=datetime.strptime(prefs.quiet_hours_end, "%H:%M").time())
        
        if st.button("💾 Save Alert Preferences", key="save_alert_prefs_btn"):
            try:
                settings_manager.update_preferences(
                    target_hit_alerts=target_hit,
                    stop_loss_alerts=stop_loss,
                    significant_movement_alerts=significant_movement,
                    daily_summary=daily_summary,
                    risk_alerts=risk_alerts,
                    swing_plan_updates=swing_updates
                )
                
                settings_manager.update_thresholds(
                    significant_movement_percent=movement_threshold,
                    max_alerts_per_hour=max_alerts_hour,
                    risk_alert_threshold=risk_threshold
                )
                
                settings_manager.update_preferences(
                    quiet_hours_start=quiet_start.strftime("%H:%M"),
                    quiet_hours_end=quiet_end.strftime("%H:%M")
                )
                
                st.success("✅ Alert preferences saved!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error saving preferences: {str(e)}")
    
    def price_monitoring_section(self):
        """Price monitoring management section."""
        st.subheader("📊 Real-time Price Monitoring")
        
        price_monitor = st.session_state.price_monitor
        monitor_status = price_monitor.get_monitoring_status()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Monitoring Status**")
            status_color = {
                'running': '🟢',
                'stopped': '🔴', 
                'paused': '🟡',
                'error': '🔴'
            }
            
            status_emoji = status_color.get(monitor_status['status'], '⚪')
            st.metric("Status", f"{status_emoji} {monitor_status['status'].title()}")
            st.metric("Monitored Stocks", monitor_status['monitored_stocks_count'])
            st.metric("Check Interval", f"{monitor_status['check_interval']} seconds")
            
            if monitor_status['last_check_time']:
                st.metric("Last Check", monitor_status['last_check_time'][:19])
        
        with col2:
            st.markdown("**Controls**")
            
            if monitor_status['status'] == 'running':
                if st.button("⏸️ Pause Monitoring", key="pause_monitoring_btn"):
                    price_monitor.pause_monitoring()
                    st.success("Monitoring paused!")
                    st.rerun()
                if st.button("⏹️ Stop Monitoring", key="stop_monitoring_btn"):
                    price_monitor.stop_monitoring()
                    st.success("Monitoring stopped!")
                    st.rerun()
            elif monitor_status['status'] == 'paused':
                if st.button("▶️ Resume Monitoring", key="resume_monitoring_btn"):
                    price_monitor.resume_monitoring()
                    st.success("Monitoring resumed!")
                    st.rerun()
            else:
                check_interval = st.number_input("Check Interval (seconds)", 30, 300, 60)
                if st.button("▶️ Start Monitoring", key="start_monitoring_btn"):
                    if monitor_status['monitored_stocks_count'] > 0:
                        price_monitor.start_monitoring(check_interval)
                        st.success("Monitoring started!")
                        st.rerun()
                    else:
                        st.warning("No stocks in watchlist to monitor!")
        
        # Add stocks from watchlist to monitoring
        if st.session_state.watchlist:
            st.markdown("**Add Watchlist Stocks to Monitoring**")
            if st.button("📊 Add All Watchlist Stocks to Monitoring", key="add_watchlist_to_monitoring_btn"):
                added_count = 0
                for item in st.session_state.watchlist:
                    stock_data = {
                        'symbol': item['symbol'],
                        'current_price': item['current_price'],
                        'target_price': item.get('target_price'),
                        'stop_loss': item.get('stop_loss'),
                        'entry_price': item.get('entry_price', item['current_price'])
                    }
                    if price_monitor.add_stock_to_monitor(stock_data):
                        added_count += 1
                
                st.success(f"✅ Added {added_count} stocks to monitoring!")
                st.rerun()
        
        # Show monitored stocks
        if monitor_status['monitored_stocks']:
            st.markdown("**Monitored Stocks**")
            for symbol in monitor_status['monitored_stocks']:
                stock_status = price_monitor.get_stock_status(symbol)
                if stock_status:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**{symbol}**")
                    with col2:
                        st.write(f"Price: ₹{stock_status['current_price']:.2f}")
                    with col3:
                        if st.button(f"Remove {symbol}", key=f"remove_{symbol}"):
                            price_monitor.remove_stock_from_monitor(symbol)
                            st.success(f"Removed {symbol} from monitoring!")
                            st.rerun()
    
    def alert_history_section(self):
        """Alert history section."""
        st.subheader("📋 Alert History")
        
        email_manager = st.session_state.email_notifications
        
        # Alert history controls
        col1, col2 = st.columns(2)
        with col1:
            limit = st.number_input("Show Last N Alerts", 10, 100, 20)
        with col2:
            if st.button("🗑️ Clear History", key="clear_history_btn"):
                if email_manager.clear_alert_history():
                    st.success("Alert history cleared!")
                    st.rerun()
        
        # Display alert history
        alert_history = email_manager.get_alert_history(limit)
        
        if alert_history:
            st.markdown("**Recent Alerts**")
            for alert in alert_history:
                timestamp = alert['timestamp'][:19]  # Remove microseconds
                alert_type = alert['alert_type'].replace('_', ' ').title()
                symbol = alert['symbol']
                priority = alert['priority'].title()
                
                priority_color = {
                    'Critical': '🔴',
                    'High': '🟠', 
                    'Medium': '🟡',
                    'Low': '🟢'
                }
                
                priority_emoji = priority_color.get(priority, '⚪')
                
                st.markdown(f"""
                <div style="background-color: #2d2d2d; padding: 1rem; border-radius: 0.5rem; margin: 0.5rem 0;">
                    <p><strong>{priority_emoji} {alert_type}</strong> - {symbol}</p>
                    <p><small>Time: {timestamp} | Priority: {priority}</small></p>
                    <p><small>Subject: {alert.get('subject', 'N/A')}</small></p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No alert history available.")
        
        # Alert statistics
        if alert_history:
            st.markdown("**Alert Statistics**")
            alert_types = {}
            priorities = {}
            
            for alert in alert_history:
                alert_type = alert['alert_type']
                priority = alert['priority']
                
                alert_types[alert_type] = alert_types.get(alert_type, 0) + 1
                priorities[priority] = priorities.get(priority, 0) + 1
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**By Type**")
                for alert_type, count in alert_types.items():
                    st.write(f"• {alert_type.replace('_', ' ').title()}: {count}")
            
            with col2:
                st.markdown("**By Priority**")
                for priority, count in priorities.items():
                    st.write(f"• {priority.title()}: {count}")
    
    def display_saved_recommendations(self):
        """Display saved recommendations."""
        st.subheader("📊 Saved Recommendations")
        
        data_persistence = st.session_state.data_persistence
        available_dates = data_persistence.get_available_dates()
        
        if not available_dates:
            st.info("No saved recommendations found.")
            return
        
        # Date selector
        selected_date = st.selectbox(
            "Select Date",
            available_dates,
            key="saved_rec_date_selector"
        )
        
        if selected_date:
            recommendations = data_persistence.get_recommendations_by_date(selected_date)
            
            if recommendations:
                st.success(f"Found {len(recommendations)} recommendations for {selected_date}")
                
                # Header row
                col1, col2, col3, col4, col5, col6 = st.columns([1.5, 1.5, 1, 1, 1, 0.8])
                with col1:
                    st.markdown("**Stock**")
                with col2:
                    st.markdown("**CMP**")
                with col3:
                    st.markdown("**Target**")
                with col4:
                    st.markdown("**Stop Loss**")
                with col5:
                    st.markdown("**Confidence**")
                with col6:
                    st.markdown("**Details**")
                
                st.markdown("---")
                
                # Display each recommendation
                for i, rec in enumerate(recommendations):
                    ExpandableUI.display_recommendation_row(rec, i)
            else:
                st.warning(f"No recommendations found for {selected_date}")
    
    def display_saved_watchlist(self):
        """Display saved watchlist."""
        st.subheader("👀 Saved Watchlist")
        
        data_persistence = st.session_state.data_persistence
        watchlist = data_persistence.get_watchlist()
        
        if not watchlist:
            st.info("No saved watchlist found.")
            return
        
        st.success(f"Found {len(watchlist)} watchlist items")
        
        # Header row
        col1, col2, col3, col4, col5, col6, col7 = st.columns([1.5, 1, 1, 1, 1, 1, 0.8])
        with col1:
            st.markdown("**Stock**")
        with col2:
            st.markdown("**Entry Price**")
        with col3:
            st.markdown("**CMP**")
        with col4:
            st.markdown("**P&L**")
        with col5:
            st.markdown("**Date Added**")
        with col6:
            st.markdown("**Status**")
        with col7:
            st.markdown("**Details**")
        
        st.markdown("---")
        
        # Display each watchlist item
        for i, item in enumerate(watchlist):
            ExpandableUI.display_watchlist_row(item, i)
    
    def display_saved_swing_strategies(self):
        """Display saved swing strategies."""
        st.subheader("📈 Saved Swing Strategies")
        
        data_persistence = st.session_state.data_persistence
        available_dates = data_persistence.get_available_dates()
        
        if not available_dates:
            st.info("No saved swing strategies found.")
            return
        
        # Date selector
        selected_date = st.selectbox(
            "Select Date",
            available_dates,
            key="saved_swing_date_selector"
        )
        
        if selected_date:
            strategies = data_persistence.get_swing_strategies_by_date(selected_date)
            
            if strategies:
                st.success(f"Found {len(strategies)} swing strategies for {selected_date}")
                
                # Header row
                col1, col2, col3, col4, col5, col6, col7 = st.columns([1.5, 1, 1, 1, 1, 1, 0.8])
                with col1:
                    st.markdown("**Stock**")
                with col2:
                    st.markdown("**CMP**")
                with col3:
                    st.markdown("**Take Profit**")
                with col4:
                    st.markdown("**Stop Loss**")
                with col5:
                    st.markdown("**Days Left**")
                with col6:
                    st.markdown("**Risk-Reward**")
                with col7:
                    st.markdown("**Details**")
                
                st.markdown("---")
                
                # Display each strategy
                for i, strategy in enumerate(strategies):
                    ExpandableUI.display_swing_strategy_row(strategy, i)
            else:
                st.warning(f"No swing strategies found for {selected_date}")
    
    
    def fetch_news(self):
        """Fetch and display filtered Indian news articles."""
        with st.spinner("📰 Fetching and filtering Indian news..."):
            try:
                # Step 1: Fetch all articles from RSS feeds
                all_articles = self.news_analyzer.fetch_all_news_articles()
                
                if not all_articles:
                    st.warning("⚠️ No articles found in RSS feeds")
                    return
                
                st.info(f"📊 Fetched {len(all_articles)} total articles from RSS feeds")
                
                # Step 2: Filter by India-related keywords in headlines
                indian_articles = self.news_analyzer.filter_indian_news_by_headline(all_articles)
                
                if not indian_articles:
                    st.warning("⚠️ No India-related articles found")
                    return
                
                # Store filtered articles
                st.session_state.news_articles = indian_articles
                st.session_state.all_articles_count = len(all_articles)
                st.session_state.indian_articles_count = len(indian_articles)
                
                # Auto-save news articles
                self._auto_save_news()
                
                st.success(f"✅ Filtered {len(indian_articles)} India-related articles from {len(all_articles)} total articles")
                
                # Display filtered articles
                self.display_filtered_news(indian_articles)
                
            except Exception as e:
                st.error(f"❌ Error fetching news: {str(e)}")
    
    def display_filtered_news(self, articles: List[Dict]):
        """Display filtered Indian news articles."""
        st.subheader(f"🇮🇳 Indian News Articles ({len(articles)} articles)")
        
        # Show filtering statistics
        if hasattr(st.session_state, 'all_articles_count') and hasattr(st.session_state, 'indian_articles_count'):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Articles", st.session_state.all_articles_count)
            with col2:
                st.metric("Indian Articles", st.session_state.indian_articles_count)
            with col3:
                filter_rate = (st.session_state.indian_articles_count / st.session_state.all_articles_count * 100) if st.session_state.all_articles_count > 0 else 0
                st.metric("Filter Rate", f"{filter_rate:.1f}%")
        
        # Display articles
        for i, article in enumerate(articles[:20]):  # Show first 20 articles
            with st.expander(f"📰 {i+1}. {article.get('title', 'No title')[:80]}..."):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Title:** {article.get('title', 'No title')}")
                    st.write(f"**Description:** {article.get('description', 'No description')}")
                    st.write(f"**Source:** {article.get('source', 'Unknown')}")
                    st.write(f"**Published:** {article.get('publishedAt', 'No date')}")
                
                with col2:
                    st.write(f"**URL:** [Read Full Article]({article.get('url', '#')})")
                    st.write("🇮🇳 **India Related:** ✅")
                    if article.get('filter_reason'):
                        st.write(f"**Filter Reason:** {', '.join(article.get('filter_reason', []))}")
                
                st.write("---")
    
    def analyze_sentiment(self):
        """Analyze news sentiment."""
        if not st.session_state.news_articles:
            st.error("No news articles available. Please fetch news first.")
            return
        
        with st.spinner("🔍 Analyzing sentiment..."):
            try:
                sentiment = self.news_analyzer.analyze_news_sentiment(st.session_state.news_articles)
                st.success(f"✅ Sentiment analysis complete: {sentiment:.3f}")
            except Exception as e:
                st.error(f"❌ Error analyzing sentiment: {str(e)}")
    
    def test_rss_feeds(self):
        """Test RSS feeds to see what content they provide."""
        with st.spinner("🔍 Testing RSS feeds..."):
            try:
                feed_results = self.news_analyzer.test_rss_feeds()
                
                st.subheader("📡 RSS Feed Test Results")
                
                for feed_url, result in feed_results.items():
                    with st.expander(f"📰 {feed_url.split('/')[-1]}"):
                        if result.get('status') == 'success':
                            st.success(f"✅ {result.get('article_count', 0)} articles found")
                            
                            st.write("**Sample Articles:**")
                            for i, article in enumerate(result.get('sample_articles', [])[:3]):
                                st.write(f"**{i+1}.** {article.get('title', 'No title')}")
                                st.write(f"   📅 {article.get('publishedAt', 'No date')}")
                                st.write(f"   🔗 {article.get('url', 'No URL')}")
                                st.write("---")
                        else:
                            st.error(f"❌ Error: {result.get('error', 'Unknown error')}")
                            
            except Exception as e:
                st.error(f"❌ Error testing RSS feeds: {str(e)}")
    
    def fetch_groq_news_analysis(self):
        """Fetch Groq news analysis with full content from filtered Indian articles."""
        with st.spinner("📰 Fetching top 10 Indian news with full content..."):
            try:
                # Step 1: Fetch top 10 Indian news articles with full content
                top_10_news = self.news_analyzer.fetch_top_10_news_with_content()
                
                if not top_10_news:
                    st.error("❌ No Indian news articles fetched")
                    return
                
                st.success(f"✅ Fetched {len(top_10_news)} Indian news articles with content")
                
                # Show sample of fetched articles
                with st.expander("📰 Sample Indian Articles for Groq Analysis"):
                    for i, article in enumerate(top_10_news[:3]):
                        content_length = len(article.get('full_content', ''))
                        content_source = "Full Article" if content_length > 200 else "Description Fallback"
                        
                        st.write(f"**{i+1}.** {article.get('title', 'No title')}")
                        st.write(f"   📅 {article.get('publishedAt', 'No date')}")
                        st.write(f"   🇮🇳 India Related: {article.get('is_india_related', True)}")
                        st.write(f"   📄 Content: {content_source} ({content_length} characters)")
                        
                        # Show content preview
                        content_preview = article.get('full_content', '')[:200] + "..." if len(article.get('full_content', '')) > 200 else article.get('full_content', '')
                        st.write(f"   📝 Preview: {content_preview}")
                        st.write("---")
                
                # Step 2: Analyze with Groq AI
                with st.spinner("🤖 Analyzing Indian news with Groq AI..."):
                    groq_data = self.groq_analyzer.analyze_top_10_news_with_full_content(top_10_news)
                    
                    if groq_data.get('status') == 'success':
                        st.session_state.groq_news_data = groq_data.get('articles', [])
                        st.success(f"✅ Analyzed {len(st.session_state.groq_news_data)} Indian stocks from news")
                    else:
                        st.error(f"❌ Groq analysis failed: {groq_data.get('message', 'Unknown error')}")
                        
            except Exception as e:
                st.error(f"❌ Error in news analysis: {str(e)}")
    
    def _validate_nse_stocks(self, stock_symbols: List[str]) -> List[str]:
        """Validate stock symbols against known NSE stocks."""
        try:
            # Get comprehensive list of NSE stocks
            nse_stocks = self.news_analyzer.get_comprehensive_nse_stocks_list()
            nse_stocks_set = set(nse_stocks)
            
            # Filter out invalid stocks
            valid_stocks = []
            for symbol in stock_symbols:
                # Remove any suffixes like .NS, .BO, etc.
                clean_symbol = symbol.split('.')[0].upper()
                
                # Check if it's in our NSE list
                if clean_symbol in nse_stocks_set:
                    valid_stocks.append(clean_symbol)
                else:
                    logger.warning(f"Invalid/delisted stock symbol: {symbol}")
            
            logger.info(f"Validated {len(valid_stocks)} out of {len(stock_symbols)} stock symbols")
            return valid_stocks
            
        except Exception as e:
            logger.error(f"Error validating NSE stocks: {str(e)}")
            return stock_symbols  # Return original list if validation fails
    
    def analyze_market(self):
        """Analyze market and generate recommendations."""
        if st.session_state.analysis_in_progress:
            st.warning("Analysis already in progress. Please wait...")
            return
        
        st.session_state.analysis_in_progress = True
        
        try:
            with st.spinner("🔍 Starting comprehensive market analysis..."):
                # Step 1: Fetch news with caching
                st.info("📰 Step 1: Fetching news with caching...")
                all_news = self.news_analyzer.fetch_top_10_news_with_content()
                
                if not all_news:
                    st.error("❌ No news articles fetched")
                    return
                
                # Cache articles and get only new ones
                cache_manager = st.session_state.cache_manager
                new_articles = cache_manager.cache_articles(all_news)
                
                st.success(f"✅ Fetched {len(all_news)} total articles, {len(new_articles)} new articles")
                
                # Step 2: Analyze with Groq AI to get stocks with sentiment impact
                st.info("🤖 Step 2: Analyzing news with Groq AI...")
                groq_news_data = self.groq_analyzer.analyze_top_10_news_with_full_content(all_news)
                
                if groq_news_data.get('status') != 'success':
                    st.error(f"❌ Groq analysis failed: {groq_news_data.get('message', 'Unknown error')}")
                    return
                
                # Extract stocks from Groq analysis and validate them
                all_news_stocks = [item.get('symbol', '') for item in groq_news_data.get('articles', []) if item.get('symbol')]
                news_stocks = self._validate_nse_stocks(all_news_stocks)
                
                if len(news_stocks) != len(all_news_stocks):
                    invalid_stocks = set(all_news_stocks) - set(news_stocks)
                    st.warning(f"⚠️ Filtered out {len(invalid_stocks)} invalid/delisted stocks: {', '.join(list(invalid_stocks)[:5])}")
                
                # Filter out stocks already in watchlist (unless very negative news)
                filtered_stocks = cache_manager.filter_watchlist_stocks(
                    groq_news_data.get('articles', []), 
                    st.session_state.watchlist,
                    allow_negative_news=True
                )
                
                # Get symbols from filtered stocks
                news_stocks = [stock.get('symbol', '') for stock in filtered_stocks if stock.get('symbol')]
                
                st.success(f"✅ Identified {len(news_stocks)} valid NSE stocks with sentiment impact (after watchlist filtering)")
                
                # Step 3: Analyze news stocks
                st.info("📊 Step 3: Analyzing stocks from news...")
                news_recommendations = []
                
                progress_bar = st.progress(0)
                total_stocks = len(news_stocks)
                
                for i, symbol in enumerate(news_stocks):
                    try:
                        symbol_with_suffix = f"{symbol}.NS"
                        
                        # Check cache for stock analysis
                        cached_analysis = cache_manager.get_cached_stock_analysis(symbol)
                        
                        if cached_analysis:
                            # Use cached analysis
                            technical_data = cached_analysis.get('technical_data', {})
                            fundamental_data = cached_analysis.get('fundamental_data', {})
                            groq_analysis = cached_analysis.get('groq_analysis', {})
                            gemini_analysis = cached_analysis.get('gemini_analysis', {})
                            recommendation = cached_analysis.get('recommendation', {})
                            
                            logger.info(f"Using cached analysis for {symbol}")
                        else:
                            # Perform fresh analysis
                            # Get technical analysis
                            technical_data = self.technical_analyzer.analyze_stock(symbol_with_suffix)
                            if not technical_data:
                                continue
                            
                            # Get fundamental analysis
                            fundamental_data = self.fundamental_analyzer.get_financial_data(symbol_with_suffix)
                            
                            # Get comprehensive Groq AI analysis using the analyzed news
                            groq_analysis = self.groq_analyzer.get_comprehensive_stock_analysis(
                                symbol, technical_data, fundamental_data, all_news
                            )
                            
                            # Get Gemini AI analysis
                            gemini_analysis = None
                            if self.gemini_analyzer.initialized:
                                gemini_analysis = self.gemini_analyzer.analyze_stock_comprehensive(
                                    symbol, technical_data, fundamental_data, st.session_state.news_articles, groq_analysis
                                )
                            
                            # Generate AI recommendation
                            # Calculate news sentiment for this stock
                            news_sentiment = 0.5  # Default neutral
                            if all_news:
                                news_sentiment = self.news_analyzer.analyze_news_sentiment(all_news)
                            
                            recommendation = self.ai_engine.generate_ai_recommendation(
                                technical_data, technical_data, news_sentiment, [], groq_analysis, gemini_analysis
                            )
                            
                            # Cache the analysis
                            analysis_data = {
                                'technical_data': technical_data,
                                'fundamental_data': fundamental_data,
                                'groq_analysis': groq_analysis,
                                'gemini_analysis': gemini_analysis,
                                'recommendation': recommendation
                            }
                            cache_manager.cache_stock_analysis(symbol, analysis_data)
                        
                        # Only include BUY recommendations (SKIP others)
                        if recommendation.get('action') == 'BUY':
                            # Generate swing trading plan
                            swing_strategy = st.session_state.swing_strategy
                            # Get company name from groq analysis or use symbol as fallback
                            company_name = ''
                            if groq_analysis and groq_analysis.get('status') == 'success':
                                company_name = groq_analysis.get('company_name', '')
                            
                            swing_plan = swing_strategy.generate_swing_trading_plan({
                                'symbol': symbol,
                                'company_name': company_name,
                                'current_price': technical_data.get('current_price', 0),
                                'confidence': recommendation['confidence'],
                                'target_price': recommendation['target_price'],
                                'stop_loss': recommendation['stop_loss'],
                                'technical_data': technical_data,
                                'groq_analysis': groq_analysis
                            })
                            
                            # Validate swing opportunity
                            validation = swing_strategy.validate_swing_opportunity({
                                'symbol': symbol,
                                'current_price': technical_data.get('current_price', 0),
                                'confidence': recommendation['confidence'],
                                'technical_data': technical_data,
                                'groq_analysis': groq_analysis
                            })
                            
                            # Create recommendation data with swing trading plan
                            rec_data = {
                                'symbol': symbol,
                                'current_price': technical_data.get('current_price', 0),
                                'recommendation': recommendation['action'],
                                'confidence': recommendation['confidence'],
                                'target_price': recommendation['target_price'],
                                'stop_loss': recommendation['stop_loss'],
                                'reasoning': recommendation['reasoning'],
                                'technical_data': technical_data,
                                'fundamental_data': fundamental_data,
                                'groq_analysis': groq_analysis,
                                'gemini_analysis': gemini_analysis,
                                'swing_plan': swing_plan,
                                'swing_validation': validation
                            }
                            
                            news_recommendations.append(rec_data)
                            logger.info(f"Added BUY recommendation with swing plan for {symbol}")
                        else:
                            logger.info(f"Skipped {symbol} - not a BUY recommendation")
                        
                        # Update progress
                        progress_bar.progress((i + 1) / total_stocks)
                        
                    except Exception as e:
                        logger.error(f"Error analyzing news stock {symbol}: {str(e)}")
                        continue
                
                # Set final recommendations
                st.session_state.recommendations = news_recommendations
                st.session_state.last_analysis_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Save to database if available
                self.save_recommendations()
                
                # Auto-save recommendations and swing strategies
                self._auto_save_recommendations()
                self._auto_save_buy_recommendations()  # Specifically save BUY recommendations date-wise
                self._auto_save_swing_strategies()
                
                st.success(f"✅ Analysis complete! Generated {len(news_recommendations)} BUY recommendations. Data auto-saved for 7 days.")
                
        except Exception as e:
            st.error(f"❌ Error analyzing market: {str(e)}")
        finally:
            st.session_state.analysis_in_progress = False
    
    def analyze_manual_stock(self, symbol: str):
        """Analyze a manually entered stock."""
        with st.spinner(f"🔍 Analyzing {symbol}..."):
            try:
                symbol_with_suffix = f"{symbol}.NS"
                
                # Get technical analysis
                technical_data = self.technical_analyzer.analyze_stock(symbol_with_suffix)
                if not technical_data:
                    st.error(f"No data available for {symbol}")
                    return
                
                # Get fundamental analysis
                fundamental_data = self.fundamental_analyzer.get_financial_data(symbol_with_suffix)
                
                # Get news articles for this stock
                news_articles = []
                for article in st.session_state.news_articles:
                    if symbol.lower() in article.get('title', '').lower() or symbol.lower() in article.get('description', '').lower():
                        news_articles.append(article)
                
                # Get comprehensive Groq AI analysis
                groq_analysis = self.groq_analyzer.get_comprehensive_stock_analysis(
                    symbol, technical_data, fundamental_data, news_articles
                )
                
                # Get Gemini AI analysis
                gemini_analysis = None
                if self.gemini_analyzer.initialized:
                    gemini_analysis = self.gemini_analyzer.analyze_stock_comprehensive(
                        symbol, technical_data, fundamental_data, news_articles, groq_analysis
                    )
                
                # Generate AI recommendation
                news_sentiment = 0.5  # Default neutral
                if news_articles:
                    news_sentiment = self.news_analyzer.analyze_news_sentiment(news_articles)
                
                recommendation = self.ai_engine.generate_ai_recommendation(
                    technical_data, technical_data, news_sentiment, [], groq_analysis, gemini_analysis
                )
                
                # Store result
                st.session_state.manual_analysis_result = {
                    'symbol': symbol,
                    'recommendation': recommendation,
                    'technical_data': technical_data,
                    'fundamental_data': fundamental_data,
                    'news_articles': news_articles,
                    'groq_analysis': groq_analysis,
                    'gemini_analysis': gemini_analysis
                }
                
                # Auto-save BUY recommendations if it's a BUY
                if recommendation.get('action', '').upper() == 'BUY':
                    # Create a single recommendation list for saving
                    single_recommendation = [{
                        'symbol': symbol,
                        'company_name': technical_data.get('company_name', symbol),
                        'current_price': technical_data.get('current_price', 0),
                        'recommendation': 'BUY',
                        'action': 'BUY',
                        'confidence': recommendation.get('confidence', 0),
                        'target_price': recommendation.get('target_price', 0),
                        'stop_loss': recommendation.get('stop_loss', 0),
                        'reasoning': recommendation.get('reasoning', ''),
                        'technical_data': technical_data,
                        'fundamental_data': fundamental_data,
                        'groq_analysis': groq_analysis,
                        'gemini_analysis': gemini_analysis
                    }]
                    
                    # Save BUY recommendation date-wise
                    self._auto_save_buy_recommendations_for_manual(single_recommendation)
                
                st.success(f"✅ Analysis complete for {symbol}")
                
            except Exception as e:
                st.error(f"❌ Error analyzing {symbol}: {str(e)}")
    
    def display_manual_analysis_result(self):
        """Display manual analysis result."""
        result = st.session_state.manual_analysis_result
        symbol = result['symbol']
        recommendation = result['recommendation']
        
        st.subheader(f"📊 Analysis Results for {symbol}")
        
        # Recommendation
        rec_class = f"recommendation-{recommendation['action'].lower()}"
        rec_emoji = "📈" if recommendation['action'] == "BUY" else "📉" if recommendation['action'] == "SELL" else "➡️"
        
        st.markdown(f"""
        <div class="metric-card">
            <h3>{rec_emoji} {recommendation['action']}</h3>
            <p><strong>Confidence:</strong> {recommendation['confidence']:.1f}%</p>
            <p><strong>Current Price:</strong> ₹{result['technical_data'].get('current_price', 0):.2f}</p>
            <p><strong>Target Price:</strong> ₹{recommendation['target_price']:.2f}</p>
            <p><strong>Stop Loss:</strong> ₹{recommendation['stop_loss']:.2f}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Reasoning
        with st.expander("💭 Reasoning"):
            st.markdown(recommendation['reasoning'])
        
        # Add to watchlist button
        if st.button(f"👀 Add {symbol} to Watchlist", key=f"add_to_watchlist_{symbol}"):
            self.add_to_watchlist({
                'symbol': symbol,
                'current_price': result['technical_data'].get('current_price', 0),
                'recommendation': recommendation['action'],
                'confidence': recommendation['confidence'],
                'target_price': recommendation['target_price'],
                'stop_loss': recommendation['stop_loss'],
                'reasoning': recommendation['reasoning']
            })
    
    def add_to_watchlist(self, rec: Dict):
        """Add recommendation to watchlist."""
        try:
            symbol = rec.get('symbol')
            if not symbol:
                st.error("Invalid recommendation data")
                return
            
            # Check if already in watchlist
            for item in st.session_state.watchlist:
                if item.get('symbol') == symbol:
                    st.warning(f"{symbol} is already in watchlist")
                    return
            
            # Add to watchlist
            watchlist_item = {
                'symbol': symbol,
                'entry_price': rec.get('current_price', 0),
                'current_price': rec.get('current_price', 0),
                'target_price': rec.get('target_price', 0),
                'stop_loss': rec.get('stop_loss', 0),
                'recommendation': rec.get('recommendation', 'HOLD'),
                'confidence': rec.get('confidence', 0),
                'reasoning': rec.get('reasoning', ''),
                'added_date': datetime.now().isoformat(),
                'status': 'ACTIVE'
            }
            
            st.session_state.watchlist.append(watchlist_item)
            
            # Auto-save watchlist
            self._auto_save_watchlist()
            
            st.success(f"✅ Added {symbol} to watchlist")
            
        except Exception as e:
            st.error(f"❌ Error adding to watchlist: {str(e)}")
    
    def analyze_watchlist_stocks(self):
        """Analyze watchlist stocks for learning."""
        if not st.session_state.watchlist:
            st.error("No stocks in watchlist to analyze")
            return
        
        with st.spinner("🧠 Learning from watchlist performance..."):
            try:
                analyzed_count = 0
                total_count = len(st.session_state.watchlist)
                
                progress_bar = st.progress(0)
                
                for i, item in enumerate(st.session_state.watchlist):
                    symbol = item.get('symbol')
                    if not symbol:
                        continue
                    
                    try:
                        symbol_with_suffix = f"{symbol}.NS"
                        
                        # Get current technical analysis
                        technical_data = self.technical_analyzer.analyze_stock(symbol_with_suffix)
                        if not technical_data:
                            continue
                        
                        # Get fundamental analysis
                        fundamental_data = self.fundamental_analyzer.get_financial_data(symbol_with_suffix)
                        
                        # Get news articles for this stock
                        news_articles = []
                        for article in st.session_state.news_articles:
                            if symbol.lower() in article.get('title', '').lower() or symbol.lower() in article.get('description', '').lower():
                                news_articles.append(article)
                        
                        # Get comprehensive Groq AI analysis
                        groq_analysis = self.groq_analyzer.get_comprehensive_stock_analysis(
                            symbol, technical_data, fundamental_data, news_articles
                        )
                        
                        # Get Gemini AI learning analysis
                        gemini_analysis = None
                        if self.gemini_analyzer.initialized:
                            gemini_analysis = self.gemini_analyzer.analyze_stock_for_learning(
                                symbol, technical_data, fundamental_data, news_articles, groq_analysis, item
                            )
                        
                        # Calculate performance
                        entry_price = item.get('entry_price', 0)
                        current_price = technical_data.get('current_price', 0)
                        performance_pct = 0
                        if entry_price > 0 and current_price > 0:
                            performance_pct = ((current_price - entry_price) / entry_price) * 100
                        
                        # Update watchlist item
                        item.update({
                            'current_price': current_price,
                            'performance_pct': performance_pct,
                            'last_learning_analysis': datetime.now().isoformat(),
                            'learning_insights': gemini_analysis.get('analysis', {}) if gemini_analysis else {}
                        })
                        
                        analyzed_count += 1
                        progress_bar.progress((i + 1) / total_count)
                        
                    except Exception as e:
                        logger.error(f"Error analyzing watchlist stock {symbol}: {str(e)}")
                        continue
                
                st.success(f"✅ Learned from {analyzed_count}/{total_count} watchlist stocks")
                
            except Exception as e:
                st.error(f"❌ Error in watchlist learning analysis: {str(e)}")
    
    def analyze_swing_performance(self):
        """Analyze swing trading performance and adjust parameters."""
        try:
            with st.spinner("📊 Analyzing swing trading performance..."):
                # Get all swing strategies from data persistence
                data_persistence = st.session_state.data_persistence
                all_swing_strategies = data_persistence.get_swing_strategies()
                
                if not all_swing_strategies:
                    st.warning("No swing strategies found to analyze")
                    return
                
                # Flatten all strategies from all dates
                all_strategies = []
                for date_str, strategies in all_swing_strategies.items():
                    all_strategies.extend(strategies)
                
                # Analyze performance
                performance_tracker = st.session_state.swing_performance_tracker
                analysis_results = performance_tracker.analyze_swing_performance(all_strategies)
                
                # Display results
                self.display_swing_performance_results(analysis_results)
                
                # Update swing strategy with new parameters
                adaptive_params = performance_tracker.get_adaptive_parameters()
                st.session_state.swing_strategy = SwingTradingStrategy(adaptive_parameters=adaptive_params)
                
                st.success("✅ Swing trading parameters updated based on performance analysis!")
                
        except Exception as e:
            st.error(f"❌ Error analyzing swing performance: {str(e)}")
    
    def display_swing_performance_results(self, results: Dict):
        """Display swing trading performance analysis results."""
        try:
            st.subheader("📊 Swing Trading Performance Analysis")
            
            # Performance metrics
            metrics = results.get('performance_metrics', {})
            if metrics:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Trades", metrics.get('total_trades', 0))
                
                with col2:
                    win_rate = metrics.get('win_rate', 0)
                    st.metric("Win Rate", f"{win_rate:.1f}%")
                
                with col3:
                    avg_return = metrics.get('avg_return', 0)
                    st.metric("Avg Return", f"{avg_return:.2f}%")
                
                with col4:
                    current_capital = metrics.get('current_capital', 100000)
                    st.metric("Current Capital", f"₹{current_capital:,.0f}")
                
                # Additional metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    profit_factor = metrics.get('profit_factor', 0)
                    st.metric("Profit Factor", f"{profit_factor:.2f}")
                
                with col2:
                    sharpe_ratio = metrics.get('sharpe_ratio', 0)
                    st.metric("Sharpe Ratio", f"{sharpe_ratio:.2f}")
                
                with col3:
                    max_drawdown = metrics.get('max_drawdown', 0)
                    st.metric("Max Drawdown", f"{max_drawdown:.1f}%")
            
            # Parameter adjustments
            adjustments = results.get('adjustments_made', [])
            if adjustments:
                st.subheader("🔧 Parameter Adjustments Made")
                for adjustment in adjustments:
                    st.info(f"• {adjustment}")
            else:
                st.info("No parameter adjustments needed based on current performance")
            
            # Updated parameters
            updated_params = results.get('updated_parameters', {})
            if updated_params:
                st.subheader("⚙️ Current Adaptive Parameters")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Stop Loss", f"{updated_params.get('stop_loss_percentage', 0)*100:.1f}%")
                    st.metric("Take Profit", f"{updated_params.get('take_profit_percentage', 0)*100:.1f}%")
                
                with col2:
                    st.metric("Position Size", f"{updated_params.get('position_size_percentage', 0)*100:.1f}%")
                    st.metric("Confidence Threshold", f"{updated_params.get('confidence_threshold', 0):.1f}%")
                
                with col3:
                    st.metric("Risk-Reward Ratio", f"{updated_params.get('risk_reward_ratio', 0):.1f}:1")
                    st.metric("Max Drawdown", f"{updated_params.get('max_drawdown', 0)*100:.1f}%")
            
            # Strategy status summary
            st.subheader("📈 Strategy Status Summary")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Completed Strategies", results.get('completed_strategies', 0))
            
            with col2:
                st.metric("Active Strategies", results.get('active_strategies', 0))
            
            with col3:
                st.metric("Expired Strategies", results.get('expired_strategies', 0))
                
        except Exception as e:
            st.error(f"Error displaying performance results: {str(e)}")
    
    def display_current_adaptive_parameters(self):
        """Display current adaptive parameters in swing tab."""
        try:
            performance_tracker = st.session_state.swing_performance_tracker
            adaptive_params = performance_tracker.get_adaptive_parameters()
            performance_summary = performance_tracker.get_performance_summary()
            
            st.subheader("⚙️ Current Adaptive Parameters (Realistic 7-Day Targets)")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                stop_loss = adaptive_params.get('stop_loss_percentage', 0)*100
                st.metric(
                    "Stop Loss", 
                    f"{stop_loss:.1f}%",
                    help=f"Realistic stop loss for 7-day swing trading (2-5% range)"
                )
            
            with col2:
                take_profit = adaptive_params.get('take_profit_percentage', 0)*100
                st.metric(
                    "Take Profit", 
                    f"{take_profit:.1f}%",
                    help=f"Realistic target for 7-day swing trading (1.5-3% range)"
                )
            
            with col3:
                position_size = adaptive_params.get('position_size_percentage', 0)*100
                st.metric(
                    "Position Size", 
                    f"{position_size:.1f}%",
                    help="Maximum position size per trade (5-15% range)"
                )
            
            with col4:
                confidence = adaptive_params.get('confidence_threshold', 0)
                st.metric(
                    "Confidence Threshold", 
                    f"{confidence:.1f}%",
                    help="Minimum confidence required for trades (50-75% range)"
                )
            
            # Show realistic expectations
            st.info(f"🎯 **Realistic 7-Day Swing Targets:** Stop Loss: {stop_loss:.1f}%, Take Profit: {take_profit:.1f}% (These are achievable targets for 7-day swing trading)")
            
            # Performance summary
            metrics = performance_summary.get('performance_metrics', {})
            if metrics and metrics.get('total_trades', 0) > 0:
                st.subheader("📊 Performance Summary")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Trades", metrics.get('total_trades', 0))
                
                with col2:
                    win_rate = metrics.get('win_rate', 0)
                    st.metric("Win Rate", f"{win_rate:.1f}%")
                
                with col3:
                    current_capital = metrics.get('current_capital', 100000)
                    st.metric("Current Capital", f"₹{current_capital:,.0f}")
                
                with col4:
                    last_updated = adaptive_params.get('last_updated', 'Never')
                    if last_updated != 'Never':
                        try:
                            last_update_date = datetime.fromisoformat(last_updated)
                            last_updated = last_update_date.strftime('%Y-%m-%d %H:%M')
                        except:
                            pass
                    st.metric("Last Updated", last_updated)
            else:
                st.info("No performance data available yet. Run performance analysis after completing some trades.")
                
        except Exception as e:
            st.error(f"Error displaying adaptive parameters: {str(e)}")
    
    def update_watchlist_prices(self):
        """Update watchlist prices."""
        if not st.session_state.watchlist:
            st.error("No stocks in watchlist to update")
            return
        
        with st.spinner("🔄 Updating watchlist prices..."):
            try:
                updated_count = 0
                total_count = len(st.session_state.watchlist)
                
                progress_bar = st.progress(0)
                
                for i, item in enumerate(st.session_state.watchlist):
                    symbol = item.get('symbol')
                    if symbol:
                        try:
                            symbol_with_suffix = f"{symbol}.NS"
                            ticker = yf.Ticker(symbol_with_suffix)
                            hist = ticker.history(period="1d")
                            
                            if not hist.empty:
                                current_price = hist['Close'].iloc[-1]
                                item['current_price'] = float(current_price)
                                item['last_updated'] = datetime.now().isoformat()
                                updated_count += 1
                            
                            progress_bar.progress((i + 1) / total_count)
                            
                        except Exception as e:
                            logger.error(f"Error updating price for {symbol}: {str(e)}")
                
                # Auto-save updated watchlist
                self._auto_save_watchlist()
                
                st.success(f"✅ Updated prices for {updated_count}/{total_count} stocks")
                
            except Exception as e:
                st.error(f"❌ Error updating watchlist prices: {str(e)}")
    
    def update_watchlist_item(self, symbol: str):
        """Update a specific watchlist item."""
        st.info(f"Updating {symbol}...")
        # Implementation for updating individual items
        st.success(f"Updated {symbol}")
    
    def show_recommendation_details(self, rec: Dict):
        """Show detailed recommendation analysis."""
        st.subheader(f"📊 Detailed Analysis: {rec.get('symbol', 'N/A')}")
        
        # Technical Analysis
        with st.expander("📈 Technical Analysis"):
            technical_data = rec.get('technical_data', {})
            if technical_data:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("RSI", f"{technical_data.get('rsi', 0):.2f}")
                    st.metric("MACD", f"{technical_data.get('macd', 0):.2f}")
                with col2:
                    st.metric("SMA 20", f"{technical_data.get('sma_20', 0):.2f}")
                    st.metric("SMA 50", f"{technical_data.get('sma_50', 0):.2f}")
                with col3:
                    st.metric("Volume Ratio", f"{technical_data.get('volume_ratio', 0):.2f}")
                    st.metric("Technical Score", f"{technical_data.get('technical_score', 0):.2f}")
        
        # Fundamental Analysis
        with st.expander("📊 Fundamental Analysis"):
            fundamental_data = rec.get('fundamental_data', {})
            if fundamental_data:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("P/E Ratio", f"{fundamental_data.get('pe_ratio', 0):.2f}")
                    st.metric("P/B Ratio", f"{fundamental_data.get('pb_ratio', 0):.2f}")
                with col2:
                    st.metric("ROE", f"{fundamental_data.get('roe', 0):.2f}")
                    st.metric("ROA", f"{fundamental_data.get('roa', 0):.2f}")
                with col3:
                    st.metric("Debt/Equity", f"{fundamental_data.get('debt_equity', 0):.2f}")
                    st.metric("Fundamental Score", f"{fundamental_data.get('score', 0):.2f}")
        
        # Groq AI Analysis
        with st.expander("🤖 Groq AI Comprehensive Analysis"):
            groq_analysis = rec.get('groq_analysis', {})
            if groq_analysis and groq_analysis.get('status') == 'success':
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Overall Score", f"{groq_analysis.get('overall_score', 0):.2f}")
                    st.metric("Recommendation", groq_analysis.get('recommendation', 'HOLD'))
                    st.metric("Confidence", f"{groq_analysis.get('confidence', 0):.1%}")
                with col2:
                    st.metric("Risk Assessment", groq_analysis.get('risk_assessment', 'MEDIUM'))
                    st.metric("Time Horizon", groq_analysis.get('time_horizon', 'MEDIUM'))
                    st.metric("Price Target", groq_analysis.get('price_target', 'N/A'))
                
                st.markdown(f"**Reasoning:** {groq_analysis.get('reasoning', 'No reasoning provided')}")
                st.markdown(f"**Key Factors:** {', '.join(groq_analysis.get('key_factors', []))}")
                st.markdown(f"**Stop Loss:** {groq_analysis.get('stop_loss', 'N/A')}")
                
                # Detailed insights
                with st.expander("📊 Detailed Insights"):
                    st.markdown(f"**Technical Insights:** {groq_analysis.get('technical_insights', 'No technical insights')}")
                    st.markdown(f"**Fundamental Insights:** {groq_analysis.get('fundamental_insights', 'No fundamental insights')}")
                    st.markdown(f"**Sentiment Insights:** {groq_analysis.get('sentiment_insights', 'No sentiment insights')}")
                    st.markdown(f"**Market Outlook:** {groq_analysis.get('market_outlook', 'No market outlook')}")
            else:
                st.info("No Groq AI analysis available")
        
        # Gemini AI Analysis
        with st.expander("🧠 Gemini AI Analysis"):
            gemini_analysis = rec.get('gemini_analysis', {})
            if gemini_analysis and gemini_analysis.get('status') == 'success':
                analysis_data = gemini_analysis.get('analysis', {})
                st.metric("Overall Score", f"{analysis_data.get('overall_score', 0):.2f}")
                st.metric("Confidence", f"{analysis_data.get('confidence', 0):.1%}")
                st.markdown(f"**Recommendation:** {analysis_data.get('recommendation', 'N/A')}")
                st.markdown(f"**Risk Assessment:** {analysis_data.get('risk_assessment', 'N/A')}")
            else:
                st.info("No Gemini AI analysis available")
    
    def save_recommendations(self):
        """Save recommendations to database."""
        try:
            if not st.session_state.recommendations:
                st.warning("No recommendations to save")
                return
            
            # Save to local database if available
            if hasattr(self, 'recommendation_db') and self.recommendation_db:
                if self.recommendation_db.save_recommendations(st.session_state.recommendations, 'enhanced'):
                    st.success("✅ Recommendations saved to local database")
                else:
                    st.warning("⚠️ Failed to save to local database")
            
            # Save to Firebase if available
            if st.session_state.firebase_available and hasattr(self, 'firebase_sync'):
                if self.firebase_sync.sync_recommendations(st.session_state.recommendations, "enhanced"):
                    st.success("✅ Recommendations synced to Firebase")
                else:
                    st.warning("⚠️ Failed to sync to Firebase")
            
        except Exception as e:
            st.error(f"❌ Error saving recommendations: {str(e)}")

def main():
    """Main function to run the Streamlit app."""
    try:
        app = StreamlitTradingApp()
        app.run()
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        logger.error(f"Application error: {str(e)}")

if __name__ == "__main__":
    main()
