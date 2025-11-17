from functools import lru_cache
import pandas as pd
import polars as pl
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "results_ecotox_ 20251117.parquet"

@lru_cache(maxsize=1)
def load_data() -> pd.DataFrame:
    """Load data as pandas DataFrame (for backward compatibility)."""
    df = pd.read_parquet(DATA_PATH)
    return df

@lru_cache(maxsize=1)
def load_data_polars() -> pl.DataFrame:
    """Load data as Polars DataFrame (for plotting functions)."""
    df = pl.read_parquet(DATA_PATH)
    return df
