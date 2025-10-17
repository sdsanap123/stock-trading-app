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
from components.price_monitor import PriceMonitor
from components.notification_settings import NotificationSettingsManager, NotificationChannel

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
        if 'saved_groq_key' not in st.session_state:
            st.session_state.saved_groq_key = self.load_saved_api_key('groq')
        if 'saved_gemini_key' not in st.session_state:
            st.session_state.saved_gemini_key = self.load_saved_api_key('gemini')
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
            
            logger.info("All components initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing components: {str(e)}")
            st.error(f"Error initializing components: {str(e)}")
    
    def load_saved_api_key(self, key_type: str) -> str:
        """Load saved API key from Streamlit secrets or environment variables."""
        try:
            # Try Streamlit secrets first (for deployment)
            if key_type == 'groq':
                return st.secrets.get('GROQ_API_KEY', '')
            elif key_type == 'gemini':
                return st.secrets.get('GEMINI_API_KEY', '')
            
            # Fallback to environment variables
            import os
            if key_type == 'groq':
                return os.getenv('GROQ_API_KEY', '')
            elif key_type == 'gemini':
                return os.getenv('GEMINI_API_KEY', '')
                
        except Exception as e:
            logger.warning(f"Could not load saved {key_type} API key: {str(e)}")
            return ""
    
    def save_api_key(self, key_type: str, api_key: str) -> bool:
        """Save API key to session state (for local development only)."""
        try:
            # For deployment, API keys should be set via environment variables or Streamlit secrets
            # This method is only for local development convenience
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
        
        # Main content
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
            "📰 News Analysis", 
            "🤖 Groq News Analysis", 
            "🎯 BUY Recommendations", 
            "📈 Swing Trading Plans", 
            "👀 Watchlist", 
            "🔍 Manual Analysis",
            "📊 Portfolio",
            "🔔 Notifications"
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
        st.sidebar.title("🎛️ Control Panel")
        
        # API Configuration Section
        st.sidebar.header("🔑 API Configuration")
        
        # Groq API Key
        groq_key = st.sidebar.text_input(
            "Groq API Key",
            value=st.session_state.saved_groq_key,
            type="password",
            help="Enter your Groq API key for AI-powered news analysis",
            placeholder="gsk_..."
        )
        
        # Groq API Key Actions
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("💾 Save", key="save_groq"):
                if groq_key and groq_key != st.session_state.saved_groq_key:
                    if self.save_api_key('groq', groq_key):
                        st.session_state.saved_groq_key = groq_key
                        st.sidebar.success("✅ Groq API key saved!")
                    else:
                        st.sidebar.error("❌ Failed to save Groq API key")
                else:
                    st.sidebar.info("ℹ️ No changes to save")
        
        with col2:
            if st.button("🗑️ Delete", key="delete_groq"):
                if self.delete_saved_api_key('groq'):
                    st.session_state.saved_groq_key = ""
                    st.sidebar.success("✅ Groq API key deleted!")
                    st.rerun()
                else:
                    st.sidebar.error("❌ Failed to delete Groq API key")
        
        if groq_key:
            # Update the Groq analyzer with the new key
            if hasattr(self, 'groq_analyzer'):
                self.groq_analyzer.api_key = groq_key
                self.groq_analyzer.initialized = True
                if groq_key == st.session_state.saved_groq_key:
                    st.sidebar.success("✅ Groq API key loaded from saved settings!")
                else:
                    st.sidebar.success("✅ Groq API key set! (Click Save to remember)")
            else:
                st.sidebar.warning("⚠️ Groq analyzer not initialized")
        else:
            if hasattr(self, 'groq_analyzer'):
                self.groq_analyzer.initialized = False
                st.sidebar.info("ℹ️ Enter Groq API key to enable AI analysis")
        
        st.sidebar.markdown("---")
        
        # Gemini API Key
        gemini_key = st.sidebar.text_input(
            "Gemini API Key",
            value=st.session_state.saved_gemini_key,
            type="password",
            help="Enter your Gemini API key for comprehensive AI analysis",
            placeholder="AIza..."
        )
        
        # Gemini API Key Actions
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("💾 Save", key="save_gemini"):
                if gemini_key and gemini_key != st.session_state.saved_gemini_key:
                    if self.save_api_key('gemini', gemini_key):
                        st.session_state.saved_gemini_key = gemini_key
                        st.sidebar.success("✅ Gemini API key saved!")
                    else:
                        st.sidebar.error("❌ Failed to save Gemini API key")
                else:
                    st.sidebar.info("ℹ️ No changes to save")
        
        with col2:
            if st.button("🗑️ Delete", key="delete_gemini"):
                if self.delete_saved_api_key('gemini'):
                    st.session_state.saved_gemini_key = ""
                    st.sidebar.success("✅ Gemini API key deleted!")
                    st.rerun()
                else:
                    st.sidebar.error("❌ Failed to delete Gemini API key")
        
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
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if st.button("📰 Fetch Latest News", type="primary"):
                self.fetch_news()
        
        with col2:
            if st.button("🔍 Analyze Sentiment"):
                self.analyze_sentiment()
        
        # Display news articles
        if st.session_state.news_articles:
            st.subheader(f"📰 Latest News ({len(st.session_state.news_articles)} articles)")
            
            for i, article in enumerate(st.session_state.news_articles[:10]):
                with st.expander(f"📄 {article.get('title', 'No title')[:80]}..."):
                    st.markdown(f"**Source:** {article.get('source', 'Unknown')}")
                    st.markdown(f"**Published:** {article.get('publishedAt', 'Unknown')}")
                    st.markdown(f"**Description:** {article.get('description', 'No description')}")
                    
                    if article.get('url'):
                        st.markdown(f"[Read Full Article]({article['url']})")
        else:
            st.info("No news articles available. Click 'Fetch Latest News' to get started.")
    
    def groq_news_analysis_tab(self):
        """Groq News Analysis tab."""
        st.header("🤖 Groq AI News Analysis with Sentiment")
        
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            if st.button("🔍 Fetch Groq News Analysis", type="primary"):
                self.fetch_groq_news_analysis()
        
        with col2:
            if st.button("📰 Fetch Indian News"):
                self.fetch_news()
        
        with col3:
            if st.button("🔄 Refresh Display"):
                st.rerun()
        
        with col4:
            if st.button("📡 Test RSS Feeds"):
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
            if st.button("🔍 Generate BUY Recommendations", type="primary"):
                self.analyze_market()
        
        with col2:
            if st.button("🔄 Refresh"):
                st.rerun()
        
        with col3:
            if st.button("💾 Save to Database"):
                self.save_recommendations()
        
        # Display recommendations
        if st.session_state.recommendations:
            st.subheader(f"🎯 BUY Recommendations ({len(st.session_state.recommendations)} stocks)")
            
            # Filter options
            col1, col2, col3 = st.columns(3)
            with col1:
                min_confidence = st.slider("Minimum Confidence", 0, 100, 35)  # Default to 35% for lenient criteria
            with col2:
                sort_by = st.selectbox("Sort by", ["Confidence", "Symbol", "Current Price", "Swing Score"])
            with col3:
                show_swing_plans = st.checkbox("Show Swing Plans", value=True)
            
            # Filter and sort recommendations (all are BUY recommendations)
            filtered_recs = st.session_state.recommendations.copy()
            
            # Filter by confidence
            filtered_recs = [rec for rec in filtered_recs if rec.get('confidence', 0) >= min_confidence]
            
            # Sort recommendations
            if sort_by == "Confidence":
                filtered_recs.sort(key=lambda x: x.get('confidence', 0), reverse=True)
            elif sort_by == "Symbol":
                filtered_recs.sort(key=lambda x: x.get('symbol', ''))
            elif sort_by == "Current Price":
                filtered_recs.sort(key=lambda x: x.get('current_price', 0), reverse=True)
            elif sort_by == "Swing Score":
                filtered_recs.sort(key=lambda x: x.get('swing_validation', {}).get('score', 0), reverse=True)
            
            # Display filtered recommendations
            for i, rec in enumerate(filtered_recs):
                self.display_buy_recommendation_card(rec, i, show_swing_plans)
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
        st.info("Detailed swing trading plans for all BUY recommendations with position sizing and risk management.")
        
        if st.session_state.recommendations:
            # Group recommendations by swing score
            high_score_recs = []
            medium_score_recs = []
            low_score_recs = []
            
            for rec in st.session_state.recommendations:
                swing_validation = rec.get('swing_validation', {})
                score = swing_validation.get('score', 0)
                
                if score >= 70:
                    high_score_recs.append(rec)
                elif score >= 50:
                    medium_score_recs.append(rec)
                else:
                    low_score_recs.append(rec)
            
            # Display high score recommendations
            if high_score_recs:
                st.subheader(f"🔥 High Score Swing Opportunities ({len(high_score_recs)} stocks)")
                st.success("These stocks have the highest swing trading potential (Score ≥ 70)")
                
                for i, rec in enumerate(high_score_recs):
                    swing_plan = rec.get('swing_plan', {})
                    if swing_plan:
                        self.display_swing_plan(swing_plan)
                        st.markdown("---")
            
            # Display medium score recommendations
            if medium_score_recs:
                st.subheader(f"⚡ Medium Score Swing Opportunities ({len(medium_score_recs)} stocks)")
                st.warning("These stocks have moderate swing trading potential (Score 50-69)")
                
                for i, rec in enumerate(medium_score_recs):
                    swing_plan = rec.get('swing_plan', {})
                    if swing_plan:
                        self.display_swing_plan(swing_plan)
                        st.markdown("---")
            
            # Display low score recommendations
            if low_score_recs:
                st.subheader(f"⚠️ Low Score Swing Opportunities ({len(low_score_recs)} stocks)")
                st.error("These stocks have lower swing trading potential (Score < 50)")
                
                for i, rec in enumerate(low_score_recs):
                    swing_plan = rec.get('swing_plan', {})
                    if swing_plan:
                        self.display_swing_plan(swing_plan)
                        st.markdown("---")
            
            # Strategy summary
            with st.expander("📚 7-Day Swing Strategy Summary"):
                swing_strategy = st.session_state.swing_strategy
                strategy_summary = swing_strategy.get_strategy_summary()
                
                st.markdown(f"**Strategy:** {strategy_summary['strategy_name']}")
                st.markdown(f"**Description:** {strategy_summary['description']}")
                
                st.markdown("**Key Rules:**")
                for rule in strategy_summary['key_rules']:
                    st.write(f"• {rule}")
        else:
            st.info("No swing trading plans available. Generate BUY recommendations first.")
    
    def watchlist_tab(self):
        """Watchlist tab."""
        st.header("👀 Watchlist Management")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            if st.button("🧠 Learn from Performance", type="primary"):
                self.analyze_watchlist_stocks()
        
        with col2:
            if st.button("🔄 Update Prices"):
                self.update_watchlist_prices()
        
        with col3:
            if st.button("🗑️ Clear Watchlist"):
                st.session_state.watchlist = []
                st.success("Watchlist cleared!")
                st.rerun()
        
        # Display watchlist
        if st.session_state.watchlist:
            st.subheader(f"👀 Watchlist ({len(st.session_state.watchlist)} stocks)")
            
            for i, item in enumerate(st.session_state.watchlist):
                self.display_watchlist_item(item, i)
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
            if st.button("🔍 Analyze Stock", type="primary"):
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
        st.info("Portfolio tracking feature will be implemented in future updates.")
    
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
            if st.button("🧪 Test Email Connection"):
                with st.spinner("Testing email connection..."):
                    result = email_manager.test_email_connection()
                    if result['success']:
                        st.success("✅ Email connection successful!")
                    else:
                        st.error(f"❌ Email connection failed: {result['message']}")
            
            # Email notifications toggle
            email_enabled = st.checkbox("Enable Email Notifications", value=settings.email_enabled)
            
            if st.button("💾 Save Email Settings"):
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
        
        if st.button("💾 Save Alert Preferences"):
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
                if st.button("⏸️ Pause Monitoring"):
                    price_monitor.pause_monitoring()
                    st.success("Monitoring paused!")
                    st.rerun()
                if st.button("⏹️ Stop Monitoring"):
                    price_monitor.stop_monitoring()
                    st.success("Monitoring stopped!")
                    st.rerun()
            elif monitor_status['status'] == 'paused':
                if st.button("▶️ Resume Monitoring"):
                    price_monitor.resume_monitoring()
                    st.success("Monitoring resumed!")
                    st.rerun()
            else:
                check_interval = st.number_input("Check Interval (seconds)", 30, 300, 60)
                if st.button("▶️ Start Monitoring"):
                    if monitor_status['monitored_stocks_count'] > 0:
                        price_monitor.start_monitoring(check_interval)
                        st.success("Monitoring started!")
                        st.rerun()
                    else:
                        st.warning("No stocks in watchlist to monitor!")
        
        # Add stocks from watchlist to monitoring
        if st.session_state.watchlist:
            st.markdown("**Add Watchlist Stocks to Monitoring**")
            if st.button("📊 Add All Watchlist Stocks to Monitoring"):
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
            if st.button("🗑️ Clear History"):
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
                
                st.success(f"✅ Analysis complete! Generated {len(news_recommendations)} BUY recommendations")
                
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
        if st.button(f"👀 Add {symbol} to Watchlist"):
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
