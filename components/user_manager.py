#!/usr/bin/env python3
"""
User Manager Component
Handles user authentication, login, and session management.
"""

import hashlib
import json
import os
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import streamlit as st

logger = logging.getLogger(__name__)

class UserManager:
    """Manages user authentication and sessions."""
    
    def __init__(self):
        self.users_file = "data/users.json"
        self.sessions_file = "data/sessions.json"
        self.users = {}
        self.sessions = {}
        self.current_user = None
        self.load_users()
        self.load_sessions()
        logger.info("User Manager initialized")
    
    def load_users(self):
        """Load users from file."""
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r') as f:
                    self.users = json.load(f)
                logger.info(f"Loaded {len(self.users)} users")
            else:
                self.users = {}
                # Create default admin user
                self._create_default_admin()
        except Exception as e:
            logger.error(f"Error loading users: {str(e)}")
            self.users = {}
            self._create_default_admin()
    
    def save_users(self):
        """Save users to file."""
        try:
            os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
            with open(self.users_file, 'w') as f:
                json.dump(self.users, f, indent=2)
            logger.info("Users saved successfully")
        except Exception as e:
            logger.error(f"Error saving users: {str(e)}")
    
    def load_sessions(self):
        """Load active sessions from file."""
        try:
            if os.path.exists(self.sessions_file):
                with open(self.sessions_file, 'r') as f:
                    self.sessions = json.load(f)
                logger.info(f"Loaded {len(self.sessions)} active sessions")
            else:
                self.sessions = {}
        except Exception as e:
            logger.error(f"Error loading sessions: {str(e)}")
            self.sessions = {}
    
    def save_sessions(self):
        """Save active sessions to file."""
        try:
            os.makedirs(os.path.dirname(self.sessions_file), exist_ok=True)
            with open(self.sessions_file, 'w') as f:
                json.dump(self.sessions, f, indent=2)
            logger.info("Sessions saved successfully")
        except Exception as e:
            logger.error(f"Error saving sessions: {str(e)}")
    
    def _create_default_admin(self):
        """Create default admin user."""
        try:
            admin_password = self._hash_password("admin123")
            self.users["admin"] = {
                "username": "admin",
                "password_hash": admin_password,
                "email": "admin@stockapp.com",
                "role": "admin",
                "created_at": datetime.now().isoformat(),
                "last_login": None,
                "preferences": {
                    "save_login": False,
                    "theme": "light",
                    "notifications": True
                }
            }
            self.save_users()
            logger.info("Default admin user created")
        except Exception as e:
            logger.error(f"Error creating default admin: {str(e)}")
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_user(self, username: str, password: str, email: str = "") -> Tuple[bool, str]:
        """Register a new user."""
        try:
            if username in self.users:
                return False, "Username already exists"
            
            if len(password) < 6:
                return False, "Password must be at least 6 characters"
            
            password_hash = self._hash_password(password)
            
            self.users[username] = {
                "username": username,
                "password_hash": password_hash,
                "email": email,
                "role": "user",
                "created_at": datetime.now().isoformat(),
                "last_login": None,
                "preferences": {
                    "save_login": False,
                    "theme": "light",
                    "notifications": True
                }
            }
            
            self.save_users()
            logger.info(f"User registered: {username}")
            return True, "User registered successfully"
            
        except Exception as e:
            logger.error(f"Error registering user: {str(e)}")
            return False, f"Registration error: {str(e)}"
    
    def authenticate_user(self, username: str, password: str, save_login: bool = False) -> Tuple[bool, str]:
        """Authenticate user login."""
        try:
            if username not in self.users:
                return False, "Invalid username or password"
            
            user = self.users[username]
            password_hash = self._hash_password(password)
            
            if user["password_hash"] != password_hash:
                return False, "Invalid username or password"
            
            # Update last login
            user["last_login"] = datetime.now().isoformat()
            user["preferences"]["save_login"] = save_login
            self.save_users()
            
            # Create session
            session_id = self._create_session(username)
            
            # Set current user
            self.current_user = username
            
            logger.info(f"User authenticated: {username}")
            return True, "Login successful"
            
        except Exception as e:
            logger.error(f"Error authenticating user: {str(e)}")
            return False, f"Authentication error: {str(e)}"
    
    def _create_session(self, username: str) -> str:
        """Create a new session for user."""
        try:
            session_id = hashlib.md5(f"{username}{datetime.now()}".encode()).hexdigest()
            
            self.sessions[session_id] = {
                "username": username,
                "created_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(days=30)).isoformat(),
                "last_activity": datetime.now().isoformat()
            }
            
            self.save_sessions()
            return session_id
            
        except Exception as e:
            logger.error(f"Error creating session: {str(e)}")
            return ""
    
    def validate_session(self, session_id: str) -> bool:
        """Validate if session is still active."""
        try:
            if session_id not in self.sessions:
                return False
            
            session = self.sessions[session_id]
            expires_at = datetime.fromisoformat(session["expires_at"])
            
            if datetime.now() > expires_at:
                # Session expired
                del self.sessions[session_id]
                self.save_sessions()
                return False
            
            # Update last activity
            session["last_activity"] = datetime.now().isoformat()
            self.save_sessions()
            
            # Set current user
            self.current_user = session["username"]
            return True
            
        except Exception as e:
            logger.error(f"Error validating session: {str(e)}")
            return False
    
    def logout_user(self, session_id: str = None):
        """Logout user and clear session."""
        try:
            if session_id and session_id in self.sessions:
                del self.sessions[session_id]
                self.save_sessions()
            
            self.current_user = None
            
            # Clear session state
            if 'user_session_id' in st.session_state:
                del st.session_state['user_session_id']
            if 'user_logged_in' in st.session_state:
                del st.session_state['user_logged_in']
            if 'current_username' in st.session_state:
                del st.session_state['current_username']
            
            logger.info("User logged out")
            
        except Exception as e:
            logger.error(f"Error logging out user: {str(e)}")
    
    def get_current_user(self) -> Optional[str]:
        """Get current logged in user."""
        return self.current_user
    
    def get_user_preferences(self, username: str = None) -> Dict:
        """Get user preferences."""
        try:
            if not username:
                username = self.current_user
            
            if username and username in self.users:
                return self.users[username].get("preferences", {})
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting user preferences: {str(e)}")
            return {}
    
    def update_user_preferences(self, username: str, preferences: Dict):
        """Update user preferences."""
        try:
            if username in self.users:
                self.users[username]["preferences"].update(preferences)
                self.save_users()
                logger.info(f"Updated preferences for user: {username}")
            
        except Exception as e:
            logger.error(f"Error updating user preferences: {str(e)}")
    
    def get_saved_login_info(self) -> Tuple[Optional[str], bool]:
        """Get saved login information."""
        try:
            # Check if user has saved login preference
            if self.current_user:
                preferences = self.get_user_preferences()
                if preferences.get("save_login", False):
                    return self.current_user, True
            
            return None, False
            
        except Exception as e:
            logger.error(f"Error getting saved login info: {str(e)}")
            return None, False
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions."""
        try:
            current_time = datetime.now()
            expired_sessions = []
            
            for session_id, session in self.sessions.items():
                expires_at = datetime.fromisoformat(session["expires_at"])
                if current_time > expires_at:
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                del self.sessions[session_id]
            
            if expired_sessions:
                self.save_sessions()
                logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
            
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {str(e)}")
    
    def get_user_stats(self) -> Dict:
        """Get user statistics."""
        try:
            total_users = len(self.users)
            active_sessions = len(self.sessions)
            
            # Count users by role
            admin_count = len([u for u in self.users.values() if u.get("role") == "admin"])
            user_count = total_users - admin_count
            
            return {
                "total_users": total_users,
                "active_sessions": active_sessions,
                "admin_count": admin_count,
                "user_count": user_count
            }
            
        except Exception as e:
            logger.error(f"Error getting user stats: {str(e)}")
            return {
                "total_users": 0,
                "active_sessions": 0,
                "admin_count": 0,
                "user_count": 0
            }
