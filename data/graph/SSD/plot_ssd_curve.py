"""
Generate SSD (Species Sensitivity Distribution) curve plot using Plotly
Based on JRC Ecotox EF3.1 methodology

Takes as input:
- A parquet dataframe with SSD parameters
- A CAS number (e.g., "107-05-1")
"""

import pandas as pd
import numpy as np
from scipy.stats import norm
import plotly.graph_objects as go
from typing import Optional, Dict, Any


def get_ssd_data(
    dataframe: pd.DataFrame,
    cas: str
) -> Dict[str, Any]:
    """
    Extract SSD (Species Sensitivity Distribution) data for a given CAS number.
    
    Args:
        dataframe: DataFrame containing SSD data
        cas: CAS number (e.g., "107-05-1")
        
    Returns:
        Dictionary containing SSD data in JSON format:
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
            } or None,
            "message": str (optional, only present when sigma_ssd == 0)
        }
        
    Raises:
        ValueError: If CAS not found or invalid data
    """
    # Filter by CAS
    row = dataframe[dataframe['cas_number'] == cas]
    if len(row) == 0:
        raise ValueError(f"CAS {cas} not found in dataframe.")
    
    row = row.iloc[0]
    
    # Extract SSD parameters with safe conversion handling NaN/None values
    # Use .get() with default values to handle missing columns gracefully
    try:
        mu_ssd = float(row.get('SSD_mu_logEC10eq', 0.0)) if pd.notna(row.get('SSD_mu_logEC10eq')) else 0.0
    except (ValueError, TypeError):
        mu_ssd = 0.0
    
    try:
        sigma_ssd = float(row.get('SSD_sigma_logEC10eq', 0.0)) if pd.notna(row.get('SSD_sigma_logEC10eq')) else 0.0
    except (ValueError, TypeError):
        sigma_ssd = 0.0
    
    try:
        hc20_val = row.get('HC20', 1e-3)
        hc20 = float(hc20_val) if pd.notna(hc20_val) and float(hc20_val) > 0 else 1e-3
    except (ValueError, TypeError):
        hc20 = 1e-3
    
    try:
        chemical_name = str(row.get('chemical_name', 'Unknown')) if pd.notna(row.get('chemical_name')) else "Unknown"
    except (ValueError, TypeError):
        chemical_name = "Unknown"
    
    try:
        n_species = int(row.get('n_species', 0)) if pd.notna(row.get('n_species')) else 0
    except (ValueError, TypeError):
        n_species = 0
    
    try:
        n_ecotox_group = int(row.get('n_ecotox_group', 0)) if pd.notna(row.get('n_ecotox_group')) else 0
    except (ValueError, TypeError):
        n_ecotox_group = 0
    
    # Extract species data
    ec10eq_list = row.get('EC10eq_list', [])
    if isinstance(ec10eq_list, np.ndarray):
        ec10eq_list = ec10eq_list.tolist()
    elif not isinstance(ec10eq_list, list):
        ec10eq_list = []
    
    species_dict_list = row.get('species_ec10eq_dict_list', [])
    if isinstance(species_dict_list, np.ndarray):
        species_dict_list = species_dict_list.tolist()
    elif not isinstance(species_dict_list, list):
        species_dict_list = []
    
    # Extract and organize species data
    species_data = []
    for item in species_dict_list:
        if isinstance(item, dict):
            # Handle both old and new data structure
            species_name = item.get('species_name') or item.get('species_common_name', 'Unknown')
            ec10eq = item.get('ec10eq') or item.get('EC10eq_species_mean', 0)
            trophic_group = item.get('trophic_group') or item.get('ecotox_group_unepsetacjrc2018', 'unknown')
            
            # Safe conversion of ec10eq to float, handling None/NaN
            try:
                if ec10eq is None:
                    ec10eq_float = 0.0
                elif isinstance(ec10eq, float) and np.isnan(ec10eq):
                    ec10eq_float = 0.0
                else:
                    ec10eq_float = float(ec10eq)
                    if np.isnan(ec10eq_float) or ec10eq_float <= 0:
                        ec10eq_float = 0.0
            except (ValueError, TypeError):
                ec10eq_float = 0.0
            
            species_data.append({
                'species_name': str(species_name) if species_name else 'Unknown',
                'ec10eq_mgL': ec10eq_float,
                'trophic_group': str(trophic_group) if trophic_group else 'unknown'
            })
    
    # Sort species data by EC10eq
    species_data.sort(key=lambda x: x['ec10eq_mgL'])
    
    # Validate parameters and calculate curve
    if sigma_ssd == 0:
        # Single species case - return data without curve
        # Get the species name from species_data if available
        species_name = "Unknown"
        if species_data and len(species_data) > 0:
            species_name = species_data[0].get('species_name', 'Unknown')
        
        message = (
            f"This substance [{chemical_name}] with CAS [{cas}] has only one EC10eq value specific to the species [{species_name}]. "
            f"Please select other substances to display SSD curves."
        )
        
        return {
            "cas_number": cas,
            "chemical_name": chemical_name,
            "ssd_parameters": {
                "mu_logEC10eq": mu_ssd,
                "sigma_logEC10eq": sigma_ssd,
                "hc20_mgL": hc20
            },
            "summary": {
                "n_species": n_species,
                "n_ecotox_group": n_ecotox_group
            },
            "species_data": species_data,
            "ssd_curve": None,
            "message": message
        }
    
    # Calculate SSD curve (CDF in log10 space)
    # All values are in mg/L (milligrams per liter) for consistency
    # Range: extend beyond data range
    # Filter out NaN/None values from ec10eq_list
    valid_ec10eq_list = []
    for x in ec10eq_list:
        try:
            if x is not None:
                x_float = float(x)
                if not np.isnan(x_float) and x_float > 0:
                    valid_ec10eq_list.append(x_float)
        except (ValueError, TypeError):
            continue
    
    if len(valid_ec10eq_list) == 0:
        # No valid EC10eq values, use defaults
        ec10_min = 1e-3  # mg/L
        ec10_max = 1e3  # mg/L
    else:
        ec10_min = min(valid_ec10eq_list)  # mg/L
        ec10_max = max(valid_ec10eq_list)  # mg/L
    
    # Ensure positive values for log10
    ec10_min = max(ec10_min, 1e-6)  # Avoid log10(0) or negative
    ec10_max = max(ec10_max, 1e-6)
    hc20 = max(hc20, 1e-6)  # Ensure HC20 is positive
    
    log_min = np.log10(ec10_min) - 1.0
    log_max = np.log10(ec10_max) + 1.0
    
    # Ensure HC20 is in range (HC20 is in mg/L)
    log_hc20 = np.log10(hc20)  # hc20 is in mg/L
    if log_hc20 < log_min:
        log_min = log_hc20 - 0.5
    if log_hc20 > log_max:
        log_max = log_hc20 + 0.5
    
    # Generate x values in log10 space, then convert to mg/L
    n_points = 400
    x_log = np.linspace(log_min, log_max, n_points)
    x_real = 10 ** x_log  # Convert to real units: mg/L (milligrams per liter)
    
    # Calculate CDF (cumulative distribution function)
    # This represents the percentage of species affected at each concentration
    cdf = 100 * norm.cdf(x_log, loc=mu_ssd, scale=sigma_ssd)
    
    # Build response
    return {
        "cas_number": cas,
        "chemical_name": chemical_name,
        "ssd_parameters": {
            "mu_logEC10eq": float(mu_ssd),
            "sigma_logEC10eq": float(sigma_ssd),
            "hc20_mgL": float(hc20)
        },
        "summary": {
            "n_species": n_species,
            "n_ecotox_group": n_ecotox_group
        },
        "species_data": species_data,
        "ssd_curve": {
            "concentrations_mgL": [float(x) for x in x_real],
            "affected_species_percent": [float(y) for y in cdf]
        }
    }


