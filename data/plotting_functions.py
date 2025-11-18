"""
Optimized visualization functions for ecotox data
Compatible with Streamlit frontend

All plotting functions use a centralized configuration class for easy customization.
"""

import numpy as np
import polars as pl
from scipy.stats import norm
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import Dict, List, Tuple, Optional
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

def filter_and_validate_data(df_params: pl.DataFrame, cas: str) -> Tuple[pl.DataFrame, str]:
    """
    Filter data for the requested CAS and validate mu/sigma values.
    
    Args:
        df_params: DataFrame with SSD parameters
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

    sub = sub.filter(
        pl.col("mu").is_finite() & pl.col("mu").is_not_null()
        & pl.col("sigma").is_finite() & (pl.col("sigma") >= 0)
    )
    if sub.height == 0:
        raise ValueError(f"No valid mu/sigma values found for CAS {cas}.")
    
    return sub, chem_name


def calculate_ssd_parameters(sub: pl.DataFrame) -> Tuple[float, float]:
    """
    Calculate global SSD parameters (mean and std of species-level mu).
    
    Args:
        sub: Filtered dataframe with mu values
        
    Returns:
        Tuple of (mu_ssd, sigma_ssd)
    """
    mu_ssd = float(sub["mu"].mean())
    sigma_ssd_val = sub["mu"].std(ddof=1)
    
    # Gérer le cas où std() retourne None (toutes les valeurs identiques ou une seule valeur)
    if sigma_ssd_val is None:
        sigma_ssd = 0.0
    else:
        sigma_ssd = float(sigma_ssd_val)
    
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
        sub: Filtered dataframe
        mu_ssd: Mean of species-level mu
        sigma_ssd: Standard deviation of species-level mu
        config: Plot configuration (uses PLOT_CONFIG if None)
        
    Returns:
        Tuple of (x_log, x_real, cdf_global)
    """
    if config is None:
        config = PLOT_CONFIG
        
    mu_min, mu_max = float(sub["mu"].min()), float(sub["mu"].max())
    mu_range = max(mu_max - mu_min, 1.0)
    x_log = np.linspace(
        mu_min - config.sigma_margin * mu_range,
        mu_max + config.sigma_margin * mu_range,
        config.n_points
    )
    x_real = 10 ** x_log
    cdf_global = 100 * norm.cdf(x_log, loc=mu_ssd, scale=sigma_ssd)
    return x_log, x_real, cdf_global


def calculate_hc20(mu_ssd: float, sigma_ssd: float, config: PlotConfig = None) -> float:
    """
    Calculate HC20 value from SSD parameters.
    
    Args:
        mu_ssd: Mean of species-level mu
        sigma_ssd: Standard deviation of species-level mu
        config: Plot configuration (uses PLOT_CONFIG if None)
        
    Returns:
        HC20 value in real units (mg/L)
    """
    if config is None:
        config = PLOT_CONFIG
        
    hc20 = 10 ** (mu_ssd + sigma_ssd * norm.ppf(config.hc20_percentile))
    if not (np.isfinite(hc20) and hc20 > 0):
        raise ValueError(f"Invalid HC20 value: {hc20}")
    return hc20


