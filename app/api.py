"""
API routes for OpenChemFacts Backend.

This module defines all the API endpoints including:
- Data access endpoints (summary, search, CAS list)
- Data endpoints (SSD data, EC10eq data, comparisons)

Note: This API returns only JSON data, not graphs or visualizations.
"""
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel
from typing import List
from .data_loader import load_data, load_benchmark_data, DATA_PATH_ec10eq
from .security import apply_rate_limit
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
    import os
    import logging
    
    logger = logging.getLogger(__name__)
    is_production = os.getenv("ENVIRONMENT", "development").lower() == "production"
    
    missing_columns = [col for col in required_columns if col not in dataframe.columns]
    if missing_columns:
        # Log detailed error server-side
        logger.error(f"Missing required columns in {data_type}: {', '.join(missing_columns)}")
        
        # Return sanitized error message
        if is_production:
            detail = "Data structure error. Please contact support."
        else:
            detail = f"Missing required columns in {data_type}: {', '.join(missing_columns)}"
        
        raise HTTPException(status_code=500, detail=detail)


def handle_data_errors(
    error: Exception,
    context: str = "data",
    cas: str = None,
    query: str = None
) -> HTTPException:
    """
    Handle common data-related errors and return appropriate HTTPException.
    
    Sanitizes error messages to avoid information disclosure in production.
    Detailed errors are logged server-side only.
    
    Args:
        error: The exception that was raised
        context: Context description for error messages (e.g., "benchmark data", "SSD data")
        cas: Optional CAS number for context-specific error messages
        query: Optional query string for search-related errors
        
    Returns:
        HTTPException with appropriate status code and sanitized detail message
    """
    import logging
    import os
    
    logger = logging.getLogger(__name__)
    is_production = os.getenv("ENVIRONMENT", "development").lower() == "production"
    
    # Log detailed error server-side
    logger.error(
        f"Error in {context}: {type(error).__name__}: {str(error)}"
        + (f" (CAS: {cas})" if cas else "")
        + (f" (Query: {query})" if query else ""),
        exc_info=True
    )
    
    if isinstance(error, HTTPException):
        # If it's already an HTTPException, sanitize the detail if in production
        if is_production and error.status_code >= 500:
            return HTTPException(
                status_code=error.status_code,
                detail="An internal server error occurred. Please try again later."
            )
        return error
    
    if isinstance(error, FileNotFoundError):
        # Don't expose file paths in production
        if is_production:
            detail = "Data file not available. Please contact support."
        else:
            detail = f"{context.capitalize()} file not found: {str(error)}"
        return HTTPException(status_code=500, detail=detail)
    
    if isinstance(error, KeyError):
        # Don't expose internal column names in production
        if is_production:
            detail = "Data structure error. Please contact support."
        else:
            if cas:
                detail = f"Missing required column in {context} for CAS '{cas}': {str(error)}"
            else:
                detail = f"Missing required column in {context}: {str(error)}"
        return HTTPException(status_code=500, detail=detail)
    
    if isinstance(error, ValueError):
        # User-facing errors can be more specific
        if cas:
            detail = f"Data not found for the specified identifier."
        elif query:
            detail = f"No results found for your search query."
        else:
            detail = f"Invalid request. Please check your parameters."
        return HTTPException(status_code=404, detail=detail)
    
    if isinstance(error, ImportError):
        # Don't expose import errors in production
        if is_production:
            detail = "Service temporarily unavailable. Please try again later."
        else:
            detail = f"Failed to import {context} processing module: {str(error)}"
        return HTTPException(status_code=500, detail=detail)
    
    # Generic error - sanitize in production
    if is_production:
        detail = "An error occurred while processing your request. Please try again later."
    else:
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
    
    def __init__(self, **data):
        super().__init__(**data)
        # Validate list size
        if len(self.cas_list) < 2:
            raise ValueError("At least 2 substances must be provided for comparison")
        if len(self.cas_list) > 5:
            raise ValueError("Maximum 5 substances can be compared")
        # Validate each identifier length
        for identifier in self.cas_list:
            if not isinstance(identifier, str) or len(identifier.strip()) == 0:
                raise ValueError("All identifiers must be non-empty strings")
            if len(identifier) > 200:  # Prevent extremely long strings
                raise ValueError("Identifier too long (max 200 characters)")


def validate_cas_number(cas: str) -> str:
    """
    Validate and sanitize CAS number input.
    
    Args:
        cas: CAS number string
        
    Returns:
        Sanitized CAS number
        
    Raises:
        HTTPException: If CAS number is invalid
    """
    if not cas or not isinstance(cas, str):
        raise HTTPException(
            status_code=400,
            detail="CAS number must be a non-empty string"
        )
    
    cas_clean = cas.strip()
    
    # Basic length validation
    if len(cas_clean) == 0:
        raise HTTPException(
            status_code=400,
            detail="CAS number cannot be empty"
        )
    
    if len(cas_clean) > 50:  # Prevent extremely long strings
        raise HTTPException(
            status_code=400,
            detail="CAS number is too long"
        )
    
    # Basic pattern validation (CAS numbers typically have format: NNNNN-NN-N)
    # But we allow more flexibility for partial matches
    # Just check for potentially dangerous characters
    if any(char in cas_clean for char in ['<', '>', '"', "'", '&', '\x00']):
        raise HTTPException(
            status_code=400,
            detail="Invalid characters in CAS number"
        )
    
    return cas_clean


