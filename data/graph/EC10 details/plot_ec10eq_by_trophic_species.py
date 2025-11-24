"""
Script to visualize EC10eq values by trophic group and species for a given CAS number.

This script creates an interactive Plotly graph showing EC10eq values grouped by
trophic_group (ecotox_group_unepsetacjrc2018) and species_common_name.
"""

import polars as pl
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
from typing import Optional


def load_and_prepare_data(
    file_path: str,
    cas_number: str
) -> pl.DataFrame:
    """
    Load parquet file and prepare data for a specific CAS number.
    
    Args:
        file_path: Path to the parquet file
        cas_number: CAS number to filter by
        
    Returns:
        DataFrame with exploded Details containing test_id, year, author, EC10eq
    """
    # Load the parquet file
    df = pl.read_parquet(file_path)
    
    # Filter by CAS number
    df_filtered = df.filter(pl.col("cas_number") == cas_number)
    
    if df_filtered.is_empty():
        raise ValueError(f"No data found for CAS number: {cas_number}")
    
    # Explode Details to get individual endpoint records
    df_exploded = df_filtered.explode("Details")
    
    # Extract fields from Details struct
    df_exploded = df_exploded.with_columns([
        pl.col("Details").struct.field("test_id").alias("test_id"),
        pl.col("Details").struct.field("year").alias("year"),
        pl.col("Details").struct.field("author").alias("author"),
        pl.col("Details").struct.field("EC10eq").alias("EC10eq")
    ])
    
    # Drop the Details column as we've extracted all fields
    df_exploded = df_exploded.drop("Details")
    
    # Rename column for clarity
    df_exploded = df_exploded.rename({
        "ecotox_group_unepsetacjrc2018": "trophic_group"
    })
    
    return df_exploded


