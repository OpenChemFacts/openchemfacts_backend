"""
Data processing module for SSD comparison.

This module provides functions to generate SSD comparison data for multiple chemicals.
It is used by app/api.py to generate JSON responses for the API endpoints.
"""

from typing import List, Dict, Any
import pandas as pd


def get_ssd_comparison_data(
    dataframe: pd.DataFrame,
    cas_list: List[str]
) -> Dict[str, Any]:
    """
    Get SSD (Species Sensitivity Distribution) data for multiple chemicals.
    
    This function processes multiple CAS numbers and returns their SSD data
    in a format suitable for comparison.
    
    Args:
        dataframe: DataFrame containing SSD data (from load_data())
        cas_list: List of CAS numbers to compare (already validated and resolved)
        
    Returns:
        Dictionary containing SSD data for all chemicals:
        {
            "comparison": [
                {
                    "cas_number": str,
                    "chemical_name": str,
                    "ssd_parameters": {
                        "mu_logEC10eq": float,
                        "sigma_logEC10eq": float,
                        "hc20_mgL": float
                    },
                    "summary": {
                        "n_species": int,
                        "n_ecotox_group": int
                    },
                    "species_data": [
                        {
                            "species_name": str,
                            "ec10eq_mgL": float,
                            "trophic_group": str
                        }
                    ],
                    "ssd_curve": {
                        "concentrations_mgL": [float],
                        "affected_species_percent": [float]
                    } or None
                }
            ]
        }
        
    Raises:
        ValueError: If any CAS number is not found in the dataframe
    """
    from data.graph.SSD.plot_ssd_curve import get_ssd_data
    
    # Validate all CAS exist in database
    for cas in cas_list:
        if cas not in dataframe['cas_number'].values:
            raise ValueError(f"CAS {cas} not found in database.")
    
    # Get SSD data for each CAS
    comparison_data = []
    for cas in cas_list:
        ssd_data = get_ssd_data(dataframe, cas)
        comparison_data.append(ssd_data)
    
    return {
        "comparison": comparison_data
    }

