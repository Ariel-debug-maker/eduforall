"""
tests/test_model.py - Unit tests for model.py using pytest.

What we test:
- Data loads correctly
- Preprocessing works
- Model trains without errors
- Recommendations are returned for a valid profile
- Unknown/missing inputs are handled gracefully
- Empty recommendations are never returned

Run with:
    pytest tests/test_model.py -v
"""

import pytest
import pandas as pd
import sys
import os

# ── Path Setup ─────────────────────────────────────────────────────────────────
# Add the parent folder to sys.path so we can import model.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from model import load_data, preprocess, train_model, get_recommendations


# ── Fixtures ───────────────────────────────────────────────────────────────────
# Fixtures are reusable setup functions pytest injects into tests.
# Instead of loading data in every test, we load it once here.

@pytest.fixture
def dataset():
    """Loads the dataset once and shares it across all tests."""
    return load_data()


@pytest.fixture
def processed(dataset):
    """
    Preprocesses the dataset and returns:
    - X: encoded feature matrix
    - encoders: LabelEncoders for each feature column
    - df: the original dataframe with encoded columns added
    """
    X, encoders, df = preprocess(dataset)
    return X, encoders, df


@pytest.fixture
def trained_model(processed):
    """Trains the Random Forest model and returns it."""
    X, encoders, df = processed
    model = train_model(X, df)
    return model


@pytest.fixture
def valid_profile():
    """A sample student profile that exists in the dataset."""
    return {
        "disability_type": "Visual Impairment",
        "specific_challenge": "Complete Blindness",
        "severity_level": "Mild",
        "age_group": "Child",
        "study_environment": "Home"
    }


# ── Tests ──────────────────────────────────────────────────────────────────────

class TestDataLoading:
    """Tests related to loading the dataset."""

    def test_data_loads_successfully(self, dataset):
        """Check that the dataset loads and is not empty."""
        assert dataset is not None
        assert len(dataset) > 0, "Dataset should have at least one row"

    def test_data_has_required_columns(self, dataset):
        """Check that all required feature and recommendation columns exist."""
        required_cols = [
            "disability_type", "specific_challenge", "severity_level",
            "age_group", "study_environment",
            "recommendation_1", "recommendation_2"
        ]
        for col in required_cols:
            assert col in dataset.columns, f"Missing column: {col}"

    def test_data_has_enough_rows(self, dataset):
        """Ensure the dataset has a reasonable number of rows."""
        assert len(dataset) >= 100, "Dataset should have at least 100 rows"

    def test_no_completely_empty_rows(self, dataset):
        """Check that no row is completely empty."""
        completely_empty = dataset.dropna(how="all")
        assert len(completely_empty) == len(dataset), "Dataset should have no completely empty rows"


class TestPreprocessing:
    """Tests related to preprocessing and encoding."""

    def test_encoders_created_for_all_features(self, processed):
        """Check that a LabelEncoder was created for each feature column."""
        _, encoders, _ = processed
        expected_cols = [
            "disability_type", "specific_challenge",
            "severity_level", "age_group", "study_environment"
        ]
        for col in expected_cols:
            assert col in encoders, f"Missing encoder for: {col}"

    def test_encoded_columns_are_numeric(self, processed):
        """Check that encoded columns contain only numbers."""
        X, _, _ = processed
        for col in X.columns:
            assert pd.api.types.is_numeric_dtype(X[col]), \
                f"Column {col} should be numeric after encoding"

    def test_no_null_values_in_features(self, processed):
        """Check that preprocessing removed all null values from features."""
        X, _, _ = processed
        assert X.isnull().sum().sum() == 0, "Encoded features should have no null values"

    def test_feature_matrix_has_correct_shape(self, processed):
        """Check that the feature matrix has exactly 5 columns (one per feature)."""
        X, _, _ = processed
        assert X.shape[1] == 5, "Feature matrix should have 5 columns"