def plot_ssd_curve(
    dataframe_path: str,
    cas: str,
    title: Optional[str] = None
) -> go.Figure:
    """
    Generate an SSD curve plot for a given CAS number.
    
    Args:
        dataframe_path: Path to the parquet file containing SSD data
        cas: CAS number (e.g., "107-05-1")
        title: Optional custom title for the plot
        
    Returns:
        go.Figure: Plotly figure with SSD curve
        
    Raises:
        ValueError: If CAS not found or invalid data
    """
    # Load dataframe
    df = pd.read_parquet(dataframe_path)
    
    # Filter by CAS
    row = df[df['cas_number'] == cas]
    if len(row) == 0:
        raise ValueError(f"CAS {cas} not found in dataframe.")
    
    row = row.iloc[0]
    
    # Extract SSD parameters
    mu_ssd = row['SSD_mu_logEC10eq']  # Mean in log10 space
    sigma_ssd = row['SSD_sigma_logEC10eq']  # Std in log10 space
    hc20 = row['HC20']  # HC20 value (already calculated)
    chemical_name = row['chemical_name']
    n_species = row['n_species']
    n_ecotox_group = row['n_ecotox_group']
    
    # Extract species data
    ec10eq_list = row['EC10eq_list']
    if isinstance(ec10eq_list, np.ndarray):
        ec10eq_list = ec10eq_list.tolist()
    
    species_dict_list = row['species_ec10eq_dict_list']
    if isinstance(species_dict_list, np.ndarray):
        species_dict_list = species_dict_list.tolist()
    
    # Validate parameters
    if sigma_ssd == 0:
        raise ValueError(f"Only one species value => no SSD curve is possible. HC20 = {hc20} mg/L")
    
    # Calculate SSD curve (CDF in log10 space)
    # All values are in mg/L (milligrams per liter) for consistency
    # Range: extend beyond data range
    ec10_min = min(ec10eq_list) if len(ec10eq_list) > 0 else 1e-3  # mg/L
    ec10_max = max(ec10eq_list) if len(ec10eq_list) > 0 else 1e3  # mg/L
    
    log_min = np.log10(ec10_min) - 1.0
    log_max = np.log10(ec10_max) + 1.0
    
    # Ensure HC20 is in range (HC20 is in mg/L)
    log_hc20 = np.log10(hc20)  # hc20 is in mg/L
    if log_hc20 < log_min:
        log_min = log_hc20 - 0.5
    if log_hc20 > log_max:
        log_max = log_hc20 + 0.5
    
    # Generate x values in log10 space, then convert to mg/L
    n_points = 400
    x_log = np.linspace(log_min, log_max, n_points)
    x_real = 10 ** x_log  # Convert to real units: mg/L (milligrams per liter)
    
    # Calculate CDF (cumulative distribution function)
    # This represents the percentage of species affected at each concentration
    cdf = 100 * norm.cdf(x_log, loc=mu_ssd, scale=sigma_ssd)
    
    # Create figure
    fig = go.Figure()
    
    # Add SSD curve
    fig.add_trace(go.Scatter(
        x=x_real,
        y=cdf,
        mode='lines',
        name='SSD Curve',
        line=dict(width=4, color='black'),
        hovertemplate='Concentration: %{x:.2g} mg/L<br>% of species affected: %{y:.1f}%<extra></extra>',
    ))
    
    # Add species points grouped by trophic_group
    # Extract and organize species data by trophic group
    species_data = []
    for item in species_dict_list:
        if isinstance(item, dict):
            # Handle both old and new data structure
            species_name = item.get('species_name') or item.get('species_common_name', 'Unknown')
            ec10eq = item.get('ec10eq') or item.get('EC10eq_species_mean', 0)
            trophic_group = item.get('trophic_group') or item.get('ecotox_group_unepsetacjrc2018', 'unknown')
            
            species_data.append({
                'name': species_name,
                'ec10eq': ec10eq,
                'trophic_group': trophic_group
            })
    
    if species_data:
        species_data.sort(key=lambda x: x['ec10eq'])
        n_species_points = len(species_data)
        
        # Calculate y positions (percentile ranks)
        y_positions = [(i + 0.5) / n_species_points * 100 for i in range(n_species_points)]
        
        # Define colors and symbols for different trophic groups
        # Based on JRC Ecotox EF3.1 standard groups
        trophic_group_styles = {
            'algae': {'color': '#2ca02c', 'symbol': 'circle'},  # Green
            'crustaceans': {'color': '#1f77b4', 'symbol': 'square'},  # Blue
            'fish': {'color': '#ff7f0e', 'symbol': 'triangle-up'},  # Orange
            'plants': {'color': '#9467bd', 'symbol': 'diamond'},  # Purple
            'molluscs': {'color': '#8c564b', 'symbol': 'diamond'},  # Brown
            'insects': {'color': '#e377c2', 'symbol': 'hash'},  # Pink
            'amphibians': {'color': '#7f7f7f', 'symbol': 'star'},  # Gray
            'annelids': {'color': '#bcbd22', 'symbol': 'hourglass'},  # Yellow-green
        }
        
        # Group species by trophic_group
        trophic_groups = {}
        for i, item in enumerate(species_data):
            tg = item['trophic_group']
            if tg not in trophic_groups:
                trophic_groups[tg] = {
                    'x': [],
                    'y': [],
                    'names': []
                }
            trophic_groups[tg]['x'].append(item['ec10eq'])
            trophic_groups[tg]['y'].append(y_positions[i])
            trophic_groups[tg]['names'].append(item['name'])
        
        # Add a trace for each trophic group
        for trophic_group, data in trophic_groups.items():
            style = trophic_group_styles.get(trophic_group, {'color': '#d62728', 'symbol': 'circle'})
            
            fig.add_trace(go.Scatter(
                x=data['x'],
                y=data['y'],
                mode='markers',
                name=trophic_group.capitalize(),
                marker=dict(
                    size=10,
                    color=style['color'],
                    symbol=style['symbol'],
                    line=dict(width=1, color='black')
                ),
                text=data['names'],
                hovertemplate=(
                    '<b>%{text}</b><br>'
                    'Trophic group: ' + trophic_group + '<br>'
                    'EC10eq: %{x:.2g} mg/L<extra></extra>'
                ),
            ))
    
    # Add HC20 lines
    # Horizontal line at 20%
    fig.add_hline(
        y=20,
        line_dash='dot',
        line_color='rgba(255,0,0,0.5)',
        line_width=2,
        annotation_position='right'
    )
    
    # Vertical line at HC20 (value in mg/L, consistent with x-axis scale)
    fig.add_vline(
        x=hc20,  # HC20 value in mg/L
        line_dash='dot',
        line_color='rgba(255,0,0,0.5)',
        line_width=2,
    )
    
    # Add HC20 annotation
    log_min_plot = np.log10(x_real.min())
    log_max_plot = np.log10(x_real.max())
    log_hc20_plot = np.log10(hc20)
    frac_x = (log_hc20_plot - log_min_plot) / (log_max_plot - log_min_plot)
    frac_x = max(0.05, min(0.95, frac_x))
    
    fig.add_annotation(
        x=frac_x,
        y=0.93,
        xref='paper',
        yref='paper',
        text=f'<b>HC20 = {hc20:.2g} mg/L</b>',
        showarrow=False,
        font=dict(color='red', size=14),
        bgcolor='rgba(255,255,255,0.8)',
        bordercolor='red',
        borderwidth=1,
    )
    
    # Set title
    if title is None:
        title = (
            f"<b>Species Sensitivity Distribution (SSD) and HC20</b><br>"
            f"<b>Chemical:</b> {chemical_name} / <b>CAS:</b> {cas}<br>"
            f"<b>Details:</b> {n_species} species / {n_ecotox_group} trophic level(s)"
        )
    
    # Update layout
    fig.update_layout(
        title=dict(
            text=title,
            x=0.5,
            xanchor='center',
            font=dict(size=14)
        ),
        xaxis_title='Concentration (mg/L)',
        yaxis_title='Affected species (%)',
        xaxis=dict(
            type='log',
            range=[np.log10(x_real.min()), np.log10(x_real.max())],
            showgrid=True,
        ),
        yaxis=dict(
            range=[0, 100],
            ticksuffix=' %',
            showgrid=True,
        ),
        width=1000,
        height=600,
        template='plotly_white',
        hovermode='closest',
        legend=dict(
            title='Legend',
            orientation='v',
            yanchor='top',
            y=0.98,
            xanchor='left',
            x=0.02,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='black',
            borderwidth=1,
        ),
        margin=dict(t=120, b=80, l=80, r=60),
    )
    
    return fig


if __name__ == '__main__':
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        cas = sys.argv[1]
    else:
        cas = "107-05-1"  # Default example
    
    dataframe_path = "/workspace/data_pipeline/results_ecotox_database.parquet"
    
    try:
        fig = plot_ssd_curve(dataframe_path, cas)
        fig.show()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