def create_ec10eq_plot(
    df: pl.DataFrame,
    cas_number: str,
    chemical_name: Optional[str] = None,
    log_scale: bool = True,
    color_by: str = "trophic_group"
) -> go.Figure:
    """
    Create an interactive Plotly graph showing EC10eq by trophic group and species.
    
    Args:
        df: DataFrame with EC10eq, trophic_group, species_common_name, test_id, year, author
        cas_number: CAS number for the title
        chemical_name: Optional chemical name for the title
        log_scale: Whether to use logarithmic scale for y-axis
        color_by: How to color points - "trophic_group", "year", or "author"
        
    Returns:
        Plotly Figure object
    """
    # Convert to pandas for easier plotting with Plotly
    df_pd = df.to_pandas()
    
    # Handle missing values
    df_pd["year"] = df_pd["year"].fillna(0).astype(int)
    df_pd["author"] = df_pd["author"].fillna("Unknown")
    df_pd["test_id"] = df_pd["test_id"].fillna(0).astype(int)
    
    # Get unique trophic groups and species
    trophic_groups = sorted(df_pd["trophic_group"].unique())
    
    # Create color palette for trophic groups
    colors = {
        "algae": "#2ca02c",  # Green
        "crustaceans": "#1f77b4",  # Blue
        "fish": "#ff7f0e",  # Orange
        "plants": "#9467bd",  # Purple
        "molluscs": "#8c564b",  # Brown
        "insects": "#e377c2",  # Pink
        "amphibians": "#7f7f7f",  # Gray
        "annelids": "#bcbd22",  # Yellow-green
    }
    
    # Create symbols for trophic groups
    symbols = {
        "algae": "circle",
        "crustaceans": "square",
        "fish": "triangle-up",
        "plants": "diamond",
        "molluscs": "diamond",
        "insects": "x",  # Changed from "hash" to "x" which is a valid Plotly symbol
        "amphibians": "star",
        "annelids": "hourglass",
    }
    
    # Create a combined label: "trophic_group - species" for better organization
    df_pd["trophic_species"] = df_pd["trophic_group"] + " - " + df_pd["species_common_name"]
    
    # Sort by trophic group, then by species
    df_pd = df_pd.sort_values(["trophic_group", "species_common_name"])
    
    # Get unique trophic_species combinations
    unique_combinations = df_pd["trophic_species"].unique()
    
    # Create figure
    fig = go.Figure()
    
    # Add traces based on color_by parameter
    if color_by == "trophic_group":
        # Original behavior: color by trophic group
        for trophic_group in trophic_groups:
            df_group = df_pd[df_pd["trophic_group"] == trophic_group]
            
            # Group by species within this trophic group
            for species in sorted(df_group["species_common_name"].unique()):
                df_species = df_group[df_group["species_common_name"] == species]
                label = f"{trophic_group} - {species}"
                
                # Create a trace for this species
                fig.add_trace(
                    go.Scatter(
                        x=[label] * len(df_species),
                        y=df_species["EC10eq"],
                        mode="markers",
                        name=trophic_group.capitalize(),
                        marker=dict(
                            color=colors.get(trophic_group, "#000000"),
                            symbol=symbols.get(trophic_group, "circle"),
                            size=10,
                            opacity=0.7,
                            line=dict(width=1, color="white")
                        ),
                        customdata=df_species[["test_id", "year", "author"]].values,
                        hovertemplate=(
                            "<b>EC10eq:</b> %{y:.4f} mg/L<br>"
                            "<b>Test ID:</b> %{customdata[0]}<br>"
                            "<b>Year:</b> %{customdata[1]}<br>"
                            "<b>Author:</b> %{customdata[2]}<br>"
                            "<extra></extra>"
                        ),
                        legendgroup=trophic_group,
                        showlegend=(species == sorted(df_group["species_common_name"].unique())[0])
                    )
                )
    elif color_by == "year":
        # Color by year - use a continuous color scale
        for trophic_group in trophic_groups:
            df_group = df_pd[df_pd["trophic_group"] == trophic_group]
            
            for species in sorted(df_group["species_common_name"].unique()):
                df_species = df_group[df_group["species_common_name"] == species]
                label = f"{trophic_group} - {species}"
                
                fig.add_trace(
                    go.Scatter(
                        x=[label] * len(df_species),
                        y=df_species["EC10eq"],
                        mode="markers",
                        name=trophic_group.capitalize(),
                        marker=dict(
                            color=df_species["year"],
                            colorscale="Viridis",
                            symbol=symbols.get(trophic_group, "circle"),
                            size=10,
                            opacity=0.7,
                            line=dict(width=1, color="white"),
                            colorbar=dict(title="Year", x=1.15) if species == sorted(df_group["species_common_name"].unique())[0] else None,
                            showscale=(species == sorted(df_group["species_common_name"].unique())[0] and trophic_group == trophic_groups[0])
                        ),
                        customdata=df_species[["test_id", "year", "author"]].values,
                        hovertemplate=(
                            "<b>EC10eq:</b> %{y:.4f} mg/L<br>"
                            "<b>Test ID:</b> %{customdata[0]}<br>"
                            "<b>Year:</b> %{customdata[1]}<br>"
                            "<b>Author:</b> %{customdata[2]}<br>"
                            "<extra></extra>"
                        ),
                        legendgroup=trophic_group,
                        showlegend=(species == sorted(df_group["species_common_name"].unique())[0])
                    )
                )
    else:  # color_by == "author" or default
        # Color by author - use distinct colors for different authors
        authors = sorted(df_pd["author"].unique())
        import plotly.express as px
        author_colors = px.colors.qualitative.Set3
        
        for trophic_group in trophic_groups:
            df_group = df_pd[df_pd["trophic_group"] == trophic_group]
            
            for species in sorted(df_group["species_common_name"].unique()):
                df_species = df_group[df_group["species_common_name"] == species]
                label = f"{trophic_group} - {species}"
                
                # Map authors to colors
                author_to_color = {auth: author_colors[i % len(author_colors)] 
                                 for i, auth in enumerate(authors)}
                marker_colors = [author_to_color.get(auth, "#000000") for auth in df_species["author"]]
                
                fig.add_trace(
                    go.Scatter(
                        x=[label] * len(df_species),
                        y=df_species["EC10eq"],
                        mode="markers",
                        name=trophic_group.capitalize(),
                        marker=dict(
                            color=marker_colors,
                            symbol=symbols.get(trophic_group, "circle"),
                            size=10,
                            opacity=0.7,
                            line=dict(width=1, color="white")
                        ),
                        customdata=df_species[["test_id", "year", "author"]].values,
                        hovertemplate=(
                            "<b>EC10eq:</b> %{y:.4f} mg/L<br>"
                            "<b>Test ID:</b> %{customdata[0]}<br>"
                            "<b>Year:</b> %{customdata[1]}<br>"
                            "<b>Author:</b> %{customdata[2]}<br>"
                            "<extra></extra>"
                        ),
                        legendgroup=trophic_group,
                        showlegend=(species == sorted(df_group["species_common_name"].unique())[0])
                    )
                )
    
    # Calculate statistics for title
    num_trophic_groups = len(trophic_groups)
    num_species = df_pd["species_common_name"].nunique()
    num_endpoints = len(df_pd)
    
    # Create title
    title = f"EC10eq Distribution by Trophic Group and Species"
    if color_by != "trophic_group":
        title += f" (colored by {color_by})"
    if chemical_name:
        title += f"<br><sub>CAS: {cas_number} - {chemical_name}</sub>"
    else:
        title += f"<br><sub>CAS: {cas_number}</sub>"
    title += f"<br><sub>Trophic group(s): {num_trophic_groups} | Species: {num_species} | Endpoints: {num_endpoints}</sub>"
    
    # Calculate powers of 10 for y-axis ticks (only show 1, 10, 100, 1000, etc.)
    yaxis_tickvals = None
    if log_scale:
        import numpy as np
        min_val = df_pd["EC10eq"].min()
        max_val = df_pd["EC10eq"].max()
        # Calculate the range of powers of 10
        min_power = int(np.floor(np.log10(max(min_val, 1e-10))))  # Avoid log(0)
        max_power = int(np.ceil(np.log10(max_val)))
        # Generate powers of 10
        yaxis_tickvals = [10**i for i in range(min_power, max_power + 1)]
    
    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title="Trophic Group - Species",
        yaxis_title="EC10eq (mg/L)" + (" - Log Scale" if log_scale else ""),
        yaxis=dict(
            type="log" if log_scale else "linear",
            tickmode="array" if log_scale and yaxis_tickvals else None,
            tickvals=yaxis_tickvals if log_scale else None,
            tickformat=".0e" if log_scale else None  # Scientific notation for cleaner display
        ),
        template="plotly_white",
        width=1800,
        height=900,
        hovermode="closest",
        legend=dict(
            title="Trophic Group",
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.01 if color_by == "trophic_group" else 1.15
        ),
        margin=dict(l=80, r=250 if color_by == "year" else 200, t=120, b=150),
        xaxis=dict(
            tickangle=-45,
            tickmode="array",
            tickvals=unique_combinations,
            ticktext=[label.split(" - ")[1] for label in unique_combinations]
        )
    )
    
    return fig


