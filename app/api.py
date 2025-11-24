"""
API routes for OpenChemFacts Backend.

This module defines all the API endpoints including:
- Data access endpoints (summary, search, CAS list)
- Visualization endpoints (SSD plots, EC10eq plots, comparisons)
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List
from .data_loader import load_data, load_data_polars, load_benchmark_data, DATA_PATH_ec10eq
import sys
from pathlib import Path
import pandas as pd

# Ajouter le dossier data au path pour importer plotting_functions
# Cela permet d'importer les fonctions de visualisation depuis data/plotting_functions.py
data_dir = Path(__file__).resolve().parent.parent / "data"
sys.path.insert(0, str(data_dir.parent))

# Lazy import des fonctions de visualisation pour éviter de charger les dépendances lourdes au démarrage
# Les fonctions seront importées uniquement quand elles sont nécessaires
_plotting_functions_loaded = False
_plot_ssd_global = None
_plot_ec10eq_by_taxa_and_species = None
_plot_ssd_comparison = None


def _load_plotting_functions():
    """Charge les fonctions de visualisation de manière paresseuse (lazy loading)."""
    global _plotting_functions_loaded, _plot_ssd_global, _plot_ec10eq_by_taxa_and_species, _plot_ssd_comparison
    
    if _plotting_functions_loaded:
        return _plot_ssd_global, _plot_ec10eq_by_taxa_and_species, _plot_ssd_comparison
    
    try:
        from data.plotting_functions import (
            plot_ssd_global,
            plot_ec10eq_by_taxa_and_species,
            plot_ssd_comparison,
        )
        _plot_ssd_global = plot_ssd_global
        _plot_ec10eq_by_taxa_and_species = plot_ec10eq_by_taxa_and_species
        _plot_ssd_comparison = plot_ssd_comparison
    except ImportError:
        # Fallback si l'import échoue
        _plot_ssd_global = None
        _plot_ec10eq_by_taxa_and_species = None
        _plot_ssd_comparison = None
    
    _plotting_functions_loaded = True
    return _plot_ssd_global, _plot_ec10eq_by_taxa_and_species, _plot_ssd_comparison

# Créer le routeur API
# Toutes les routes définies ici seront préfixées par /api (défini dans main.py)
router = APIRouter()


class ComparisonRequest(BaseModel):
    """
    Request model for SSD comparison endpoint.
    
    Attributes:
        cas_list: List of CAS numbers or chemical names to compare (between 2 and 5)
        width: Optional plot width in pixels (200-3000, default: 1600) - deprecated
        height: Optional plot height in pixels (200-3000, default: 900) - deprecated
    """
    cas_list: List[str]
    width: int = None
    height: int = None


def resolve_cas_from_identifier(identifier: str) -> str:
    """
    Resolve a CAS number or chemical name to a CAS number.
    
    Args:
        identifier: CAS number or chemical name (case-insensitive, partial match supported)
        
    Returns:
        CAS number as string
        
    Raises:
        ValueError: If no matching substance is found or multiple matches found
    """
    df = load_data()
    
    # Normalize identifier (strip whitespace, case-insensitive)
    identifier_clean = identifier.strip()
    
    # First, try exact CAS match
    cas_exact = df[df["cas_number"] == identifier_clean]
    if not cas_exact.empty:
        return identifier_clean
    
    # Try exact name match (case-insensitive)
    name_exact = df[df["chemical_name"].str.lower() == identifier_clean.lower()]
    if not name_exact.empty:
        cas_numbers = name_exact["cas_number"].unique()
        if len(cas_numbers) == 1:
            return str(cas_numbers[0])
        else:
            raise ValueError(
                f"Multiple CAS numbers found for name '{identifier}': {list(cas_numbers)}. "
                f"Please use a CAS number instead."
            )
    
    # Try partial name match (case-insensitive)
    name_partial = df[df["chemical_name"].str.lower().str.contains(identifier_clean.lower(), na=False)]
    if not name_partial.empty:
        cas_numbers = name_partial["cas_number"].unique()
        if len(cas_numbers) == 1:
            return str(cas_numbers[0])
        else:
            # Return multiple matches for user to choose
            matches = name_partial[["cas_number", "chemical_name"]].drop_duplicates()
            matches_list = [
                {"cas": str(row["cas_number"]), "name": str(row["chemical_name"])}
                for _, row in matches.iterrows()
            ]
            raise ValueError(
                f"Multiple substances found matching '{identifier}': {matches_list}. "
                f"Please be more specific or use a CAS number."
            )
    
    # Try partial CAS match
    cas_partial = df[df["cas_number"].str.contains(identifier_clean, na=False)]
    if not cas_partial.empty:
        cas_numbers = cas_partial["cas_number"].unique()
        if len(cas_numbers) == 1:
            return str(cas_numbers[0])
        else:
            matches = cas_partial[["cas_number", "chemical_name"]].drop_duplicates()
            matches_list = [
                {"cas": str(row["cas_number"]), "name": str(row["chemical_name"])}
                for _, row in matches.iterrows()
            ]
            raise ValueError(
                f"Multiple CAS numbers found matching '{identifier}': {matches_list}. "
                f"Please use the full CAS number."
            )
    
    raise ValueError(f"No substance found matching '{identifier}'. Please check the CAS number or name.")


@router.get("/summary")
def get_summary():
    """
    Get a summary of available results in OpenChemFacts database.
    
    Returns a dictionary containing:\n
            - chemicals: Total number of CAS with a calculated effect factor (EF)
            - EF_openchemfacts(calculated): Total number of EF calculated by OpenChemFacts
            - EF_usetox(official): Total number of EF officially provided by USETOX
            - EF_ef3.1(official): Total number of EF officially provided by EF 3.1
    """
    
    df = load_benchmark_data()
    return {
        "chemicals": int(df["cas_number"].nunique()),
        "EF_openchemfacts(calculated)": int((df["Source"] == "OpenChemFacts 0.1").sum()),
        "EF_usetox(official)": int((df["Source"] == "USETOX 2.14").sum()),
        "EF_ef3.1(official)": int((df["Source"] == "EF 3.1").sum()),
    }

@router.get("/list")
def get_list():
    """
    Get list of all available chemicals in the database.

    Returns a list of dictionaries with CAS + INCHIKEY + NAME
    """
    df = load_benchmark_data()
    
    cas_data = df[["cas_number", "INCHIKEY", "name"]].drop_duplicates(subset=["cas_number", "INCHIKEY"])
    
    return [
        {"cas_number": str(row["cas_number"]), "INCHIKEY": str(row["INCHIKEY"]), "name": str(row["name"])}
        for _, row in cas_data.iterrows()
    ]

@router.get("/cas/{cas}")
def get_cas_data(cas: str):
    """
    Compile available effect factors (EF) for a specific chemical.

    Args:
        cas: CAS number of the substance
        
    Returns a dictionary containing:\n
        - cas_number: CAS number of the substance
        - name: Chemical name
        - INCHIKEY: INCHIKEY of the chemical
        - Kingdom: Classyfire classification kingdom
        - Superclass: Classyfire classification superclass
        - Class: Classyfire classification class
        - EffectFactor(s): List of dictionaries with Source and EF
    """
    try:
        # Load benchmark data
        df_benchmark = load_benchmark_data()
        
        # Filter by CAS number
        substance_data = df_benchmark[df_benchmark["cas_number"] == cas]
        
        if substance_data.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Substance with CAS number '{cas}' not found in benchmark data"
            )
        
        # Get the first entry (single substance) and select only required columns
        # Select only the required fields and convert to dict, handling NaN values
        required_fields = ["cas_number", "name", "INCHIKEY", "Kingdom", "Superclass", "Class"]
        selected_data = substance_data[required_fields].iloc[0]
        
        # Convert to dict and replace NaN/None values with None for JSON serialization
        data_record = {}
        for field in required_fields:
            value = selected_data[field]
            # Check if value is NaN using pandas
            if pd.isna(value):
                data_record[field] = None
            else:
                data_record[field] = value
        
        # Build EffectFactor(s) list from all available sources for this CAS
        effect_factors = []
        for _, row in substance_data.iterrows():
            source = row["Source"]
            ef_value = row["EF"]
            
            # Handle NaN values for EF
            if pd.isna(ef_value):
                ef_value = None
            else:
                ef_value = float(ef_value)
            
            effect_factors.append({
                "Source": str(source),
                "EF": ef_value
            })
        
        # Add EffectFactor(s) to the response
        data_record["EffectFactor(s)"] = effect_factors
        
        return data_record
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving data: {str(e)}")


@router.get("/search")
def search_substances(
    query: str = Query(..., description="Search term (CAS number or chemical name, partial match supported)"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results to return")
):
    """
    Search for substances by CAS number or chemical name.
    
    Supports:
    - Exact CAS number match
    - Exact chemical name match (case-insensitive)
    - Partial name match (case-insensitive)
    - Partial CAS match
    
    Args:
        query: Search term (CAS number or chemical name)
        limit: Maximum number of results (default: 20, max: 100)
        
    Returns:
        Dictionary with matching substances (CAS number and chemical name)
    """
    df = load_data()
    
    query_clean = query.strip()
    
    # Try exact CAS match first
    cas_exact = df[df["cas_number"] == query_clean]
    if not cas_exact.empty:
        results = cas_exact[["cas_number", "chemical_name"]].drop_duplicates()
        matches = [
            {"cas": str(row["cas_number"]), "name": str(row["chemical_name"])}
            for _, row in results.iterrows()
        ]
        return {
            "query": query,
            "count": len(matches),
            "matches": matches[:limit],
        }
    
    # Try exact name match (case-insensitive)
    name_exact = df[df["chemical_name"].str.lower() == query_clean.lower()]
    if not name_exact.empty:
        results = name_exact[["cas_number", "chemical_name"]].drop_duplicates()
        matches = [
            {"cas": str(row["cas_number"]), "name": str(row["chemical_name"])}
            for _, row in results.iterrows()
        ]
        return {
            "query": query,
            "count": len(matches),
            "matches": matches[:limit],
        }
    
    # Try partial name match (case-insensitive)
    name_partial = df[df["chemical_name"].str.lower().str.contains(query_clean.lower(), na=False)]
    if not name_partial.empty:
        results = name_partial[["cas_number", "chemical_name"]].drop_duplicates()
        matches = [
            {"cas": str(row["cas_number"]), "name": str(row["chemical_name"])}
            for _, row in results.iterrows()
        ]
        return {
            "query": query,
            "count": len(matches),
            "matches": matches[:limit],
        }
    
    # Try partial CAS match
    cas_partial = df[df["cas_number"].str.contains(query_clean, na=False)]
    if not cas_partial.empty:
        results = cas_partial[["cas_number", "chemical_name"]].drop_duplicates()
        matches = [
            {"cas": str(row["cas_number"]), "name": str(row["chemical_name"])}
            for _, row in results.iterrows()
        ]
        return {
            "query": query,
            "count": len(matches),
            "matches": matches[:limit],
        }
    
    # No matches found
    return {
        "query": query,
        "count": 0,
        "matches": [],
    }


@router.get("/plot/ssd/{cas}")
def get_ssd_plot(cas: str):
    """
    Get SSD (Species Sensitivity Distribution) data for a single chemical in JSON format.
    
    Returns all the data needed to generate the SSD plot, including:
    - SSD parameters (mu, sigma, HC20)
    - Chemical information (name, number of species, trophic groups)
    - Species data (EC10eq values, species names, trophic groups)
    - SSD curve points (concentrations and corresponding affected species percentages)
    
    Args:
        cas: CAS number (e.g., "107-05-1")
        
    Returns:
        JSON object containing SSD data structured as:
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
    """
    try:
        # Load data
        df = load_data()
        
        # Import and use the function from plot_ssd_curve
        from data.graph.SSD.plot_ssd_curve import get_ssd_data
        
        # Get SSD data (get_ssd_data handles CAS validation internally)
        ssd_data = get_ssd_data(df, cas)
        
        return ssd_data
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving SSD data: {str(e)}")


@router.get("/plot/ec10eq/{cas}")
def get_ec10eq_plot(
    cas: str,
    output_format: str = Query("detailed", description="Format de sortie: 'detailed' ou 'simple'"),
    width: int = Query(None, ge=200, le=3000, description="Plot width in pixels (default: 1000) - deprecated"),
    height: int = Query(None, ge=200, le=2000, description="Plot height in pixels (default: 600) - deprecated")
):
    """
    Get EC10eq data for a single chemical in JSON format.
    
    Returns EC10eq data organized by trophic group and species, including:
    - Chemical information (CAS, name)
    - Data organized by trophic groups and species
    - Individual endpoints with EC10eq values, test_id, year, and author
    
    Args:
        cas: CAS number (e.g., "60-51-5")
        output_format: Output format - 'detailed' (default) or 'simple'
        width: Optional plot width in pixels (200-3000, default: 1000) - deprecated, kept for compatibility
        height: Optional plot height in pixels (200-2000, default: 600) - deprecated, kept for compatibility
        
    Returns:
        JSON object containing EC10eq data structured as:
        {
            "cas": str,
            "chemical_name": str,
            "trophic_groups": {
                "trophic_group_name": {
                    "species_name": [
                        {
                            "EC10eq": float,
                            "test_id": int,
                            "year": int,
                            "author": str
                        }
                    ]
                }
            }
        }
        Or in 'simple' format:
        {
            "cas": str,
            "chemical_name": str,
            "endpoints": [
                {
                    "trophic_group": str,
                    "species": str,
                    "EC10eq": float,
                    "test_id": int,
                    "year": int,
                    "author": str
                }
            ]
        }
    """
    try:
        # Import the function from EC10eq_details
        from data.EC10eq_details import get_ec10eq_data_json
        
        # Get EC10eq data using the data path from data_loader
        ec10eq_data = get_ec10eq_data_json(cas, data_path=str(DATA_PATH_ec10eq), format=output_format)
        
        return ec10eq_data
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving EC10eq data: {str(e)}")


@router.post("/plot/ssd/comparison")
def get_ssd_comparison(request: ComparisonRequest):
    """
    Get SSD (Species Sensitivity Distribution) data for multiple chemicals in JSON format.
    
    Returns all the data used to generate SSD curves for comparison, including:
    - SSD parameters (mu, sigma, HC20) for each chemical
    - Chemical information (name, number of species, trophic groups) for each chemical
    - Species data (EC10eq values, species names, trophic groups) for each chemical
    - SSD curve points (concentrations and corresponding affected species percentages) for each chemical
    
    Uses the same logic as /plot/ssd/{cas} but for multiple chemicals (2 to 5).
    
    Args:
        request: Request body containing:
                - cas_list: List of CAS numbers or chemical names (between 2 and 5)
                - width: Optional plot width in pixels (200-3000, default: 1600) - deprecated, kept for compatibility
                - height: Optional plot height in pixels (200-3000, default: 900) - deprecated, kept for compatibility
                Each identifier can be a CAS number or chemical name (case-insensitive, partial match supported)
        
    Returns:
        JSON object containing SSD data for all chemicals structured as:
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
    """
    if len(request.cas_list) < 2:
        raise HTTPException(
            status_code=400, 
            detail=f"At least 2 substances must be provided for comparison. Provided: {len(request.cas_list)}"
        )
    
    if len(request.cas_list) > 5:
        raise HTTPException(
            status_code=400, 
            detail=f"Maximum 5 substances can be compared. Provided: {len(request.cas_list)}"
        )
    
    # Validate dimensions if provided (deprecated but kept for compatibility)
    if request.width is not None and (request.width < 200 or request.width > 3000):
        raise HTTPException(status_code=400, detail="Width must be between 200 and 3000 pixels")
    if request.height is not None and (request.height < 200 or request.height > 3000):
        raise HTTPException(status_code=400, detail="Height must be between 200 and 3000 pixels")
    
    try:
        # Load data
        df = load_data()
        
        # Resolve all identifiers to CAS numbers
        resolved_cas_list = []
        for identifier in request.cas_list:
            cas = resolve_cas_from_identifier(identifier)
            resolved_cas_list.append(cas)
        
        # Validate all CAS exist in database
        for cas in resolved_cas_list:
            if cas not in df['cas_number'].values:
                raise HTTPException(
                    status_code=404,
                    detail=f"CAS {cas} not found in database."
                )
        
        # Import and use the function from plot_ssd_curve (same as /plot/ssd/{cas})
        from data.graph.SSD.plot_ssd_curve import get_ssd_data
        
        # Get SSD data for each CAS
        comparison_data = []
        for cas in resolved_cas_list:
            ssd_data = get_ssd_data(df, cas)
            comparison_data.append(ssd_data)
        
        return {
            "comparison": comparison_data
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving SSD comparison data: {str(e)}")