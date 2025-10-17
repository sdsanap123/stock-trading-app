#!/usr/bin/env python3
"""
Expandable UI Components
Reusable UI components for displaying data in expandable rows with + icons.
"""

import streamlit as st
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)

class ExpandableUI:
    """Reusable expandable UI components for data display."""
    
    @staticmethod
    def display_news_row(article: Dict, index: int) -> bool:
        """Display a news article in an expandable row format."""
        try:
            title = article.get('title', 'No title')
            source = article.get('source', 'Unknown')
            published = article.get('publishedAt', 'Unknown')
            sentiment = article.get('sentiment', 0)
            
            # Truncate title for display
            display_title = title[:60] + "..." if len(title) > 60 else title
            
            # Format published date
            try:
                if published and published != 'Unknown':
                    # Try to parse and format the date
                    from datetime import datetime
                    if 'T' in published:
                        date_obj = datetime.fromisoformat(published.replace('Z', '+00:00'))
                        formatted_date = date_obj.strftime('%m/%d %H:%M')
                    else:
                        formatted_date = published[:10]
                else:
                    formatted_date = 'N/A'
            except:
                formatted_date = published[:10] if published else 'N/A'
            
            # Create main row
            col1, col2, col3, col4, col5 = st.columns([3, 1.5, 1, 1, 0.8])
            
            with col1:
                st.write(f"**{display_title}**")
            
            with col2:
                st.write(source)
            
            with col3:
                st.write(formatted_date)
            
            with col4:
                # Sentiment with color
                if sentiment > 0.1:
                    st.markdown(f'<span style="color: #28a745;">+{sentiment:.2f}</span>', unsafe_allow_html=True)
                elif sentiment < -0.1:
                    st.markdown(f'<span style="color: #dc3545;">{sentiment:.2f}</span>', unsafe_allow_html=True)
                else:
                    st.write(f"{sentiment:.2f}")
            
            with col5:
                # Use popup modal instead of expander
                if st.button("➕", key=f"news_details_{index}", help="View full article details"):
                    ExpandableUI._show_news_modal(article, index)
            
            return False
            
        except Exception as e:
            logger.error(f"Error displaying news row: {str(e)}")
            return False
    
    @staticmethod
    def _display_news_details(article: Dict):
        """Display detailed news article information."""
        try:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**📰 Article Details**")
                st.write(f"• **Title:** {article.get('title', 'N/A')}")
                st.write(f"• **Source:** {article.get('source', 'N/A')}")
                st.write(f"• **Published:** {article.get('publishedAt', 'N/A')}")
                st.write(f"• **URL:** {article.get('url', 'N/A')}")
                
                # Sentiment analysis
                sentiment = article.get('sentiment', 0)
                if sentiment > 0.1:
                    st.markdown(f"• **Sentiment:** <span style='color: #28a745;'>Positive ({sentiment:.3f})</span>", unsafe_allow_html=True)
                elif sentiment < -0.1:
                    st.markdown(f"• **Sentiment:** <span style='color: #dc3545;'>Negative ({sentiment:.3f})</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"• **Sentiment:** <span style='color: #ffc107;'>Neutral ({sentiment:.3f})</span>", unsafe_allow_html=True)
            
            with col2:
                st.markdown("**📝 Content**")
                description = article.get('description', 'No description available')
                if description:
                    st.write(description)
                else:
                    st.write("No description available")
            
            # Full article link
            if article.get('url'):
                st.markdown("**🔗 Full Article**")
                st.markdown(f"[Read Full Article]({article['url']})")
            
        except Exception as e:
            logger.error(f"Error displaying news details: {str(e)}")
    
    @staticmethod
    def _show_news_modal(article: Dict, index: int):
        """Show news article details in a modal popup."""
        try:
            # Create modal title
            title = article.get('title', 'Article Details')
            modal_title = f"📰 {title[:50]}{'...' if len(title) > 50 else ''}"
            
            # Use Streamlit's modal
            with st.modal(modal_title):
                st.markdown("### 📰 Article Details")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**📋 Basic Information**")
                    st.write(f"• **Title:** {article.get('title', 'N/A')}")
                    st.write(f"• **Source:** {article.get('source', 'N/A')}")
                    st.write(f"• **Published:** {article.get('publishedAt', 'N/A')}")
                    st.write(f"• **URL:** {article.get('url', 'N/A')}")
                    
                    # Sentiment analysis
                    sentiment = article.get('sentiment', 0)
                    if sentiment > 0.1:
                        st.markdown(f"• **Sentiment:** <span style='color: #28a745;'>Positive ({sentiment:.3f})</span>", unsafe_allow_html=True)
                    elif sentiment < -0.1:
                        st.markdown(f"• **Sentiment:** <span style='color: #dc3545;'>Negative ({sentiment:.3f})</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"• **Sentiment:** <span style='color: #ffc107;'>Neutral ({sentiment:.3f})</span>", unsafe_allow_html=True)
                
                with col2:
                    st.markdown("**📊 Content Analysis**")
                    
                    # Content length
                    content = article.get('content', '')
                    if content:
                        word_count = len(content.split())
                        st.write(f"• **Word Count:** {word_count}")
                        
                        # Show first 200 characters of content
                        preview = content[:200] + "..." if len(content) > 200 else content
                        st.write(f"• **Content Preview:**")
                        st.text(preview)
                    else:
                        st.write("• **Content:** Not available")
                    
                    # Keywords (if available)
                    keywords = article.get('keywords', [])
                    if keywords:
                        st.write(f"• **Keywords:** {', '.join(keywords[:5])}")
                    
                    # Impact assessment
                    impact = article.get('impact_level', 'MEDIUM')
                    if impact == 'HIGH':
                        st.markdown(f"• **Impact:** <span style='color: #dc3545;'>High</span>", unsafe_allow_html=True)
                    elif impact == 'MEDIUM':
                        st.markdown(f"• **Impact:** <span style='color: #ffc107;'>Medium</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"• **Impact:** <span style='color: #28a745;'>Low</span>", unsafe_allow_html=True)
                
                # Full content section
                if content and len(content) > 200:
                    st.markdown("### 📄 Full Article Content")
                    st.markdown(content)
                
                # Close button
                if st.button("❌ Close", key=f"close_news_modal_{index}"):
                    st.rerun()
                    
        except Exception as e:
            logger.error(f"Error showing news modal: {str(e)}")
            st.error("Error displaying article details")
    
    @staticmethod
    def display_recommendation_row(rec: Dict, index: int, show_actions: bool = True) -> bool:
        """Display a recommendation in an expandable row format."""
        try:
            symbol = rec.get('symbol', 'UNKNOWN')
            company_name = rec.get('company_name', '')
            current_price = rec.get('current_price', 0)
            recommendation = rec.get('recommendation', '')
            confidence = rec.get('confidence', 0)
            target_price = rec.get('target_price', 0)
            stop_loss = rec.get('stop_loss', 0)
            created_at = rec.get('created_at', '')
            
            # Format date
            try:
                if created_at:
                    date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    formatted_date = date_obj.strftime('%Y-%m-%d %H:%M')
                else:
                    formatted_date = 'N/A'
            except:
                formatted_date = created_at[:19] if created_at else 'N/A'
            
            # Create main row - more compact with unique key
            col1, col2, col3, col4, col5, col6, col7 = st.columns([1.5, 1.5, 1, 1, 1, 0.8, 0.8])
            
            with col1:
                # Add warning symbol if recommendation has changed
                warning_symbol = ""
                if rec.get('change_detected', False):
                    change_type = rec.get('change_type', '')
                    if change_type == 'action_change':
                        warning_symbol = "🔄 "
                    elif change_type == 'confidence_change':
                        warning_symbol = "📊 "
                    elif change_type == 'target_change':
                        warning_symbol = "🎯 "
                    elif change_type == 'stop_loss_change':
                        warning_symbol = "🛑 "
                    else:
                        warning_symbol = "⚠️ "
                
                st.write(f"{warning_symbol}**{symbol}**")
                if company_name:
                    st.caption(company_name)
            
            with col2:
                st.write(f"₹{current_price:.2f}")
                st.caption(f"Confidence: {confidence:.1f}%")
            
            with col3:
                # Recommendation with color
                if recommendation == 'BUY':
                    st.markdown('<span style="color: #28a745; font-weight: bold;">📈 BUY</span>', unsafe_allow_html=True)
                elif recommendation == 'SELL':
                    st.markdown('<span style="color: #dc3545; font-weight: bold;">📉 SELL</span>', unsafe_allow_html=True)
                else:
                    st.markdown('<span style="color: #ffc107; font-weight: bold;">➡️ HOLD</span>', unsafe_allow_html=True)
            
            with col4:
                st.write(f"₹{target_price:.2f}")
                st.caption("Target")
            
            with col5:
                st.write(f"₹{stop_loss:.2f}")
                st.caption("Stop Loss")
            
            with col6:
                # Use popup modal instead of expander
                if st.button("➕", key=f"rec_details_{index}", help="View full analysis details"):
                    ExpandableUI._show_recommendation_modal(rec, index)
            
            with col7:
                # Add to watchlist button
                if show_actions:
                    watchlist_key = f"add_watchlist_{index}_{symbol}"
                    if st.button("👀", key=watchlist_key, help="Add to watchlist"):
                        # This will be handled by the calling function
                        st.session_state[f"add_to_watchlist_{index}"] = True
            
            return False
            
        except Exception as e:
            logger.error(f"Error displaying recommendation row: {str(e)}")
            return False
    
    @staticmethod
    def _display_recommendation_details(rec: Dict):
        """Display detailed recommendation information."""
        try:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**📊 Trading Details**")
                st.write(f"• **Current Price:** ₹{rec.get('current_price', 0):.2f}")
                st.write(f"• **Target Price:** ₹{rec.get('target_price', 0):.2f}")
                st.write(f"• **Stop Loss:** ₹{rec.get('stop_loss', 0):.2f}")
                st.write(f"• **Confidence:** {rec.get('confidence', 0):.1f}%")
                
                # Risk-Reward Ratio
                current_price = rec.get('current_price', 0)
                target_price = rec.get('target_price', 0)
                stop_loss = rec.get('stop_loss', 0)
                
                if current_price > 0 and target_price > 0 and stop_loss > 0:
                    potential_profit = target_price - current_price
                    potential_loss = current_price - stop_loss
                    if potential_loss > 0:
                        risk_reward = potential_profit / potential_loss
                        st.write(f"• **Risk-Reward Ratio:** {risk_reward:.2f}:1")
            
            with col2:
                st.markdown("**📈 Swing Trading Plan**")
                swing_plan = rec.get('swing_plan', {})
                if swing_plan:
                    st.write(f"• **Position Size:** {swing_plan.get('position_size', 0)} shares")
                    st.write(f"• **Investment:** ₹{swing_plan.get('investment_amount', 0):,.0f}")
                    st.write(f"• **Risk Amount:** ₹{swing_plan.get('risk_amount', 0):,.0f}")
                    st.write(f"• **Holding Period:** {swing_plan.get('holding_period_days', 7)} days")
                else:
                    st.write("No swing plan available")
            
            # Change Information
            if rec.get('change_detected', False):
                st.markdown("**⚠️ Recent Changes**")
                change_type = rec.get('change_type', '')
                change_details = rec.get('change_details', {})
                
                if change_type == 'action_change':
                    st.markdown(f"• **Action Changed:** {change_details.get('change', 'N/A')}")
                elif change_type == 'confidence_change':
                    st.markdown(f"• **Confidence Changed:** {change_details.get('change', 'N/A')}")
                elif change_type == 'target_change':
                    st.markdown(f"• **Target Price Changed:** {change_details.get('change', 'N/A')}")
                elif change_type == 'stop_loss_change':
                    st.markdown(f"• **Stop Loss Changed:** {change_details.get('change', 'N/A')}")
                else:
                    st.markdown(f"• **Recommendation Updated:** {change_type}")
                
                last_updated = rec.get('last_updated', '')
                if last_updated:
                    try:
                        from datetime import datetime
                        update_time = datetime.fromisoformat(last_updated)
                        formatted_time = update_time.strftime('%Y-%m-%d %H:%M:%S')
                        st.caption(f"Last updated: {formatted_time}")
                    except:
                        st.caption(f"Last updated: {last_updated}")
            
            # Reasoning
            reasoning = rec.get('reasoning', '')
            if reasoning:
                st.markdown("**💭 AI Reasoning**")
                st.markdown(reasoning)
            
            # Technical Analysis
            technical_data = rec.get('technical_data', {})
            if technical_data:
                st.markdown("**📊 Technical Indicators**")
                tech_col1, tech_col2 = st.columns(2)
                
                with tech_col1:
                    st.write(f"• **RSI:** {technical_data.get('rsi', 0):.1f}")
                    st.write(f"• **MACD:** {technical_data.get('macd', 0):.4f}")
                    st.write(f"• **SMA 20:** ₹{technical_data.get('sma_20', 0):.2f}")
                
                with tech_col2:
                    st.write(f"• **Volume Ratio:** {technical_data.get('volume_ratio_20', 0):.2f}")
                    st.write(f"• **ATR:** ₹{technical_data.get('atr', 0):.2f}")
                    st.write(f"• **Bollinger Position:** {technical_data.get('bb_position', 0):.2f}")
            
            # Groq Analysis
            groq_analysis = rec.get('groq_analysis', {})
            if groq_analysis and groq_analysis.get('status') == 'success':
                st.markdown("**🤖 Groq AI Analysis**")
                st.write(f"• **Sentiment:** {groq_analysis.get('sentiment_label', 'N/A')}")
                st.write(f"• **Impact Level:** {groq_analysis.get('impact_level', 'N/A')}")
                st.write(f"• **Price Impact:** {groq_analysis.get('price_impact', 'N/A')}")
                st.write(f"• **Swing Potential:** {groq_analysis.get('swing_trading_potential', 'N/A')}")
            
        except Exception as e:
            logger.error(f"Error displaying recommendation details: {str(e)}")
    
    @staticmethod
    def _show_recommendation_modal(rec: Dict, index: int):
        """Show recommendation details in a modal popup."""
        try:
            symbol = rec.get('symbol', 'UNKNOWN')
            company_name = rec.get('company_name', '')
            modal_title = f"📊 {symbol} Analysis"
            if company_name:
                modal_title += f" - {company_name}"
            
            # Use Streamlit's modal
            with st.modal(modal_title):
                st.markdown("### 📊 Trading Analysis")
                
                # Trading Details
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**💰 Trading Details**")
                    st.write(f"• **Current Price:** ₹{rec.get('current_price', 0):.2f}")
                    st.write(f"• **Target Price:** ₹{rec.get('target_price', 0):.2f}")
                    st.write(f"• **Stop Loss:** ₹{rec.get('stop_loss', 0):.2f}")
                    st.write(f"• **Confidence:** {rec.get('confidence', 0):.1f}%")
                    
                    # Risk-Reward Ratio
                    current_price = rec.get('current_price', 0)
                    target_price = rec.get('target_price', 0)
                    stop_loss = rec.get('stop_loss', 0)
                    
                    if current_price > 0 and target_price > 0 and stop_loss > 0:
                        potential_profit = target_price - current_price
                        potential_loss = current_price - stop_loss
                        if potential_loss > 0:
                            risk_reward = potential_profit / potential_loss
                            st.write(f"• **Risk-Reward Ratio:** {risk_reward:.2f}:1")
                
                with col2:
                    st.markdown("**📈 Swing Trading Plan**")
                    swing_plan = rec.get('swing_plan', {})
                    if swing_plan:
                        st.write(f"• **Position Size:** {swing_plan.get('position_size', 0)} shares")
                        st.write(f"• **Investment:** ₹{swing_plan.get('investment_amount', 0):,.0f}")
                        st.write(f"• **Risk Amount:** ₹{swing_plan.get('risk_amount', 0):,.0f}")
                        st.write(f"• **Holding Period:** {swing_plan.get('holding_period_days', 7)} days")
                    else:
                        st.write("No swing plan available")
                
                # Change Information
                if rec.get('change_detected', False):
                    st.markdown("### ⚠️ Recent Changes")
                    change_type = rec.get('change_type', '')
                    change_details = rec.get('change_details', {})
                    
                    if change_type == 'action_change':
                        st.markdown(f"• **Action Changed:** {change_details.get('change', 'N/A')}")
                    elif change_type == 'confidence_change':
                        st.markdown(f"• **Confidence Changed:** {change_details.get('change', 'N/A')}")
                    elif change_type == 'target_change':
                        st.markdown(f"• **Target Price Changed:** {change_details.get('change', 'N/A')}")
                    elif change_type == 'stop_loss_change':
                        st.markdown(f"• **Stop Loss Changed:** {change_details.get('change', 'N/A')}")
                    else:
                        st.markdown(f"• **Recommendation Updated:** {change_type}")
                    
                    last_updated = rec.get('last_updated', '')
                    if last_updated:
                        try:
                            from datetime import datetime
                            update_time = datetime.fromisoformat(last_updated)
                            formatted_time = update_time.strftime('%Y-%m-%d %H:%M:%S')
                            st.caption(f"Last updated: {formatted_time}")
                        except:
                            st.caption(f"Last updated: {last_updated}")
                
                # AI Reasoning
                reasoning = rec.get('reasoning', '')
                if reasoning:
                    st.markdown("### 💭 AI Reasoning")
                    st.markdown(reasoning)
                
                # Technical Analysis
                technical_data = rec.get('technical_data', {})
                if technical_data:
                    st.markdown("### 📊 Technical Indicators")
                    tech_col1, tech_col2 = st.columns(2)
                    
                    with tech_col1:
                        st.write(f"• **RSI:** {technical_data.get('rsi', 0):.1f}")
                        st.write(f"• **MACD:** {technical_data.get('macd', 0):.4f}")
                        st.write(f"• **SMA 20:** ₹{technical_data.get('sma_20', 0):.2f}")
                    
                    with tech_col2:
                        st.write(f"• **Volume Ratio:** {technical_data.get('volume_ratio_20', 0):.2f}")
                        st.write(f"• **ATR:** ₹{technical_data.get('atr', 0):.2f}")
                        st.write(f"• **Bollinger Position:** {technical_data.get('bb_position', 0):.2f}")
                
                # Groq Analysis
                groq_analysis = rec.get('groq_analysis', {})
                if groq_analysis and groq_analysis.get('status') == 'success':
                    st.markdown("### 🤖 Groq AI Analysis")
                    st.write(f"• **Sentiment:** {groq_analysis.get('sentiment_label', 'N/A')}")
                    st.write(f"• **Impact Level:** {groq_analysis.get('impact_level', 'N/A')}")
                    st.write(f"• **Price Impact:** {groq_analysis.get('price_impact', 'N/A')}")
                    st.write(f"• **Swing Potential:** {groq_analysis.get('swing_trading_potential', 'N/A')}")
                
                # Close button
                if st.button("❌ Close", key=f"close_rec_modal_{index}"):
                    st.rerun()
                    
        except Exception as e:
            logger.error(f"Error showing recommendation modal: {str(e)}")
            st.error("Error displaying recommendation details")
    
    @staticmethod
    def display_watchlist_row(item: Dict, index: int, show_actions: bool = True) -> bool:
        """Display a watchlist item in an expandable row format."""
        try:
            symbol = item.get('symbol', 'UNKNOWN')
            company_name = item.get('company_name', '')
            current_price = item.get('current_price', 0)
            entry_price = item.get('entry_price', 0)
            target_price = item.get('target_price', 0)
            stop_loss = item.get('stop_loss', 0)
            status = item.get('status', 'ACTIVE')
            added_date = item.get('added_date', '')
            
            # Calculate P&L
            if entry_price > 0:
                pnl = ((current_price - entry_price) / entry_price) * 100
                pnl_amount = current_price - entry_price
            else:
                pnl = 0
                pnl_amount = 0
            
            # Format date
            try:
                if added_date:
                    date_obj = datetime.fromisoformat(added_date.replace('Z', '+00:00'))
                    formatted_date = date_obj.strftime('%Y-%m-%d')
                else:
                    formatted_date = 'N/A'
            except:
                formatted_date = added_date[:10] if added_date else 'N/A'
            
            # Create main row - more compact
            col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([1.5, 1, 1, 1, 1, 1, 1, 0.8])
            
            with col1:
                # Add warning symbol if there are recommendation changes for this stock
                warning_symbol = ""
                # Check if this stock has recommendation changes (this would be passed from the app)
                if item.get('recommendation_changed', False):
                    change_type = item.get('recommendation_change_type', '')
                    if change_type == 'action_change':
                        warning_symbol = "🔄 "
                    elif change_type == 'confidence_change':
                        warning_symbol = "📊 "
                    elif change_type == 'target_change':
                        warning_symbol = "🎯 "
                    elif change_type == 'stop_loss_change':
                        warning_symbol = "🛑 "
                    else:
                        warning_symbol = "⚠️ "
                
                st.write(f"{warning_symbol}**{symbol}**")
                if company_name:
                    st.caption(company_name)
                st.caption(f"Added: {formatted_date}")
            
            with col2:
                st.write(f"₹{current_price:.2f}")
                st.caption("Current")
            
            with col3:
                st.write(f"₹{entry_price:.2f}")
                st.caption("Entry")
            
            with col4:
                # P&L with color
                if pnl > 0:
                    st.markdown(f'<span style="color: #28a745;">+{pnl:.1f}%</span>', unsafe_allow_html=True)
                    st.caption(f"+₹{pnl_amount:.2f}")
                elif pnl < 0:
                    st.markdown(f'<span style="color: #dc3545;">{pnl:.1f}%</span>', unsafe_allow_html=True)
                    st.caption(f"₹{pnl_amount:.2f}")
                else:
                    st.write("0.0%")
                    st.caption("₹0.00")
            
            with col5:
                st.write(f"₹{target_price:.2f}")
                st.caption("Target")
            
            with col6:
                st.write(f"₹{stop_loss:.2f}")
                st.caption("Stop Loss")
            
            with col7:
                # Status with color
                if status == 'ACTIVE':
                    st.markdown('<span style="color: #28a745;">🟢 Active</span>', unsafe_allow_html=True)
                elif status == 'TARGET_HIT':
                    st.markdown('<span style="color: #ffc107;">🎯 Target Hit</span>', unsafe_allow_html=True)
                elif status == 'STOP_LOSS_HIT':
                    st.markdown('<span style="color: #dc3545;">🛑 Stop Loss</span>', unsafe_allow_html=True)
                else:
                    st.write(f"📊 {status}")
            
            with col8:
                # Use popup modal instead of expander
                if st.button("➕", key=f"watchlist_details_{index}", help="View full watchlist details"):
                    ExpandableUI._show_watchlist_modal(item, index)
            
            return False
            
        except Exception as e:
            logger.error(f"Error displaying watchlist row: {str(e)}")
            return False
    
    @staticmethod
    def _display_watchlist_details(item: Dict):
        """Display detailed watchlist information."""
        try:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**📊 Position Details**")
                st.write(f"• **Symbol:** {item.get('symbol', 'N/A')}")
                st.write(f"• **Entry Price:** ₹{item.get('entry_price', 0):.2f}")
                st.write(f"• **Current Price:** ₹{item.get('current_price', 0):.2f}")
                st.write(f"• **Target Price:** ₹{item.get('target_price', 0):.2f}")
                st.write(f"• **Stop Loss:** ₹{item.get('stop_loss', 0):.2f}")
                
                # Calculate distances to targets
                current_price = item.get('current_price', 0)
                target_price = item.get('target_price', 0)
                stop_loss = item.get('stop_loss', 0)
                
                if current_price > 0:
                    if target_price > 0:
                        target_distance = ((target_price - current_price) / current_price) * 100
                        st.write(f"• **Distance to Target:** {target_distance:.1f}%")
                    
                    if stop_loss > 0:
                        stop_distance = ((current_price - stop_loss) / current_price) * 100
                        st.write(f"• **Distance to Stop Loss:** {stop_distance:.1f}%")
            
            with col2:
                st.markdown("**📈 Performance Metrics**")
                
                # P&L calculations
                entry_price = item.get('entry_price', 0)
                current_price = item.get('current_price', 0)
                
                if entry_price > 0:
                    pnl_percent = ((current_price - entry_price) / entry_price) * 100
                    pnl_amount = current_price - entry_price
                    
                    st.write(f"• **P&L Percentage:** {pnl_percent:.2f}%")
                    st.write(f"• **P&L Amount:** ₹{pnl_amount:.2f}")
                    
                    # Risk-Reward
                    target_price = item.get('target_price', 0)
                    stop_loss = item.get('stop_loss', 0)
                    
                    if target_price > 0 and stop_loss > 0:
                        potential_profit = target_price - entry_price
                        potential_loss = entry_price - stop_loss
                        if potential_loss > 0:
                            risk_reward = potential_profit / potential_loss
                            st.write(f"• **Risk-Reward Ratio:** {risk_reward:.2f}:1")
                
                st.write(f"• **Status:** {item.get('status', 'N/A')}")
                st.write(f"• **Confidence:** {item.get('confidence', 0):.1f}%")
            
            # Notes
            notes = item.get('notes', '')
            if notes:
                st.markdown("**📝 Notes**")
                st.write(notes)
            
            # Action buttons
            st.markdown("**⚡ Actions**")
            action_col1, action_col2, action_col3 = st.columns(3)
            
            with action_col1:
                if st.button(f"📊 Update Price", key=f"update_{item.get('symbol')}"):
                    st.info("Price update functionality will be implemented")
            
            with action_col2:
                if st.button(f"✏️ Edit", key=f"edit_{item.get('symbol')}"):
                    st.info("Edit functionality will be implemented")
            
            with action_col3:
                if st.button(f"🗑️ Remove", key=f"remove_{item.get('symbol')}"):
                    st.info("Remove functionality will be implemented")
            
        except Exception as e:
            logger.error(f"Error displaying watchlist details: {str(e)}")
    
    @staticmethod
    def _show_watchlist_modal(item: Dict, index: int):
        """Show watchlist details in a modal popup."""
        try:
            symbol = item.get('symbol', 'UNKNOWN')
            company_name = item.get('company_name', '')
            modal_title = f"👀 {symbol} Watchlist"
            if company_name:
                modal_title += f" - {company_name}"
            
            # Use Streamlit's modal
            with st.modal(modal_title):
                st.markdown("### 👀 Watchlist Position")
                
                # Position Details
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**📊 Position Details**")
                    st.write(f"• **Symbol:** {item.get('symbol', 'N/A')}")
                    st.write(f"• **Entry Price:** ₹{item.get('entry_price', 0):.2f}")
                    st.write(f"• **Current Price:** ₹{item.get('current_price', 0):.2f}")
                    st.write(f"• **Target Price:** ₹{item.get('target_price', 0):.2f}")
                    st.write(f"• **Stop Loss:** ₹{item.get('stop_loss', 0):.2f}")
                    
                    # Calculate distances to targets
                    current_price = item.get('current_price', 0)
                    target_price = item.get('target_price', 0)
                    stop_loss = item.get('stop_loss', 0)
                    
                    if current_price > 0:
                        if target_price > 0:
                            target_distance = ((target_price - current_price) / current_price) * 100
                            st.write(f"• **Distance to Target:** {target_distance:.1f}%")
                        
                        if stop_loss > 0:
                            stop_distance = ((current_price - stop_loss) / current_price) * 100
                            st.write(f"• **Distance to Stop Loss:** {stop_distance:.1f}%")
                
                with col2:
                    st.markdown("**📈 Performance Metrics**")
                    
                    # P&L calculations
                    entry_price = item.get('entry_price', 0)
                    current_price = item.get('current_price', 0)
                    
                    if entry_price > 0:
                        pnl_percent = ((current_price - entry_price) / entry_price) * 100
                        pnl_amount = current_price - entry_price
                        
                        st.write(f"• **P&L Percentage:** {pnl_percent:.2f}%")
                        st.write(f"• **P&L Amount:** ₹{pnl_amount:.2f}")
                        
                        # Risk-Reward
                        target_price = item.get('target_price', 0)
                        stop_loss = item.get('stop_loss', 0)
                        
                        if target_price > 0 and stop_loss > 0:
                            potential_profit = target_price - entry_price
                            potential_loss = entry_price - stop_loss
                            if potential_loss > 0:
                                risk_reward = potential_profit / potential_loss
                                st.write(f"• **Risk-Reward Ratio:** {risk_reward:.2f}:1")
                    
                    st.write(f"• **Status:** {item.get('status', 'N/A')}")
                    st.write(f"• **Confidence:** {item.get('confidence', 0):.1f}%")
                
                # Recommendation Changes (if any)
                if item.get('recommendation_changed', False):
                    st.markdown("### ⚠️ Recent Recommendation Changes")
                    change_type = item.get('recommendation_change_type', '')
                    change_details = item.get('recommendation_change_details', {})
                    
                    if change_type == 'action_change':
                        st.markdown(f"• **Action Changed:** {change_details.get('change', 'N/A')}")
                    elif change_type == 'confidence_change':
                        st.markdown(f"• **Confidence Changed:** {change_details.get('change', 'N/A')}")
                    elif change_type == 'target_change':
                        st.markdown(f"• **Target Price Changed:** {change_details.get('change', 'N/A')}")
                    elif change_type == 'stop_loss_change':
                        st.markdown(f"• **Stop Loss Changed:** {change_details.get('change', 'N/A')}")
                    else:
                        st.markdown(f"• **Recommendation Updated:** {change_type}")
                    
                    last_updated = item.get('recommendation_last_updated', '')
                    if last_updated:
                        try:
                            from datetime import datetime
                            update_time = datetime.fromisoformat(last_updated)
                            formatted_time = update_time.strftime('%Y-%m-%d %H:%M:%S')
                            st.caption(f"Last updated: {formatted_time}")
                        except:
                            st.caption(f"Last updated: {last_updated}")
                
                # Notes
                notes = item.get('notes', '')
                if notes:
                    st.markdown("### 📝 Notes")
                    st.write(notes)
                
                # Action buttons
                st.markdown("### ⚡ Actions")
                action_col1, action_col2, action_col3 = st.columns(3)
                
                with action_col1:
                    if st.button(f"📊 Update Price", key=f"modal_update_{symbol}_{index}"):
                        st.info("Price update functionality will be implemented")
                
                with action_col2:
                    if st.button(f"✏️ Edit", key=f"modal_edit_{symbol}_{index}"):
                        st.info("Edit functionality will be implemented")
                
                with action_col3:
                    if st.button(f"🗑️ Remove", key=f"modal_remove_{symbol}_{index}"):
                        st.info("Remove functionality will be implemented")
                
                # Close button
                if st.button("❌ Close", key=f"close_watchlist_modal_{index}"):
                    st.rerun()
                    
        except Exception as e:
            logger.error(f"Error showing watchlist modal: {str(e)}")
            st.error("Error displaying watchlist details")
    
    @staticmethod
    def display_swing_strategy_row(strategy: Dict, index: int, show_actions: bool = True) -> bool:
        """Display a swing strategy in an expandable row format."""
        try:
            symbol = strategy.get('symbol', 'UNKNOWN')
            company_name = strategy.get('company_name', '')
            entry_price = strategy.get('entry_price', 0)
            take_profit = strategy.get('take_profit', 0)
            stop_loss = strategy.get('stop_loss', 0)
            position_size = strategy.get('position_size', 0)
            investment_amount = strategy.get('investment_amount', 0)
            risk_reward_ratio = strategy.get('risk_reward_ratio', 0)
            status = strategy.get('status', 'ACTIVE')
            created_at = strategy.get('created_at', '')
            
            # Format date
            try:
                if created_at:
                    date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    formatted_date = date_obj.strftime('%Y-%m-%d %H:%M')
                else:
                    formatted_date = 'N/A'
            except:
                formatted_date = created_at[:19] if created_at else 'N/A'
            
            # Create main row - more compact
            col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([1.5, 1, 1, 1, 1, 1, 0.8, 0.8])
            
            with col1:
                st.write(f"**{symbol}**")
                if company_name:
                    st.caption(company_name)
                st.caption(f"Created: {formatted_date}")
            
            with col2:
                st.write(f"₹{entry_price:.2f}")
                st.caption("Entry Price")
            
            with col3:
                st.write(f"₹{take_profit:.2f}")
                st.caption("Take Profit")
            
            with col4:
                st.write(f"₹{stop_loss:.2f}")
                st.caption("Stop Loss")
            
            with col5:
                st.write(f"{position_size}")
                st.caption("Position Size")
            
            with col6:
                # Risk-Reward with color
                if risk_reward_ratio >= 2.0:
                    st.markdown(f'<span style="color: #28a745;">{risk_reward_ratio:.2f}:1</span>', unsafe_allow_html=True)
                elif risk_reward_ratio >= 1.5:
                    st.markdown(f'<span style="color: #ffc107;">{risk_reward_ratio:.2f}:1</span>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<span style="color: #dc3545;">{risk_reward_ratio:.2f}:1</span>', unsafe_allow_html=True)
                st.caption("Risk-Reward")
            
            with col7:
                # Use popup modal instead of expander
                if st.button("➕", key=f"swing_details_{index}", help="View full swing strategy details"):
                    ExpandableUI._show_swing_strategy_modal(strategy, index)
            
            with col8:
                # Add to watchlist button
                if show_actions:
                    watchlist_key = f"add_swing_watchlist_{index}_{symbol}"
                    if st.button("👀", key=watchlist_key, help="Add to watchlist"):
                        # This will be handled by the calling function
                        st.session_state[f"add_swing_to_watchlist_{index}"] = True
            
            return False
            
        except Exception as e:
            logger.error(f"Error displaying swing strategy row: {str(e)}")
            return False
    
    @staticmethod
    def _display_swing_strategy_details(strategy: Dict):
        """Display detailed swing strategy information."""
        try:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**📊 Strategy Overview**")
                st.write(f"• **Symbol:** {strategy.get('symbol', 'N/A')}")
                st.write(f"• **Strategy Name:** {strategy.get('strategy_name', 'N/A')}")
                st.write(f"• **Entry Price:** ₹{strategy.get('entry_price', 0):.2f}")
                st.write(f"• **Take Profit:** ₹{strategy.get('take_profit', 0):.2f}")
                st.write(f"• **Stop Loss:** ₹{strategy.get('stop_loss', 0):.2f}")
                st.write(f"• **Holding Period:** {strategy.get('holding_period_days', 7)} days")
            
            with col2:
                st.markdown("**💰 Position Details**")
                st.write(f"• **Position Size:** {strategy.get('position_size', 0)} shares")
                st.write(f"• **Investment Amount:** ₹{strategy.get('investment_amount', 0):,.0f}")
                st.write(f"• **Risk Amount:** ₹{strategy.get('risk_amount', 0):,.0f}")
                st.write(f"• **Risk-Reward Ratio:** {strategy.get('risk_reward_ratio', 0):.2f}:1")
                st.write(f"• **Confidence:** {strategy.get('confidence', 0):.1f}%")
                st.write(f"• **Status:** {strategy.get('status', 'N/A')}")
            
            # Timeline
            st.markdown("**📅 Timeline**")
            timeline_col1, timeline_col2 = st.columns(2)
            
            with timeline_col1:
                st.write(f"• **Entry Date:** {strategy.get('entry_date', 'N/A')[:10]}")
                st.write(f"• **Created:** {strategy.get('created_at', 'N/A')[:19]}")
            
            with timeline_col2:
                st.write(f"• **Expected Exit:** {strategy.get('expected_exit_date', 'N/A')[:10]}")
                
                # Calculate days remaining
                try:
                    exit_date = datetime.fromisoformat(strategy.get('expected_exit_date', '').replace('Z', '+00:00'))
                    days_remaining = (exit_date - datetime.now()).days
                    if days_remaining > 0:
                        st.write(f"• **Days Remaining:** {days_remaining}")
                    else:
                        st.write(f"• **Status:** Expired")
                except:
                    st.write(f"• **Days Remaining:** N/A")
            
            # Strategy Rules
            st.markdown("**📋 Strategy Rules**")
            st.write("• Hold for maximum 7 days")
            st.write("• Stop loss at 8% below entry")
            st.write("• Take profit at 15% above entry")
            st.write("• Monitor daily for exit signals")
            st.write("• Do not average down if trade goes against you")
            
            # Action buttons
            st.markdown("**⚡ Actions**")
            action_col1, action_col2, action_col3 = st.columns(3)
            
            with action_col1:
                if st.button(f"📊 Update Status", key=f"update_swing_{strategy.get('symbol')}"):
                    st.info("Status update functionality will be implemented")
            
            with action_col2:
                if st.button(f"✏️ Edit Strategy", key=f"edit_swing_{strategy.get('symbol')}"):
                    st.info("Edit functionality will be implemented")
            
            with action_col3:
                if st.button(f"🗑️ Remove Strategy", key=f"remove_swing_{strategy.get('symbol')}"):
                    st.info("Remove functionality will be implemented")
            
        except Exception as e:
            logger.error(f"Error displaying swing strategy details: {str(e)}")
    
    @staticmethod
    def _show_swing_strategy_modal(strategy: Dict, index: int):
        """Show swing strategy details in a modal popup."""
        try:
            symbol = strategy.get('symbol', 'UNKNOWN')
            company_name = strategy.get('company_name', '')
            modal_title = f"📈 {symbol} Swing Strategy"
            if company_name:
                modal_title += f" - {company_name}"
            
            # Use Streamlit's modal
            with st.modal(modal_title):
                st.markdown("### 📈 Swing Trading Strategy")
                
                # Strategy Details
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**💰 Trading Parameters**")
                    st.write(f"• **Symbol:** {strategy.get('symbol', 'N/A')}")
                    st.write(f"• **Entry Price:** ₹{strategy.get('entry_price', 0):.2f}")
                    st.write(f"• **Take Profit:** ₹{strategy.get('take_profit', 0):.2f}")
                    st.write(f"• **Stop Loss:** ₹{strategy.get('stop_loss', 0):.2f}")
                    st.write(f"• **Position Size:** {strategy.get('position_size', 0)} shares")
                    st.write(f"• **Investment:** ₹{strategy.get('investment_amount', 0):,.0f}")
                
                with col2:
                    st.markdown("**📊 Risk Management**")
                    st.write(f"• **Risk Amount:** ₹{strategy.get('risk_amount', 0):,.0f}")
                    st.write(f"• **Risk-Reward Ratio:** {strategy.get('risk_reward_ratio', 0):.2f}:1")
                    st.write(f"• **Holding Period:** {strategy.get('holding_period_days', 7)} days")
                    st.write(f"• **Status:** {strategy.get('status', 'N/A')}")
                    st.write(f"• **Created:** {strategy.get('created_at', 'N/A')}")
                
                # Strategy Rules
                strategy_rules = strategy.get('strategy_rules', [])
                if strategy_rules:
                    st.markdown("### 📋 Strategy Rules")
                    for i, rule in enumerate(strategy_rules, 1):
                        st.write(f"{i}. {rule}")
                
                # Market Conditions
                market_conditions = strategy.get('market_conditions', {})
                if market_conditions:
                    st.markdown("### 🌍 Market Conditions")
                    st.write(f"• **Trend:** {market_conditions.get('trend', 'N/A')}")
                    st.write(f"• **Volatility:** {market_conditions.get('volatility', 'N/A')}")
                    st.write(f"• **Volume:** {market_conditions.get('volume', 'N/A')}")
                
                # Technical Analysis
                technical_analysis = strategy.get('technical_analysis', {})
                if technical_analysis:
                    st.markdown("### 📊 Technical Analysis")
                    tech_col1, tech_col2 = st.columns(2)
                    
                    with tech_col1:
                        st.write(f"• **RSI:** {technical_analysis.get('rsi', 0):.1f}")
                        st.write(f"• **MACD:** {technical_analysis.get('macd', 0):.4f}")
                        st.write(f"• **SMA 20:** ₹{technical_analysis.get('sma_20', 0):.2f}")
                    
                    with tech_col2:
                        st.write(f"• **Volume Ratio:** {technical_analysis.get('volume_ratio_20', 0):.2f}")
                        st.write(f"• **ATR:** ₹{technical_analysis.get('atr', 0):.2f}")
                        st.write(f"• **Bollinger Position:** {technical_analysis.get('bb_position', 0):.2f}")
                
                # Action buttons
                st.markdown("### ⚡ Actions")
                action_col1, action_col2, action_col3 = st.columns(3)
                
                with action_col1:
                    if st.button(f"📊 Update Price", key=f"modal_swing_update_{symbol}_{index}"):
                        st.info("Price update functionality will be implemented")
                
                with action_col2:
                    if st.button(f"✏️ Edit Strategy", key=f"modal_swing_edit_{symbol}_{index}"):
                        st.info("Edit functionality will be implemented")
                
                with action_col3:
                    if st.button(f"🗑️ Remove Strategy", key=f"modal_swing_remove_{symbol}_{index}"):
                        st.info("Remove functionality will be implemented")
                
                # Close button
                if st.button("❌ Close", key=f"close_swing_modal_{index}"):
                    st.rerun()
                    
        except Exception as e:
            logger.error(f"Error showing swing strategy modal: {str(e)}")
            st.error("Error displaying swing strategy details")
    
    @staticmethod
    def display_data_summary(summary: Dict):
        """Display a summary of all saved data."""
        try:
            st.markdown("**📊 Data Summary**")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Recommendations",
                    summary.get('recommendations', {}).get('total_count', 0),
                    f"{summary.get('recommendations', {}).get('dates_count', 0)} dates"
                )
            
            with col2:
                watchlist_data = summary.get('watchlist', {})
                st.metric(
                    "Watchlist Items",
                    watchlist_data.get('total_count', 0),
                    f"{watchlist_data.get('active_count', 0)} active"
                )
            
            with col3:
                swing_data = summary.get('swing_strategies', {})
                st.metric(
                    "Swing Strategies",
                    swing_data.get('total_count', 0),
                    f"{swing_data.get('dates_count', 0)} dates"
                )
            
        except Exception as e:
            logger.error(f"Error displaying data summary: {str(e)}")
