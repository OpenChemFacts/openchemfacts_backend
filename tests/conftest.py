"""
Configuration and fixtures for pytest tests.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """
    Create a test client for the API.
    
    This fixture provides a TestClient instance that can be used
    to make HTTP requests to the API without starting a real server.
    """
    return TestClient(app)


@pytest.fixture
def sample_cas():
    """
    Provide a sample CAS number for testing.
    
    Note: This should be a CAS number that exists in your data file.
    You may need to update this with a valid CAS from your dataset.
    """
    return "335104-84-2"  # Update with a valid CAS from your data

