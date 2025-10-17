#!/usr/bin/env python3
"""
Login Interface Component
Provides login and registration UI components.
"""

import streamlit as st
import logging
from typing import Tuple, Optional
from .user_manager import UserManager

logger = logging.getLogger(__name__)

class LoginInterface:
    """Handles login and registration interface."""
    
    def __init__(self, user_manager: UserManager):
        self.user_manager = user_manager
    
    def show_login_page(self) -> bool:
        """Show login page and return True if user is authenticated."""
        try:
            # Check if user is already logged in
            if self._check_existing_session():
                return True
            
            # Main login interface
            st.title("🚀 Stock Trading App")
            st.markdown("### Welcome to the Enhanced Swing Trading Platform")
            
            # Create tabs for login and register
            tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
            
            with tab1:
                if self._show_login_form():
                    return True
            
            with tab2:
                self._show_register_form()
            
            return False
            
        except Exception as e:
            logger.error(f"Error showing login page: {str(e)}")
            st.error("Error loading login page")
            return False
    
    def _check_existing_session(self) -> bool:
        """Check if user has an existing valid session."""
        try:
            # Check session state
            if 'user_logged_in' in st.session_state and st.session_state['user_logged_in']:
                session_id = st.session_state.get('user_session_id')
                if session_id and self.user_manager.validate_session(session_id):
                    return True
            
            # Check for saved login
            saved_username, has_saved_login = self.user_manager.get_saved_login_info()
            if has_saved_login and saved_username:
                # Auto-login with saved credentials
                st.session_state['user_logged_in'] = True
                st.session_state['current_username'] = saved_username
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking existing session: {str(e)}")
            return False
    
    def _show_login_form(self) -> bool:
        """Show login form and handle authentication."""
        try:
            st.markdown("#### Login to your account")
            
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    save_login = st.checkbox("Remember me", help="Save login for next time")
                
                with col2:
                    login_button = st.form_submit_button("🔐 Login", type="primary")
                
                if login_button:
                    if not username or not password:
                        st.error("Please enter both username and password")
                        return False
                    
                    with st.spinner("Authenticating..."):
                        success, message = self.user_manager.authenticate_user(username, password, save_login)
                        
                        if success:
                            # Set session state
                            st.session_state['user_logged_in'] = True
                            st.session_state['current_username'] = username
                            
                            # Create session ID for this session
                            session_id = f"session_{username}_{st.session_state.get('session_id', 'default')}"
                            st.session_state['user_session_id'] = session_id
                            
                            st.success(f"Welcome back, {username}!")
                            st.rerun()
                            return True
                        else:
                            st.error(message)
                            return False
            
            # Show default credentials
            with st.expander("ℹ️ Default Credentials"):
                st.markdown("""
                **Default Admin Account:**
                - Username: `admin`
                - Password: `admin123`
                
                You can use these credentials to get started, or register a new account.
                """)
            
            return False
            
        except Exception as e:
            logger.error(f"Error showing login form: {str(e)}")
            st.error("Error in login form")
            return False
    
    def _show_register_form(self):
        """Show registration form."""
        try:
            st.markdown("#### Create a new account")
            
            with st.form("register_form"):
                new_username = st.text_input("Username", placeholder="Choose a username")
                new_password = st.text_input("Password", type="password", placeholder="Choose a password (min 6 characters)")
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
                email = st.text_input("Email (Optional)", placeholder="your.email@example.com")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    save_login_new = st.checkbox("Remember me", help="Save login for next time")
                
                with col2:
                    register_button = st.form_submit_button("📝 Register", type="primary")
                
                if register_button:
                    # Validate inputs
                    if not new_username or not new_password:
                        st.error("Please enter username and password")
                        return
                    
                    if len(new_password) < 6:
                        st.error("Password must be at least 6 characters long")
                        return
                    
                    if new_password != confirm_password:
                        st.error("Passwords do not match")
                        return
                    
                    with st.spinner("Creating account..."):
                        success, message = self.user_manager.register_user(new_username, new_password, email)
                        
                        if success:
                            st.success("Account created successfully! You can now login.")
                            
                            # Auto-login after registration
                            auth_success, auth_message = self.user_manager.authenticate_user(new_username, new_password, save_login_new)
                            
                            if auth_success:
                                st.session_state['user_logged_in'] = True
                                st.session_state['current_username'] = new_username
                                
                                session_id = f"session_{new_username}_{st.session_state.get('session_id', 'default')}"
                                st.session_state['user_session_id'] = session_id
                                
                                st.success(f"Welcome, {new_username}! You are now logged in.")
                                st.rerun()
                        else:
                            st.error(message)
            
            # Registration guidelines
            with st.expander("📋 Registration Guidelines"):
                st.markdown("""
                **Account Requirements:**
                - Username must be unique
                - Password must be at least 6 characters
                - Email is optional but recommended
                
                **Features:**
                - Save login preferences
                - Personalized dashboard
                - Data persistence across sessions
                """)
            
        except Exception as e:
            logger.error(f"Error showing register form: {str(e)}")
            st.error("Error in registration form")
    
    def show_logout_button(self):
        """Show logout button in sidebar."""
        try:
            if st.session_state.get('user_logged_in', False):
                username = st.session_state.get('current_username', 'User')
                
                with st.sidebar:
                    st.markdown("---")
                    st.markdown(f"**👤 Logged in as:** {username}")
                    
                    if st.button("🚪 Logout", key="logout_button"):
                        session_id = st.session_state.get('user_session_id')
                        self.user_manager.logout_user(session_id)
                        st.success("Logged out successfully!")
                        st.rerun()
            
        except Exception as e:
            logger.error(f"Error showing logout button: {str(e)}")
    
    def get_current_user(self) -> Optional[str]:
        """Get current logged in user."""
        try:
            if st.session_state.get('user_logged_in', False):
                return st.session_state.get('current_username')
            return None
        except Exception as e:
            logger.error(f"Error getting current user: {str(e)}")
            return None
    
    def is_user_logged_in(self) -> bool:
        """Check if user is currently logged in."""
        try:
            return st.session_state.get('user_logged_in', False)
        except Exception as e:
            logger.error(f"Error checking login status: {str(e)}")
            return False
