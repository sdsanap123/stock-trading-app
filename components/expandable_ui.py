#!/usr/bin/env python3
"""
Expandable UI Components
Reusable UI components for displaying data in expandable rows with + icons.
"""

import streamlit as st
import pandas as pd
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import json
import os
import time
import uuid

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache the stock data loading to avoid reading the file multiple times
@st.cache_data(ttl=86400)  # Cache for 24 hours
def load_stock_data():
    """Load stock data from the EQUITY_L.csv file."""
    try:
        # Path to the CSV file
        csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'EQUITY_L.csv')
        
        # Read the CSV file
        df = pd.read_csv(csv_path, encoding='utf-8')
        
        # Create a dictionary with symbol as key and company name as value
        stock_data = {}
        for _, row in df.iterrows():
            symbol = row['SYMBOL'].strip().upper()
            company_name = row['NAME OF COMPANY'].strip()
            stock_data[symbol] = company_name
            
        logger.info(f"Loaded stock data for {len(stock_data)} companies")
        return stock_data
    except Exception as e:
        logger.error(f"Error loading stock data: {str(e)}")
        return {}

class ModalWindow:
    """Custom modal window component for Streamlit."""
    
    @staticmethod
    def create_modal(modal_id: str, title: str, content: str, width: str = "80%", height: str = "80%"):
        """Create a modal window with HTML/CSS/JavaScript."""
        modal_html = f"""
        <div id="{modal_id}" class="modal" style="display: none;">
            <div class="modal-content" style="width: {width}; height: {height};">
                <div class="modal-header">
                    <h2>{title}</h2>
                    <span class="close" onclick="closeModal('{modal_id}')">&times;</span>
                </div>
                <div class="modal-body">
                    {content}
                </div>
            </div>
        </div>
        
        <style>
        .modal {{
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
            backdrop-filter: blur(5px);
        }}
        
        .modal-content {{
            background-color: #1e1e1e;
            margin: 5% auto;
            padding: 0;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.5);
            border: 1px solid #333;
            max-height: 90vh;
            overflow: hidden;
        }}
        
        .modal-header {{
            background-color: #2d2d2d;
            padding: 15px 20px;
            border-bottom: 1px solid #444;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .modal-header h2 {{
            margin: 0;
            color: #ffffff;
            font-size: 1.5rem;
        }}
        
        .close {{
            color: #aaa;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
            transition: color 0.3s;
        }}
        
        .close:hover {{
            color: #ffffff;
        }}
        
        .modal-body {{
            padding: 20px;
            max-height: calc(90vh - 80px);
            overflow-y: auto;
            color: #ffffff;
        }}
        
        .modal-body h3 {{
            color: #4CAF50;
            margin-top: 20px;
            margin-bottom: 10px;
        }}
        
        .modal-body p {{
            margin: 8px 0;
            line-height: 1.5;
        }}
        
        .modal-body .metric {{
            background-color: #2d2d2d;
            padding: 10px;
            border-radius: 5px;
            margin: 5px 0;
            border-left: 3px solid #4CAF50;
            flex: 1;
            min-width: 300px;
        }}
        </style>
        
        <script>
        function openModal(modalId) {{
            document.getElementById(modalId).style.display = "block";
            document.body.style.overflow = "hidden";
        }}
        
        function closeModal(modalId) {{
            document.getElementById(modalId).style.display = "none";
            document.body.style.overflow = "auto";
        }}
        
        // Close modal when clicking outside of it
        window.onclick = function(event) {{
            var modals = document.querySelectorAll('.modal');
            modals.forEach(function(modal) {{
                if (event.target == modal) {{
                    modal.style.display = "none";
                    document.body.style.overflow = "auto";
                }}
            }});
        }}
        </script>
        """
        return modal_html
    
    @staticmethod
    def show_modal_button(button_text: str, modal_id: str, title: str, content: str):
        """Show a button that opens a wide modal-like display."""
        # Create a unique key for the button
        button_key = f"modal_btn_{modal_id}"
        
        # Use Streamlit button with session state
        if st.button(f"🔍 {button_text}", key=button_key, help="Click to view details in a wide popup"):
            # Store the modal data in session state
            st.session_state[f"show_modal_{modal_id}"] = True
            st.session_state[f"modal_title_{modal_id}"] = title
            st.session_state[f"modal_content_{modal_id}"] = content
        
        # Show wide modal if triggered
        if st.session_state.get(f"show_modal_{modal_id}", False):
            # Create a wide popup-like container
            st.markdown("---")
            
            # Add custom CSS for popup styling
            st.markdown("""
            <style>
            .popup-container {
                background-color: #1e1e1e;
                border: 2px solid #4CAF50;
                border-radius: 10px;
                padding: 20px;
                margin: 10px 0;
                box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            }
            .popup-header {
                background-color: #2d2d2d;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 15px;
                border-left: 4px solid #4CAF50;
            }
            .popup-content {
                background-color: #2a2a2a;
                padding: 20px;
                border-radius: 8px;
                color: white;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Create the popup container
            with st.container():
                st.markdown(f"""
                <div class="popup-container">
                    <div class="popup-header">
                        <h2 style="color: #4CAF50; margin: 0;">{title}</h2>
                    </div>
                    <div class="popup-content">
                        {content}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Close button
                col1, col2, col3 = st.columns([1, 1, 1])
                with col2:
                    if st.button("❌ Close Details", key=f"close_{modal_id}", help="Close this popup"):
                        st.session_state[f"show_modal_{modal_id}"] = False
                        st.rerun()
            
            st.markdown("---")
    
    @staticmethod
    def show_full_width_modal(button_text: str, modal_id: str, title: str, content: str):
        """Show a full-width modal that takes up most of the screen."""
        # Create a unique key for the button
        button_key = f"full_modal_btn_{modal_id}"
        
        # Use Streamlit button with session state
        if st.button(f"🔍 {button_text}", key=button_key, help="Click to view details in a popup window"):
            # Store the modal data in session state
            st.session_state[f"show_full_modal_{modal_id}"] = True
            st.session_state[f"full_modal_title_{modal_id}"] = title
            st.session_state[f"full_modal_content_{modal_id}"] = content
        
        # Show full-width modal if triggered
        if st.session_state.get(f"show_full_modal_{modal_id}", False):
            # Create a simple popup using pure Streamlit components
            st.markdown("---")
            
            # Add CSS for horizontal layout styling
            st.markdown("""
            <style>
            .popup-container {
                background-color: #1e1e1e;
                border: 3px solid #4CAF50;
                border-radius: 15px;
                padding: 20px;
                margin: 20px 0;
                box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            }
            .popup-header {
                background-color: #2d2d2d;
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 20px;
                border-left: 4px solid #4CAF50;
            }
            .popup-content-wrapper {
                display: flex;
                flex-direction: row;
                flex-wrap: wrap;
                gap: 20px;
                justify-content: space-between;
            }
            .popup-metric {
                background-color: #2d2d2d;
                padding: 20px;
                border-radius: 10px;
                margin: 10px 0;
                border-left: 4px solid #4CAF50;
                flex: 1;
                min-width: 300px;
                max-width: 48%;
                box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            }
            .popup-metric h3 {
                color: #4CAF50;
                margin-top: 0;
                margin-bottom: 15px;
                font-size: 1.2rem;
            }
            .popup-metric p {
                margin: 8px 0;
                font-size: 15px;
                color: white;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Create the popup container using Streamlit
            with st.container():
                st.markdown(f"""
                <div class="popup-container">
                    <div class="popup-header">
                        <h1 style="color: #4CAF50; margin: 0; text-align: center;">{title}</h1>
                    </div>
                    <div class="popup-content-wrapper">
                        {content}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Close button
                st.markdown("---")
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if st.button("❌ Close Popup", key=f"close_popup_{modal_id}", help="Close the popup window", type="primary"):
                        st.session_state[f"show_full_modal_{modal_id}"] = False
                        st.rerun()
                
                st.markdown("---")
    
    
    @staticmethod
    def show_popup_window(button_text: str, modal_id: str, title: str, content: str):
        """Show a button that opens a new browser window popup."""
        # Create a unique key for the button
        button_key = f"popup_btn_{modal_id}"
        
        # Create HTML content for popup window
        popup_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #1e1e1e;
                    color: white;
                    margin: 0;
                    padding: 20px;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background-color: #2d2d2d;
                    padding: 20px;
                    border-radius: 10px;
                    border: 2px solid #4CAF50;
                }}
                .header {{
                    background-color: #4CAF50;
                    color: white;
                    padding: 15px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                    text-align: center;
                }}
                .content {{
                    background-color: #2a2a2a;
                    padding: 20px;
                    border-radius: 8px;
                    line-height: 1.6;
                }}
                .close-btn {{
                    background-color: #dc3545;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 16px;
                    margin: 20px auto;
                    display: block;
                }}
                .close-btn:hover {{
                    background-color: #c82333;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{title}</h1>
                </div>
                <div class="content">
                    {content}
                </div>
                <button class="close-btn" onclick="window.close()">Close Window</button>
            </div>
        </body>
        </html>
        """
        
        # Encode the HTML content for URL
        import base64
        import urllib.parse
        encoded_html = base64.b64encode(popup_html.encode()).decode()
        
        # Create the popup button with JavaScript
        popup_script = f"""
        <script>
        function openPopup{modal_id}() {{
            var popup = window.open('', 'popup_{modal_id}', 'width=1200,height=800,scrollbars=yes,resizable=yes');
            popup.document.write(atob('{encoded_html}'));
            popup.document.close();
        }}
        </script>
        <button onclick="openPopup{modal_id}()" 
                style="background-color: #4CAF50; 
                       color: white; 
                       border: none; 
                       padding: 8px 16px; 
                       text-align: center; 
                       text-decoration: none; 
                       display: inline-block; 
                       font-size: 14px; 
                       margin: 4px 2px; 
                       cursor: pointer; 
                       border-radius: 4px;
                       transition: background-color 0.3s;">
            🪟 {button_text}
        </button>
        """
        
        st.markdown(popup_script, unsafe_allow_html=True)

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
            col1, col2, col3, col4 = st.columns([3, 1.5, 1, 1])
            
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
            
            return False
            
        except Exception as e:
            logger.error(f"Error displaying news row: {str(e)}")
            return False
    
    @staticmethod
    def _display_news_details(article: Dict) -> None:
        """Display detailed news article information."""
        try:
            # Get stock data for company name lookup
            stock_data = load_stock_data()
            
            # Extract symbols from article content
            mentioned_symbols = []
            content = article.get('content', '') or article.get('description', '')
            if content:
                # Simple pattern to find potential stock symbols (1-5 uppercase letters)
                import re
                potential_symbols = re.findall(r'\b[A-Z]{1,5}\b', content)
                mentioned_symbols = [s for s in potential_symbols if s in stock_data]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**📰 Article Details**")
                st.write(f"• **Title:** {article.get('title', 'N/A')}")
                st.write(f"• **Source:** {article.get('source', 'N/A')}")
                st.write(f"• **Published:** {article.get('publishedAt', 'N/A')}")
                st.write(f"• **URL:** {article.get('url', 'N/A')}")
                
                # Display mentioned companies if any
                if mentioned_symbols:
                    st.markdown("**📈 Mentioned Stocks**")
                    for symbol in mentioned_symbols[:3]:  # Show max 3 to avoid clutter
                        st.write(f"• **{symbol}** - {stock_data.get(symbol, 'N/A')}")
                
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
    def display_recommendation_row(rec: Dict, index: int, show_actions: bool = True) -> bool:
        """Display a recommendation in an expandable row format."""
        try:
            symbol = rec.get('symbol', 'UNKNOWN').strip().upper()
            
            # Try to get company name from the stock data
            stock_data = load_stock_data()
            company_name = rec.get('company_name', '')
            
            # If company name is not in the recommendation, try to get it from the stock data
            if not company_name and symbol in stock_data:
                company_name = stock_data[symbol]
                # Update the recommendation with the company name for future use
                rec['company_name'] = company_name
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
            
            # Create main row with 7 columns (added details button)
            col1, col2, col3, col4, col5, col6, col7 = st.columns([0.5, 1.5, 1, 1, 1, 0.8, 0.8])
            
            with col1:
                # Generate a unique ID for this recommendation using symbol, index, and a random component
                unique_id = f"{symbol}_{index}_{uuid.uuid4().hex}"
                
                # Toggle button with unique key
                toggle_key = f"toggle_{unique_id}"
                if st.button("🔍", key=toggle_key, help="Toggle details"):
                    st.session_state[f"show_details_{unique_id}"] = not st.session_state.get(f"show_details_{unique_id}", False)
            
            with col2:
                if company_name:
                    st.markdown(f"**{symbol}** - {company_name}")
                else:
                    st.markdown(f"**{symbol}**")
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
                # Details button
                details_key = f"details_{unique_id}"
                if st.button("📊", key=details_key, help="View analysis details"):
                    st.session_state[f"show_analysis_{unique_id}"] = True
            
            with col7:
                # Add to watchlist button
                if show_actions:
                    watchlist_key = f"add_watchlist_{unique_id}"
                    if st.button("👀", key=watchlist_key, help="Add to watchlist"):
                        st.session_state[f"add_to_watchlist_{unique_id}"] = True
            
            # Show analysis popup if details button was clicked
            if st.session_state.get(f"show_analysis_{unique_id}", False):
                # Add custom CSS for the popup
                st.markdown("""
                <style>
                    .popup-overlay {
                        position: fixed;
                        top: 0;
                        left: 0;
                        right: 0;
                        bottom: 0;
                        background-color: rgba(0, 0, 0, 0.7);
                        z-index: 1000;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                    }
                    .popup-content {
                        background: white;
                        padding: 2rem;
                        border-radius: 10px;
                        max-width: 90%;
                        max-height: 90vh;
                        overflow-y: auto;
                        position: relative;
                    }
                    .close-btn {
                        position: absolute;
                        top: 10px;
                        right: 10px;
                        font-size: 1.5rem;
                        cursor: pointer;
                        background: none;
                        border: none;
                        color: #666;
                    }
                </style>
                """, unsafe_allow_html=True)
                
                # Create the popup content
                with st.container():
                    # Close button - Using a callback to ensure proper state management
                    def close_popup():
                        st.session_state[f"show_analysis_{unique_id}"] = False
                    
                    if st.button("✕", key=f"close_analysis_{index}", on_click=close_popup):
                        # The callback will handle the state change
                        st.rerun()
                    
                    # Main content
                    st.title(f"📊 Analysis Details - {symbol}")
                    
                    # Analysis section
                    with st.expander("📈 Technical Analysis", expanded=True):
                        # Check groq_analysis first
                        groq_analysis = rec.get('groq_analysis', {})
                        if groq_analysis and (groq_analysis.get('status') == 'success' or 'analysis' in groq_analysis or 'technical_indicators' in groq_analysis):
                            st.write("### Groq AI Analysis")
                            
                            # Show main analysis content if available
                            if 'analysis' in groq_analysis and groq_analysis['analysis']:
                                st.write(groq_analysis['analysis'])
                            
                            # Show key technical indicators if available
                            if 'technical_indicators' in groq_analysis and groq_analysis['technical_indicators']:
                                st.write("#### Technical Indicators")
                                st.json(groq_analysis['technical_indicators'])
                            
                            # If we have analysis data but no content was shown, show the raw data
                            if not any(['analysis' in groq_analysis, 'technical_indicators' in groq_analysis]):
                                st.json({k: v for k, v in groq_analysis.items() if k != 'status'})
                        
                        # Check gemini_analysis
                        gemini_analysis = rec.get('gemini_analysis', {})
                        if gemini_analysis and isinstance(gemini_analysis, dict):
                            st.write("### Gemini AI Analysis")
                            if 'analysis' in gemini_analysis:
                                st.write(gemini_analysis['analysis'])
                            elif 'summary' in gemini_analysis:
                                st.write(gemini_analysis['summary'])
                        
                        # Fallback to technical_data if available
                        if not groq_analysis and not gemini_analysis and 'technical_data' in rec:
                            st.json(rec['technical_data'])
                        
                        if not any([groq_analysis, gemini_analysis, 'technical_data' in rec]):
                            st.info("No technical analysis available for this recommendation.")
                    
                    # Parameters used
                    with st.expander("⚙️ Parameters & Indicators"):
                        # Show technical parameters if available
                        if 'technical_data' in rec and rec['technical_data']:
                            st.write("#### Technical Parameters")
                            tech_data = {k: v for k, v in rec['technical_data'].items() 
                                      if not isinstance(v, (dict, list)) and not k.startswith('_')}
                            if tech_data:
                                st.json(tech_data)
                        
                        # Show swing plan parameters if available
                        swing_plan = rec.get('swing_plan', {})
                        if swing_plan:
                            st.write("#### Swing Trading Plan")
                            plan_data = {k: v for k, v in swing_plan.items() 
                                       if not isinstance(v, (dict, list)) and not k.startswith('_')}
                            if plan_data:
                                st.json(plan_data)
                        
                        if not any(['technical_data' in rec, 'swing_plan' in rec]):
                            st.info("No parameter details available.")
                    
                    # Additional notes and reasoning
                    with st.expander("📝 Notes & Reasoning"):
                        # Show reasoning if available
                        if 'reasoning' in rec and rec['reasoning']:
                            st.write("#### Recommendation Reasoning")
                            st.write(rec['reasoning'])
                        
                        # Show groq_analysis notes if available
                        groq_analysis = rec.get('groq_analysis', {})
                        if groq_analysis and 'notes' in groq_analysis:
                            st.write("#### Groq AI Notes")
                            st.write(groq_analysis['notes'])
                        
                        # Show gemini_analysis notes if available
                        gemini_analysis = rec.get('gemini_analysis', {})
                        if gemini_analysis and 'notes' in gemini_analysis:
                            st.write("#### Gemini AI Notes")
                            st.write(gemini_analysis['notes'])
                        
                        # Show validation notes from swing plan if available
                        swing_validation = rec.get('swing_validation', {})
                        if swing_validation and 'notes' in swing_validation:
                            st.write("#### Swing Validation Notes")
                            st.write(swing_validation['notes'])
                        
                        if not any(['reasoning' in rec, 
                                  groq_analysis and 'notes' in groq_analysis,
                                  gemini_analysis and 'notes' in gemini_analysis,
                                  swing_validation and 'notes' in swing_validation]):
                            st.info("No additional notes available.")
                    
                    # Close button at bottom - Using the same callback for consistency
                    if st.button("Close", key=f"bottom_close_{index}", on_click=close_popup):
                        # The callback will handle the state change
                        st.rerun()
            
            return False
            
        except Exception as e:
            logger.error(f"Error displaying recommendation row: {str(e)}")
            return False
    
    @staticmethod
    def _get_recommendation_details_html(rec: Dict) -> str:
        """Get HTML content for recommendation details modal."""
        try:
            symbol = rec.get('symbol', 'N/A')
            current_price = rec.get('current_price', 0)
            target_price = rec.get('target_price', 0)
            stop_loss = rec.get('stop_loss', 0)
            confidence = rec.get('confidence', 0)
            recommendation = rec.get('recommendation', 'N/A')
            reasoning = rec.get('reasoning', '')
            swing_plan = rec.get('swing_plan', {})
            technical_data = rec.get('technical_data', {})
            groq_analysis = rec.get('groq_analysis', {})
            
            # Calculate risk-reward ratio
            risk_reward_html = ""
            if current_price > 0 and target_price > 0 and stop_loss > 0:
                potential_profit = target_price - current_price
                potential_loss = current_price - stop_loss
                if potential_loss > 0:
                    risk_reward = potential_profit / potential_loss
                    risk_reward_html = f"<p><strong>Risk-Reward Ratio:</strong> {risk_reward:.2f}:1</p>"
            
            # Recommendation color
            rec_color = "#28a745" if recommendation == "BUY" else "#dc3545" if recommendation == "SELL" else "#ffc107"
            
            # Build HTML content step by step
            html_content = ""
            
            # Trading Details
            html_content += f"""
            <div class="popup-metric">
                <h3>📊 Trading Details</h3>
                <p><strong>Symbol:</strong> {symbol}</p>
                <p><strong>Current Price:</strong> ₹{current_price:.2f}</p>
                <p><strong>Target Price:</strong> ₹{target_price:.2f}</p>
                <p><strong>Stop Loss:</strong> ₹{stop_loss:.2f}</p>
                <p><strong>Confidence:</strong> {confidence:.1f}%</p>
                <p><strong>Recommendation:</strong> <span style="color: {rec_color}; font-weight: bold;">{recommendation}</span></p>
                {risk_reward_html}
            </div>
            """
            
            # Swing Trading Plan
            html_content += f"""
            <div class="popup-metric">
                <h3>📈 Swing Trading Plan</h3>
            """
            if swing_plan:
                html_content += f"""
                <p><strong>Position Size:</strong> {swing_plan.get('position_size', 0)} shares</p>
                <p><strong>Investment:</strong> ₹{swing_plan.get('investment_amount', 0):,.0f}</p>
                <p><strong>Risk Amount:</strong> ₹{swing_plan.get('risk_amount', 0):,.0f}</p>
                <p><strong>Holding Period:</strong> {swing_plan.get('holding_period_days', 7)} days</p>
                """
            else:
                html_content += "<p>No swing plan available</p>"
            html_content += "</div>"
            
            # AI Reasoning
            html_content += f"""
            <div class="popup-metric">
                <h3>💭 AI Reasoning</h3>
                <p>{reasoning if reasoning else 'No reasoning provided'}</p>
            </div>
            """
            
            # Technical Analysis
            html_content += f"""
            <div class="popup-metric">
                <h3>📊 Technical Indicators</h3>
            """
            if technical_data:
                html_content += f"""
                <p><strong>RSI:</strong> {technical_data.get('rsi', 0):.1f}</p>
                <p><strong>MACD:</strong> {technical_data.get('macd', 0):.4f}</p>
                <p><strong>SMA 20:</strong> ₹{technical_data.get('sma_20', 0):.2f}</p>
                <p><strong>Volume Ratio:</strong> {technical_data.get('volume_ratio_20', 0):.2f}</p>
                <p><strong>ATR:</strong> ₹{technical_data.get('atr', 0):.2f}</p>
                <p><strong>Bollinger Position:</strong> {technical_data.get('bb_position', 0):.2f}</p>
                """
            else:
                html_content += "<p>No technical data available</p>"
            html_content += "</div>"
            
            # Groq Analysis
            html_content += f"""
            <div class="popup-metric">
                <h3>🤖 Groq AI Analysis</h3>
            """
            if groq_analysis and groq_analysis.get('status') == 'success':
                html_content += f"""
                <p><strong>Sentiment:</strong> {groq_analysis.get('sentiment_label', 'N/A')}</p>
                <p><strong>Impact Level:</strong> {groq_analysis.get('impact_level', 'N/A')}</p>
                <p><strong>Price Impact:</strong> {groq_analysis.get('price_impact', 'N/A')}</p>
                <p><strong>Swing Potential:</strong> {groq_analysis.get('swing_trading_potential', 'N/A')}</p>
                """
            else:
                html_content += "<p>No Groq analysis available</p>"
            html_content += "</div>"
            
            # Actions
            html_content += """
            <div class="popup-metric">
                <h3>⚡ Actions</h3>
                <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                    <button onclick="alert('Add to Watchlist functionality will be implemented')" 
                            style="background-color: #4CAF50; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">
                        👀 Add to Watchlist
                    </button>
                    <button onclick="alert('Share functionality will be implemented')" 
                            style="background-color: #2196F3; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">
                        📤 Share
                    </button>
                    <button onclick="alert('Export functionality will be implemented')" 
                            style="background-color: #ffc107; color: black; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">
                        📊 Export
                    </button>
                </div>
            </div>
            """
            
            return html_content
            
        except Exception as e:
            logger.error(f"Error creating recommendation details HTML: {str(e)}")
            return "<p>Error loading details</p>"
    
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
                    if 'T' in added_date:
                        # Handle ISO format with time
                        date_obj = datetime.fromisoformat(added_date.replace('Z', '+00:00'))
                    else:
                        # Handle date-only string
                        date_obj = datetime.strptime(added_date, '%Y-%m-%d')
                    formatted_date = date_obj.strftime('%Y-%m-%d')
                else:
                    formatted_date = datetime.now().strftime('%Y-%m-%d')  # Default to current date
            except Exception as e:
                logger.warning(f"Error parsing date {added_date}: {str(e)}")
                formatted_date = datetime.now().strftime('%Y-%m-%d')  # Default to current date on error
            
            # Create main row with 7 columns (added details button)
            col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 1, 1, 1, 1, 1.5, 0.8])
            
            with col1:
                st.markdown(f"**{symbol}**")
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
                # Details button
                details_key = f"watchlist_details_{index}_{symbol}"
                if st.button("📊", key=details_key, help="View analysis details"):
                    st.session_state[f"show_watchlist_analysis_{index}"] = True
            
            # Show analysis popup if details button was clicked
            if st.session_state.get(f"show_watchlist_analysis_{index}", False):
                # Add custom CSS for the popup
                st.markdown("""
                <style>
                    .popup-overlay {
                        position: fixed;
                        top: 0;
                        left: 0;
                        right: 0;
                        bottom: 0;
                        background-color: rgba(0, 0, 0, 0.7);
                        z-index: 1000;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                    }
                    .popup-content {
                        background: white;
                        padding: 2rem;
                        border-radius: 10px;
                        max-width: 90%;
                        max-height: 90vh;
                        overflow-y: auto;
                        position: relative;
                    }
                    .close-btn {
                        position: absolute;
                        top: 10px;
                        right: 10px;
                        font-size: 1.5rem;
                        cursor: pointer;
                        background: none;
                        border: none;
                        color: #666;
                    }
                </style>
                """, unsafe_allow_html=True)
                
                # Create the popup content
                with st.container():
                    # Close button - Using a callback to ensure proper state management
                    def close_watchlist_popup():
                        st.session_state[f"show_watchlist_analysis_{index}"] = False
                    
                    if st.button("✕", key=f"close_watchlist_analysis_{index}", on_click=close_watchlist_popup):
                        # The callback will handle the state change
                        st.rerun()
                    
                    # Main content - Match the recommendations tab style
                    st.title(f"📊 Analysis Details - {symbol}")
                    
                    # Analysis section - Match recommendations tab
                    with st.expander("📈 Technical Analysis", expanded=True):
                        # Check groq_analysis first
                        groq_analysis = item.get('groq_analysis', {})
                        if groq_analysis and groq_analysis.get('status') == 'success':
                            st.write("### Groq AI Analysis")
                            st.write(groq_analysis.get('analysis', 'No analysis available'))
                            
                            # Show key technical indicators if available
                            if 'technical_indicators' in groq_analysis:
                                st.write("#### Technical Indicators")
                                st.json(groq_analysis['technical_indicators'])
                        
                        # Check gemini_analysis
                        gemini_analysis = item.get('gemini_analysis', {})
                        if gemini_analysis and isinstance(gemini_analysis, dict):
                            st.write("### Gemini AI Analysis")
                            if 'analysis' in gemini_analysis:
                                st.write(gemini_analysis['analysis'])
                            else:
                                st.json(gemini_analysis)
                        
                        # Fallback to technical_data if no AI analysis
                        technical_data = item.get('technical_data', {})
                        if technical_data and not (groq_analysis or gemini_analysis):
                            st.write("### Technical Analysis")
                            st.json(technical_data)
                        
                        if not any([groq_analysis, gemini_analysis, technical_data]):
                            st.info("No technical analysis available for this watchlist item.")
                    
                    # Parameters section
                    with st.expander("⚙️ Parameters"):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Current Price", f"₹{current_price:.2f}")
                            st.metric("Entry Price", f"₹{entry_price:.2f}")
                        with col2:
                            st.metric("Target Price", f"₹{item.get('target_price', 0):.2f}")
                            st.metric("Stop Loss", f"₹{item.get('stop_loss', 0):.2f}")
                        with col3:
                            st.metric("P&L", f"{pnl:+.2f}%", delta=f"₹{pnl_amount:+.2f}")
                            st.metric("Confidence", f"{item.get('confidence', 0)}%")
                        
                        # Show technical parameters if available
                        if technical_data:
                            st.subheader("Technical Parameters")
                            st.json(technical_data)
                        elif 'technical_indicators' in groq_analysis:
                            st.subheader("Technical Parameters")
                            st.json(groq_analysis['technical_indicators'])
                        else:
                            st.info("No parameter details available.")
                    
                    # Swing Plan section if available
                    swing_plan = item.get('swing_plan', {})
                    if swing_plan:
                        with st.expander("📋 Swing Trading Plan"):
                            st.write(swing_plan.get('strategy_details', swing_plan.get('strategy', 'No swing trading plan available.')))
                            
                            st.subheader("Trade Parameters")
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Position Size", swing_plan.get('position_size', 'N/A'))
                                st.metric("Risk Amount", f"₹{swing_plan.get('risk_amount', 0):.2f}")
                            with col2:
                                st.metric("Timeframe", swing_plan.get('timeframe', 'N/A'))
                                st.metric("Risk-Reward", swing_plan.get('risk_reward_ratio', 'N/A'))
                    
                    # Notes section - Combine all available notes
                    with st.expander("📝 Notes"):
                        notes = []
                        
                        # Add reasoning if available
                        reasoning = item.get('reasoning')
                        if reasoning:
                            notes.append(f"**Reasoning:** {reasoning}")
                        
                        # Add Groq notes if available
                        if groq_analysis and 'notes' in groq_analysis:
                            notes.append(f"**Groq Analysis Notes:** {groq_analysis['notes']}")
                        
                        # Add Gemini notes if available
                        if gemini_analysis and 'notes' in gemini_analysis:
                            notes.append(f"**Gemini Analysis Notes:** {gemini_analysis['notes']}")
                        
                        # Add any additional notes
                        if item.get('notes'):
                            notes.append(f"**Additional Notes:** {item['notes']}")
                        elif item.get('additional_notes'):
                            notes.append(f"**Additional Notes:** {item['additional_notes']}")
                        
                        if notes:
                            st.markdown("\n\n".join(notes))
                        else:
                            st.info("No additional notes available.")
                    
                    # Close button at bottom - Using the same callback for consistency
                    if st.button("Close", key=f"bottom_close_watchlist_{index}", on_click=close_watchlist_popup):
                        # The callback will handle the state change
                        st.rerun()
            
            return False
            
        except Exception as e:
            logger.error(f"Error displaying watchlist row: {str(e)}")
            return False
    
    @staticmethod
    def _get_watchlist_details_html(item: Dict) -> str:
        """Get HTML content for watchlist details modal."""
        try:
            symbol = item.get('symbol', 'N/A')
            entry_price = item.get('entry_price', 0)
            current_price = item.get('current_price', 0)
            target_price = item.get('target_price', 0)
            stop_loss = item.get('stop_loss', 0)
            status = item.get('status', 'N/A')
            confidence = item.get('confidence', 0)
            notes = item.get('notes', '')
            
            # Calculate P&L
            pnl_percent = 0
            pnl_amount = 0
            if entry_price > 0:
                pnl_percent = ((current_price - entry_price) / entry_price) * 100
                pnl_amount = current_price - entry_price
            
            # Calculate distances
            target_distance_html = ""
            stop_distance_html = ""
            if current_price > 0:
                if target_price > 0:
                    target_distance = ((target_price - current_price) / current_price) * 100
                    target_distance_html = f"<p><strong>Distance to Target:</strong> {target_distance:.1f}%</p>"
                
                if stop_loss > 0:
                    stop_distance = ((current_price - stop_loss) / current_price) * 100
                    stop_distance_html = f"<p><strong>Distance to Stop Loss:</strong> {stop_distance:.1f}%</p>"
            
            # Risk-Reward calculation
            risk_reward_html = ""
            if target_price > 0 and stop_loss > 0 and entry_price > 0:
                potential_profit = target_price - entry_price
                potential_loss = entry_price - stop_loss
                if potential_loss > 0:
                    risk_reward = potential_profit / potential_loss
                    risk_reward_html = f"<p><strong>Risk-Reward Ratio:</strong> {risk_reward:.2f}:1</p>"
            
            # P&L color
            pnl_color = "#28a745" if pnl_percent > 0 else "#dc3545" if pnl_percent < 0 else "#ffc107"
            
            html_content = f"""
            <div class="popup-metric">
                <h3>📊 Position Details</h3>
                <p><strong>Symbol:</strong> {symbol}</p>
                <p><strong>Entry Price:</strong> ₹{entry_price:.2f}</p>
                <p><strong>Current Price:</strong> ₹{current_price:.2f}</p>
                <p><strong>Target Price:</strong> ₹{target_price:.2f}</p>
                <p><strong>Stop Loss:</strong> ₹{stop_loss:.2f}</p>
                {target_distance_html}
                {stop_distance_html}
            </div>
            <div class="popup-metric">
                <h3>📈 Performance Metrics</h3>
                <p><strong>P&L Percentage:</strong> <span style="color: {pnl_color}; font-weight: bold;">{pnl_percent:.2f}%</span></p>
                <p><strong>P&L Amount:</strong> <span style="color: {pnl_color}; font-weight: bold;">₹{pnl_amount:.2f}</span></p>
                <p><strong>Status:</strong> {status}</p>
                <p><strong>Confidence:</strong> {confidence:.1f}%</p>
                {risk_reward_html}
            </div>
            """
            
            # Notes section - Always show this section
            html_content += f"""
            <div class="popup-metric">
                <h3>📝 Notes</h3>
                <p>{notes if notes else 'No notes available'}</p>
            </div>
            """
            
            # Action buttons - Always show this section
            html_content += """
            <div class="popup-metric">
                <h3>⚡ Actions</h3>
                <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                    <button onclick="alert('Update Price functionality will be implemented')" 
                            style="background-color: #4CAF50; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">
                        📊 Update Price
                    </button>
                    <button onclick="alert('Edit Notes functionality will be implemented')" 
                            style="background-color: #2196F3; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">
                        ✏️ Edit Notes
                    </button>
                    <button onclick="alert('Delete functionality will be implemented')" 
                            style="background-color: #f44336; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">
                        🗑️ Delete
                    </button>
                </div>
            </div>
            """
            
            return html_content
            
        except Exception as e:
            logger.error(f"Error creating watchlist details HTML: {str(e)}")
            return "<p>Error loading details</p>"
    
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
                if st.button(f"📊 Update Price", key=f"update_{item.get('symbol')}_watchlist"):
                    st.session_state[f"update_price_{item.get('symbol')}"] = True
            
            with action_col2:
                if st.button(f"✏️ Edit Notes", key=f"edit_{item.get('symbol')}_watchlist"):
                    st.session_state[f"edit_notes_{item.get('symbol')}"] = True
            
            with action_col3:
                if st.button(f"🗑️ Delete", key=f"remove_{item.get('symbol')}_watchlist", type="primary"):
                    st.session_state[f"delete_from_watchlist_{item.get('symbol')}"] = True
                    st.rerun()
            
        except Exception as e:
            logger.error(f"Error displaying watchlist details: {str(e)}")
    
    @staticmethod
    def display_swing_strategy_row(strategy: Dict, index: int, show_actions: bool = True) -> bool:
        """Display a swing strategy in an expandable row format."""
        try:
            symbol = strategy.get('symbol', 'UNKNOWN').strip().upper()
            company_name = strategy.get('company_name', '')
            entry_price = float(strategy.get('entry_price', 0))
            current_price = float(strategy.get('current_price', entry_price))  # Fallback to entry_price if not available
            take_profit = float(strategy.get('take_profit', 0))
            stop_loss = float(strategy.get('stop_loss', 0))
            position_size = int(strategy.get('position_size', 0))
            investment_amount = float(strategy.get('investment_amount', 0))
            risk_reward_ratio = float(strategy.get('risk_reward_ratio', 0))
            status = strategy.get('status', 'ACTIVE')
            created_at = strategy.get('created_at', '')
            
            # Calculate days left
            days_left = 0
            try:
                exit_date_str = strategy.get('expected_exit_date', '')
                if exit_date_str:
                    if 'T' in exit_date_str:
                        exit_date = datetime.fromisoformat(exit_date_str.replace('Z', '+00:00'))
                    else:
                        exit_date = datetime.strptime(exit_date_str, "%Y-%m-%d")
                    days_left = max(0, (exit_date - datetime.now()).days)
            except Exception as e:
                logger.warning(f"Error calculating days left: {str(e)}")
                days_left = int(strategy.get('holding_period_days', 5))
            
            # Format date
            try:
                if created_at:
                    date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    formatted_date = date_obj.strftime('%Y-%m-%d %H:%M')
                else:
                    formatted_date = 'N/A'
            except:
                formatted_date = created_at[:19] if created_at else 'N/A'
            
            # Create main row with 8 columns (added details button)
            col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([1.5, 1, 1, 1, 1, 1, 0.8, 0.8])
            
            with col1:
                if company_name:
                    st.markdown(f"**{symbol}** - {company_name}")
                else:
                    st.markdown(f"**{symbol}**")
            
            with col2:
                st.markdown(f"₹{current_price:.2f}")
                st.caption("CMP")
            
            with col3:
                st.markdown(f"₹{take_profit:.2f}" if take_profit > 0 else "N/A")
                st.caption("Target")
            
            with col4:
                st.markdown(f"₹{stop_loss:.2f}" if stop_loss > 0 else "N/A")
                st.caption("Stop Loss")
            
            with col5:
                st.markdown(f"{days_left}d" if days_left >= 0 else "Expired")
                st.caption("Days Left")
            
            # Risk-Reward with color
            with col6:
                if risk_reward_ratio > 0:
                    if risk_reward_ratio >= 2.0:
                        st.markdown(f'<span style="color: #28a745;">{risk_reward_ratio:.2f}:1</span>', unsafe_allow_html=True)
                    elif risk_reward_ratio >= 1.5:
                        st.markdown(f'<span style="color: #ffc107;">{risk_reward_ratio:.2f}:1</span>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<span style="color: #dc3545;">{risk_reward_ratio:.2f}:1</span>', unsafe_allow_html=True)
                else:
                    st.markdown("N/A")
                st.caption("Risk-Reward")
            
            with col7:
                # Details button - Include timestamp in key to ensure uniqueness
                timestamp = int(time.time() * 1000)  # Current time in milliseconds
                details_key = f"swing_details_{index}_{symbol}_{timestamp}"
                if st.button("📊", key=details_key, help="View strategy details"):
                    st.session_state[f"show_swing_analysis_{index}_{timestamp}"] = True
            
            with col8:
                # Add to watchlist button - Include timestamp in key to ensure uniqueness
                if show_actions:
                    watchlist_key = f"add_swing_watchlist_{index}_{symbol}_{timestamp}"
                    if st.button("👀", key=watchlist_key, help="Add to watchlist"):
                        st.session_state[f"add_swing_to_watchlist_{index}_{timestamp}"] = True
            
            # Show analysis popup if details button was clicked
            if st.session_state.get(f"show_swing_analysis_{index}_{timestamp}", False):
                # Add custom CSS for the popup
                st.markdown("""
                <style>
                    .popup-overlay {
                        position: fixed;
                        top: 0;
                        left: 0;
                        right: 0;
                        bottom: 0;
                        background-color: rgba(0, 0, 0, 0.7);
                        z-index: 1000;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                    }
                    .popup-content {
                        background: white;
                        padding: 2rem;
                        border-radius: 10px;
                        max-width: 90%;
                        max-height: 90vh;
                        overflow-y: auto;
                        position: relative;
                    }
                    .close-btn {
                        position: absolute;
                        top: 10px;
                        right: 10px;
                        font-size: 1.5rem;
                        cursor: pointer;
                        background: none;
                        border: none;
                        color: #666;
                    }
                </style>
                """, unsafe_allow_html=True)
                
                # Create the popup content
                with st.container():
                    # Close button - Using a callback to ensure proper state management
                    def close_swing_popup():
                        st.session_state[f"show_swing_analysis_{index}_{timestamp}"] = False
                    
                    if st.button("✕", key=f"close_swing_analysis_{index}_{timestamp}", on_click=close_swing_popup):
                        # The callback will handle the state change
                        st.rerun()
                    
                    # Main content - Match the recommendations tab style
                    st.title(f"📊 Analysis Details - {symbol}")
                    
                    # Analysis section - Match recommendations tab
                    with st.expander("📈 Technical Analysis", expanded=True):
                        # Check groq_analysis first
                        groq_analysis = strategy.get('groq_analysis', {})
                        if groq_analysis and groq_analysis.get('status') == 'success':
                            st.write("### Groq AI Analysis")
                            st.write(groq_analysis.get('analysis', 'No analysis available'))
                            
                            # Show key technical indicators if available
                            if 'technical_indicators' in groq_analysis:
                                st.write("#### Technical Indicators")
                                st.json(groq_analysis['technical_indicators'])
                        
                        # Check gemini_analysis
                        gemini_analysis = strategy.get('gemini_analysis', {})
                        if gemini_analysis and isinstance(gemini_analysis, dict):
                            st.write("### Gemini AI Analysis")
                            if 'analysis' in gemini_analysis:
                                st.write(gemini_analysis['analysis'])
                            else:
                                st.json(gemini_analysis)
                        
                        # Show technical parameters if available
                        technical_data = strategy.get('technical_data', {})
                        if technical_data:
                            st.subheader("Technical Parameters")
                            st.json({k: v for k, v in technical_data.items() 
                                  if not isinstance(v, (dict, list)) and not k.startswith('_')})
                        else:
                            st.info("No parameter details available.")
                    
                    # Swing Plan section
                    swing_plan = strategy.get('swing_plan', {})
                    if swing_plan:
                        with st.expander("📋 Swing Trading Plan"):
                            st.write(swing_plan.get('strategy_details', swing_plan.get('strategy', 'No swing trading plan available.')))
                            
                            st.subheader("Trade Parameters")
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Position Size", position_size)
                                st.metric("Risk Amount", f"₹{risk_amount:.2f}")
                            with col2:
                                st.metric("Timeframe", swing_plan.get('timeframe', 'N/A'))
                                st.metric("Confidence", f"{swing_plan.get('confidence', 0)}%")
                    
                    # Notes section - Combine all available notes
                    with st.expander("📝 Notes"):
                        notes = []
                        
                        # Add reasoning if available
                        reasoning = strategy.get('reasoning')
                        if reasoning:
                            notes.append(f"**Reasoning:** {reasoning}")
                        
                        # Add Groq notes if available
                        if groq_analysis and 'notes' in groq_analysis:
                            notes.append(f"**Groq Analysis Notes:** {groq_analysis['notes']}")
                        
                        # Add Gemini notes if available
                        if gemini_analysis and 'notes' in gemini_analysis:
                            notes.append(f"**Gemini Analysis Notes:** {gemini_analysis['notes']}")
                        
                        # Add swing validation notes if available
                        swing_validation = strategy.get('swing_validation', {})
                        if swing_validation and 'notes' in swing_validation:
                            notes.append(f"**Swing Validation Notes:** {swing_validation['notes']}")
                        
                        # Add any additional notes
                        if strategy.get('notes'):
                            notes.append(f"**Additional Notes:** {strategy['notes']}")
                        elif strategy.get('additional_notes'):
                            notes.append(f"**Additional Notes:** {strategy['additional_notes']}")
                        
                        if notes:
                            st.markdown("\n\n".join(notes))
                        else:
                            st.info("No additional notes available.")
                    
                    # Close button at bottom - Using the same callback for consistency
                    if st.button("Close", key=f"bottom_close_swing_{index}", on_click=close_swing_popup):
                        # The callback will handle the state change
                        st.rerun()
            
            return False
            
        except Exception as e:
            logger.error(f"Error displaying swing strategy row: {str(e)}")
            return False
    
    @staticmethod
    def _get_swing_strategy_details_html(strategy: Dict) -> str:
        """Get HTML content for swing strategy details modal."""
        try:
            symbol = strategy.get('symbol', 'N/A')
            strategy_name = strategy.get('strategy_name', 'N/A')
            entry_price = strategy.get('entry_price', 0)
            take_profit = strategy.get('take_profit', 0)
            stop_loss = strategy.get('stop_loss', 0)
            holding_period = strategy.get('holding_period_days', 7)
            position_size = strategy.get('position_size', 0)
            investment_amount = strategy.get('investment_amount', 0)
            risk_amount = strategy.get('risk_amount', 0)
            risk_reward_ratio = strategy.get('risk_reward_ratio', 0)
            confidence = strategy.get('confidence', 0)
            status = strategy.get('status', 'N/A')
            entry_date = strategy.get('entry_date', 'N/A')
            created_at = strategy.get('created_at', 'N/A')
            expected_exit_date = strategy.get('expected_exit_date', 'N/A')
            
            # Calculate days remaining
            days_remaining_html = ""
            try:
                if expected_exit_date and expected_exit_date != 'N/A':
                    exit_date = datetime.fromisoformat(expected_exit_date.replace('Z', '+00:00'))
                    days_remaining = (exit_date - datetime.now()).days
                    if days_remaining > 0:
                        days_remaining_html = f"<p><strong>Days Remaining:</strong> {days_remaining}</p>"
                    else:
                        days_remaining_html = "<p><strong>Status:</strong> <span style='color: #dc3545;'>Expired</span></p>"
            except:
                days_remaining_html = "<p><strong>Days Remaining:</strong> N/A</p>"
            
            html_content = f"""
            <div class="popup-metric">
                <h3>📊 Strategy Overview</h3>
                <p><strong>Symbol:</strong> {symbol}</p>
                <p><strong>Strategy Name:</strong> {strategy_name}</p>
                <p><strong>Entry Price:</strong> ₹{entry_price:.2f}</p>
                <p><strong>Take Profit:</strong> ₹{take_profit:.2f}</p>
                <p><strong>Stop Loss:</strong> ₹{stop_loss:.2f}</p>
                <p><strong>Holding Period:</strong> {holding_period} days</p>
            </div>
            <div class="popup-metric">
                <h3>💰 Position Details</h3>
                <p><strong>Position Size:</strong> {position_size} shares</p>
                <p><strong>Investment Amount:</strong> ₹{investment_amount:,.0f}</p>
                <p><strong>Risk Amount:</strong> ₹{risk_amount:,.0f}</p>
                <p><strong>Risk-Reward Ratio:</strong> {risk_reward_ratio:.2f}:1</p>
                <p><strong>Confidence:</strong> {confidence:.1f}%</p>
                <p><strong>Status:</strong> {status}</p>
            </div>
            <div class="popup-metric">
                <h3>📅 Timeline</h3>
                <p><strong>Entry Date:</strong> {entry_date[:10] if entry_date != 'N/A' else 'N/A'}</p>
                <p><strong>Created:</strong> {created_at[:19] if created_at != 'N/A' else 'N/A'}</p>
                <p><strong>Expected Exit:</strong> {expected_exit_date[:10] if expected_exit_date != 'N/A' else 'N/A'}</p>
                {days_remaining_html}
            </div>
            <div class="popup-metric">
                <h3>📋 Strategy Rules</h3>
                <p>• Hold for maximum 7 days</p>
                <p>• Stop loss at 8% below entry</p>
                <p>• Take profit at 15% above entry</p>
                <p>• Monitor daily for exit signals</p>
                <p>• Do not average down if trade goes against you</p>
            </div>
            <div class="popup-metric">
                <h3>⚡ Actions</h3>
                <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                    <button onclick="alert('Update Status functionality will be implemented')" 
                            style="background-color: #4CAF50; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">
                        📊 Update Status
                    </button>
                    <button onclick="alert('Edit Strategy functionality will be implemented')" 
                            style="background-color: #2196F3; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">
                        ✏️ Edit Strategy
                    </button>
                    <button onclick="alert('Remove Strategy functionality will be implemented')" 
                            style="background-color: #f44336; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">
                        🗑️ Remove Strategy
                    </button>
                </div>
            </div>
            """
            
            return html_content
            
        except Exception as e:
            logger.error(f"Error creating swing strategy details HTML: {str(e)}")
            return "<p>Error loading details</p>"
    
    @staticmethod
    def _display_swing_strategy_details(strategy: Dict):
        """Display detailed swing strategy information."""
        try:
            # Get stock data for company name
            stock_data = load_stock_data()
            symbol = strategy.get('symbol', '').strip().upper()
            company_name = strategy.get('company_name', '')
            
            # If company name is not in the strategy, try to get it from the stock data
            if not company_name and symbol in stock_data:
                company_name = stock_data[symbol]
                # Update the strategy with the company name for future use
                strategy['company_name'] = company_name
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**📊 Strategy Overview**")
                if company_name:
                    st.write(f"• **Company:** {company_name}")
                st.write(f"• **Symbol:** {symbol if symbol else 'N/A'}")
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
