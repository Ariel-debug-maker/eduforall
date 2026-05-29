"""
model.py - Handles all Machine Learning logic for EduForAll.

This module:
- Loads and preprocesses the training dataset
- Trains a Random Forest classifier
- Takes a student's profile as input
- Returns personalized study recommendations
"""

import logging
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

# ── Logging Setup ──────────────────────────────────────────────────────────────
# Reuse the same log file as database.py so all logs are in one place
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("eduforall.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ── Dataset Path ───────────────────────────────────────────────────────────────
DATA_PATH = "data/eduforall_training_dataset.csv"

# Columns that are input features (what the student fills in their profile)
FEATURE_COLS = [
    "disability_type",
    "specific_challenge",
    "severity_level",
    "age_group",
    "study_environment"
]

# Columns that are output recommendations (what the model should return)
RECOMMENDATION_COLS = [
    "recommendation_1",
    "recommendation_2",
    "recommendation_3",
    "recommendation_4",
    "recommendation_5",
    "recommendation_6",
    "recommendation_7"
]


def load_data():
    """
    Loads the training dataset from the CSV file.
    Returns a pandas DataFrame.
    """
    try:
        df = pd.read_csv("eduforall_training_dataset.csv")
        logger.info("Dataset loaded successfully. Rows: %d", len(df))
        return df
    except FileNotFoundError as e:
        logger.error("Dataset file not found at %s: %s", DATA_PATH, e)
        raise


def preprocess(df):
    """
    Encodes categorical text columns into numbers so the ML model can use them.

    The Random Forest algorithm only works with numbers, so we use
    LabelEncoders to convert text like 'Visual Impairment' → 0, 'ADHD' → 1, etc.

    Returns:
        X           - encoded feature matrix (inputs)
        encoders    - dict of LabelEncoders (needed later to encode new student input)
        df          - the original dataframe (used to look up recommendations)
    """
    encoders = {}  # store one encoder per feature column

    for col in FEATURE_COLS:
        # Fill any missing values with 'Unknown'
        df[col] = df[col].fillna("Unknown")

        # Create and fit a LabelEncoder for this column
        le = LabelEncoder()
        df[col + "_encoded"] = le.fit_transform(df[col])
        encoders[col] = le

    # Build the encoded feature matrix using the new encoded columns
    encoded_cols = [col + "_encoded" for col in FEATURE_COLS]
    X = df[encoded_cols]

    logger.info("Data preprocessing complete.")
    return X, encoders, df


def train_model(X, df):
    """
    Trains a Random Forest classifier on the dataset.

    We use 'disability_type' as the target label (y) because it's the
    main grouping factor for recommendations. The model learns which
    feature combinations map to which disability type, then we use
    that to find the closest matching rows in the dataset.

    Returns the trained RandomForestClassifier.
    """
    # Use the encoded disability_type as the prediction target
    y = df["disability_type_encoded"]

    # Initialize the Random Forest with 100 decision trees
    # random_state=42 ensures results are reproducible
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)

    logger.info("Random Forest model trained successfully.")
    return model


def get_recommendations(profile: dict, model, encoders, df):
    """
    Takes a student's profile and returns all matching recommendations.

    Steps:
    1. Encode the student's profile input using the saved LabelEncoders
    2. Use the model to predict the best matching disability group
    3. Filter the dataset to rows matching all profile fields
    4. Collect all non-empty recommendations from those rows
    5. Return a unique list of recommendations

    Args:
        profile  - dict with keys: disability_type, specific_challenge,
                   severity_level, age_group, study_environment
        model    - trained RandomForestClassifier
        encoders - dict of LabelEncoders from preprocess()
        df       - original dataframe

    Returns:
        List of recommendation strings
    """
    try:
        # ── Step 1: Encode the student's input ────────────────────────────────
        encoded_input = []
        for col in FEATURE_COLS:
            value = profile.get(col, "Unknown")
            le = encoders[col]

            # If the value is unseen (not in training data), default to index 0
            if value in le.classes_:
                encoded_value = le.transform([value])[0]
            else:
                logger.warning("Unseen value '%s' for column '%s'. Defaulting to 0.", value, col)
                encoded_value = 0

            encoded_input.append(encoded_value)

        # ── Step 2: Predict using the model (not strictly used for filtering
        #            but validates the input and logs confidence) ─────────────
        prediction = model.predict([encoded_input])
        logger.info("Model prediction (disability group index): %s", prediction[0])

        # ── Step 3: Filter dataset rows that match the student's profile ──────
        # Start with the full dataset and narrow down by each field
        filtered = df.copy()
        for col in FEATURE_COLS:
            value = profile.get(col, "Unknown")
            filtered = filtered[filtered[col] == value]

        logger.info("Matching rows found: %d", len(filtered))

        # ── Step 4: Collect all recommendations from matching rows ────────────
        recommendations = []
        for _, row in filtered.iterrows():
            for rec_col in RECOMMENDATION_COLS:
                rec = row.get(rec_col, "")
                # Only add non-empty, non-duplicate recommendations
                if pd.notna(rec) and rec.strip() != "" and rec not in recommendations:
                    recommendations.append(rec.strip())

        # ── Step 5: Fallback — if no exact match, use model prediction ────────
        # Filter only by disability_type if no rows matched all fields
        if not recommendations:
            logger.warning("No exact match found. Falling back to disability_type filter.")
            fallback = df[df["disability_type"] == profile.get("disability_type", "")]
            for _, row in fallback.iterrows():
                for rec_col in RECOMMENDATION_COLS:
                    rec = row.get(rec_col, "")
                    if pd.notna(rec) and rec.strip() != "" and rec not in recommendations:
                        recommendations.append(rec.strip())

        logger.info("Total recommendations returned: %d", len(recommendations))
        return recommendations

    except Exception as e:
        logger.error("Error generating recommendations: %s", e)
        raise


# ── Module-level model loading ─────────────────────────────────────────────────
# These are loaded once when the module is first imported,
# so we don't retrain on every page refresh in Streamlit.
try:
    _df = load_data()
    _X, _encoders, _df = preprocess(_df)
    _model = train_model(_X, _df)
    logger.info("Model ready for use.")
except Exception as e:
    logger.critical("Failed to initialize model: %s", e)
    _model = None
    _encoders = None
    _df = None


def recommend(profile: dict):
    """
    Public function called by the Streamlit app.
    Takes a profile dict and returns a list of recommendations.
    """
    if _model is None:
        raise RuntimeError("Model not initialized. Check your dataset path.")
    return get_recommendations(profile, _model, _encoders, _df)