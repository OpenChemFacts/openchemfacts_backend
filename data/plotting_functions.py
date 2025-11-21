"""
Optimized visualization functions for ecotox data
Compatible with Streamlit frontend

All plotting functions use a centralized configuration class for easy customization.
"""

import numpy as np
import polars as pl
from scipy.stats import norm
import plotly.graph_objects as go
# plotly.express and make_subplots are kept for future use when plot_ec10eq_by_taxa_and_species is reimplemented
# from plotly.express import px
# from plotly.subplots import make_subplots
from typing import Dict, List, Tuple
from dataclasses import dataclass


# ============================================================================
# Centralized Configuration Class
# ============================================================================

@dataclass
class PlotConfig:
    """Centralized configuration for all visualization plots."""
    
    # Plot parameters
    n_points: int = 400
    sigma_margin: float = 2.0
    hc20_percentile: float = 0.20
    
    # Axis padding
    pad_log: float = 0.5
    extra_hc20_pad: float = 0.2
    
    # Visual styling
    ssd_line_width: int = 4
    ssd_line_color: str = "black"
    marker_size: int = 9
    hc20_line_color: str = "rgba(255,0,0,0.30)"
    hc20_line_width: float = 1.5
    hc20_annotation_y: float = 0.93
    hc20_font_size: int = 12
    
    # Template
    template: str = "plotly_white"
    
    # Taxonomic group symbols
    taxa_symbols: Dict[str, str] = None
    
    # Comparison plot colors (max 3 substances)
    comparison_colors: List[str] = None
    
    # Species color palette
    species_palette_multiplier: int = 10
    
    # Plot dimensions (fixed for web UI consistency)
    plot_width: int = 1000
    plot_height: int = 600
    
    # Margins (in pixels) - optimized for multi-line titles
    margin_top: int = 120  # Extra space for multi-line titles
    margin_bottom: int = 80  # Space for x-axis labels and legend if needed
    margin_left: int = 80  # Space for y-axis labels
    margin_right: int = 60  # Space for annotations
    
    def __post_init__(self):
        """Initialize default values for dictionaries/lists."""
        if self.taxa_symbols is None:
            self.taxa_symbols = {
                "algae": "circle",
                "crustaceans": "square",
                "fish": "triangle-up",
                "plants": "diamond",
                "molluscs": "diamond",
                "insects": "hash",
                "amphibians": "star",
                "annelids": "hourglass",
            }
        
        if self.comparison_colors is None:
            self.comparison_colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]  # Blue, Orange, Green


# Global configuration instance
PLOT_CONFIG = PlotConfig()


# ============================================================================
# Shared Helper Functions
# ============================================================================

def get_config(config: PlotConfig = None) -> PlotConfig:
    """
    Get plot configuration, using default if None provided.
    
    Args:
        config: Optional plot configuration
        
    Returns:
        PlotConfig instance
    """
    return config if config is not None else PLOT_CONFIG


def extract_values_list(sub: pl.DataFrame) -> List[float]:
    """
    Safely extract the values list from a Polars DataFrame.
    
    Args:
        sub: DataFrame with a 'values' column containing lists
        
    Returns:
        List of float values, or empty list if not available
    """
    if "values" not in sub.columns or sub.height == 0:
        return []
    
    values_series = sub["values"][0]
    if isinstance(values_series, pl.Series):
        return values_series.to_list()
    elif values_series is not None:
        return values_series if isinstance(values_series, list) else []
    else:
        return []


def get_valid_values(values_list: List[float]) -> np.ndarray:
    """
    Extract and filter valid (positive) values from a list.
    
    Args:
        values_list: List of float values
        
    Returns:
        NumPy array of valid (positive) values
    """
    if len(values_list) == 0:
        return np.array([])
    
    values_array = np.array(values_list)
    return values_array[values_array > 0]


