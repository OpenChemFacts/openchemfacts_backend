"""
API routes for OpenChemFacts Backend.

This module defines all the API endpoints including:
- Data access endpoints (summary, search, CAS list)
- Visualization endpoints (SSD plots, EC10eq plots, comparisons)
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List
from .data_loader import load_data, load_data_polars
import sys
from pathlib import Path

# Ajouter le dossier data au path pour importer plotting_functions
# Cela permet d'importer les fonctions de visualisation depuis data/plotting_functions.py
data_dir = Path(__file__).resolve().parent.parent / "data"
sys.path.insert(0, str(data_dir.parent))

# Importer les fonctions de visualisation
# Si l'import échoue (par exemple si les dépendances ne sont pas installées),
# on définit les fonctions à None pour gérer l'erreur gracieusement
try:
    from data.plotting_functions import (
        plot_ssd_global,
        plot_ec10eq_by_taxa_and_species,
        plot_ssd_comparison,
    )
except ImportError:
    # Fallback si l'import échoue
    plot_ssd_global = None
    plot_ec10eq_by_taxa_and_species = None
    plot_ssd_comparison = None

# Créer le routeur API
# Toutes les routes définies ici seront préfixées par /api (défini dans main.py)
router = APIRouter()


class ComparisonRequest(BaseModel):
    """
    Request model for SSD comparison endpoint.
    
    Attributes:
        cas_list: List of CAS numbers or chemical names to compare (maximum 3)
    """
    cas_list: List[str]


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
    Get a summary of the available data.
    
    Returns:
        Dictionary containing:
        - rows: Total number of data rows
        - columns: Total number of columns
        - columns_names: List of all column names
        
    Raises:
        HTTPException: 404 if no data is available
    """
    df = load_data()

    # Vérifier que les données existent
    if df.empty:
        raise HTTPException(status_code=404, detail="Aucune donnée")

    # Retourner les statistiques de base
    return {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "columns_names": list(df.columns),
    }


@router.get("/by_column")
def get_by_column(column: str):
    """
    Get unique values for a specific column.
    
    Args:
        column: Name of the column to query
        
    Returns:
        Dictionary containing:
        - column: Name of the queried column
        - unique_values: List of unique values in the column
        - count: Number of unique values
        
    Raises:
        HTTPException: 400 if the column doesn't exist
    """
    df = load_data()

    # Vérifier que la colonne existe
    if column not in df.columns:
        raise HTTPException(status_code=400, detail="Colonne inconnue")

    # Récupérer les valeurs uniques (sans les valeurs nulles)
    values = df[column].dropna().unique().tolist()
    return {
        "column": column,
        "unique_values": values,
        "count": len(values),
    }


@router.get("/cas/list")
def get_cas_list():
    """
    Get list of all available CAS numbers with their chemical names.
    
    Returns:
        Dictionary with CAS numbers and their corresponding chemical names
    """
    df = load_data()
    
    cas_data = df[["cas_number", "chemical_name"]].drop_duplicates()
    cas_list = cas_data.groupby("cas_number")["chemical_name"].first().to_dict()
    
    return {
        "count": len(cas_list),
        "cas_numbers": list(cas_list.keys()),
        "cas_with_names": {cas: name for cas, name in cas_list.items()},
    }


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
def get_ssd_plot(identifier: str):
    """
    Generate SSD (Species Sensitivity Distribution) and HC20 plot for a single chemical.
    
    Args:
        identifier: CAS number or chemical name (case-insensitive, partial match supported)
        
    Returns:
        JSON representation of the Plotly figure
    """
    if plot_ssd_global is None:
        raise HTTPException(
            status_code=503, 
            detail="Plotting functions not available. Please check dependencies."
        )
    
    try:
        # Resolve identifier to CAS number
        cas = resolve_cas_from_identifier(identifier)
        
        df_params = load_data_polars()
        fig = plot_ssd_global(df_params, cas)
        return fig.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating plot: {str(e)}")


@router.get("/plot/ec10eq/{identifier}")
def get_ec10eq_plot(identifier: str):
    """
    Generate EC10eq results plot organized by taxa and species.
    
    Args:
        identifier: CAS number or chemical name (case-insensitive, partial match supported)
        
    Returns:
        JSON representation of the Plotly figure
    """
    if plot_ec10eq_by_taxa_and_species is None:
        raise HTTPException(
            status_code=503, 
            detail="Plotting functions not available. Please check dependencies."
        )
    
    try:
        # Resolve identifier to CAS number
        cas = resolve_cas_from_identifier(identifier)
        
        df_params = load_data_polars()
        fig = plot_ec10eq_by_taxa_and_species(df_params, cas)
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
        request: Request body containing a list of CAS numbers or chemical names (maximum 3)
                Each identifier can be a CAS number or chemical name (case-insensitive, partial match supported)
        
    Returns:
        JSON representation of the Plotly figure
    """
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
    
    try:
        # Resolve all identifiers to CAS numbers
        resolved_cas_list = []
        for identifier in request.cas_list:
            cas = resolve_cas_from_identifier(identifier)
            resolved_cas_list.append(cas)
        
        df_params = load_data_polars()
        fig = plot_ssd_comparison(df_params, resolved_cas_list)
        return fig.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating plot: {str(e)}")
