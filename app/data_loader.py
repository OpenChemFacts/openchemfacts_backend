from functools import lru_cache
import pandas as pd
import polars as pl
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "results_ecotox_ 20251117.parquet"

@lru_cache(maxsize=1)
def load_data() -> pd.DataFrame:
    """Load data as pandas DataFrame (for backward compatibility)."""
    logger.info(f"Loading data from: {DATA_PATH}")
    logger.info(f"File exists: {DATA_PATH.exists()}")
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Data file not found at {DATA_PATH}")
    df = pd.read_parquet(DATA_PATH)
    logger.info(f"Data loaded: {df.shape[0]} rows, {df.shape[1]} columns")
    return df

@lru_cache(maxsize=1)
def load_data_polars() -> pl.DataFrame:
    """Load data as Polars DataFrame (for plotting functions)."""
    logger.info(f"Loading data (Polars) from: {DATA_PATH}")
    logger.info(f"File exists: {DATA_PATH.exists()}")
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Data file not found at {DATA_PATH}")
    df = pl.read_parquet(DATA_PATH)
    logger.info(f"Data loaded (Polars): {df.shape[0]} rows, {df.shape[1]} columns")
    return df