class TestModelTraining:
    """Tests related to training the Random Forest model."""

    def test_model_trains_without_error(self, trained_model):
        """Check that the model object is created successfully."""
        assert trained_model is not None

    def test_model_has_estimators(self, trained_model):
        """Check that the model has the expected number of decision trees."""
        assert len(trained_model.estimators_) == 100, \
            "Model should have 100 decision trees"

    def test_model_has_feature_importances(self, trained_model):
        """Check that the model computed feature importances after training."""
        importances = trained_model.feature_importances_
        assert len(importances) > 0, "Model should have feature importances"

    def test_feature_importances_sum_to_one(self, trained_model):
        """Feature importances should always sum to 1.0 in a Random Forest."""
        total = sum(trained_model.feature_importances_)
        assert abs(total - 1.0) < 0.001, "Feature importances should sum to ~1.0"


class TestRecommendations:
    """Tests related to generating recommendations."""

    def test_returns_recommendations_for_valid_profile(
        self, valid_profile, trained_model, processed
    ):
        """Check that a valid profile returns a non-empty list of recommendations."""
        _, encoders, df = processed
        recs = get_recommendations(valid_profile, trained_model, encoders, df)
        assert isinstance(recs, list), "Recommendations should be a list"
        assert len(recs) > 0, "Should return at least one recommendation"

    def test_recommendations_are_strings(
        self, valid_profile, trained_model, processed
    ):
        """Check that every recommendation is a non-empty string."""
        _, encoders, df = processed
        recs = get_recommendations(valid_profile, trained_model, encoders, df)
        for rec in recs:
            assert isinstance(rec, str), "Each recommendation should be a string"
            assert rec.strip() != "", "Recommendations should not be empty strings"

    def test_no_duplicate_recommendations(
        self, valid_profile, trained_model, processed
    ):
        """Check that the same recommendation is not returned twice."""
        _, encoders, df = processed
        recs = get_recommendations(valid_profile, trained_model, encoders, df)
        assert len(recs) == len(set(recs)), "Recommendations should be unique"

    def test_handles_unknown_disability_type(self, trained_model, processed):
        """
        Check that the model handles an unknown disability type gracefully.
        It should not crash — it should fall back and return an empty list.
        """
        _, encoders, df = processed
        unknown_profile = {
            "disability_type": "Unknown Disability XYZ",  # not in dataset
            "specific_challenge": "Complete Blindness",
            "severity_level": "Mild",
            "age_group": "Child",
            "study_environment": "Home"
        }
        # Should not raise an exception — just return empty or fallback list
        try:
            recs = get_recommendations(unknown_profile, trained_model, encoders, df)
            assert isinstance(recs, list), "Should still return a list even for unknown input"
        except Exception as e:
            pytest.fail(f"Model crashed on unknown input: {e}")

    def test_handles_missing_profile_keys(self, trained_model, processed):
        """
        Check that the model handles a profile with missing keys gracefully.
        Missing keys should default to 'Unknown' without crashing.
        """
        _, encoders, df = processed
        incomplete_profile = {
            "disability_type": "Visual Impairment"
            # all other keys are missing
        }
        try:
            recs = get_recommendations(incomplete_profile, trained_model, encoders, df)
            assert isinstance(recs, list), "Should return a list even for incomplete profile"
        except Exception as e:
            pytest.fail(f"Model crashed on incomplete profile: {e}")

    def test_different_profiles_can_return_different_recommendations(
        self, trained_model, processed
    ):
        """
        Check that two very different profiles don't always return the same results.
        This validates that the model is actually personalizing recommendations.
        """
        _, encoders, df = processed

        profile_a = {
            "disability_type": "Visual Impairment",
            "specific_challenge": "Complete Blindness",
            "severity_level": "Severe",
            "age_group": "Adult",
            "study_environment": "Home"
        }
        profile_b = {
            "disability_type": "ADHD",
            "specific_challenge": "Attention Difficulties",
            "severity_level": "Mild",
            "age_group": "Teenager",
            "study_environment": "Online"
        }

        recs_a = get_recommendations(profile_a, trained_model, encoders, df)
        recs_b = get_recommendations(profile_b, trained_model, encoders, df)

        # They should not be identical — different profiles, different strategies
        assert recs_a != recs_b, \
            "Different profiles should produce different recommendations"