"""
Data loading module for OpenChemFacts Backend.

This module provides functions to load ecotoxicology data from Parquet files.
The data is cached using lru_cache to improve performance by avoiding
repeated file reads.
"""
from functools import lru_cache
import pandas as pd
import polars as pl
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

# Path to the data file
# Note: Update this path if your data file has a different name or location
DATA_PATH_ssd = Path(__file__).resolve().parent.parent / "data" / "results_ecotox_ssd.parquet"
DATA_PATH_benchmark = Path(__file__).resolve().parent.parent / "data" / "results_EF_benchmark.parquet"

@lru_cache(maxsize=1)
def load_data() -> pd.DataFrame:
    """
    Load ecotoxicology data as a pandas DataFrame.
    
    This function uses caching (@lru_cache) to load the data only once
    and reuse it for subsequent calls, improving performance.
    
    Returns:
        pandas.DataFrame: DataFrame containing ecotoxicology data
        
    Raises:
        FileNotFoundError: If the data file doesn't exist at DATA_PATH_ecotox_database
        
    Example:
        >>> df = load_data()
        >>> print(df.head())
    """
    logger.info(f"Loading data from: {DATA_PATH_ssd}")
    logger.info(f"File exists: {DATA_PATH_ssd.exists()}")
    
    if not DATA_PATH_ssd.exists():
        raise FileNotFoundError(f"Data file not found at {DATA_PATH_ssd}")
    
    # Read the Parquet file
    df = pd.read_parquet(DATA_PATH_ssd)
    logger.info(f"Data loaded: {df.shape[0]} rows, {df.shape[1]} columns")
    
    return df


@lru_cache(maxsize=1)
def load_data_polars() -> pl.DataFrame:
    """
    Load ecotoxicology data as a Polars DataFrame.
    
    Polars is faster than Pandas for certain operations, especially
    on large datasets. This function is used by plotting functions
    that need better performance.
    
    This function uses caching (@lru_cache) to load the data only once
    and reuse it for subsequent calls.
    
    Returns:
        polars.DataFrame: DataFrame containing ecotoxicology data
        
    Raises:
        FileNotFoundError: If the data file doesn't exist at DATA_PATH_ecotox_database
        
    Example:
        >>> df = load_data_polars()
        >>> print(df.head())
    """
    logger.info(f"Loading data (Polars) from: {DATA_PATH_ssd}")
    logger.info(f"File exists: {DATA_PATH_ssd.exists()}")
    
    if not DATA_PATH_ssd.exists():
        raise FileNotFoundError(f"Data file not found at {DATA_PATH_ssd}")
    
    # Read the Parquet file with Polars
    df = pl.read_parquet(DATA_PATH_ssd)
    logger.info(f"Data loaded (Polars): {df.height} rows, {df.width} columns")
    
    return df


@lru_cache(maxsize=1)
def load_benchmark_data() -> pd.DataFrame:
    """
    Load benchmark data as a pandas DataFrame.
    
    This function uses caching (@lru_cache) to load the data only once
    and reuse it for subsequent calls, improving performance.
    
    Returns:
        pandas.DataFrame: DataFrame containing benchmark data
        
    Raises:
        FileNotFoundError: If the data file doesn't exist at DATA_PATH_benchmark
        
    Example:
        >>> df = load_benchmark_data()
        >>> print(df.head())
    """
    logger.info(f"Loading benchmark data from: {DATA_PATH_benchmark}")
    logger.info(f"File exists: {DATA_PATH_benchmark.exists()}")
    
    if not DATA_PATH_benchmark.exists():
        raise FileNotFoundError(f"Benchmark data file not found at {DATA_PATH_benchmark}")
    
    # Read the Parquet file
    df = pd.read_parquet(DATA_PATH_benchmark)
    logger.info(f"Benchmark data loaded: {df.shape[0]} rows, {df.shape[1]} columns")
    
    return df


@lru_cache(maxsize=1)
def load_benchmark_data_polars() -> pl.DataFrame:
    """
    Load benchmark data as a Polars DataFrame.
    
    Polars is faster than Pandas for certain operations, especially
    on large datasets. This function is used by plotting functions
    that need better performance.
    
    This function uses caching (@lru_cache) to load the data only once
    and reuse it for subsequent calls.
    
    Returns:
        polars.DataFrame: DataFrame containing benchmark data
        
    Raises:
        FileNotFoundError: If the data file doesn't exist at DATA_PATH_benchmark
        
    Example:
        >>> df = load_benchmark_data_polars()
        >>> print(df.head())
    """
    logger.info(f"Loading benchmark data (Polars) from: {DATA_PATH_benchmark}")
    logger.info(f"File exists: {DATA_PATH_benchmark.exists()}")
    
    if not DATA_PATH_benchmark.exists():
        raise FileNotFoundError(f"Benchmark data file not found at {DATA_PATH_benchmark}")
    
    # Read the Parquet file with Polars
    df = pl.read_parquet(DATA_PATH_benchmark)
    logger.info(f"Benchmark data loaded (Polars): {df.height} rows, {df.width} columns")
    
    return df