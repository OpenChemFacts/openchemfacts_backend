"""
Data processing module for EC10eq data by trophic group and species.

This module provides functions to load and format EC10eq data from parquet files.
It is used by app/api.py to generate JSON responses for the API endpoints.
"""

from typing import Optional, Dict, Any
from pathlib import Path
import os
import polars as pl

# Default data path (can be overridden via data_path parameter)
current_dir = Path(__file__).parent
DATA_PATH = os.getenv(
    "EC10EQ_DATA_PATH",
    str(current_dir / "results_ecotox_EC10_list_per_species.parquet")
)


def load_and_prepare_data(cas_number: str, data_path: Optional[str] = None) -> pl.DataFrame:
    """
    Load parquet file and prepare data for a specific CAS number.
    
    Args:
        cas_number: CAS number to filter by
        data_path: Optional path to the data file. If None, uses DATA_PATH from environment or default.
        
    Returns:
        DataFrame with exploded Details containing test_id, year, author, EC10eq
        
    Raises:
        FileNotFoundError: If data file not found
        ValueError: If CAS number not found
    """
    file_path = data_path or DATA_PATH
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Data file not found: {file_path}")
    
    # Load the parquet file
    df = pl.read_parquet(file_path)
    
    # Filter by CAS number
    df_filtered = df.filter(pl.col("cas_number") == cas_number)
    
    if df_filtered.is_empty():
        raise ValueError(f"No data found for CAS number: {cas_number}")
    
    # Explode Details to get individual endpoint records
    df_exploded = df_filtered.explode("Details")
    
    # Extract fields from Details struct
    df_exploded = df_exploded.with_columns([
        pl.col("Details").struct.field("test_id").alias("test_id"),
        pl.col("Details").struct.field("year").alias("year"),
        pl.col("Details").struct.field("author").alias("author"),
        pl.col("Details").struct.field("EC10eq").alias("EC10eq")
    ])
    
    # Drop the Details column as we've extracted all fields
    df_exploded = df_exploded.drop("Details")
    
    # Rename column for clarity
    df_exploded = df_exploded.rename({
        "ecotox_group_unepsetacjrc2018": "trophic_group"
    })
    
    return df_exploded


def get_ec10eq_data_json(cas_number: str, data_path: Optional[str] = None, output_format: str = "detailed") -> Dict[str, Any]:
    """
    Get EC10eq data for a CAS number in JSON format.
    
    This function is used by app/api.py to generate API responses.
    
    Args:
        cas_number: CAS number to filter by
        data_path: Optional path to the data file. If None, uses DATA_PATH from environment or default.
        output_format: Format of output - 'detailed' (default) or 'simple'
        
    Returns:
        Dictionary containing EC10eq data organized by trophic group and species:
        - 'detailed' format: nested structure by trophic_group -> species -> endpoints
        - 'simple' format: flat list of endpoints
        
    Raises:
        ValueError: If CAS number not found
        FileNotFoundError: If data file not found
    """
    df = load_and_prepare_data(cas_number, data_path)
    
    # Get chemical name
    chemical_name = None
    if "chemical_name" in df.columns:
        chemical_name = df["chemical_name"][0]
    
    # Convert to pandas for easier JSON serialization
    df_pd = df.to_pandas()
    
    # Handle missing values
    df_pd["year"] = df_pd["year"].fillna(0).astype(int)
    df_pd["author"] = df_pd["author"].fillna("Unknown")
    df_pd["test_id"] = df_pd["test_id"].fillna(0).astype(int)
    
    if output_format == "simple":
        # Simple format: just the endpoints
        endpoints = []
        for _, row in df_pd.iterrows():
            endpoints.append({
                "trophic_group": row["trophic_group"],
                "species": row["species_common_name"],
                "EC10eq": float(row["EC10eq"]),
                "test_id": int(row["test_id"]),
                "year": int(row["year"]),
                "author": row["author"]
            })
        
        return {
            "cas": cas_number,
            "chemical_name": chemical_name,
            "endpoints": endpoints
        }
    else:
        # Detailed format: organized by trophic group and species
        result = {
            "cas": cas_number,
            "chemical_name": chemical_name,
            "trophic_groups": {}
        }
        
        # Group by trophic group
        for trophic_group in sorted(df_pd["trophic_group"].unique()):
            df_group = df_pd[df_pd["trophic_group"] == trophic_group]
            result["trophic_groups"][trophic_group] = {}
            
            # Group by species
            for species in sorted(df_group["species_common_name"].unique()):
                df_species = df_group[df_group["species_common_name"] == species]
                endpoints = []
                
                for _, row in df_species.iterrows():
                    endpoints.append({
                        "EC10eq": float(row["EC10eq"]),
                        "test_id": int(row["test_id"]),
                        "year": int(row["year"]),
                        "author": row["author"]
                    })
                
                result["trophic_groups"][trophic_group][species] = endpoints
        
        return result
