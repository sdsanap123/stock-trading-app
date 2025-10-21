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
            
            # Create main row
            col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 1.5, 1.5, 1.5, 1])
            
            with col1:
                st.write(f"**{symbol}**")
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
                # Expandable button
                expand_key = f"expand_rec_{index}_{symbol}"
                expanded = st.button("➕", key=expand_key, help="Click to expand details")
            
            # Display expanded content if button was clicked
            if expanded:
                with st.expander(f"📊 Detailed Analysis for {symbol}", expanded=True):
                    ExpandableUI._display_recommendation_details(rec)
            
            return expanded
            
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
            
            # Create main row
            col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 1.5, 1.5, 1.5, 1.5, 1.5, 1])
            
            with col1:
                st.write(f"**{symbol}**")
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
                # Status with color
                if status == 'ACTIVE':
                    st.markdown('<span style="color: #28a745;">🟢 Active</span>', unsafe_allow_html=True)
                elif status == 'TARGET_HIT':
                    st.markdown('<span style="color: #ffc107;">🎯 Target Hit</span>', unsafe_allow_html=True)
                elif status == 'STOP_LOSS_HIT':
                    st.markdown('<span style="color: #dc3545;">🛑 Stop Loss</span>', unsafe_allow_html=True)
                else:
                    st.write(f"📊 {status}")
            
            with col7:
                # Expandable button
                expand_key = f"expand_watch_{index}_{symbol}"
                expanded = st.button("➕", key=expand_key, help="Click to expand details")
            
            # Display expanded content if button was clicked
            if expanded:
                with st.expander(f"👀 Watchlist Details for {symbol}", expanded=True):
                    ExpandableUI._display_watchlist_details(item)
            
            return expanded
            
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
            
            # Create main row
            col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 1.5, 1.5, 1.5, 1.5, 1.5, 1])
            
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
                # Expandable button
                expand_key = f"expand_swing_{index}_{symbol}"
                expanded = st.button("➕", key=expand_key, help="Click to expand details")
            
            # Display expanded content if button was clicked
            if expanded:
                with st.expander(f"📈 Swing Strategy Details for {symbol}", expanded=True):
                    ExpandableUI._display_swing_strategy_details(strategy)
            
            return expanded
            
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
