"""
metrics.py - Prometheus metrics definitions for EduForAll.

Uses a singleton pattern to avoid duplicate registration errors
when Streamlit reruns the script on every interaction.
"""

from prometheus_client import Counter, Gauge, Histogram, REGISTRY

def _get_or_create(metric_class, name, description, **kwargs):
    """
    Returns existing metric if already registered, otherwise creates it.
    This prevents the 'Duplicated timeseries' error on Streamlit reruns.
    """
    try:
        return metric_class(name, description, **kwargs)
    except ValueError:
        # Already registered — retrieve it from the registry
        return REGISTRY._names_to_collectors.get(name) or \
               REGISTRY._names_to_collectors.get(name + "_total")


LOGIN_COUNTER = _get_or_create(
    Counter, "eduforall_logins_total", "Total number of successful user logins"
)

SIGNUP_COUNTER = _get_or_create(
    Counter, "eduforall_signups_total", "Total number of new user registrations"
)

RECOMMENDATIONS_COUNTER = _get_or_create(
    Counter, "eduforall_recommendations_total", "Total number of times recommendations were generated"
)

RATINGS_COUNTER = _get_or_create(
    Counter, "eduforall_ratings_total", "Total number of recommendation ratings submitted"
)

ACTIVE_USERS_GAUGE = _get_or_create(
    Gauge, "eduforall_active_users", "Number of currently active user sessions"
)

RECOMMENDATIONS_HISTOGRAM = _get_or_create(
    Histogram, "eduforall_recommendations_count",
    "Distribution of how many recommendations are returned per request",
    buckets=[1, 5, 10, 20, 30, 50]
)