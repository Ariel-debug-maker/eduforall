"""
auth.py - Handles all authentication logic for EduForAll.

This module:
- Manages user signup (creating new accounts)
- Manages user login using streamlit-authenticator
- Stores hashed passwords securely (never plain text)
- Integrates with database.py for user storage
- Builds the authenticator config dynamically from the database
"""

import logging
import bcrypt
import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from database import create_user, get_user_by_username, init_db

# ── Logging Setup ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("eduforall.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ── Password Hashing ───────────────────────────────────────────────────────────

def hash_password(plain_password: str) -> str:
    """
    Hashes a plain text password using bcrypt.
    bcrypt automatically adds a salt, making it secure against rainbow table attacks.

    Args:
        plain_password: the raw password the user typed

    Returns:
        A hashed password string safe to store in the database
    """
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain password against a stored hashed password.

    Args:
        plain_password: what the user typed at login
        hashed_password: what's stored in the database

    Returns:
        True if they match, False otherwise
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )


# ── Signup ─────────────────────────────────────────────────────────────────────

def signup_page(on_success=None):
    """
    Renders the signup form in Streamlit.
    Validates input, hashes the password, and stores the new user in the database.

    Args:
        on_success: optional callback function called after successful signup.
                    Used by app.py to switch the view to the login tab automatically.
    """
    st.markdown("## Create Your Account")
    st.markdown("Join EduForAll and get personalized study strategies.")

    # Input fields for signup
    username = st.text_input("Username", placeholder="e.g. ariel123")
    email = st.text_input("Email", placeholder="e.g. ariel@example.com")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")

    if st.button("Sign Up", use_container_width=True):
        # ── Validation ─────────────────────────────────────────────────────────
        if not username or not email or not password:
            st.error("All fields are required.")
            return

        if password != confirm_password:
            st.error("Passwords do not match.")
            return

        if len(password) < 6:
            st.error("Password must be at least 6 characters.")
            return

        # Check if username already exists
        existing_user = get_user_by_username(username)
        if existing_user:
            st.error("Username already taken. Please choose another.")
            return

        # ── Save User ──────────────────────────────────────────────────────────
        hashed = hash_password(password)
        user_id = create_user(username, email, hashed)

        if user_id:
            logger.info("New user signed up: %s", username)
            # ── Prometheus: increment signup counter ───────────────────────────
            try:
                from metrics import SIGNUP_COUNTER
                SIGNUP_COUNTER.inc()
            except Exception:
                pass
            if on_success:
                on_success()
            st.rerun()
        else:
            st.error("Signup failed. Email may already be in use.")


# ── Login ──────────────────────────────────────────────────────────────────────

def login_page():
    """
    Renders the login form in Streamlit.
    Checks credentials against the database and sets session state on success.

    Session state keys set on successful login:
        st.session_state["authenticated"] = True
        st.session_state["username"] = username
        st.session_state["user_id"] = user_id
    """
    st.markdown("## Welcome Back!")
    st.markdown("Log in to access your personalized dashboard.")

    username = st.text_input("Username", placeholder="Enter your username")
    password = st.text_input("Password", type="password", placeholder="Enter your password")

    if st.button("Log In", use_container_width=True):
        if not username or not password:
            st.error("Please enter both username and password.")
            return

        # Fetch user from database
        user = get_user_by_username(username)

        if not user:
            # Don't reveal whether username or password is wrong (security best practice)
            st.error("Invalid username or password.")
            logger.warning("Failed login attempt for username: %s", username)
            return

        # Verify the password
        if verify_password(password, user["hashed_password"]):
            # ── Set session state on success ───────────────────────────────────
            st.session_state["authenticated"] = True
            st.session_state["username"] = username
            st.session_state["user_id"] = user["id"]
            logger.info("User logged in: %s", username)
            # ── Prometheus: increment login counter ────────────────────────────
            try:
                from metrics import LOGIN_COUNTER, ACTIVE_USERS_GAUGE
                LOGIN_COUNTER.inc()
                ACTIVE_USERS_GAUGE.inc()
            except Exception:
                pass
            st.rerun()
        else:
            st.error("Invalid username or password.")
            logger.warning("Wrong password for username: %s", username)


# ── Logout ─────────────────────────────────────────────────────────────────────

def logout():
    """
    Clears all session state to log the user out.
    Called from the dashboard sidebar.
    """
    logger.info("User logged out: %s", st.session_state.get("username", "unknown"))
    # Clear all session keys related to authentication
    for key in ["authenticated", "username", "user_id"]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()


# ── Auth Guard ─────────────────────────────────────────────────────────────────

def is_authenticated() -> bool:
    """
    Checks if the current user is logged in.
    Used in app.py to decide whether to show login or dashboard.

    Returns:
        True if the user is logged in, False otherwise
    """
    return st.session_state.get("authenticated", False)