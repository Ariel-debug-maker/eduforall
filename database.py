"""
database.py - Handles all SQLite database operations for EduForAll.
"""

import sqlite3
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("eduforall.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

DB_PATH = "eduforall.db"


def get_connection():
    """Returns a connection to the SQLite database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error("Failed to connect to database: %s", e)
        raise


def init_db():
    """Creates all tables if they don't exist."""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Profiles table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                disability_type TEXT,
                specific_challenge TEXT,
                severity_level TEXT,
                age_group TEXT,
                study_environment TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Ratings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                recommendation_text TEXT NOT NULL,
                stars INTEGER CHECK(stars BETWEEN 1 AND 5),
                helpful INTEGER CHECK(helpful IN (0, 1)),
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        conn.commit()
        conn.close()
        logger.info("Database initialized successfully.")
    except sqlite3.Error as e:
        logger.error("Error initializing database: %s", e)
        raise


def save_profile(user_id, disability_type, specific_challenge,
                 severity_level, age_group, study_environment):
    """Saves or updates a student's profile."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO profiles 
                (user_id, disability_type, specific_challenge,
                 severity_level, age_group, study_environment, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                disability_type=excluded.disability_type,
                specific_challenge=excluded.specific_challenge,
                severity_level=excluded.severity_level,
                age_group=excluded.age_group,
                study_environment=excluded.study_environment,
                updated_at=excluded.updated_at
        """, (user_id, disability_type, specific_challenge,
              severity_level, age_group, study_environment,
              datetime.now().isoformat()))
        conn.commit()
        conn.close()
        logger.info("Profile saved for user_id: %s", user_id)
    except sqlite3.Error as e:
        logger.error("Error saving profile for user_id %s: %s", user_id, e)
        raise


def get_profile(user_id):
    """Fetches a student's profile by user_id."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,))
        profile = cursor.fetchone()
        conn.close()
        return dict(profile) if profile else None
    except sqlite3.Error as e:
        logger.error("Error fetching profile for user_id %s: %s", user_id, e)
        raise


def save_rating(user_id, recommendation_text, stars, helpful):
    """Saves a student's rating for a recommendation."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ratings (user_id, recommendation_text, stars, helpful, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, recommendation_text, stars, helpful,
              datetime.now().isoformat()))
        conn.commit()
        conn.close()
        logger.info("Rating saved for user_id: %s", user_id)
    except sqlite3.Error as e:
        logger.error("Error saving rating for user_id %s: %s", user_id, e)
        raise


def get_user_ratings(user_id):
    """Fetches all ratings submitted by a student."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM ratings WHERE user_id = ? ORDER BY timestamp DESC",
            (user_id,)
        )
        ratings = cursor.fetchall()
        conn.close()
        return [dict(r) for r in ratings]
    except sqlite3.Error as e:
        logger.error("Error fetching ratings for user_id %s: %s", user_id, e)
        raise


def get_user_by_username(username):
    """Fetches a user record by username."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None
    except sqlite3.Error as e:
        logger.error("Error fetching user %s: %s", username, e)
        raise


def create_user(username, email, hashed_password):
    """Creates a new user in the database."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (username, email, hashed_password)
            VALUES (?, ?, ?)
        """, (username, email, hashed_password))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        logger.info("User created: %s", username)
        return user_id
    except sqlite3.IntegrityError as e:
        logger.warning("Duplicate user attempt: %s - %s", username, e)
        return None
    except sqlite3.Error as e:
        logger.error("Error creating user %s: %s", username, e)
        raise