from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from .data_loader import load_data, load_data_polars
import sys
from pathlib import Path

# Ajouter le dossier data au path pour importer plotting_functions
data_dir = Path(__file__).resolve().parent.parent / "data"
sys.path.insert(0, str(data_dir.parent))

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

router = APIRouter()


class ComparisonRequest(BaseModel):
    """Request model for SSD comparison endpoint."""
    cas_list: List[str]


@router.get("/summary")
def get_summary():
    df = load_data()

    # Exemple : retour d'un tableau de stats globales
    if df.empty:
        raise HTTPException(status_code=404, detail="Aucune donnée")

    # Exemple minimal : nombre de lignes et colonnes
    return {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "columns_names": list(df.columns),
    }


@router.get("/by_column")
def get_by_column(column: str):
    df = load_data()

    if column not in df.columns:
        raise HTTPException(status_code=400, detail="Colonne inconnue")

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


@router.get("/plot/ssd/{cas}")
def get_ssd_plot(cas: str):
    """
    Generate SSD (Species Sensitivity Distribution) and HC20 plot for a single chemical.
    
    Args:
        cas: CAS number of the chemical
        
    Returns:
        JSON representation of the Plotly figure
    """
    if plot_ssd_global is None:
        raise HTTPException(
            status_code=503, 
            detail="Plotting functions not available. Please check dependencies."
        )
    
    try:
        df_params = load_data_polars()
        fig = plot_ssd_global(df_params, cas)
        return fig.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating plot: {str(e)}")


@router.get("/plot/ec10eq/{cas}")
def get_ec10eq_plot(cas: str):
    """
    Generate EC10eq results plot organized by taxa and species.
    
    Args:
        cas: CAS number of the chemical
        
    Returns:
        JSON representation of the Plotly figure
    """
    if plot_ec10eq_by_taxa_and_species is None:
        raise HTTPException(
            status_code=503, 
            detail="Plotting functions not available. Please check dependencies."
        )
    
    try:
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
        request: Request body containing a list of CAS numbers (maximum 3)
        
    Returns:
        JSON representation of the Plotly figure
    """
    if plot_ssd_comparison is None:
        raise HTTPException(
            status_code=503, 
            detail="Plotting functions not available. Please check dependencies."
        )
    
    if len(request.cas_list) == 0:
        raise HTTPException(status_code=400, detail="At least one CAS number must be provided")
    
    if len(request.cas_list) > 3:
        raise HTTPException(
            status_code=400, 
            detail=f"Maximum 3 substances can be compared. Provided: {len(request.cas_list)}"
        )
    
    try:
        df_params = load_data_polars()
        fig = plot_ssd_comparison(df_params, request.cas_list)
        return fig.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating plot: {str(e)}")
