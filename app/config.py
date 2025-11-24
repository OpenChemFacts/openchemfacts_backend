"""
Configuration module for OpenChemFacts Backend.

This module centralizes configuration settings that can be customized
via environment variables or default values.
"""
import os
from pathlib import Path
from typing import List


# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# Data file path
# Note: Update this if your data file has a different name
DATA_FILE_PATTERN = "results_ecotox_*.parquet"

# API Configuration
API_TITLE = "openchemfacts_API_0.1"
API_VERSION = "0.1.0"
API_DESCRIPTION = "API for accessing ecotoxicology data and generating scientific visualizations"

# CORS Configuration
# Default allowed origins (can be overridden with ALLOWED_ORIGINS environment variable)
DEFAULT_ALLOWED_ORIGINS = [
    "https://openchemfacts.com",
    "https://www.openchemfacts.com",
    "https://openchemfacts.lovable.app",
    "https://lovableproject.com",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

# Regex patterns for CORS
LOVABLE_APP_REGEX = r"https://.*\.lovable\.app"
LOVABLEPROJECT_REGEX = r"https://.*\.lovableproject\.com"
LOCALHOST_REGEX = r"http://localhost:\d+|http://127\.0\.0\.1:\d+"


def get_allowed_origins() -> List[str]:
    """
    Get list of allowed CORS origins.
    
    Reads from ALLOWED_ORIGINS environment variable if set,
    otherwise returns default origins.
    
    Returns:
        List of allowed origin strings
    """
    allowed_origins_str = os.getenv(
        "ALLOWED_ORIGINS",
        ",".join(DEFAULT_ALLOWED_ORIGINS)
    )
    return [origin.strip() for origin in allowed_origins_str.split(",") if origin.strip()]


def get_cors_regex() -> str:
    """
    Get CORS regex pattern for dynamic origins.
    
    Returns:
        Combined regex pattern for lovable.app, lovableproject.com and localhost
    """
    return f"{LOVABLE_APP_REGEX}|{LOVABLEPROJECT_REGEX}|{LOCALHOST_REGEX}"


# Server Configuration
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8000

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Security Configuration
# Rate Limiting
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
RATE_LIMIT_PLOT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PLOT_PER_MINUTE", "10"))
RATE_LIMIT_HEALTH_PER_MINUTE = int(os.getenv("RATE_LIMIT_HEALTH_PER_MINUTE", "120"))

# Request Size Limiting
MAX_REQUEST_SIZE = int(os.getenv("MAX_REQUEST_SIZE", "1048576"))  # Default: 1MB

# Security Headers
ENABLE_SECURITY_HEADERS = os.getenv("ENABLE_SECURITY_HEADERS", "true").lower() == "true"

# API Keys (for Phase 2)
API_KEYS = os.getenv("API_KEYS", "").split(",") if os.getenv("API_KEYS") else []

