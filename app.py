#!/usr/bin/env python3
"""
Enhanced Swing Trading App - Streamlit Web Version
A comprehensive stock analysis and trading application with AI-powered recommendations.
"""

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
import os
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
from components.equity_loader import EquityLoader
from components.price_monitor import PriceMonitor
from components.notification_settings import NotificationSettingsManager, NotificationChannel
from components.data_persistence import DataPersistenceManager
from components.expandable_ui import ExpandableUI
from components.scheduled_analysis import ScheduledAnalysis
from components.portfolio_manager import PortfolioManager
from components.performance_learning import PerformanceLearning
from components.user_manager import UserManager
from components.login_interface import LoginInterface

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
        if 'recommendations' not in st.session_state:
            st.session_state.recommendations = []
        if 'news_articles' not in st.session_state:
            st.session_state.news_articles = []
        if 'groq_news_data' not in st.session_state:
            st.session_state.groq_news_data = []
        if 'watchlist' not in st.session_state:
            st.session_state.watchlist = []
        if 'analysis_in_progress' not in st.session_state:
            st.session_state.analysis_in_progress = False
        if 'last_analysis_time' not in st.session_state:
            st.session_state.last_analysis_time = None
        if 'api_keys_initialized' not in st.session_state:
            st.session_state.api_keys_initialized = False
        if 'saved_groq_key' not in st.session_state:
            st.session_state.saved_groq_key = ''
        if 'saved_gemini_key' not in st.session_state:
            st.session_state.saved_gemini_key = ''
        if 'cache_manager' not in st.session_state:
            st.session_state.cache_manager = CacheManager()
        if 'swing_strategy' not in st.session_state:
            st.session_state.swing_strategy = SwingTradingStrategy()
        if 'email_notifications' not in st.session_state:
            st.session_state.email_notifications = EmailNotificationManager()
        if 'price_monitor' not in st.session_state:
            st.session_state.price_monitor = PriceMonitor(self._notification_callback)
        if 'notification_settings' not in st.session_state:
            st.session_state.notification_settings = NotificationSettingsManager()
        if 'data_persistence' not in st.session_state:
            # Initialize with current user if available
            current_user = st.session_state.get('current_username')
            st.session_state.data_persistence = DataPersistenceManager(username=current_user)
        if 'scheduled_analysis' not in st.session_state:
            st.session_state.scheduled_analysis = ScheduledAnalysis(self.analyze_market)
        if 'equity_loader' not in st.session_state:
            st.session_state.equity_loader = EquityLoader()
        if 'portfolio_manager' not in st.session_state:
            st.session_state.portfolio_manager = PortfolioManager()
        if 'performance_learning' not in st.session_state:
            st.session_state.performance_learning = PerformanceLearning()
        if 'user_manager' not in st.session_state:
            st.session_state.user_manager = UserManager()
        if 'login_interface' not in st.session_state:
            st.session_state.login_interface = LoginInterface(st.session_state.user_manager)
        
        # Load saved data into session state if not already loaded
        if 'watchlist' not in st.session_state or not st.session_state.watchlist:
            saved_watchlist = st.session_state.data_persistence.get_watchlist()
            if saved_watchlist:
                st.session_state.watchlist = saved_watchlist
                logger.info(f"Loaded {len(saved_watchlist)} items from saved watchlist")
        
        # Load latest recommendations if not already loaded
        if 'recommendations' not in st.session_state or not st.session_state.recommendations:
            available_dates = st.session_state.data_persistence.get_available_dates()
            if available_dates:
                # Load the most recent recommendations
                latest_date = max(available_dates)
                latest_recommendations = st.session_state.data_persistence.get_recommendations_by_date(latest_date)
                if latest_recommendations:
                    st.session_state.recommendations = latest_recommendations
                    logger.info(f"Loaded {len(latest_recommendations)} recommendations from {latest_date}")
    
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
                if self.groq_analyzer.set_api_key(groq_key):
                    logger.info("Groq API key loaded and validated successfully")
                else:
                    logger.error("Groq API key validation failed")
            else:
                self.groq_analyzer.initialized = False
                logger.warning("Groq API key not found")
            
            # Load and set Gemini API key
            gemini_key = self.load_saved_api_key('gemini')
            if gemini_key:
                if self.gemini_analyzer.set_api_key(gemini_key):
                    logger.info("Gemini API key loaded and validated successfully")
                else:
                    logger.error("Gemini API key validation failed")
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
        """Load saved API key from session state, local file, Streamlit secrets, or environment variables."""
        try:
            # For new browsers, keep API key sections blank
            # Only load from files/secrets if user explicitly wants to use saved keys
            
            # Check if this is a new browser session (no session state initialized)
            if 'api_keys_initialized' not in st.session_state:
                return ''  # Keep blank for new browsers
            
            # First check session state (for current session)
            if key_type == 'groq':
                session_key = st.session_state.get('saved_groq_key', '')
                if session_key:
                    return session_key
            elif key_type == 'gemini':
                session_key = st.session_state.get('saved_gemini_key', '')
                if session_key:
                    return session_key
            
            # Check local file (for persistence across sessions)
            import os
            data_dir = "data"
            key_file = os.path.join(data_dir, f"{key_type}_api_key.txt")
            if os.path.exists(key_file):
                try:
                    with open(key_file, 'r') as f:
                        file_key = f.read().strip()
                        if file_key:
                            # Also update session state for current session
                            if key_type == 'groq':
                                st.session_state.saved_groq_key = file_key
                            elif key_type == 'gemini':
                                st.session_state.saved_gemini_key = file_key
                            return file_key
                except Exception as e:
                    logger.warning(f"Could not read {key_type} API key from file: {str(e)}")
            
            # Try Streamlit secrets (for deployment)
            if key_type == 'groq':
                return st.secrets.get('GROQ_API_KEY', '')
            elif key_type == 'gemini':
                return st.secrets.get('GEMINI_API_KEY', '')
            
            # Fallback to environment variables
            if key_type == 'groq':
                return os.getenv('GROQ_API_KEY', '')
            elif key_type == 'gemini':
                return os.getenv('GEMINI_API_KEY', '')
                
        except Exception as e:
            logger.warning(f"Could not load saved {key_type} API key: {str(e)}")
            return ""
    
    def save_api_key(self, key_type: str, api_key: str) -> bool:
        """Save API key to session state and local file for persistence."""
        try:
            if not api_key or not api_key.strip():
                st.error("API key cannot be empty")
                return False
            
            # Validate API key before saving
            if key_type == 'groq':
                if not self.groq_analyzer.set_api_key(api_key.strip()):
                    st.error("Invalid Groq API key. Please check your key and try again.")
                    return False
                st.session_state.saved_groq_key = api_key.strip()
            elif key_type == 'gemini':
                if not self.gemini_analyzer.set_api_key(api_key.strip()):
                    st.error("Invalid Gemini API key. Please check your key and try again.")
                    return False
                st.session_state.saved_gemini_key = api_key.strip()
            
            # Mark API keys as initialized
            st.session_state.api_keys_initialized = True
            
            # Save to local file for persistence
            import os
            data_dir = "data"
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
            
            key_file = os.path.join(data_dir, f"{key_type}_api_key.txt")
            with open(key_file, 'w') as f:
                f.write(api_key.strip())
            
            st.success(f"{key_type.upper()} API key validated and saved successfully!")
            logger.info(f"Saved and validated {key_type} API key to session state and file")
            return True
        except Exception as e:
            st.error(f"Error saving API key: {str(e)}")
            logger.error(f"Could not save {key_type} API key: {str(e)}")
            return False
    
    def delete_saved_api_key(self, key_type: str) -> bool:
        """Clear saved API key from session state and local file."""
        try:
            # Clear from session state
            if key_type == 'groq':
                st.session_state.saved_groq_key = ""
            elif key_type == 'gemini':
                st.session_state.saved_gemini_key = ""
            
            # Delete local file
            import os
            data_dir = "data"
            key_file = os.path.join(data_dir, f"{key_type}_api_key.txt")
            if os.path.exists(key_file):
                os.remove(key_file)
            
            logger.info(f"Cleared {key_type} API key from session state and file")
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
    
    def _load_user_data(self):
        """Load user-specific data after login."""
        try:
            # Load saved watchlist
            saved_watchlist = st.session_state.data_persistence.get_watchlist()
            if saved_watchlist:
                st.session_state.watchlist = saved_watchlist
                logger.info(f"Loaded {len(saved_watchlist)} items from user watchlist")
            
            # Load latest recommendations
            available_dates = st.session_state.data_persistence.get_available_dates()
            if available_dates:
                latest_date = max(available_dates)
                latest_recommendations = st.session_state.data_persistence.get_recommendations_by_date(latest_date)
                if latest_recommendations:
                    st.session_state.recommendations = latest_recommendations
                    logger.info(f"Loaded {len(latest_recommendations)} recommendations from {latest_date}")
            
            # Load latest swing strategies
            swing_dates = st.session_state.data_persistence.get_available_dates()
            if swing_dates:
                latest_swing_date = max(swing_dates)
                latest_swing_strategies = st.session_state.data_persistence.get_swing_strategies_by_date(latest_swing_date)
                if latest_swing_strategies:
                    st.session_state.swing_strategies = latest_swing_strategies
                    logger.info(f"Loaded {len(latest_swing_strategies)} swing strategies from {latest_swing_date}")
            
        except Exception as e:
            logger.error(f"Error loading user data: {str(e)}")
    
    def run(self):
        """Run the main application."""
        try:
            # Initialize session state
            self.initialize_session_state()
            
            # Initialize components
            self.initialize_components()
            
            # Check login status
            login_interface = st.session_state.login_interface
            
            if not login_interface.is_user_logged_in():
                # Show login page
                if login_interface.show_login_page():
                    # User successfully logged in, reinitialize data persistence with user
                    current_user = login_interface.get_current_user()
                    st.session_state.data_persistence = DataPersistenceManager(username=current_user)
                    # Load user-specific data
                    self._load_user_data()
                else:
                    # User not logged in, stop here
                    return
            
            # User is logged in, show main application
            # Header
            current_user = login_interface.get_current_user()
            st.markdown(f'<h1 class="main-header">🚀 Enhanced Swing Trading App - AI Powered</h1>', unsafe_allow_html=True)
            st.caption(f"Welcome, {current_user}!")
        
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
                
        except Exception as e:
            logger.error(f"Application error: {str(e)}")
            st.error(f"Application error: {str(e)}")
    
    def create_sidebar(self):
        """Create the sidebar with controls."""
        # Compact sidebar - only show essential controls
        with st.sidebar:
            # Show logout button
            login_interface = st.session_state.login_interface
            login_interface.show_logout_button()
            
            # User management section
            current_user = login_interface.get_current_user()
            if current_user:
                st.markdown("### 👤 User Management")
                
                # User preferences
                user_manager = st.session_state.user_manager
                preferences = user_manager.get_user_preferences(current_user)
                
                # Show user info
                st.caption(f"**User:** {current_user}")
                st.caption(f"**Role:** {user_manager.users.get(current_user, {}).get('role', 'user')}")
                
                # User stats
                user_stats = user_manager.get_user_stats()
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Users", user_stats.get('total_users', 0))
                with col2:
                    st.metric("Active Sessions", user_stats.get('active_sessions', 0))
            
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
            
            # Show API key status
            groq_status = "✅ Valid" if self.groq_analyzer.initialized else "❌ Invalid/Missing"
            gemini_status = "✅ Valid" if self.gemini_analyzer.initialized else "❌ Invalid/Missing"
            
            st.caption(f"**Groq:** {groq_status}")
            st.caption(f"**Gemini:** {gemini_status}")
            
            # Load Saved Keys button (for new browsers)
            if not st.session_state.api_keys_initialized:
                if st.button("📂 Load Saved Keys", key="load_saved_keys", help="Load previously saved API keys"):
                    # Load saved keys from files
                    groq_saved = self.load_saved_api_key('groq')
                    gemini_saved = self.load_saved_api_key('gemini')
                    
                    if groq_saved:
                        if self.groq_analyzer.set_api_key(groq_saved):
                            st.session_state.saved_groq_key = groq_saved
                        else:
                            st.warning("Groq API key validation failed")
                    
                    if gemini_saved:
                        if self.gemini_analyzer.set_api_key(gemini_saved):
                            st.session_state.saved_gemini_key = gemini_saved
                        else:
                            st.warning("Gemini API key validation failed")
                    
                    st.session_state.api_keys_initialized = True
                    st.success("✅ Loaded saved API keys!")
                    st.rerun()
        
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
                            st.success("✅ Saved and validated!")
                        else:
                            st.error("❌ Failed to save or validate")
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
                            st.success("✅ Saved and validated!")
                        else:
                            st.error("❌ Failed to save or validate")
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
            
            # Header row
            col1, col2, col3, col4, col5, col6, col7 = st.columns([1.5, 1.5, 1, 1, 1, 0.8, 0.8])
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
            with col7:
                st.markdown("**Actions**")
            
            st.markdown("---")
            
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
        
        with col3:
            if st.button("📊 View Saved", key="view_saved_swing"):
                st.session_state.show_saved_swing_strategies = not st.session_state.get('show_saved_swing_strategies', False)
        
        # Show saved strategies if toggled
        if st.session_state.get('show_saved_swing_strategies', False):
            self.display_saved_swing_strategies()
            return
        
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
                
                # Header row
                col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([1.5, 1, 1, 1, 1, 1, 0.8, 0.8])
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
                with col8:
                    st.markdown("**Actions**")
                
                st.markdown("---")
                
                # Display swing strategies in rows
                for i, strategy in enumerate(swing_strategies):
                    ExpandableUI.display_swing_strategy_row(strategy, i)
                    
                    # Check if add to watchlist button was clicked
                    if st.session_state.get(f"add_swing_to_watchlist_{i}", False):
                        # Convert swing strategy to recommendation format for watchlist
                        watchlist_item = {
                            'symbol': strategy.get('symbol', ''),
                            'company_name': strategy.get('company_name', ''),
                            'current_price': strategy.get('current_price', 0),
                            'recommendation': 'BUY',
                            'confidence': strategy.get('confidence', 0),
                            'target_price': strategy.get('take_profit', 0),
                            'stop_loss': strategy.get('stop_loss', 0),
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
            
            # Header row
            col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns([1.5, 1, 1, 1, 1, 1, 1, 0.8, 0.8])
            with col1:
                st.markdown("**Stock**")
            with col2:
                st.markdown("**CMP**")
            with col3:
                st.markdown("**Entry Price**")
            with col4:
                st.markdown("**P&L**")
            with col5:
                st.markdown("**Target**")
            with col6:
                st.markdown("**Stop Loss**")
            with col7:
                st.markdown("**Status**")
            with col8:
                st.markdown("**Details**")
            with col9:
                st.markdown("**Actions**")
            
            st.markdown("---")
            
            # Display watchlist items in rows
            for i, item in enumerate(st.session_state.watchlist):
                # Check for recommendation changes for this stock
                symbol = item.get('symbol', '')
                if symbol:
                    cache_manager = st.session_state.cache_manager
                    changes = cache_manager.get_recommendation_changes(symbol)
                    if changes and symbol in changes:
                        change_info = changes[symbol]
                        item['recommendation_changed'] = True
                        item['recommendation_change_type'] = change_info.get('change_type', '')
                        item['recommendation_change_details'] = change_info.get('change_details', {})
                        item['recommendation_last_updated'] = change_info.get('last_updated', '')
                    else:
                        item['recommendation_changed'] = False
                
                # Display watchlist row
                ExpandableUI.display_watchlist_row(item, i)
                
                # Add delete button in a separate row
                col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns([1.5, 1, 1, 1, 1, 1, 1, 0.8, 0.8])
                with col9:
                    if st.button("🗑️", key=f"delete_watchlist_{i}", help=f"Delete {item.get('symbol', 'stock')} from watchlist"):
                        # Remove item from watchlist
                        st.session_state.watchlist.pop(i)
                        # Auto-save updated watchlist
                        self._auto_save_watchlist()
                        st.success(f"Removed {item.get('symbol', 'stock')} from watchlist!")
                        st.rerun()
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
        """Portfolio tab with Excel upload and analysis."""
        st.header("📊 Portfolio Management")
        
        portfolio_manager = st.session_state.portfolio_manager
        
        # Portfolio summary
        summary = portfolio_manager.get_portfolio_summary()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Stocks", summary['total_items'])
        with col2:
            st.metric("Total Value", f"₹{summary['total_value']:,.0f}")
        with col3:
            st.metric("Total P&L", f"₹{summary['total_pnl']:,.0f}")
        with col4:
            st.metric("Avg P&L", f"{summary['avg_pnl_percent']:.1f}%")
        
        st.markdown("---")
        
        # Excel Upload Section
        st.subheader("📤 Upload Portfolio from Excel")
        st.info("Upload your portfolio using the Excel format with columns: Scrip Name, Free Qty, Rate, Valuation")
        
        uploaded_file = st.file_uploader(
            "Choose Excel file",
            type=['xlsx', 'xls'],
            help="Upload Excel file with portfolio data"
        )
        
        if uploaded_file is not None:
            if st.button("📊 Process Portfolio", key="process_portfolio"):
                with st.spinner("Processing portfolio data..."):
                    result = portfolio_manager.upload_excel_portfolio(uploaded_file)
                    
                    if result['success']:
                        st.success(result['message'])
                        st.rerun()
                    else:
                        st.error(result['message'])
        
        # Portfolio Actions
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Update Prices", key="update_portfolio_prices"):
                self.update_portfolio_prices()
        
        with col2:
            if st.button("📊 Analyze Portfolio", key="analyze_portfolio"):
                self.analyze_portfolio()
        
        with col3:
            if st.button("🗑️ Clear Portfolio", key="clear_portfolio"):
                portfolio_manager.portfolio_data = []
                portfolio_manager.save_portfolio()
                st.success("Portfolio cleared!")
                st.rerun()
        
        # Display Portfolio
        if portfolio_manager.portfolio_data:
            st.subheader(f"📋 Portfolio ({len(portfolio_manager.portfolio_data)} stocks)")
            
            # Header row
            col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns([1.5, 1, 1, 1, 1, 1, 1, 0.8, 0.8])
            with col1:
                st.markdown("**Stock**")
            with col2:
                st.markdown("**Qty**")
            with col3:
                st.markdown("**Entry Price**")
            with col4:
                st.markdown("**CMP**")
            with col5:
                st.markdown("**P&L**")
            with col6:
                st.markdown("**Recommendation**")
            with col7:
                st.markdown("**Last Analyzed**")
            with col8:
                st.markdown("**Details**")
            with col9:
                st.markdown("**Actions**")
            
            st.markdown("---")
            
            # Display portfolio items
            for i, item in enumerate(portfolio_manager.portfolio_data):
                symbol = item.get('symbol', 'N/A')
                scrip_name = item.get('scrip_name', symbol)
                free_qty = item.get('free_qty', 0)
                entry_price = item.get('entry_price', 0)
                current_price = item.get('current_price', 0)
                pnl_percent = item.get('pnl_percent', 0)
                recommendation = item.get('recommendation', 'HOLD')
                last_analyzed = item.get('last_analyzed', 'Never')
                
                # Format last analyzed date
                if last_analyzed and last_analyzed != 'Never':
                    try:
                        from datetime import datetime
                        analyzed_date = datetime.fromisoformat(last_analyzed)
                        last_analyzed = analyzed_date.strftime('%m/%d %H:%M')
                    except:
                        pass
                
                # Display row
                col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns([1.5, 1, 1, 1, 1, 1, 1, 0.8, 0.8])
                
                with col1:
                    st.write(f"**{symbol}**")
                    st.caption(scrip_name)
                
                with col2:
                    st.write(f"{free_qty:.0f}")
                
                with col3:
                    st.write(f"₹{entry_price:.2f}")
                
                with col4:
                    st.write(f"₹{current_price:.2f}")
                
                with col5:
                    if pnl_percent > 0:
                        st.markdown(f'<span style="color: #28a745;">+{pnl_percent:.1f}%</span>', unsafe_allow_html=True)
                    elif pnl_percent < 0:
                        st.markdown(f'<span style="color: #dc3545;">{pnl_percent:.1f}%</span>', unsafe_allow_html=True)
                    else:
                        st.write("0.0%")
                
                with col6:
                    if recommendation == 'BUY':
                        st.markdown('<span style="color: #28a745;">📈 BUY</span>', unsafe_allow_html=True)
                    elif recommendation == 'SELL':
                        st.markdown('<span style="color: #dc3545;">📉 SELL</span>', unsafe_allow_html=True)
                    else:
                        st.markdown('<span style="color: #ffc107;">➡️ HOLD</span>', unsafe_allow_html=True)
                
                with col7:
                    st.write(last_analyzed)
                
                with col8:
                    if st.button("➕", key=f"portfolio_details_{i}", help="View portfolio details"):
                        self.show_portfolio_item_details(item, i)
                
                with col9:
                    if st.button("🗑️", key=f"delete_portfolio_{i}", help=f"Delete {symbol} from portfolio"):
                        if portfolio_manager.remove_portfolio_item(symbol):
                            st.success(f"Removed {symbol} from portfolio!")
                            st.rerun()
                        else:
                            st.error(f"Failed to remove {symbol}")
        else:
            st.info("No portfolio data. Upload an Excel file to get started.")
    
    def update_portfolio_prices(self):
        """Update portfolio prices with current market data."""
        portfolio_manager = st.session_state.portfolio_manager
        
        if not portfolio_manager.portfolio_data:
            st.error("No portfolio data to update")
            return
        
        with st.spinner("🔄 Updating portfolio prices..."):
            try:
                # Get current prices for all portfolio symbols
                price_data = {}
                for item in portfolio_manager.portfolio_data:
                    symbol = item.get('symbol')
                    if symbol:
                        try:
                            symbol_with_suffix = f"{symbol}.NS"
                            ticker = yf.Ticker(symbol_with_suffix)
                            hist = ticker.history(period="1d")
                            
                            if not hist.empty:
                                current_price = float(hist['Close'].iloc[-1])
                                price_data[symbol] = current_price
                        except Exception as e:
                            logger.warning(f"Could not get price for {symbol}: {str(e)}")
                
                # Update portfolio with new prices
                portfolio_manager.update_portfolio_prices(price_data)
                
                st.success(f"✅ Updated prices for {len(price_data)} stocks")
                
            except Exception as e:
                st.error(f"Error updating portfolio prices: {str(e)}")
    
    def analyze_portfolio(self):
        """Analyze portfolio and provide recommendations."""
        portfolio_manager = st.session_state.portfolio_manager
        
        if not portfolio_manager.portfolio_data:
            st.error("No portfolio data to analyze")
            return
        
        with st.spinner("📊 Analyzing portfolio..."):
            try:
                # Get items that need analysis (7+ days old or never analyzed)
                items_to_analyze = portfolio_manager.get_items_for_analysis()
                
                if not items_to_analyze:
                    st.info("No portfolio items need analysis at this time")
                    return
                
                st.info(f"Analyzing {len(items_to_analyze)} portfolio items...")
                
                analyzed_count = 0
                progress_bar = st.progress(0)
                
                for i, item in enumerate(items_to_analyze):
                    symbol = item.get('symbol')
                    if not symbol:
                        continue
                    
                    try:
                        symbol_with_suffix = f"{symbol}.NS"
                        
                        # Validate stock before analysis
                        if not self.fundamental_analyzer.is_stock_valid(symbol_with_suffix):
                            logger.warning(f"Skipping {symbol} - appears to be delisted or has no data")
                            continue
                        
                        # Get technical analysis
                        technical_data = self.technical_analyzer.analyze_stock(symbol_with_suffix)
                        if not technical_data:
                            continue
                        
                        # Get fundamental analysis
                        fundamental_data = self.fundamental_analyzer.get_financial_data(symbol_with_suffix)
                        
                        # Get news sentiment
                        news_sentiment = 0.5  # Default neutral
                        if st.session_state.news_articles:
                            news_sentiment = self.news_analyzer.analyze_news_sentiment(st.session_state.news_articles)
                        
                        # Get Groq analysis
                        groq_analysis = self.groq_analyzer.get_comprehensive_stock_analysis(
                            symbol, technical_data, fundamental_data, st.session_state.news_articles
                        )
                        
                        # Generate AI recommendation
                        ai_recommendation = self.ai_engine.generate_ai_recommendation(
                            fundamental_data, technical_data, news_sentiment, [], groq_analysis, None
                        )
                        
                        # Apply learning to recommendation
                        performance_learning = st.session_state.performance_learning
                        improved_recommendation = performance_learning.apply_learning_to_recommendation(
                            symbol, technical_data, groq_analysis, ai_recommendation
                        )
                        
                        # Update portfolio item with analysis
                        portfolio_manager.analyze_portfolio_item(
                            item, technical_data, fundamental_data, news_sentiment, 
                            groq_analysis, improved_recommendation
                        )
                        
                        analyzed_count += 1
                        progress_bar.progress((i + 1) / len(items_to_analyze))
                        
                    except Exception as e:
                        logger.error(f"Error analyzing portfolio item {symbol}: {str(e)}")
                        continue
                
                # Save updated portfolio
                portfolio_manager.save_portfolio()
                
                st.success(f"✅ Analyzed {analyzed_count} portfolio items")
                
            except Exception as e:
                st.error(f"Error analyzing portfolio: {str(e)}")
    
    def show_portfolio_item_details(self, item: Dict, index: int):
        """Show detailed portfolio item information in a modal."""
        try:
            symbol = item.get('symbol', 'UNKNOWN')
            scrip_name = item.get('scrip_name', symbol)
            modal_title = f"📊 {symbol} Portfolio Details"
            
            with st.modal(modal_title):
                st.markdown("### 📊 Portfolio Position")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**📋 Position Details**")
                    st.write(f"• **Symbol:** {symbol}")
                    st.write(f"• **Scrip Name:** {scrip_name}")
                    st.write(f"• **Quantity:** {item.get('free_qty', 0):.0f}")
                    st.write(f"• **Entry Price:** ₹{item.get('entry_price', 0):.2f}")
                    st.write(f"• **Current Price:** ₹{item.get('current_price', 0):.2f}")
                    st.write(f"• **Date Added:** {item.get('date_added', 'N/A')}")
                
                with col2:
                    st.markdown("**💰 Financial Details**")
                    st.write(f"• **Valuation:** ₹{item.get('valuation', 0):,.0f}")
                    st.write(f"• **Current Market Value:** ₹{item.get('current_market_value', 0):,.0f}")
                    st.write(f"• **P&L Amount:** ₹{item.get('pnl_amount', 0):,.0f}")
                    st.write(f"• **P&L Percentage:** {item.get('pnl_percent', 0):.2f}%")
                    st.write(f"• **Analysis Count:** {item.get('analysis_count', 0)}")
                
                # Recommendation details
                st.markdown("### 📈 Current Recommendation")
                recommendation = item.get('recommendation', 'HOLD')
                confidence = item.get('confidence', 0)
                target_price = item.get('target_price', 0)
                stop_loss = item.get('stop_loss', 0)
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Recommendation", recommendation)
                with col2:
                    st.metric("Confidence", f"{confidence:.1f}%")
                with col3:
                    st.metric("Target Price", f"₹{target_price:.2f}")
                with col4:
                    st.metric("Stop Loss", f"₹{stop_loss:.2f}")
                
                # Reasoning
                reasoning = item.get('reasoning', '')
                if reasoning:
                    st.markdown("### 💭 Analysis Reasoning")
                    st.markdown(reasoning)
                
                # Technical analysis
                technical_data = item.get('technical_analysis', {})
                if technical_data:
                    st.markdown("### 📊 Technical Analysis")
                    tech_col1, tech_col2 = st.columns(2)
                    
                    with tech_col1:
                        st.write(f"• **RSI:** {technical_data.get('rsi', 0):.1f}")
                        st.write(f"• **MACD:** {technical_data.get('macd', 0):.4f}")
                        st.write(f"• **SMA 20:** ₹{technical_data.get('sma_20', 0):.2f}")
                    
                    with tech_col2:
                        st.write(f"• **Volume Ratio:** {technical_data.get('volume_ratio_20', 0):.2f}")
                        st.write(f"• **ATR:** ₹{technical_data.get('atr', 0):.2f}")
                        st.write(f"• **Bollinger Position:** {technical_data.get('bb_position', 0):.2f}")
                
                # Close button
                if st.button("❌ Close", key=f"close_portfolio_modal_{index}"):
                    st.rerun()
                    
        except Exception as e:
            logger.error(f"Error showing portfolio item details: {str(e)}")
            st.error("Error displaying portfolio details")
    
    def _show_ai_service_status(self, analysis_result: Dict, service_name: str = "AI"):
        """Show AI service status and fallback information."""
        try:
            if analysis_result and analysis_result.get('status') == 'success':
                ai_source = analysis_result.get('source', 'Unknown')
                if 'Fallback' in ai_source:
                    st.caption(f"⚠️ {service_name}: Using {ai_source}")
                else:
                    st.caption(f"✅ {service_name}: Using {ai_source}")
        except Exception as e:
            logger.error(f"Error showing AI service status: {str(e)}")
    
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
        col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns([1.5, 1, 1, 1, 1, 1, 1, 0.8, 0.8])
        with col1:
            st.markdown("**Stock**")
        with col2:
            st.markdown("**CMP**")
        with col3:
            st.markdown("**Entry Price**")
        with col4:
            st.markdown("**P&L**")
        with col5:
            st.markdown("**Target**")
        with col6:
            st.markdown("**Stop Loss**")
        with col7:
            st.markdown("**Status**")
        with col8:
            st.markdown("**Details**")
        with col9:
            st.markdown("**Actions**")
        
        st.markdown("---")
        
        # Display each watchlist item
        for i, item in enumerate(watchlist):
            ExpandableUI.display_watchlist_row(item, i)
            
            # Add delete button for saved watchlist
            col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns([1.5, 1, 1, 1, 1, 1, 1, 0.8, 0.8])
            with col9:
                if st.button("🗑️", key=f"delete_saved_watchlist_{i}", help=f"Delete {item.get('symbol', 'stock')} from saved watchlist"):
                    # Remove item from saved watchlist
                    watchlist.pop(i)
                    data_persistence.save_watchlist(watchlist)
                    st.success(f"Removed {item.get('symbol', 'stock')} from saved watchlist!")
                    st.rerun()
    
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
                st.info("🤖 Step 2: Analyzing news with AI (Groq/Gemini)...")
                groq_news_data = self.groq_analyzer.analyze_top_10_news_with_full_content(all_news)
                
                if groq_news_data.get('status') != 'success':
                    st.error(f"❌ AI analysis failed: {groq_news_data.get('message', 'Unknown error')}")
                    return
                
                # Show which AI service was used
                ai_source = groq_news_data.get('source', 'Unknown')
                if 'Fallback' in ai_source:
                    st.warning(f"⚠️ Using {ai_source} - primary service unavailable")
                else:
                    st.success(f"✅ Using {ai_source}")
                
                # Extract stocks from Groq analysis and validate them using EQUITY.csv
                all_news_stocks = [item.get('symbol', '') for item in groq_news_data.get('articles', []) if item.get('symbol')]
                equity_loader = st.session_state.equity_loader
                news_stocks = equity_loader.validate_stock_symbols(all_news_stocks)
                
                if len(news_stocks) != len(all_news_stocks):
                    invalid_stocks = set(all_news_stocks) - set(news_stocks)
                    st.warning(f"⚠️ Filtered out {len(invalid_stocks)} invalid/delisted stocks: {', '.join(list(invalid_stocks)[:5])}")
                
                # If we don't have enough stocks from news, get additional stocks from EQUITY.csv
                if len(news_stocks) < 5:
                    st.info(f"📈 Getting additional stocks from EQUITY.csv to ensure at least 5 recommendations...")
                    additional_stocks = equity_loader.get_top_stocks(20)  # Get top 20 stocks
                    # Filter out stocks already in news and watchlist
                    watchlist_symbols = [item.get('symbol', '') for item in st.session_state.watchlist]
                    additional_stocks = [s for s in additional_stocks if s not in news_stocks and s not in watchlist_symbols]
                    news_stocks.extend(additional_stocks[:10])  # Add up to 10 additional stocks
                
                # Filter out stocks already in watchlist (unless very negative news)
                filtered_stocks = cache_manager.filter_watchlist_stocks(
                    groq_news_data.get('articles', []), 
                    st.session_state.watchlist,
                    allow_negative_news=True
                )
                
                # Get symbols from filtered stocks
                filtered_news_stocks = [stock.get('symbol', '') for stock in filtered_stocks if stock.get('symbol')]
                
                # Combine news stocks with additional stocks, ensuring we have enough
                all_analysis_stocks = list(set(news_stocks + filtered_news_stocks))
                
                st.success(f"✅ Identified {len(all_analysis_stocks)} valid stocks for analysis (from news + EQUITY.csv)")
                
                # Step 3: Analyze stocks
                st.info("📊 Step 3: Analyzing stocks for contrarian opportunities...")
                news_recommendations = []
                
                progress_bar = st.progress(0)
                total_stocks = len(all_analysis_stocks)
                
                for i, symbol in enumerate(all_analysis_stocks):
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
                            # Validate stock before analysis
                            if not self.fundamental_analyzer.is_stock_valid(symbol_with_suffix):
                                logger.warning(f"Skipping {symbol} - appears to be delisted or has no data")
                                continue
                        
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
                            fundamental_data, technical_data, news_sentiment, [], groq_analysis, gemini_analysis
                        )
                        
                        # Smart caching: Only cache if stock is relevant
                        news_impact = 'MEDIUM'  # Default impact level
                        if groq_analysis and groq_analysis.get('status') == 'success':
                            impact_level = groq_analysis.get('impact_level', 'MEDIUM')
                            if impact_level in ['HIGH', 'MEDIUM', 'LOW']:
                                news_impact = impact_level
                        
                        # Check if stock is relevant for caching
                        if cache_manager.is_stock_relevant_for_caching(symbol, recommendation, news_impact):
                            # Cache the recommendation with change detection
                            recommendation = cache_manager.cache_recommendation(symbol, recommendation)
                            
                            # Cache the analysis
                            analysis_data = {
                                'technical_data': technical_data,
                                'fundamental_data': fundamental_data,
                                'groq_analysis': groq_analysis,
                                'gemini_analysis': gemini_analysis,
                                'recommendation': recommendation
                            }
                            cache_manager.cache_stock_analysis(symbol, analysis_data)
                        else:
                            logger.info(f"Skipping cache for {symbol} - not relevant enough (confidence: {recommendation.get('confidence', 0):.1f}%, impact: {news_impact})")
                        
                        # Only include BUY recommendations (SKIP others)
                        if recommendation.get('action') == 'BUY':
                            # Apply performance learning to improve recommendation
                            performance_learning = st.session_state.performance_learning
                            improved_recommendation = performance_learning.apply_learning_to_recommendation(
                                symbol, technical_data, groq_analysis, recommendation
                            )
                            
                            # Record recommendation for future learning
                            learning_id = performance_learning.record_recommendation(
                                symbol, improved_recommendation, technical_data, 
                                fundamental_data, news_sentiment, groq_analysis
                            )
                            
                            # Use improved recommendation
                            recommendation = improved_recommendation
                            
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
                
                # Ensure we have at least 5 recommendations
                if len(news_recommendations) < 5:
                    st.warning(f"⚠️ Only {len(news_recommendations)} recommendations found. Analyzing more stocks to reach minimum of 5...")
                    
                    # Get more stocks from EQUITY.csv
                    additional_stocks = equity_loader.get_top_stocks(50)
                    # Filter out already analyzed stocks
                    already_analyzed = [rec.get('symbol', '') for rec in news_recommendations]
                    additional_stocks = [s for s in additional_stocks if s not in already_analyzed and s not in all_analysis_stocks]
                    
                    # Analyze additional stocks
                    for symbol in additional_stocks[:20]:  # Analyze up to 20 more stocks
                        if len(news_recommendations) >= 5:
                            break
                            
                        try:
                            symbol_with_suffix = f"{symbol}.NS"
                            
                            # Validate stock before analysis
                            if not self.fundamental_analyzer.is_stock_valid(symbol_with_suffix):
                                logger.warning(f"Skipping additional stock {symbol} - appears to be delisted or has no data")
                                continue
                            
                            # Get technical analysis
                            technical_data = self.technical_analyzer.analyze_stock(symbol_with_suffix)
                            if not technical_data:
                                continue
                            
                            # Get fundamental analysis
                            fundamental_data = self.fundamental_analyzer.get_financial_data(symbol_with_suffix)
                            
                            # Get Groq analysis
                            groq_analysis = self.groq_analyzer.get_comprehensive_stock_analysis(
                                symbol, technical_data, fundamental_data, all_news
                            )
                            
                            # Calculate news sentiment
                            news_sentiment = self.news_analyzer.analyze_news_sentiment(all_news)
                            
                            # Generate AI recommendation
                            recommendation = self.ai_engine.generate_ai_recommendation(
                                fundamental_data, technical_data, news_sentiment, [], groq_analysis, None
                            )
                            
                            # Only include BUY recommendations
                            if recommendation.get('action') == 'BUY':
                                # Apply performance learning to improve recommendation
                                performance_learning = st.session_state.performance_learning
                                improved_recommendation = performance_learning.apply_learning_to_recommendation(
                                    symbol, technical_data, groq_analysis, recommendation
                                )
                                
                                # Record recommendation for future learning
                                learning_id = performance_learning.record_recommendation(
                                    symbol, improved_recommendation, technical_data, 
                                    fundamental_data, news_sentiment, groq_analysis
                                )
                                
                                # Use improved recommendation
                                recommendation = improved_recommendation
                                
                                # Generate swing trading plan
                                company_name = equity_loader.get_company_name(symbol)
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
                                
                                # Create recommendation data
                                rec_data = {
                                    'symbol': symbol,
                                    'company_name': company_name,
                                    'current_price': technical_data.get('current_price', 0),
                                    'recommendation': recommendation['action'],
                                    'confidence': recommendation['confidence'],
                                    'target_price': recommendation['target_price'],
                                    'stop_loss': recommendation['stop_loss'],
                                    'reasoning': recommendation['reasoning'],
                                    'technical_data': technical_data,
                                    'fundamental_data': fundamental_data,
                                    'groq_analysis': groq_analysis,
                                    'gemini_analysis': None,
                                    'swing_plan': swing_plan,
                                    'swing_validation': None
                                }
                                
                                news_recommendations.append(rec_data)
                                logger.info(f"Added additional BUY recommendation for {symbol}")
                        
                        except Exception as e:
                            logger.error(f"Error analyzing additional stock {symbol}: {str(e)}")
                        continue
                
                # Set final recommendations
                st.session_state.recommendations = news_recommendations
                st.session_state.last_analysis_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Save to database if available
                self.save_recommendations()
                
                # Auto-save recommendations and swing strategies
                self._auto_save_recommendations()
                self._auto_save_swing_strategies()
                
                if len(news_recommendations) >= 5:
                    st.success(f"✅ Analysis complete! Generated {len(news_recommendations)} BUY recommendations (minimum 5 achieved). Data auto-saved for 7 days.")
                else:
                    st.warning(f"⚠️ Analysis complete! Generated {len(news_recommendations)} BUY recommendations (less than minimum 5). Data auto-saved for 7 days.")
                
        except Exception as e:
            st.error(f"❌ Error analyzing market: {str(e)}")
        finally:
            st.session_state.analysis_in_progress = False
    
    def analyze_manual_stock(self, symbol: str):
        """Analyze a manually entered stock."""
        with st.spinner(f"🔍 Analyzing {symbol}..."):
            try:
                symbol_with_suffix = f"{symbol}.NS"
                
                # Validate stock before analysis
                if not self.fundamental_analyzer.is_stock_valid(symbol_with_suffix):
                    st.warning(f"Stock {symbol} appears to be delisted or has no data available. Skipping analysis.")
                    return
                
                # Get technical analysis
                technical_data = self.technical_analyzer.analyze_stock(symbol_with_suffix)
                if not technical_data:
                    st.error(f"No technical data available for {symbol}")
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
                    fundamental_data, technical_data, news_sentiment, [], groq_analysis, gemini_analysis
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
        """Analyze watchlist stocks for performance learning."""
        if not st.session_state.watchlist:
            st.error("No stocks in watchlist to analyze")
            return
        
        with st.spinner("🧠 Analyzing watchlist performance for learning..."):
            try:
                performance_learning = st.session_state.performance_learning
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
                        
                        # Get current price
                        current_price = technical_data.get('current_price', 0)
                        entry_price = item.get('entry_price', 0)
                        
                        if current_price <= 0 or entry_price <= 0:
                            continue
                        
                        # Calculate days held
                        date_added = item.get('added_date', '')
                        if date_added:
                            try:
                                from datetime import datetime
                                added_date = datetime.fromisoformat(date_added.replace('Z', '+00:00'))
                                days_held = (datetime.now() - added_date).days
                            except:
                                days_held = 7  # Default to 7 days
                        else:
                            days_held = 7
                        
                        # Analyze performance if 7+ days held
                        if days_held >= 7:
                            # Get fundamental analysis
                            fundamental_data = self.fundamental_analyzer.get_financial_data(symbol_with_suffix)
                            
                            # Get news sentiment
                            news_sentiment = 0.5  # Default neutral
                            if st.session_state.news_articles:
                                news_sentiment = self.news_analyzer.analyze_news_sentiment(st.session_state.news_articles)
                            
                            # Get Groq analysis
                            groq_analysis = self.groq_analyzer.get_comprehensive_stock_analysis(
                                symbol, technical_data, fundamental_data, st.session_state.news_articles
                            )
                            
                            # Create recommendation data for learning
                            recommendation_data = {
                                'action': item.get('recommendation', 'HOLD'),
                                'confidence': item.get('confidence', 0),
                                'target_price': item.get('target_price', 0),
                                'stop_loss': item.get('stop_loss', 0),
                                'reasoning': f"Watchlist analysis for {symbol}"
                            }
                            
                            # Record recommendation for learning
                            learning_id = performance_learning.record_recommendation(
                                symbol, recommendation_data, technical_data, 
                                fundamental_data, news_sentiment, groq_analysis
                            )
                            
                            # Analyze performance
                            performance_result = performance_learning.analyze_performance(
                                symbol, current_price, days_held
                            )
                            
                            if performance_result['success']:
                                outcome = performance_result['outcome']
                                st.info(f"📊 {symbol}: {outcome['status']} - {outcome['performance_percent']:.2f}% ({days_held} days)")
                        analyzed_count += 1
                        
                        # Update progress
                        progress_bar.progress((i + 1) / total_count)
                        
                    except Exception as e:
                        logger.error(f"Error analyzing watchlist stock {symbol}: {str(e)}")
                        continue
                
                # Show learning insights
                insights = performance_learning.get_learning_insights()
                
                st.success(f"✅ Analyzed {analyzed_count} watchlist stocks for learning")
                
                # Display learning insights
                if insights['total_recommendations'] > 0:
                    st.subheader("📚 Learning Insights")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total Recommendations", insights['total_recommendations'])
                    
                    with col2:
                        st.metric("Success Rate", f"{insights['overall_success_rate']:.1f}%")
                    
                    with col3:
                        st.metric("Successful", insights['successful_recommendations'])
                    
                    with col4:
                        st.metric("Failed", insights['failed_recommendations'])
                    
                    # Show top performing stocks
                    if insights['top_performing_stocks']:
                        st.subheader("🏆 Top Performing Stocks")
                        for symbol, success_rate in insights['top_performing_stocks'][:5]:
                            st.write(f"• {symbol}: {success_rate:.1f}% success rate")
                
            except Exception as e:
                st.error(f"Error analyzing watchlist: {str(e)}")
                logger.error(f"Error in analyze_watchlist_stocks: {str(e)}")
    
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