def validate_search_query(query: str) -> str:
    """
    Validate and sanitize search query input.
    
    Args:
        query: Search query string
        
    Returns:
        Sanitized query string
        
    Raises:
        HTTPException: If query is invalid
    """
    if not query or not isinstance(query, str):
        raise HTTPException(
            status_code=400,
            detail="Search query must be a non-empty string"
        )
    
    query_clean = query.strip()
    
    if len(query_clean) == 0:
        raise HTTPException(
            status_code=400,
            detail="Search query cannot be empty"
        )
    
    if len(query_clean) > 200:  # Prevent extremely long queries
        raise HTTPException(
            status_code=400,
            detail="Search query is too long (max 200 characters)"
        )
    
    # Check for potentially dangerous characters
    if any(char in query_clean for char in ['<', '>', '"', "'", '&', '\x00']):
        raise HTTPException(
            status_code=400,
            detail="Invalid characters in search query"
        )
    
    return query_clean


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
@apply_rate_limit("60/minute")
def get_summary(request: Request):
    """
    Number of chemicals and endpoints available on the platform.
    
    Returns a dictionary containing:\n
            - chemicals: Total number of CAS with a calculated effect factor (EF)
            - EF_openchemfacts(calculated): Total number of EF calculated by OpenChemFacts
            - EF_usetox(official): Total number of EF officially provided by USEtox
            - EF_ef(official): Total number of EF officially provided by European Footprint method (JRC team)
    """
    try:
        df = load_and_validate_benchmark_data(["cas_number", "Source"])
        
        return {
            "chemicals": int(df["cas_number"].nunique()),
            "EF_openchemfacts(calculated)": int((df["Source"] == "OpenChemFacts").sum()),
            "EF_usetox(official)": int((df["Source"] == "USEtox").sum()),
            "EF_ef(official)": int((df["Source"] == "EF").sum()),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise handle_data_errors(e, "summary data")


@router.get("/metadata")
@apply_rate_limit("60/minute")
def get_metadata(request: Request):
    """
    Get contextual information about parameters and modules displayed in the frontend.
    
    This endpoint provides definitions, units, and other contextual information
    for various parameters used throughout the application. The metadata is
    organized by category and can be easily extended with additional information.
    
    Returns:
        JSON object containing metadata grouped by category:\n
        - HC20: Unit + Definition + Why
        - EC10eq: Unit + Definition + Why
        - SSD: Definition + Summary + Why
        - EF: Unit + Formula + Summary + Details
    """
    return {
        "HC20": {
            "unit": "mg/L",
            "definition": "HC20 represents the environmental concentration affecting 20% of species.",
            "why": "HC20 is used to calculate the Effect Factor (EF) of any chemical by taking the slope on the SSD at the HC20.",
        },
        "EC10eq": {
            "unit": "mg/L",
            "definition": "EC10eq values represent the concentration affecting 10% of a specific species based on relevant endpoints (e.g. LC50, EC50, etc.). They are used to construct the SSD.",
            "why": "EC10eq values are used to construct the SSD of a chemical. These values are based on toxicological tests conducted on specific species.",
        },
        "SSD": {
            "definition": "Species Sensitivity Distribution",
            "summary": "SSD is constructed by fitting a log-normal distribution to chronic EC10eq toxicity endpoints from multiple species, showing the range of concentrations at which they are affected.",
            "why": "SSD is used to calculate the Effect Factor (EF) of any chemical by taking the slope on the SSD at the HC20.",
        },
        "EF": {
            "unit": "PAF·m³/kg",
            "formula": "EF = O,2 / HC20",
            "summary": "EF is the HC20 concentration-response slope factor expressed in PAF·m³·kg⁻¹.",
            "details": "The Effect Factor represents the increase in the potentially affected fraction of species (PAF) per unit increase in chemical concentration, based on a concentration–response relationship.",
        }
    }


@router.get("/cas/{cas}")
@apply_rate_limit("60/minute")
def get_cas_data(cas: str, request: Request):
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
        - EffectFactor(s): List of dictionaries with Source, Version and EF
    """
    # Validate CAS number input
    cas = validate_cas_number(cas)
    try:
        # Load benchmark data - Version is required
        df_benchmark = load_and_validate_benchmark_data(["cas_number", "name", "INCHIKEY", "Kingdom", "Superclass", "Class", "Source", "Version", "EF"])
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
                    "Version": None if pd.isna(row["Version"]) else str(row["Version"]),
                    "EF": None if pd.isna(row["EF"]) else float(row["EF"])
                })
            except (ValueError, TypeError, KeyError) as e:
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
@apply_rate_limit("60/minute")
def search_substances(
    request: Request,
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
        # Validate and sanitize query
        query_clean = validate_search_query(query)
        
        df = load_and_validate_ssd_data(["cas_number", "chemical_name"])
        
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
@apply_rate_limit("10/minute")
def get_ssd_plot(cas: str, request: Request):
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
    # Validate CAS number input
    cas = validate_cas_number(cas)
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
@apply_rate_limit("10/minute")
def get_ec10eq_plot(cas: str, request: Request):
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
    # Validate CAS number input
    cas = validate_cas_number(cas) 
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
@apply_rate_limit("10/minute")
def get_ssd_comparison(request_body: ComparisonRequest, request: Request):
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
    if len(request_body.cas_list) < 2:
        raise HTTPException(
            status_code=400, 
            detail=f"At least 2 substances must be provided for comparison. Provided: {len(request_body.cas_list)}"
        )
    
    if len(request_body.cas_list) > 5:
        raise HTTPException(
            status_code=400, 
            detail=f"Maximum 5 substances can be compared. Provided: {len(request_body.cas_list)}"
        )
    
    try:
        df = load_and_validate_ssd_data()
        
        # Resolve all identifiers to CAS numbers (API-level logic)
        # Pass dataframe to avoid reloading data for each identifier
        resolved_cas_list = []
        invalid_identifiers = []
        
        for identifier in request_body.cas_list:
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