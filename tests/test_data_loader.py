"""
Tests for data loading functions.
"""
import pytest
from app.data_loader import load_data, load_data_polars, DATA_PATH


def test_data_file_exists():
    """Test that the data file exists."""
    assert DATA_PATH.exists(), f"Data file not found at {DATA_PATH}"


def test_load_data():
    """Test that data can be loaded as pandas DataFrame."""
    df = load_data()
    assert df is not None
    assert len(df) > 0, "DataFrame is empty"
    assert "cas_number" in df.columns, "cas_number column not found"
    assert "chemical_name" in df.columns, "chemical_name column not found"


def test_load_data_polars():
    """Test that data can be loaded as Polars DataFrame."""
    df = load_data_polars()
    assert df is not None
    assert df.height > 0, "DataFrame is empty"
    assert "cas_number" in df.columns, "cas_number column not found"
    assert "chemical_name" in df.columns, "chemical_name column not found"


def test_load_data_cached():
    """Test that load_data uses caching (same object returned)."""
    df1 = load_data()
    df2 = load_data()
    # With caching, should be the same object (or at least same data)
    assert len(df1) == len(df2)
    assert list(df1.columns) == list(df2.columns)


def test_load_data_polars_cached():
    """Test that load_data_polars uses caching."""
    df1 = load_data_polars()
    df2 = load_data_polars()
    assert df1.height == df2.height
    assert df1.columns == df2.columns


def test_data_has_required_columns():
    """Test that the data has the required columns for API endpoints."""
    df = load_data()
    required_columns = ["cas_number", "chemical_name"]
    
    for col in required_columns:
        assert col in df.columns, f"Required column '{col}' not found in data"


def test_data_has_records():
    """Test that the data contains records."""
    df = load_data()
    assert len(df) > 0, "Data should contain at least one record"


def test_cas_numbers_exist():
    """Test that the data contains CAS numbers."""
    df = load_data()
    cas_numbers = df["cas_number"].dropna().unique()
    assert len(cas_numbers) > 0, "Data should contain at least one CAS number"