def calculate_x_axis_range(
    sub: pl.DataFrame,
    hc20: float,
    config: PlotConfig = None,
) -> Tuple[float, float]:
    """
    Compute an adaptive x-axis range based on species EC10eq (10**mu),
    then extend just enough to include HC20.
    
    Args:
        sub: Filtered dataframe
        hc20: HC20 value
        config: Plot configuration (uses PLOT_CONFIG if None)
        
    Returns:
        Tuple of (x_plot_min, x_plot_max) in mg/L
    """
    if config is None:
        config = PLOT_CONFIG
        
    ec10_species = np.power(10.0, sub["mu"].to_numpy())
    x_min_data = float(ec10_species.min())
    x_max_data = float(ec10_species.max())

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
    config: PlotConfig = None,
) -> Tuple[float, float]:
    """
    Compute a global x-axis range that encompasses all substances.
    
    Args:
        all_subs: List of filtered dataframes (one per CAS)
        all_hc20s: List of HC20 values (one per CAS)
        config: Plot configuration (uses PLOT_CONFIG if None)
    
    Returns:
        Tuple of (x_plot_min, x_plot_max) in mg/L
    """
    if config is None:
        config = PLOT_CONFIG
        
    all_mins = []
    all_maxs = []
    
    for sub in all_subs:
        ec10_species = np.power(10.0, sub["mu"].to_numpy())
        all_mins.append(float(ec10_species.min()))
        all_maxs.append(float(ec10_species.max()))
    
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
    if config is None:
        config = PLOT_CONFIG
        
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
    if config is None:
        config = PLOT_CONFIG

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
    """Add species points grouped by taxa to the figure."""
    if config is None:
        config = PLOT_CONFIG
        
    n_species = sub.height
    
    # Calculer n_results à partir de la colonne values (liste de valeurs EC10eq)
    sub_with_n = sub.with_columns([
        pl.col("values").list.len().alias("n_results")
    ])
    
    sub_sorted = sub_with_n.sort("mu").with_columns([
        ((pl.arange(1, n_species + 1) - 0.5) / n_species * 100).alias("fraction_pct"),
        (10 ** pl.col("mu")).alias("EC10eq"),
    ])
    
    for (taxa,), g in sub_sorted.group_by(["ecotox_group_unepsetacjrc2018"], maintain_order=True):
        taxa = str(taxa) if taxa is not None else "unknown"
        custom_n = g["n_results"].to_list()
        fig.add_trace(go.Scatter(
            x=g["EC10eq"].to_list(), 
            y=g["fraction_pct"].to_list(),
            mode="markers", 
            marker=dict(
                symbol=config.taxa_symbols.get(taxa, "circle"), 
                size=config.marker_size
            ),
            name=taxa, 
            text=g["species_common_name"].to_list(),
            customdata=custom_n,
            hovertemplate=(
                "Species: %{text}<br>Taxon: " + taxa + "<br>"
                "# EC10eq results used: %{customdata}"
            ),
        ))


