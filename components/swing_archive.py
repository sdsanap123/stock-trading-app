"""
Swing Trading Archive Component

This module provides components for displaying and analyzing archived swing trading strategies.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from loguru import logger

class SwingArchive:
    """Class to handle the display and analysis of archived swing trading strategies."""
    
    def __init__(self, data_persistence):
        """Initialize the SwingArchive component.
        
        Args:
            data_persistence: Data persistence manager instance
        """
        self.data_persistence = data_persistence
    
    def display_archive(self):
        """Display the archive tab with all archived swing trading strategies."""
        st.subheader("📈 Swing Trading Archive")
        
        try:
            # Get all archived strategies
            archived_strategies = self.get_archived_strategies()
            
            if not archived_strategies:
                st.info("No archived strategies found.")
                return
                
            # Display the archive UI with search and analysis
            self.display_archive_ui(archived_strategies)
            
        except Exception as e:
            st.error(f"Error loading archived strategies: {str(e)}")
            logger.error(f"Error in display_archive: {str(e)}")
    
    def get_archived_strategies(self) -> List[Dict[str, Any]]:
        """Get all archived swing strategies."""
        try:
            all_strategies = []
            
            # Get saved strategies from data persistence
            saved_strategies = self.data_persistence.get_swing_strategies()
            
            # Process all strategies
            for date_str, strategies in saved_strategies.items():
                for strategy in strategies:
                    # Only include strategies with an exit date
                    if strategy.get('exit_date'):
                        strategy['entry_date_str'] = date_str
                        all_strategies.append(strategy)
            
            # Sort by exit date (newest first)
            all_strategies.sort(
                key=lambda x: x.get('exit_date', ''), 
                reverse=True
            )
            
            return all_strategies
            
        except Exception as e:
            logger.error(f"Error getting archived strategies: {str(e)}")
            return []
    
    def display_archive_ui(self, strategies: List[Dict[str, Any]]) -> None:
        """Display the archive UI with search and strategy analysis."""
        st.subheader("🗄️ Archived Strategies")
        
        # Add search and filter options
        search_term = st.text_input("🔍 Search by symbol or company name:", "")
        
        # Filter strategies based on search term
        filtered_strategies = []
        for strategy in strategies:
            symbol_match = search_term.lower() in strategy.get('symbol', '').lower()
            name_match = search_term.lower() in strategy.get('company_name', '').lower()
            if not search_term or symbol_match or name_match:
                filtered_strategies.append(strategy)
        
        if not filtered_strategies:
            st.warning("No strategies match your search criteria.")
            return
        
        # Display strategies in expandable sections
        for i, strategy in enumerate(filtered_strategies):
            symbol = strategy.get('symbol', 'UNKNOWN')
            company = strategy.get('company_name', '')
            
            with st.expander(f"{symbol} - {company}", expanded=False):
                # Display basic strategy info
                self._display_strategy_details(strategy)
                
                # Add analyze button
                if st.button(f"🔍 Analyze Strategy", key=f"analyze_{i}"):
                    with st.spinner("Analyzing strategy performance..."):
                        # Perform analysis
                        analysis = self.analyze_strategy(strategy)
                        
                        # Display analysis
                        self.display_strategy_analysis(strategy, analysis)
                        
                        # Add learning section
                        st.markdown("---")
                        st.markdown("### 🎓 Learn from this Strategy")
                        
                        # Generate learning points
                        learning_points = self._generate_learning_points(strategy, analysis)
                        
                        # Display learning points
                        if learning_points:
                            st.markdown("#### Key Learnings")
                            for point in learning_points:
                                st.info(f"📌 {point}")
                        else:
                            st.info("No specific learning points identified for this strategy.")
                        
                        # Add feedback mechanism
                        self._display_feedback_ui(i)
        
        # Add overall archive statistics
        st.markdown("---")
        self.display_archive_statistics(strategies)
    
    def _display_strategy_details(self, strategy: Dict[str, Any]) -> None:
        """Display basic details of a strategy."""
        entry_price = strategy.get('entry_price', 0)
        exit_price = strategy.get('exit_price', entry_price)
        entry_date = strategy.get('entry_date', '')
        exit_date = strategy.get('exit_date', '')
        pnl_pct = ((exit_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Entry")
            st.write(f"**Date:** {entry_date[:10] if entry_date else 'N/A'}")
            st.write(f"**Price:** ₹{entry_price:.2f}")
            
            st.markdown("#### Exit")
            st.write(f"**Date:** {exit_date[:10] if exit_date else 'N/A'}")
            st.write(f"**Price:** ₹{exit_price:.2f}")
        
        with col2:
            st.markdown("#### Performance")
            st.metric("P&L %", f"{pnl_pct:+.2f}%")
            
            # Calculate days held
            days_held = 0
            if entry_date and exit_date:
                try:
                    start = datetime.fromisoformat(entry_date.replace('Z', '+00:00'))
                    end = datetime.fromisoformat(exit_date.replace('Z', '+00:00'))
                    days_held = (end - start).days
                except (ValueError, TypeError):
                    pass
            
            st.metric("Days Held", days_held)
            
            # Determine status
            status = "PROFIT" if pnl_pct >= 0 else "LOSS"
            status_color = "#28a745" if status == "PROFIT" else "#dc3545"
            st.markdown(f"**Status:** <span style='color:{status_color}'>{status}</span>", 
                       unsafe_allow_html=True)
    
    def analyze_strategy(self, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single strategy's performance."""
        entry_price = strategy.get('entry_price', 0)
        exit_price = strategy.get('exit_price', entry_price)
        stop_loss = strategy.get('stop_loss', 0)
        take_profit = strategy.get('take_profit', 0)
        entry_date = strategy.get('entry_date', '')
        exit_date = strategy.get('exit_date', '')
        
        # Calculate metrics
        pnl_pct = ((exit_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
        days_held = 0
        
        if entry_date and exit_date:
            try:
                start = datetime.fromisoformat(entry_date.replace('Z', '+00:00'))
                end = datetime.fromisoformat(exit_date.replace('Z', '+00:00'))
                days_held = (end - start).days
            except (ValueError, TypeError):
                days_held = 0
        
        # Determine outcome
        outcome = {
            'status': 'UNKNOWN',
            'target_hit': exit_price >= take_profit if take_profit > 0 else False,
            'stop_hit': exit_price <= stop_loss if stop_loss > 0 else False,
            'days_to_outcome': days_held,
            'actual_pnl': pnl_pct,
            'expected_pnl': ((take_profit - entry_price) / entry_price * 100) if take_profit > 0 else 0,
            'analysis': ""
        }
        
        # Generate analysis
        analysis = []
        if outcome['target_hit']:
            outcome['status'] = 'TARGET_HIT'
            analysis.append(f"✅ Target hit at ₹{take_profit:.2f} ({(outcome['expected_pnl']):.1f}% profit)")
        elif outcome['stop_hit']:
            outcome['status'] = 'STOP_HIT'
            analysis.append(f"❌ Stop loss hit at ₹{stop_loss:.2f} ({(outcome['actual_pnl']):.1f}% loss)")
        elif days_held >= strategy.get('holding_period_days', 7):
            outcome['status'] = 'EXPIRED'
            analysis.append(f"⏰ Strategy expired after {days_held} days with {pnl_pct:+.1f}% P&L")
        
        # Add performance analysis
        if 'analysis' in strategy:
            analysis.append(f"\n**Previous Analysis:**\n{strategy['analysis']}")
        
        outcome['analysis'] = "\n\n".join(analysis)
        return outcome
    
    def display_strategy_analysis(self, strategy: Dict[str, Any], analysis: Dict[str, Any]) -> None:
        """Display the analysis of a strategy."""
        st.markdown("### 📊 Strategy Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Expected vs Actual")
            st.metric("Expected P&L", f"{analysis.get('expected_pnl', 0):.1f}%")
            st.metric("Actual P&L", f"{analysis.get('actual_pnl', 0):.1f}%")
            
            if 'days_to_outcome' in analysis:
                st.metric("Days to Outcome", analysis['days_to_outcome'])
            
            status = analysis.get('status', 'UNKNOWN')
            status_color = "#28a745" if status == 'TARGET_HIT' else "#dc3545" if status in ['STOP_HIT', 'ERROR'] else "#ffc107"
            st.markdown(f"**Status:** <span style='color:{status_color}'>{status.replace('_', ' ').title()}</span>", 
                      unsafe_allow_html=True)
        
        with col2:
            st.markdown("#### Key Metrics")
            st.metric("Entry Price", f"₹{strategy.get('entry_price', 0):.2f}")
            st.metric("Exit Price", f"₹{strategy.get('exit_price', strategy.get('entry_price', 0)):.2f}")
            
            if analysis.get('target_hit'):
                st.success("🎯 Target Price Reached")
            elif analysis.get('stop_hit'):
                st.error("⛔ Stop Loss Triggered")
            
            if 'learning_points' in analysis:
                st.markdown("#### Key Learnings")
                for point in analysis['learning_points']:
                    st.info(f"📌 {point}")
        
        if analysis.get('analysis'):
            st.markdown("---")
            st.markdown(analysis['analysis'])
    
    def _generate_learning_points(self, strategy: Dict[str, Any], analysis: Dict[str, Any]) -> List[str]:
        """Generate learning points from strategy analysis."""
        learning_points = []
        
        if analysis.get('target_hit'):
            learning_points.append(
                f"The strategy successfully reached its target price of ₹{strategy.get('take_profit', 0):.2f} "
                f"in {analysis.get('days_to_outcome', 'N/A')} days."
            )
        elif analysis.get('stop_hit'):
            learning_points.append(
                f"The stop loss was triggered at ₹{strategy.get('stop_loss', 0):.2f} "
                f"after {analysis.get('days_to_outcome', 'N/A')} days."
            )
        
        # Add risk management learning points
        risk_reward = strategy.get('risk_reward_ratio', 0)
        if 0 < risk_reward < 1:
            learning_points.append(
                f"The risk-reward ratio was {risk_reward:.2f}:1, which is below the recommended 2:1 ratio. "
                "Consider strategies with better risk-reward profiles."
            )
        
        # Add confidence level analysis
        confidence = strategy.get('confidence', 0)
        if confidence < 60:
            learning_points.append(
                f"The confidence level was {confidence}%, which is below the recommended threshold. "
                "Consider waiting for higher confidence setups."
            )
        
        return learning_points
    
    def _display_feedback_ui(self, index: int) -> None:
        """Display the feedback UI for strategy analysis."""
        st.markdown("---")
        st.markdown("### 📝 Provide Feedback")
        feedback = st.text_area(
            "Share your thoughts on this analysis or suggest improvements:",
            key=f"feedback_{index}"
        )
        
        if st.button("Submit Feedback", key=f"submit_feedback_{index}"):
            if feedback:
                # Here you would typically save the feedback
                st.success("Thank you for your feedback! It will help improve future strategies.")
            else:
                st.warning("Please provide some feedback before submitting.")
    
    def display_archive_statistics(self, strategies: List[Dict[str, Any]]) -> None:
        """Display statistics for archived strategies."""
        st.subheader("📊 Archive Statistics")
        
        if not strategies:
            st.info("No strategies available for analysis.")
            return
        
        # Calculate basic statistics
        total_strategies = len(strategies)
        profitable = sum(1 for s in strategies if (s.get('exit_price', 0) - s.get('entry_price', 0)) > 0)
        win_rate = (profitable / total_strategies * 100) if total_strategies > 0 else 0
        
        # Calculate average metrics
        avg_holding_days = sum(
            self._calculate_days_held(s) for s in strategies 
            if s.get('entry_date') and s.get('exit_date')
        ) / total_strategies if total_strategies > 0 else 0
        
        avg_pnl = sum(
            ((s.get('exit_price', 0) - s.get('entry_price', 0)) / s.get('entry_price', 1) * 100)
            for s in strategies if s.get('entry_price', 0) > 0
        ) / total_strategies if total_strategies > 0 else 0
        
        # Display metrics in columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Strategies", total_strategies)
        with col2:
            st.metric("Win Rate", f"{win_rate:.1f}%")
        with col3:
            st.metric("Avg Holding Days", f"{avg_holding_days:.1f}")
        with col4:
            st.metric("Avg P&L", f"{avg_pnl:+.1f}%")
        
        # Add a simple chart of strategy outcomes
        self._display_outcomes_chart(strategies)
    
    def _calculate_days_held(self, strategy: Dict[str, Any]) -> int:
        """Calculate the number of days a strategy was held."""
        try:
            entry_date = datetime.fromisoformat(strategy.get('entry_date', '').replace('Z', '+00:00'))
            exit_date = datetime.fromisoformat(strategy.get('exit_date', '').replace('Z', '+00:00'))
            return (exit_date - entry_date).days
        except (ValueError, TypeError):
            return 0
    
    def _display_outcomes_chart(self, strategies: List[Dict[str, Any]]) -> None:
        """Display a pie chart of strategy outcomes."""
        try:
            outcomes = {'Target Hit': 0, 'Stop Loss': 0, 'Expired': 0, 'Other': 0}
            
            for s in strategies:
                exit_price = s.get('exit_price', 0)
                take_profit = s.get('take_profit', 0)
                stop_loss = s.get('stop_loss', 0)
                
                if exit_price >= take_profit > 0:
                    outcomes['Target Hit'] += 1
                elif exit_price <= stop_loss > 0:
                    outcomes['Stop Loss'] += 1
                else:
                    days_held = self._calculate_days_held(s)
                    if days_held >= s.get('holding_period_days', 7):
                        outcomes['Expired'] += 1
                    else:
                        outcomes['Other'] += 1
            
            # Remove 'Other' if it's zero
            if outcomes['Other'] == 0:
                del outcomes['Other']
            
            # Create a pie chart
            fig = go.Figure(data=[go.Pie(
                labels=list(outcomes.keys()),
                values=list(outcomes.values()),
                hole=.3,
                marker_colors=['#28a745', '#dc3545', '#ffc107', '#6c757d']
            )])
            
            fig.update_layout(
                title='Strategy Outcomes',
                showlegend=True,
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            logger.warning(f"Could not generate outcomes chart: {str(e)}")
            
        except Exception as e:
            logger.warning(f"Could not generate P&L chart: {str(e)}")