def calculate_data_range(
    sub: pl.DataFrame,
    mu_ssd: float,
    sigma_ssd: float,
    config: PlotConfig = None,
) -> Tuple[float, float]:
    """
    Calculate data range (min, max) from actual values or SSD parameters.
    
    Args:
        sub: Filtered dataframe (aggregated at CAS level)
        mu_ssd: SSD mean parameter
        sigma_ssd: SSD sigma parameter
        config: Plot configuration (uses PLOT_CONFIG if None)
        
    Returns:
        Tuple of (min_value, max_value) in real units (mg/L)
    """
    config = get_config(config)
    values_list = extract_values_list(sub)
    valid_values = get_valid_values(values_list)
    
    if len(valid_values) > 0:
        return float(valid_values.min()), float(valid_values.max())
    else:
        # Fallback to SSD-based range
        return (
            10 ** (mu_ssd - 3 * sigma_ssd),
            10 ** (mu_ssd + 3 * sigma_ssd)
        )


def filter_and_validate_data(df_params: pl.DataFrame, cas: str) -> Tuple[pl.DataFrame, str]:
    """
    Filter data for the requested CAS and validate SSD parameters.
    
    Args:
        df_params: DataFrame with SSD parameters (aggregated at CAS level)
        cas: CAS number to filter
        
    Returns:
        Tuple of (filtered_dataframe, chemical_name)
        
    Raises:
        ValueError: If CAS not found or no valid data
    """
    sub = df_params.filter(pl.col("cas_number") == cas)
    if sub.height == 0:
        raise ValueError(f"CAS {cas} not found in dataframe.")
    
    chem_name = sub["chemical_name"][0] if "chemical_name" in sub.columns else cas

    # Validate SSD parameters (new structure: SSD_mu_logEC10eq and SSD_sigma_logEC10eq)
    sub = sub.filter(
        pl.col("SSD_mu_logEC10eq").is_finite() & pl.col("SSD_mu_logEC10eq").is_not_null()
        & pl.col("SSD_sigma_logEC10eq").is_finite() & (pl.col("SSD_sigma_logEC10eq") >= 0)
    )
    if sub.height == 0:
        raise ValueError(f"No valid SSD parameters found for CAS {cas}.")
    
    return sub, chem_name


def calculate_ssd_parameters(sub: pl.DataFrame) -> Tuple[float, float]:
    """
    Extract SSD parameters from aggregated data.
    
    Args:
        sub: Filtered dataframe with SSD_mu_logEC10eq and SSD_sigma_logEC10eq
        
    Returns:
        Tuple of (mu_ssd, sigma_ssd)
    """
    mu_ssd = float(sub["SSD_mu_logEC10eq"][0])
    sigma_ssd = float(sub["SSD_sigma_logEC10eq"][0])
    
    # Si sigma est 0 ou négatif, utiliser une valeur minimale
    if sigma_ssd <= 0:
        sigma_ssd = 0.01  # Valeur minimale pour éviter les erreurs
    
    if not (np.isfinite(mu_ssd) and np.isfinite(sigma_ssd) and sigma_ssd > 0):
        raise ValueError(f"Invalid SSD parameters: mu={mu_ssd}, sigma={sigma_ssd}")
    return mu_ssd, sigma_ssd


