"""
API routes for OpenChemFacts Backend.

This module defines all the API endpoints including:
- Data access endpoints (summary, search, CAS list)
- Visualization endpoints (SSD plots, EC10eq plots, comparisons)
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List
from .data_loader import load_data, load_data_polars, load_benchmark_data
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
        cas_list: List of CAS numbers or chemical names to compare (maximum 3)
        width: Optional plot width in pixels (200-3000, default: 1600)
        height: Optional plot height in pixels (200-3000, default: 900)
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
    Get a summary of the available benchmark data.
    
    Returns:
        Dictionary containing:
        - rows: Total number of data rows
        - columns: Total number of columns
        - columns_names: List of all column names
        
    Raises:
        HTTPException: 404 if no data is available
    """
    df = load_benchmark_data()

    # Vérifier que les données existent
    if df.empty:
        raise HTTPException(status_code=404, detail="Aucune donnée")

    # Retourner les statistiques de base
    return {
        "chemicals": int(df["cas_number"].nunique()),
        "EF_openchemfacts(calculated)": int((df["Source"] == "OpenChemFacts 0.1").sum()),
        "EF_usetox(official)": int((df["Source"] == "USETOX 2.14").sum()),
        "EF_ef3.1(official)": int((df["Source"] == "EF 3.1").sum()),
    }

@router.get("/cas/list")
def get_cas_list():
    """
    Get list of all available CAS numbers with their chemical names from benchmark data.
    
    Returns:
        List of dictionaries, each containing cas_number and name
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
    Get benchmark data for a specific substance identified by CAS number.
    Returns a single entry (first match) from the benchmark data.
    
    Args:
        cas: CAS number of the substance
        
    Returns:
        Dictionary containing the benchmark data for the substance:
        - cas_number: CAS number of the substance
        - name: Chemical name
        - INCHIKEY: INCHI key
        - Kingdom: Chemical kingdom
        - Superclass: Chemical superclass
        - Class: Chemical class
        - EffectFactor(s): List of dictionaries with Source and EF (maximum 3 entries)
        
    Raises:
        HTTPException: 404 if the substance is not found
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


@router.get("/plot/ssd/{identifier}")
def get_ssd_plot(
    identifier: str,
    width: int = Query(None, ge=200, le=3000, description="Plot width in pixels (default: 1600)"),
    height: int = Query(None, ge=200, le=3000, description="Plot height in pixels (default: 900)")
):
    """
    Generate SSD (Species Sensitivity Distribution) and HC20 plot for a single chemical.
    
    The SSD uses pre-calculated parameters (SSD_mu_logEC10eq, SSD_sigma_logEC10eq) when available.
    When these parameters are 0 (indicating a single value case), the SSD is calculated
    from the Effect Factor (EF) in PAF.m3.kg from OpenChemFacts.
    
    Args:
        identifier: CAS number or chemical name (case-insensitive, partial match supported)
        width: Optional plot width in pixels (200-3000, default: 1600)
        height: Optional plot height in pixels (200-3000, default: 900)
        
    Returns:
        JSON representation of the Plotly figure (responsive and auto-sized)
    """
    plot_ssd_global, _, _ = _load_plotting_functions()
    if plot_ssd_global is None:
        raise HTTPException(
            status_code=503, 
            detail="Plotting functions not available. Please check dependencies."
        )
    
    try:
        # Resolve identifier to CAS number
        cas = resolve_cas_from_identifier(identifier)
        
        # Create custom config if dimensions are provided
        config = None
        if width is not None or height is not None:
            from data.plotting_functions import PlotConfig
            config = PlotConfig()
            if width is not None:
                config.plot_width = width
            if height is not None:
                config.plot_height = height
        
        df_params = load_data_polars()
        # Use the loaded function
        fig = plot_ssd_global(df_params, cas, config=config)
        return fig.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating plot: {str(e)}")


@router.get("/plot/ec10eq/{identifier}")
def get_ec10eq_plot(
    identifier: str,
    width: int = Query(None, ge=200, le=3000, description="Plot width in pixels (default: 1000)"),
    height: int = Query(None, ge=200, le=2000, description="Plot height in pixels (default: 600)")
):
    """
    Generate EC10eq results plot organized by taxa and species.
    
    Args:
        identifier: CAS number or chemical name (case-insensitive, partial match supported)
        width: Optional plot width in pixels (200-3000, default: 1000)
        height: Optional plot height in pixels (200-2000, default: 600)
        
    Returns:
        JSON representation of the Plotly figure
    """
    _, plot_ec10eq_by_taxa_and_species, _ = _load_plotting_functions()
    if plot_ec10eq_by_taxa_and_species is None:
        raise HTTPException(
            status_code=503, 
            detail="Plotting functions not available. Please check dependencies."
        )
    
    try:
        # Resolve identifier to CAS number
        cas = resolve_cas_from_identifier(identifier)
        
        # Create custom config if dimensions are provided
        config = None
        if width is not None or height is not None:
            from data.plotting_functions import PlotConfig
            config = PlotConfig()
            if width is not None:
                config.plot_width = width
            if height is not None:
                config.plot_height = height
        
        df_params = load_data_polars()
        # Use the loaded function
        fig = plot_ec10eq_by_taxa_and_species(df_params, cas, config=config)
        return fig.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating plot: {str(e)}")


@router.post("/plot/ssd/comparison")
def get_ssd_comparison(request: ComparisonRequest):
    """
    Create a comparison plot with multiple SSD curves superposed.
    
    Args:
        request: Request body containing:
                - cas_list: List of CAS numbers or chemical names (maximum 3)
                - width: Optional plot width in pixels (200-3000, default: 1600)
                - height: Optional plot height in pixels (200-3000, default: 900)
                Each identifier can be a CAS number or chemical name (case-insensitive, partial match supported)
        
    Returns:
        JSON representation of the Plotly figure (responsive and auto-sized)
    """
    _, _, plot_ssd_comparison = _load_plotting_functions()
    if plot_ssd_comparison is None:
        raise HTTPException(
            status_code=503, 
            detail="Plotting functions not available. Please check dependencies."
        )
    
    if len(request.cas_list) == 0:
        raise HTTPException(status_code=400, detail="At least one CAS number or chemical name must be provided")
    
    if len(request.cas_list) > 3:
        raise HTTPException(
            status_code=400, 
            detail=f"Maximum 3 substances can be compared. Provided: {len(request.cas_list)}"
        )
    
    # Validate dimensions if provided
    if request.width is not None and (request.width < 200 or request.width > 3000):
        raise HTTPException(status_code=400, detail="Width must be between 200 and 3000 pixels")
    if request.height is not None and (request.height < 200 or request.height > 3000):
        raise HTTPException(status_code=400, detail="Height must be between 200 and 3000 pixels")
    
    try:
        # Resolve all identifiers to CAS numbers
        resolved_cas_list = []
        for identifier in request.cas_list:
            cas = resolve_cas_from_identifier(identifier)
            resolved_cas_list.append(cas)
        
        # Create custom config if dimensions are provided
        config = None
        if request.width is not None or request.height is not None:
            from data.plotting_functions import PlotConfig
            config = PlotConfig()
            if request.width is not None:
                config.plot_width = request.width
            if request.height is not None:
                config.plot_height = request.height
        
        df_params = load_data_polars()
        # Use the loaded function
        fig = plot_ssd_comparison(df_params, resolved_cas_list, config=config)
        return fig.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating plot: {str(e)}")