def main():
    """
    Main function to run the visualization script.
    """
    # Default file path
    file_path = "/workspace/data_pipeline/results_ecotox_EC10_list_per_species.parquet"
    
    # Get CAS number from command line argument or use default
    if len(sys.argv) > 1:
        cas_number = sys.argv[1]
    else:
        # Use a default CAS number for demonstration
        # You can change this or make it interactive
        print("Usage: python plot_ec10eq_by_trophic_species.py <CAS_NUMBER>")
        print("\nExample CAS numbers available:")
        print("  - 60-51-5")
        print("  - 636-30-6")
        print("  - 2116-65-6")
        print("\nPlease provide a CAS number as argument.")
        sys.exit(1)
    
    try:
        # Load and prepare data
        print(f"Loading data for CAS: {cas_number}...")
        df = load_and_prepare_data(file_path, cas_number)
        
        # Get chemical name if available
        chemical_name = None
        if "chemical_name" in df.columns:
            chemical_name = df["chemical_name"][0]
            print(f"Chemical: {chemical_name}")
        
        # Print summary statistics
        print(f"\nData summary:")
        print(f"  Total EC10eq endpoints: {len(df)}")
        print(f"  Trophic groups: {df['trophic_group'].n_unique()}")
        print(f"  Species: {df['species_common_name'].n_unique()}")
        print(f"  Unique tests: {df['test_id'].n_unique()}")
        print(f"  Year range: {df['year'].min()} - {df['year'].max()}")
        print(f"  Unique authors: {df['author'].n_unique()}")
        print(f"\nTrophic groups: {sorted(df['trophic_group'].unique().to_list())}")
        
        # Create plot (default: color by trophic_group)
        # You can change color_by to "year" or "author" for different visualizations
        print("\nCreating visualization...")
        color_by = sys.argv[2] if len(sys.argv) > 2 else "trophic_group"
        if color_by not in ["trophic_group", "year", "author"]:
            print(f"Warning: Invalid color_by '{color_by}', using 'trophic_group'")
            color_by = "trophic_group"
        fig = create_ec10eq_plot(df, cas_number, chemical_name, log_scale=True, color_by=color_by)
        
        # Show plot
        print("\nDisplaying plot...")
        fig.show()
        
        # Optionally save to HTML
        output_file = f"ec10eq_plot_{cas_number.replace('-', '_')}.html"
        fig.write_html(output_file)
        print(f"\nPlot saved to: {output_file}")
        
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
