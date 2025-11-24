"""
API routes for OpenChemFacts Backend.

This module defines all the API endpoints including:
- Data access endpoints (summary, search, CAS list)
- Data endpoints (SSD data, EC10eq data, comparisons)

Note: This API returns only JSON data, not graphs or visualizations.
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List
from .data_loader import load_data, load_benchmark_data, DATA_PATH_ec10eq
import sys
from pathlib import Path
import pandas as pd

# Add data directory to path for importing data processing functions
data_dir = Path(__file__).resolve().parent.parent / "data"
sys.path.insert(0, str(data_dir.parent))

# ============================================================================
# Data processing function imports
# ============================================================================
# These functions are imported from separate modules to keep business logic
# separate from API routing logic.

# Cache for the EC10eq data function (lazy import with caching)
_ec10eq_get_data_func = None


def _get_ec10eq_data_function():
    """
    Import and cache the get_ec10eq_data_json function from api_ec10eq module.
    
    This function provides a clean separation between API routing (this file)
    and data processing logic (api_ec10eq.py module).
    
    Returns:
        Function get_ec10eq_data_json from api_ec10eq module
        
    Raises:
        ImportError: If the module cannot be imported
    """
    global _ec10eq_get_data_func
    
    if _ec10eq_get_data_func is not None:
        return _ec10eq_get_data_func
    
    # Import using importlib to handle spaces in directory name ("EC10 details")
    ec10eq_module_path = Path(__file__).resolve().parent.parent / "data" / "graph" / "EC10 details" / "api_ec10eq.py"
    
    if not ec10eq_module_path.exists():
        raise ImportError(f"EC10eq module not found at {ec10eq_module_path}")
    
    import importlib.util
    spec = importlib.util.spec_from_file_location("api_ec10eq", ec10eq_module_path)
    ec10eq_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ec10eq_module)
    
    _ec10eq_get_data_func = ec10eq_module.get_ec10eq_data_json
    return _ec10eq_get_data_func


# Cache for the SSD comparison data function (lazy import with caching)
_ssd_comparison_get_data_func = None


def _get_ssd_comparison_data_function():
    """
    Import and cache the get_ssd_comparison_data function from ssd_comparison_data module.
    
    This function provides a clean separation between API routing (this file)
    and data processing logic (ssd_comparison_data.py module).
    
    Returns:
        Function get_ssd_comparison_data from ssd_comparison_data module
        
    Raises:
        ImportError: If the module cannot be imported
    """
    global _ssd_comparison_get_data_func
    
    if _ssd_comparison_get_data_func is not None:
        return _ssd_comparison_get_data_func
    
    # Import using importlib to handle spaces in directory name ("SSD comparison")
    ssd_comparison_module_path = Path(__file__).resolve().parent.parent / "data" / "graph" / "SSD comparison" / "ssd_comparison_data.py"
    
    if not ssd_comparison_module_path.exists():
        raise ImportError(f"SSD comparison module not found at {ssd_comparison_module_path}")
    
    import importlib.util
    spec = importlib.util.spec_from_file_location("ssd_comparison_data", ssd_comparison_module_path)
    ssd_comparison_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ssd_comparison_module)
    
    _ssd_comparison_get_data_func = ssd_comparison_module.get_ssd_comparison_data
    return _ssd_comparison_get_data_func


# Créer le routeur API
# Toutes les routes définies ici seront préfixées par /api (défini dans main.py)
router = APIRouter()


# ============================================================================
# Helper functions for error handling and data validation
# ============================================================================

def validate_columns(dataframe: pd.DataFrame, required_columns: List[str], data_type: str = "data") -> None:
    """
    Validate that required columns exist in the dataframe.
    
    Args:
        dataframe: DataFrame to validate
        required_columns: List of required column names
        data_type: Type of data (for error messages), e.g., "benchmark data", "SSD data"
        
    Raises:
        HTTPException: If any required columns are missing
    """
    missing_columns = [col for col in required_columns if col not in dataframe.columns]
    if missing_columns:
        raise HTTPException(
            status_code=500,
            detail=f"Missing required columns in {data_type}: {', '.join(missing_columns)}"
        )


def handle_data_errors(
    error: Exception,
    context: str = "data",
    cas: str = None,
    query: str = None
) -> HTTPException:
    """
    Handle common data-related errors and return appropriate HTTPException.
    
    Args:
        error: The exception that was raised
        context: Context description for error messages (e.g., "benchmark data", "SSD data")
        cas: Optional CAS number for context-specific error messages
        query: Optional query string for search-related errors
        
    Returns:
        HTTPException with appropriate status code and detail message
    """
    if isinstance(error, HTTPException):
        return error
    
    if isinstance(error, FileNotFoundError):
        detail = f"{context.capitalize()} file not found: {str(error)}"
        return HTTPException(status_code=500, detail=detail)
    
    if isinstance(error, KeyError):
        if cas:
            detail = f"Missing required column in {context} for CAS '{cas}': {str(error)}"
        else:
            detail = f"Missing required column in {context}: {str(error)}"
        return HTTPException(status_code=500, detail=detail)
    
    if isinstance(error, ValueError):
        if cas:
            detail = f"{context.capitalize()} not found for CAS '{cas}': {str(error)}"
        elif query:
            detail = f"Error searching for query '{query}': {str(error)}"
        else:
            detail = f"Error in {context}: {str(error)}"
        return HTTPException(status_code=404, detail=detail)
    
    if isinstance(error, ImportError):
        detail = f"Failed to import {context} processing module: {str(error)}"
        return HTTPException(status_code=500, detail=detail)
    
    # Generic error
    if cas:
        detail = f"Error retrieving {context} for CAS '{cas}': {str(error)}"
    elif query:
        detail = f"Error searching for query '{query}': {str(error)}"
    else:
        detail = f"Error retrieving {context}: {str(error)}"
    return HTTPException(status_code=500, detail=detail)


def load_and_validate_benchmark_data(required_columns: List[str]) -> pd.DataFrame:
    """
    Load benchmark data and validate required columns.
    
    Args:
        required_columns: List of required column names
        
    Returns:
        DataFrame with benchmark data
        
    Raises:
        HTTPException: If data cannot be loaded or columns are missing
    """
    try:
        df = load_benchmark_data()
        validate_columns(df, required_columns, "benchmark data")
        return df
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Benchmark data file not found: {str(e)}"
        )
    except Exception as e:
        raise handle_data_errors(e, "benchmark data")


def load_and_validate_ssd_data(required_columns: List[str] = None) -> pd.DataFrame:
    """
    Load SSD data and optionally validate required columns.
    
    Args:
        required_columns: Optional list of required column names
        
    Returns:
        DataFrame with SSD data
        
    Raises:
        HTTPException: If data cannot be loaded or columns are missing
    """
    try:
        df = load_data()
        if required_columns:
            validate_columns(df, required_columns, "SSD data")
        return df
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=500,
            detail=f"SSD data file not found: {str(e)}"
        )
    except Exception as e:
        raise handle_data_errors(e, "SSD data")


class ComparisonRequest(BaseModel):
    """
    Request model for SSD comparison endpoint.
    
    Attributes:
        cas_list: List of CAS numbers or chemical names to compare (between 2 and 5)
    """
    cas_list: List[str]


def resolve_cas_from_identifier(identifier: str, dataframe: pd.DataFrame = None) -> str:
    """
    Resolve a CAS number or chemical name to a CAS number.
    
    Args:
        identifier: CAS number or chemical name (case-insensitive, partial match supported)
        dataframe: Optional DataFrame to use (if None, loads data)
        
    Returns:
        CAS number as string
        
    Raises:
        ValueError: If no matching substance is found or multiple matches found
    """
    df = dataframe if dataframe is not None else load_data()
    identifier_clean = identifier.strip()
    
    # Try exact CAS match
    cas_exact = df[df["cas_number"] == identifier_clean]
    if not cas_exact.empty:
        return identifier_clean
    
    # Try exact name match (case-insensitive)
    name_exact = df[df["chemical_name"].str.lower() == identifier_clean.lower()]
    if not name_exact.empty:
        cas_numbers = name_exact["cas_number"].unique()
        if len(cas_numbers) == 1:
            return str(cas_numbers[0])
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
    try:
        df = load_and_validate_benchmark_data(["cas_number", "Source"])
        
        return {
            "chemicals": int(df["cas_number"].nunique()),
            "EF_openchemfacts(calculated)": int((df["Source"] == "OpenChemFacts 0.1").sum()),
            "EF_usetox(official)": int((df["Source"] == "USETOX 2.14").sum()),
            "EF_ef3.1(official)": int((df["Source"] == "EF 3.1").sum()),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise handle_data_errors(e, "summary data")

@router.get("/list")
def get_list():
    """
    Get list of all available chemicals in the database.

    Returns:
        JSON array of dictionaries, each containing:\n
        - cas_number: CAS number
        - INCHIKEY: INCHIKEY identifier
        - name: Chemical name
    """
    try:
        df = load_and_validate_benchmark_data(["cas_number", "INCHIKEY", "name"])
        
        cas_data = df[["cas_number", "INCHIKEY", "name"]].drop_duplicates(subset=["cas_number", "INCHIKEY"])
        
        return [
            {"cas_number": str(row["cas_number"]), "INCHIKEY": str(row["INCHIKEY"]), "name": str(row["name"])}
            for _, row in cas_data.iterrows()
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise handle_data_errors(e, "chemical list")

@router.get("/cas/{cas}")
def get_cas_data(cas: str):
    """
    Compile available effect factors (EF) for a specific chemical.

    Args:
        cas: CAS number of the substance
        
    Returns:
        JSON object containing:\n
        - cas_number: CAS number of the substance
        - name: Chemical name
        - INCHIKEY: INCHIKEY of the chemical
        - Kingdom: Classyfire classification kingdom
        - Superclass: Classyfire classification superclass
        - Class: Classyfire classification class
        - EffectFactor(s): List of dictionaries with Source and EF
    """
    try:
        df_benchmark = load_and_validate_benchmark_data(["cas_number", "name", "INCHIKEY", "Kingdom", "Superclass", "Class", "Source", "EF"])
        substance_data = df_benchmark[df_benchmark["cas_number"] == cas]
        
        if substance_data.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Substance with CAS number '{cas}' not found in benchmark data. Please verify the CAS number is correct."
            )
        
        # Get first entry and required fields
        required_fields = ["cas_number", "name", "INCHIKEY", "Kingdom", "Superclass", "Class"]
        selected_data = substance_data[required_fields].iloc[0]
        
        # Convert to dict, handling NaN values for JSON serialization
        data_record = {
            field: None if pd.isna(selected_data[field]) else selected_data[field]
            for field in required_fields
        }
        
        # Build EffectFactor(s) list
        effect_factors = []
        for _, row in substance_data.iterrows():
            try:
                effect_factors.append({
                    "Source": str(row["Source"]),
                    "EF": None if pd.isna(row["EF"]) else float(row["EF"])
                })
            except (ValueError, TypeError) as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error processing effect factor data for CAS '{cas}': {str(e)}"
                )
        
        data_record["EffectFactor(s)"] = effect_factors
        return data_record
    except HTTPException:
        raise
    except Exception as e:
        raise handle_data_errors(e, "benchmark data", cas=cas)


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
        JSON object containing:\n
        - query: Original search query
        - count: Number of matches found
        - matches: List of matching substances, each with:
          - cas: CAS number
          - name: Chemical name
    """
    try:
        df = load_and_validate_ssd_data(["cas_number", "chemical_name"])
        
        query_clean = query.strip()
        
        if not query_clean:
            raise HTTPException(
                status_code=400,
                detail="Search query cannot be empty"
            )
        
        # Helper function to format results
        def format_matches(results_df):
            results = results_df[["cas_number", "chemical_name"]].drop_duplicates()
            matches = [
                {"cas": str(row["cas_number"]), "name": str(row["chemical_name"])}
                for _, row in results.iterrows()
            ]
            return {
                "query": query,
                "count": len(matches),
                "matches": matches[:limit],
            }
        
        # Try exact CAS match first
        cas_exact = df[df["cas_number"] == query_clean]
        if not cas_exact.empty:
            return format_matches(cas_exact)
        
        # Try exact name match (case-insensitive)
        name_exact = df[df["chemical_name"].str.lower() == query_clean.lower()]
        if not name_exact.empty:
            return format_matches(name_exact)
        
        # Try partial name match (case-insensitive)
        name_partial = df[df["chemical_name"].str.lower().str.contains(query_clean.lower(), na=False)]
        if not name_partial.empty:
            return format_matches(name_partial)
        
        # Try partial CAS match
        cas_partial = df[df["cas_number"].str.contains(query_clean, na=False)]
        if not cas_partial.empty:
            return format_matches(cas_partial)
        
        # No matches found
        return {
            "query": query,
            "count": 0,
            "matches": [],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise handle_data_errors(e, "search", query=query)


@router.get("/plot/ssd/{cas}")
def get_ssd_plot(cas: str):
    """
    Get SSD (Species Sensitivity Distribution) data for a single chemical in JSON format.
    
    Args:
        cas: CAS number (e.g., "107-05-1")
        
    Returns:
        JSON object containing detailed data to generate SSD curve:\n
        - cas_number: CAS number
        - chemical_name: Chemical name
        - ssd_parameters: SSD parameters (mu, sigma, HC20)
        - summary: Summary statistics (n_species, n_ecotox_group)
        - species_data: List of species data
        - ssd_curve: SSD curve points (concentrations and affected species percentages)
    """
    try:
        df = load_and_validate_ssd_data()
        
        # Import and use the function from plot_ssd_curve
        from data.graph.SSD.plot_ssd_curve import get_ssd_data
        
        # Get SSD data (get_ssd_data handles CAS validation internally)
        ssd_data = get_ssd_data(df, cas)
        
        return ssd_data
    except HTTPException:
        raise
    except Exception as e:
        error = handle_data_errors(e, "SSD data", cas=cas)
        # Add additional context for KeyError in SSD data
        if isinstance(e, KeyError):
            error.detail += ". Please check the data structure."
        raise error


@router.get("/plot/ec10eq/{cas}")
def get_ec10eq_plot(cas: str):
    """
    List all calculated EC10eq results per species and trophic group in JSON format.

    Args:
        cas: CAS number (e.g., "60-51-5")
        
    Returns:
        JSON object containing EC10eq data organized by trophic group and species:\n
        - cas: CAS number
        - chemical_name: Chemical name
        - trophic_groups: Nested structure by trophic_group -> species -> endpoints
          Each endpoint contains EC10eq, test_id, year, and author
    """ 
    try:
        # Import data processing function (cached after first call)
        get_ec10eq_data = _get_ec10eq_data_function()
        
        # Call data processing function with API configuration
        return get_ec10eq_data(
            cas_number=cas,
            data_path=str(DATA_PATH_ec10eq),
            output_format="detailed"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise handle_data_errors(e, "EC10eq data", cas=cas)


@router.post("/plot/ssd/comparison")
def get_ssd_comparison(request: ComparisonRequest):
    """
    Get SSD (Species Sensitivity Distribution) data for multiple chemicals in JSON format.
    
    This endpoint delegates data processing to the ssd_comparison_data module,
    keeping API routing separate from business logic.
    
    Uses the same logic as /plot/ssd/{cas} but for multiple chemicals (2 to 5).
    
    Args:
        request: Request body containing:
                - cas_list: List of CAS numbers or chemical names (between 2 and 5)
                Each identifier can be a CAS number or chemical name (case-insensitive, partial match supported)
        
    Returns:
        JSON object containing SSD data for all chemicals.
    """
    # API-level validation
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
    
    try:
        df = load_and_validate_ssd_data()
        
        # Resolve all identifiers to CAS numbers (API-level logic)
        # Pass dataframe to avoid reloading data for each identifier
        resolved_cas_list = []
        invalid_identifiers = []
        
        for identifier in request.cas_list:
            try:
                resolved_cas = resolve_cas_from_identifier(identifier, dataframe=df)
                resolved_cas_list.append(resolved_cas)
            except ValueError as e:
                invalid_identifiers.append(f"'{identifier}': {str(e)}")
        
        if invalid_identifiers:
            raise HTTPException(
                status_code=404,
                detail=f"Invalid or not found identifiers: {', '.join(invalid_identifiers)}"
            )
        
        # Import data processing function (cached after first call)
        get_ssd_comparison_data = _get_ssd_comparison_data_function()
        
        # Call data processing function
        return get_ssd_comparison_data(
            dataframe=df,
            cas_list=resolved_cas_list
        )
    except HTTPException:
        raise
    except Exception as e:
        raise handle_data_errors(e, "SSD comparison data")