def plot_ssd_global(
    df_params: pl.DataFrame,
    cas: str,
    config: PlotConfig = None,
) -> go.Figure:
    """
    Generate SSD (Species Sensitivity Distribution) and HC20 plot for a single chemical.
    
    Args:
        df_params: DataFrame with SSD parameters (mu, sigma) per species
        cas: CAS number of the chemical
        config: Plot configuration (uses PLOT_CONFIG if None)
        
    Returns:
        go.Figure: Plotly figure ready for display (compatible with Streamlit)
        
    Raises:
        ValueError: If CAS not found or no valid data
    """
    if config is None:
        config = PLOT_CONFIG

    sub, chem_name = filter_and_validate_data(df_params, cas)
    n_species = sub["species_common_name"].n_unique()
    n_trophic_level = sub["ecotox_group_unepsetacjrc2018"].n_unique()
    n_results = sub.height

    mu_ssd, sigma_ssd = calculate_ssd_parameters(sub)
    x_log, x_real, cdf_global = calculate_ssd_curve(sub, mu_ssd, sigma_ssd, config)
    hc20 = calculate_hc20(mu_ssd, sigma_ssd, config)
    x_plot_min, x_plot_max = calculate_x_axis_range(sub, hc20, config)
    
    tickvals, ticktext = generate_log_ticks(x_plot_min, x_plot_max)
    
    fig = go.Figure()
    
    add_ssd_trace(fig, x_real, cdf_global, config)
    add_species_points(fig, sub, config)
    add_hc20_annotation(fig, hc20, x_plot_min, x_plot_max, config)
    
    fig.update_layout(
        width=config.plot_width,
        height=config.plot_height,
        margin=dict(
            t=config.margin_top,
            b=config.margin_bottom,
            l=config.margin_left,
            r=config.margin_right,
        ),
        title=dict(
            text=(
                "<b>Species Sensitivity Distribution (SSD) and HC20</b><br>"
                f"<b>Chemical:</b> {chem_name} (CAS {cas})<br>"
                f"<b>Details:</b> {n_results} EC10eq result(s) / "
                f"{n_species} species / {n_trophic_level} trophic level(s)"
            ),
            x=0.5,
            xanchor="center",
        ),
        xaxis_title="Concentration (mg/L)",
        yaxis_title="Affected species (%)",
        yaxis=dict(range=[0, 100], ticksuffix=" %"),
        xaxis=dict(
            type="log",
            range=[np.log10(x_plot_min), np.log10(x_plot_max)],
            tickmode="array",
            tickvals=tickvals,
            ticktext=ticktext,
            showgrid=True,
            ticks="outside",
        ),
        template=config.template,
        legend_title="Taxa / SSD",
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
    
    Args:
        df_params: DataFrame with EC10eq values
        cas: CAS number of the chemical
        config: Plot configuration (uses PLOT_CONFIG if None)
        
    Returns:
        go.Figure: Plotly figure ready for display (compatible with Streamlit)
        
    Raises:
        ValueError: If CAS not found or no valid data
    """
    if config is None:
        config = PLOT_CONFIG

    sub = df_params.filter(pl.col("cas_number") == cas)
    if sub.height == 0:
        raise ValueError(f"CAS {cas} not found in dataframe.")

    chem_name = sub["chemical_name"][0] if "chemical_name" in sub.columns else cas
    n_species = sub["species_common_name"].n_unique()
    n_trophic_level = sub["ecotox_group_unepsetacjrc2018"].n_unique()

    exploded = (
        sub
        .explode("values")
        .rename({"values": "EC10eq"})
        .filter(pl.col("EC10eq").is_finite() & (pl.col("EC10eq") > 0))
    )
    if exploded.height == 0:
        raise ValueError("No valid EC10eq values found for this CAS.")

    n_results = exploded.height

    taxa_counts = (
        exploded
        .group_by("ecotox_group_unepsetacjrc2018")
        .agg([
            pl.col("species_common_name").n_unique().alias("n_species"),
            pl.col("EC10eq").count().alias("n_results"),
        ])
        .sort("ecotox_group_unepsetacjrc2018")
    )

    taxa_list = taxa_counts["ecotox_group_unepsetacjrc2018"].to_list()
    counts_species = [int(x) for x in taxa_counts["n_species"].to_list()]
    counts_results = [int(x) for x in taxa_counts["n_results"].to_list()]

    total_species = sum(counts_species)
    column_widths = [ns / total_species for ns in counts_species]

    species_list = exploded["species_common_name"].unique().to_list()
    palette = px.colors.qualitative.Dark24 * config.species_palette_multiplier
    color_map = {sp: palette[i % len(palette)] for i, sp in enumerate(species_list)}

    y_min = float(exploded["EC10eq"].min())
    y_max = float(exploded["EC10eq"].max())
    min_pow = int(np.floor(np.log10(y_min)))
    max_pow = int(np.ceil(np.log10(y_max)))
    y_tickvals = [10 ** p for p in range(min_pow, max_pow + 1)]
    y_ticktext = [f"{v:g}" for v in y_tickvals]

    fig = make_subplots(
        rows=1,
        cols=len(taxa_list),
        shared_yaxes=True,
        horizontal_spacing=0.05,
        column_widths=column_widths,
        subplot_titles=[None] * len(taxa_list),
    )

    for idx, (taxa, n_res_taxa) in enumerate(zip(taxa_list, counts_results), start=1):
        g_taxa = exploded.filter(pl.col("ecotox_group_unepsetacjrc2018") == taxa)
        if g_taxa.height == 0:
            continue

        species_in_taxa = g_taxa["species_common_name"].unique().to_list()

        for sp in species_in_taxa:
            g_sp = g_taxa.filter(pl.col("species_common_name") == sp)

            fig.add_trace(
                go.Scatter(
                    x=g_sp["species_common_name"].to_list(),
                    y=g_sp["EC10eq"].to_list(),
                    mode="markers",
                    marker=dict(
                        color=color_map[sp],
                        size=config.marker_size,
                        line=dict(width=0.5, color="black"),
                    ),
                    showlegend=False,
                    hovertemplate=(
                        f"Taxon: {taxa}<br>"
                        "Species: %{x}<br>"
                        "EC10eq = %{y:.4g} mg/L"
                        "<extra></extra>"
                    ),
                ),
                row=1,
                col=idx,
            )

        fig.update_xaxes(
            type="category",
            showticklabels=True,
            title_text=None,
            row=1,
            col=idx,
        )

        axis_suffix = "" if idx == 1 else str(idx)
        fig.add_annotation(
            xref=f"x{axis_suffix} domain",
            yref="paper",
            x=0.5,
            y=1.02,
            text=f"<b>{taxa} ({n_res_taxa} results)</b>",
            showarrow=False,
            font=dict(size=14),
        )

    for col in range(1, len(taxa_list) + 1):
        fig.update_yaxes(
            type="log",
            tickmode="array",
            tickvals=y_tickvals,
            ticktext=y_ticktext,
            range=[min_pow - 0.2, max_pow + 0.2],
            row=1,
            col=col,
        )

    fig.update_yaxes(title_text="EC10eq (mg/L)", row=1, col=1)

    fig.update_layout(
        width=config.plot_width,
        height=config.plot_height,
        margin=dict(
            t=config.margin_top,
            b=config.margin_bottom,
            l=config.margin_left,
            r=config.margin_right,
        ),
        title=dict(
            text=(
                "<b>EC10eq calculated results per chemical</b><br>"
                f"<b>Chemical:</b> {chem_name} (CAS {cas})<br>"
                f"<b>Details:</b> {n_results} EC10eq result(s) / "
                f"{n_species} species / {n_trophic_level} trophic level(s)"
            ),
            x=0.5,
            xanchor="center",
            y=0.98,
            yanchor="top",
        ),
        template=config.template,
        hovermode="closest",
        showlegend=False,
    )

    return fig


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
    if config is None:
        config = PLOT_CONFIG
        
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
    cas: str,
    x_plot_min: float,
    x_plot_max: float,
    color: str,
    y_position: float,
    config: PlotConfig = None,
) -> None:
    """Add HC20 vertical line and annotation for comparison plot."""
    if config is None:
        config = PLOT_CONFIG
    
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
        df_params: DataFrame with SSD parameters (mu, sigma) per species
        cas_list: List of CAS numbers to compare (maximum 3)
        config: Plot configuration (uses PLOT_CONFIG if None)
    
    Returns:
        go.Figure: Plotly figure with superposed SSD curves
    
    Raises:
        ValueError: If more than 3 CAS numbers are provided or if any CAS is invalid
    """
    if config is None:
        config = PLOT_CONFIG
        
    if len(cas_list) > 3:
        raise ValueError(f"Maximum 3 substances can be compared. Provided: {len(cas_list)}")
    
    if len(cas_list) == 0:
        raise ValueError("At least one CAS number must be provided")
    
    colors = config.comparison_colors[:len(cas_list)]
    
    all_subs = []
    all_chem_names = []
    all_hc20s = []
    all_x_reals = []
    all_cdfs = []
    
    for cas in cas_list:
        sub, chem_name = filter_and_validate_data(df_params, cas)
        all_subs.append(sub)
        all_chem_names.append(chem_name)
        
        mu_ssd, sigma_ssd = calculate_ssd_parameters(sub)
        hc20 = calculate_hc20(mu_ssd, sigma_ssd, config)
        all_hc20s.append(hc20)
        
        x_log, x_real, cdf_global = calculate_ssd_curve(sub, mu_ssd, sigma_ssd, config)
        all_x_reals.append(x_real)
        all_cdfs.append(cdf_global)
    
    x_plot_min, x_plot_max = calculate_global_x_axis_range(all_subs, all_hc20s, config)
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
    
    fig.update_layout(
        width=config.plot_width,
        height=config.plot_height,
        margin=dict(
            t=config.margin_top,
            b=config.margin_bottom + 60,  # Extra space for bottom legend
            l=config.margin_left,
            r=config.margin_right,
        ),
        title=dict(
            text="<b>Species Sensitivity Distribution (SSD) Comparison</b>",
            x=0.5,
            xanchor="center",
        ),
        xaxis_title="Concentration (mg/L)",
        yaxis_title="Affected species (%)",
        yaxis=dict(range=[0, 100], ticksuffix=" %"),
        xaxis=dict(
            type="log",
            range=[np.log10(x_plot_min), np.log10(x_plot_max)],
            tickmode="array",
            tickvals=tickvals,
            ticktext=ticktext,
            showgrid=True,
            ticks="outside",
        ),
        template=config.template,
        legend=dict(
            title="Substances",
            orientation="h",
            yanchor="bottom",
            y=-0.15,
            xanchor="center",
            x=0.5,
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

