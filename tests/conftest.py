"""Pytest configuration and fixtures."""

import pytest
from unittest.mock import Mock


@pytest.fixture
def mock_ads_client():
    """Mock Google Ads client for testing."""
    return Mock()


@pytest.fixture
def sample_customer_id():
    """Sample customer ID for testing."""
    return "1234567890"