def calculate_ssd_curve(
    sub: pl.DataFrame,
    mu_ssd: float,
    sigma_ssd: float,
    config: PlotConfig = None,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Calculate the SSD curve (CDF) in log10-space and real units.
    
    Args:
        sub: Filtered dataframe (aggregated at CAS level)
        mu_ssd: SSD mean parameter
        sigma_ssd: SSD sigma parameter
        config: Plot configuration (uses PLOT_CONFIG if None)
        
    Returns:
        Tuple of (x_log, x_real, cdf_global)
    """
    config = get_config(config)
    
    # For aggregated data, use a range around mu_ssd
    # Use values from the 'values' column if available to determine range
    values_list = extract_values_list(sub)
    valid_values = get_valid_values(values_list)
    
    if len(valid_values) > 0:
        # Use actual EC10eq values to determine range
        log_values = np.log10(valid_values)
        mu_min, mu_max = float(log_values.min()), float(log_values.max())
        mu_range = max(mu_max - mu_min, 1.0)
    else:
        # Fallback: use range around mu_ssd
        mu_range = max(3.0 * sigma_ssd, 1.0)
        mu_min = mu_ssd - config.sigma_margin * mu_range
        mu_max = mu_ssd + config.sigma_margin * mu_range
    
    x_log = np.linspace(
        mu_min - config.sigma_margin * mu_range,
        mu_max + config.sigma_margin * mu_range,
        config.n_points
    )
    x_real = 10 ** x_log
    cdf_global = 100 * norm.cdf(x_log, loc=mu_ssd, scale=sigma_ssd)
    return x_log, x_real, cdf_global


def calculate_hc20(sub: pl.DataFrame, mu_ssd: float, sigma_ssd: float, config: PlotConfig = None) -> float:
    """
    Get or calculate HC20 value from SSD parameters.
    
    Args:
        sub: Filtered dataframe (may contain pre-calculated HC20)
        mu_ssd: SSD mean parameter
        sigma_ssd: SSD sigma parameter
        config: Plot configuration (uses PLOT_CONFIG if None)
        
    Returns:
        HC20 value in real units (mg/L)
    """
    config = get_config(config)
    
    # Try to use pre-calculated HC20 if available
    if "HC20" in sub.columns:
        hc20_val = sub["HC20"][0]
        if hc20_val is not None and np.isfinite(hc20_val) and hc20_val > 0:
            return float(hc20_val)
    
    # Otherwise calculate from SSD parameters
    hc20 = 10 ** (mu_ssd + sigma_ssd * norm.ppf(config.hc20_percentile))
    if not (np.isfinite(hc20) and hc20 > 0):
        raise ValueError(f"Invalid HC20 value: {hc20}")
    return hc20


def calculate_x_axis_range(
    sub: pl.DataFrame,
    hc20: float,
    mu_ssd: float,
    sigma_ssd: float,
    config: PlotConfig = None,
) -> Tuple[float, float]:
    """
    Compute an adaptive x-axis range based on EC10eq values or SSD parameters,
    then extend just enough to include HC20.
    
    Args:
        sub: Filtered dataframe (aggregated at CAS level)
        hc20: HC20 value
        mu_ssd: SSD mean parameter
        sigma_ssd: SSD sigma parameter
        config: Plot configuration (uses PLOT_CONFIG if None)
        
    Returns:
        Tuple of (x_plot_min, x_plot_max) in mg/L
    """
    config = get_config(config)
    
    # Try to use actual EC10eq values from 'values' column
    x_min_data, x_max_data = calculate_data_range(sub, mu_ssd, sigma_ssd, config)

    log_min = np.log10(x_min_data)
    log_max = np.log10(x_max_data)

    log_min -= config.pad_log
    log_max += config.pad_log

    log_hc20 = np.log10(hc20)
    if log_hc20 < log_min:
        log_min = log_hc20 - config.extra_hc20_pad
    if log_hc20 > log_max:
        log_max = log_hc20 + config.extra_hc20_pad

    x_plot_min = max(10 ** log_min, 1e-9)
    x_plot_max = 10 ** log_max

    return x_plot_min, x_plot_max


def calculate_global_x_axis_range(
    all_subs: List[pl.DataFrame],
    all_hc20s: List[float],
    all_mu_ssds: List[float],
    all_sigma_ssds: List[float],
    config: PlotConfig = None,
) -> Tuple[float, float]:
    """
    Compute a global x-axis range that encompasses all substances.
    
    Args:
        all_subs: List of filtered dataframes (one per CAS, aggregated)
        all_hc20s: List of HC20 values (one per CAS)
        all_mu_ssds: List of SSD mu parameters (one per CAS)
        all_sigma_ssds: List of SSD sigma parameters (one per CAS)
        config: Plot configuration (uses PLOT_CONFIG if None)
    
    Returns:
        Tuple of (x_plot_min, x_plot_max) in mg/L
    """
    config = get_config(config)
        
    all_mins = []
    all_maxs = []
    
    for sub, mu_ssd, sigma_ssd in zip(all_subs, all_mu_ssds, all_sigma_ssds):
        # Use shared function to calculate data range
        x_min, x_max = calculate_data_range(sub, mu_ssd, sigma_ssd, config)
        all_mins.append(x_min)
        all_maxs.append(x_max)
    
    x_min_data = min(all_mins)
    x_max_data = max(all_maxs)
    
    log_min = np.log10(x_min_data)
    log_max = np.log10(x_max_data)
    
    log_min -= config.pad_log
    log_max += config.pad_log
    
    for hc20 in all_hc20s:
        log_hc20 = np.log10(hc20)
        if log_hc20 < log_min:
            log_min = log_hc20 - config.extra_hc20_pad
        if log_hc20 > log_max:
            log_max = log_hc20 + config.extra_hc20_pad
    
    x_plot_min = max(10 ** log_min, 1e-9)
    x_plot_max = 10 ** log_max
    
    return x_plot_min, x_plot_max


def generate_log_ticks(x_min: float, x_max: float) -> Tuple[List[float], List[str]]:
    """
    Generate tick values and labels for log scale axis.
    
    Args:
        x_min: Minimum value
        x_max: Maximum value
        
    Returns:
        Tuple of (tickvals, ticktext)
    """
    log_min = np.floor(np.log10(x_min))
    log_max = np.ceil(np.log10(x_max))
    exponents = range(int(log_min), int(log_max) + 1)
    tickvals = [10 ** k for k in exponents]
    ticktext = [f"{v:g}" for v in tickvals]
    return tickvals, ticktext


def get_base_layout_config(config: PlotConfig) -> dict:
    """
    Get base layout configuration (dimensions and margins).
    
    Args:
        config: Plot configuration
        
    Returns:
        Dictionary with width, height, and margin settings
    """
    return {
        "width": config.plot_width,
        "height": config.plot_height,
        "autosize": False,  # Use exact dimensions, don't auto-resize
        "margin": dict(
            t=config.margin_top,
            b=config.margin_bottom,
            l=config.margin_left,
            r=config.margin_right,
        ),
    }


def get_log_xaxis_config(
    x_plot_min: float,
    x_plot_max: float,
    tickvals: List[float] = None,
    ticktext: List[str] = None,
) -> dict:
    """
    Get log-scale x-axis configuration.
    
    Args:
        x_plot_min: Minimum x value
        x_plot_max: Maximum x value
        tickvals: Optional tick values (auto-generated if None)
        ticktext: Optional tick labels (auto-generated if None)
        
    Returns:
        Dictionary with x-axis configuration
    """
    if tickvals is None or ticktext is None:
        tickvals, ticktext = generate_log_ticks(x_plot_min, x_plot_max)
    
    return {
        "type": "log",
        "range": [np.log10(x_plot_min), np.log10(x_plot_max)],
        "tickmode": "array",
        "tickvals": tickvals,
        "ticktext": ticktext,
        "showgrid": True,
        "ticks": "outside",
    }


# ============================================================================
# Graph 1: SSD and HC20 per Chemical
# ============================================================================

def add_ssd_trace(
    fig: go.Figure, 
    x_real: np.ndarray, 
    cdf_global: np.ndarray,
    config: PlotConfig = None,
) -> None:
    """Add the global SSD curve trace to the figure."""
    config = get_config(config)
        
    fig.add_trace(go.Scatter(
        x=x_real, 
        y=cdf_global, 
        mode="lines",
        line=dict(width=config.ssd_line_width, color=config.ssd_line_color),
        name="Average SSD",
        hovertemplate="Concentration: %{x:.2g} mg/L<br>% of species affected: %{y:.0f}%<extra></extra>",
    ))


def add_hc20_annotation(
    fig: go.Figure,
    hc20: float,
    x_plot_min: float,
    x_plot_max: float,
    config: PlotConfig = None,
) -> None:
    """Add HC20 lines and annotation to the figure."""
    config = get_config(config)

    fig.add_hline(
        y=config.hc20_percentile * 100,
        line_dash="dot",
        line_color=config.hc20_line_color,
        line_width=config.hc20_line_width
    )

    fig.add_vline(
        x=hc20,
        line_dash="dot",
        line_color=config.hc20_line_color,
        line_width=config.hc20_line_width
    )

    log_min = np.log10(x_plot_min)
    log_max = np.log10(x_plot_max)
    log_hc20 = np.log10(hc20)

    frac_x = (log_hc20 - log_min) / (log_max - log_min)
    frac_x = max(0.0, min(1.0, frac_x))

    fig.add_annotation(
        x=frac_x,
        y=config.hc20_annotation_y,
        xref="paper",
        yref="paper",
        text=f"<b>HC20 = {hc20:.2g} mg/L</b>",
        showarrow=False,
        font=dict(color="red", size=config.hc20_font_size),
        xanchor="right",
        yanchor="top",
        xshift=-4,
        yshift=-4,
    )


def add_species_points(
    fig: go.Figure, 
    sub: pl.DataFrame,
    config: PlotConfig = None,
) -> None:
    """
    Add species points to the figure.
    
    NOTE: With the new aggregated data structure, individual species data
    is no longer available. This function is kept for API compatibility
    but does not add any points (as per requirement 1A).
    """
    # With aggregated data structure, we don't have individual species data
    # so we don't add any points (requirement: remove species points)
    # Arguments are kept for API compatibility but unused
    _ = fig, sub, config


def plot_ssd_global(
    df_params: pl.DataFrame,
    cas: str,
    config: PlotConfig = None,
) -> go.Figure:
    """
    Generate SSD (Species Sensitivity Distribution) and HC20 plot for a single chemical.
    
    Args:
        df_params: DataFrame with aggregated SSD parameters (SSD_mu_logEC10eq, SSD_sigma_logEC10eq)
        cas: CAS number of the chemical
        config: Plot configuration (uses PLOT_CONFIG if None)
        
    Returns:
        go.Figure: Plotly figure ready for display (compatible with Streamlit)
        
    Raises:
        ValueError: If CAS not found or no valid data
    """
    config = get_config(config)

    sub, chem_name = filter_and_validate_data(df_params, cas)
    
    # Get aggregated statistics from new structure
    n_species = int(sub["n_species"][0]) if "n_species" in sub.columns else 0
    values_list = extract_values_list(sub)
    n_results = len(values_list)

    mu_ssd, sigma_ssd = calculate_ssd_parameters(sub)
    _, x_real, cdf_global = calculate_ssd_curve(sub, mu_ssd, sigma_ssd, config)
    hc20 = calculate_hc20(sub, mu_ssd, sigma_ssd, config)
    x_plot_min, x_plot_max = calculate_x_axis_range(sub, hc20, mu_ssd, sigma_ssd, config)
    
    tickvals, ticktext = generate_log_ticks(x_plot_min, x_plot_max)
    
    fig = go.Figure()
    
    add_ssd_trace(fig, x_real, cdf_global, config)
    # Note: add_species_points is called but does nothing with aggregated data (requirement 1A)
    add_species_points(fig, sub, config)
    add_hc20_annotation(fig, hc20, x_plot_min, x_plot_max, config)
    
    base_layout = get_base_layout_config(config)
    # Ensure legend doesn't overlap with plot area
    base_layout["margin"]["r"] = max(base_layout["margin"]["r"], 100)
    fig.update_layout(
        **base_layout,
        title=dict(
            text=(
                "<b>Species Sensitivity Distribution (SSD) and HC20</b><br>"
                f"<b>Chemical:</b> {chem_name} (CAS {cas})<br>"
                f"<b>Details:</b> {n_results} EC10eq result(s) / {n_species} species"
            ),
            x=0.5,
            xanchor="center",
        ),
        xaxis_title="Concentration (mg/L)",
        yaxis_title="Affected species (%)",
        yaxis=dict(range=[0, 100], ticksuffix=" %"),
        xaxis=get_log_xaxis_config(x_plot_min, x_plot_max, tickvals, ticktext),
        template=config.template,
        legend=dict(
            title="SSD",
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="right",
            x=1,
            xshift=-10,
            yshift=-10,
        ),
        hovermode="closest",
    )

    return fig


# ============================================================================
# Graph 2: EC10eq Results per Chemical
# ============================================================================

def plot_ec10eq_by_taxa_and_species(
    df_params: pl.DataFrame,
    cas: str,
    config: PlotConfig = None,
) -> go.Figure:
    """
    Generate EC10eq results plot organized by taxa (subplots) and species (x-axis).
    
    NOTE: This function is temporarily disabled due to data structure changes.
    The new aggregated data structure no longer contains individual species/taxa information.
    This function will be modified in a second phase to work with the new structure.
    
    Args:
        df_params: DataFrame with EC10eq values
        cas: CAS number of the chemical
        config: Plot configuration (uses PLOT_CONFIG if None)
        
    Returns:
        go.Figure: Plotly figure ready for display (compatible with Streamlit)
        
    Raises:
        ValueError: Always raised with explanation message
    """
    raise ValueError(
        "The EC10eq by taxa and species plot is temporarily disabled. "
        "The data structure has changed to an aggregated format that no longer "
        "contains individual species/taxa information. This function will be "
        "modified in a second phase to work with the new structure."
    )


# ============================================================================
# Graph 3: SSD Comparison
# ============================================================================

def add_ssd_trace_comparison(
    fig: go.Figure,
    x_real: np.ndarray,
    cdf_global: np.ndarray,
    chem_name: str,
    cas: str,
    color: str,
    config: PlotConfig = None,
) -> None:
    """Add an SSD curve trace to the comparison figure with a specific color."""
    config = get_config(config)
        
    fig.add_trace(go.Scatter(
        x=x_real, 
        y=cdf_global, 
        mode="lines",
        line=dict(width=3, color=color),
        name=f"{chem_name} (CAS {cas})",
        hovertemplate=(
            f"<b>{chem_name}</b> (CAS {cas})<br>"
            "Concentration: %{x:.2g} mg/L<br>"
            "% of species affected: %{y:.0f}%<extra></extra>"
        ),
    ))


def add_hc20_annotation_comparison(
    fig: go.Figure,
    hc20: float,
    chem_name: str,
    cas: str,  # kept for API compatibility but unused
    x_plot_min: float,
    x_plot_max: float,
    color: str,
    y_position: float,
    config: PlotConfig = None,
) -> None:
    """Add HC20 vertical line and annotation for comparison plot."""
    config = get_config(config)
    
    _ = cas  # unused parameter kept for API compatibility
    
    fig.add_vline(
        x=hc20,
        line_dash="dot",
        line_color=color,
        line_width=config.hc20_line_width,
        opacity=0.5,
    )
    
    log_min = np.log10(x_plot_min)
    log_max = np.log10(x_plot_max)
    log_hc20 = np.log10(hc20)
    
    frac_x = (log_hc20 - log_min) / (log_max - log_min)
    frac_x = max(0.0, min(1.0, frac_x))
    
    fig.add_annotation(
        x=frac_x,
        y=y_position,
        xref="paper",
        yref="paper",
        text=f"<b>{chem_name}</b><br>HC20 = {hc20:.2g} mg/L",
        showarrow=False,
        font=dict(color=color, size=10),
        xanchor="left",
        yanchor="middle",
        xshift=5,
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor=color,
        borderwidth=1,
    )


def plot_ssd_comparison(
    df_params: pl.DataFrame,
    cas_list: List[str],
    config: PlotConfig = None,
) -> go.Figure:
    """
    Create a comparison plot with multiple SSD curves superposed.
    
    Args:
        df_params: DataFrame with aggregated SSD parameters (SSD_mu_logEC10eq, SSD_sigma_logEC10eq)
        cas_list: List of CAS numbers to compare (maximum 3)
        config: Plot configuration (uses PLOT_CONFIG if None)
    
    Returns:
        go.Figure: Plotly figure with superposed SSD curves
    
    Raises:
        ValueError: If more than 3 CAS numbers are provided or if any CAS is invalid
    """
    config = get_config(config)
        
    # Validation: ensure cas_list is not empty and has at most 3 elements
    # Note: This validation is also done in the API layer, but kept here
    # as a defensive programming practice
    if len(cas_list) == 0:
        raise ValueError("At least one CAS number must be provided")
    if len(cas_list) > 3:
        raise ValueError(f"Maximum 3 substances can be compared. Provided: {len(cas_list)}")
    
    colors = config.comparison_colors[:len(cas_list)]
    
    all_subs = []
    all_chem_names = []
    all_hc20s = []
    all_mu_ssds = []
    all_sigma_ssds = []
    all_x_reals = []
    all_cdfs = []
    
    for cas in cas_list:
        sub, chem_name = filter_and_validate_data(df_params, cas)
        all_subs.append(sub)
        all_chem_names.append(chem_name)
        
        mu_ssd, sigma_ssd = calculate_ssd_parameters(sub)
        all_mu_ssds.append(mu_ssd)
        all_sigma_ssds.append(sigma_ssd)
        
        hc20 = calculate_hc20(sub, mu_ssd, sigma_ssd, config)
        all_hc20s.append(hc20)
        
        _, x_real, cdf_global = calculate_ssd_curve(sub, mu_ssd, sigma_ssd, config)
        all_x_reals.append(x_real)
        all_cdfs.append(cdf_global)
    
    x_plot_min, x_plot_max = calculate_global_x_axis_range(
        all_subs, all_hc20s, all_mu_ssds, all_sigma_ssds, config
    )
    tickvals, ticktext = generate_log_ticks(x_plot_min, x_plot_max)
    
    fig = go.Figure()
    
    for cas, chem_name, x_real, cdf, color in zip(
        cas_list, all_chem_names, all_x_reals, all_cdfs, colors
    ):
        add_ssd_trace_comparison(fig, x_real, cdf, chem_name, cas, color, config)
    
    y_positions = [0.85, 0.75, 0.65]
    for i, (cas, chem_name, hc20, color) in enumerate(
        zip(cas_list, all_chem_names, all_hc20s, colors)
    ):
        add_hc20_annotation_comparison(
            fig, hc20, chem_name, cas, x_plot_min, x_plot_max, color, y_positions[i], config
        )
    
    base_layout = get_base_layout_config(config)
    # Add extra space for bottom legend in comparison plot
    # Increased margin to ensure legend doesn't overlap with x-axis
    base_layout["margin"]["b"] = max(base_layout["margin"]["b"] + 100, 180)
    
    fig.update_layout(
        **base_layout,
        title=dict(
            text="<b>Species Sensitivity Distribution (SSD) Comparison</b>",
            x=0.5,
            xanchor="center",
        ),
        xaxis_title="Concentration (mg/L)",
        yaxis_title="Affected species (%)",
        yaxis=dict(range=[0, 100], ticksuffix=" %"),
        xaxis=get_log_xaxis_config(x_plot_min, x_plot_max, tickvals, ticktext),
        template=config.template,
        legend=dict(
            title="Substances",
            orientation="h",
            yanchor="bottom",
            y=-0.18,
            xanchor="center",
            x=0.5,
            # Ensure legend is within visible area
            entrywidthmode="fraction",
            entrywidth=0.3,
        ),
        hovermode="closest",
    )
    
    fig.add_hline(
        y=config.hc20_percentile * 100,
        line_dash="dot",
        line_color="rgba(128,128,128,0.5)",
        line_width=1,
    )
    
    return fig

