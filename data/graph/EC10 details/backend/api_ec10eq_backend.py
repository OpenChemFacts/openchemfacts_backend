"""
API Backend pour exposer les données EC10eq par groupe trophique et espèce
Basé sur FastAPI

Usage:
    uvicorn api_ec10eq_backend:app --host 0.0.0.0 --port 8000

Pour Scalingo:
    Ajouter dans Procfile: web: uvicorn api_ec10eq_backend:app --host 0.0.0.0 --port $PORT
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
import sys
from pathlib import Path
import os
import polars as pl

# Configuration
current_dir = Path(__file__).parent
DATA_PATH = os.getenv(
    "EC10EQ_DATA_PATH",
    str(current_dir / "results_ecotox_EC10_list_per_species.parquet")
)

# Initialiser l'application FastAPI
app = FastAPI(
    title="EC10eq by Trophic Group and Species API",
    description="API RESTful pour récupérer les données EC10eq par groupe trophique et espèce",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifier les domaines autorisés
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def load_and_prepare_data(cas_number: str) -> pl.DataFrame:
    """
    Load parquet file and prepare data for a specific CAS number.
    
    Args:
        cas_number: CAS number to filter by
        
    Returns:
        DataFrame with exploded Details containing test_id, year, author, EC10eq
    """
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Data file not found: {DATA_PATH}")
    
    # Load the parquet file
    df = pl.read_parquet(DATA_PATH)
    
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


@app.get("/")
async def root():
    """Endpoint racine avec informations sur l'API"""
    return {
        "message": "EC10eq by Trophic Group and Species API",
        "version": "1.0.0",
        "data_path": DATA_PATH,
        "endpoints": {
            "/ec10eq/data": "GET - Retourne les données EC10eq au format JSON",
            "/ec10eq/stats": "GET - Retourne les statistiques pour un CAS",
            "/ec10eq/plot/json": "GET - Retourne le graphique Plotly en JSON"
        },
        "example": "/ec10eq/data?cas=60-51-5"
    }


@app.get("/ec10eq/data")
async def get_ec10eq_data(
    cas: str = Query(..., description="Numéro CAS du produit chimique (ex: 60-51-5)"),
    format: Optional[str] = Query("detailed", description="Format de sortie: 'detailed' ou 'simple'")
):
    """
    Récupère les données EC10eq pour un CAS donné.
    
    **Paramètres:**
    - `cas`: Numéro CAS du produit chimique (requis)
    - `format`: Format de sortie - 'detailed' (par défaut) ou 'simple'
    
    **Retour:**
    - JSON avec les données EC10eq organisées par groupe trophique et espèce
    
    **Exemple:**
    ```
    GET /ec10eq/data?cas=60-51-5
    ```
    """
    try:
        df = load_and_prepare_data(cas)
        
        # Get chemical name
        chemical_name = None
        if "chemical_name" in df.columns:
            chemical_name = df["chemical_name"][0]
        
        # Convert to pandas for easier JSON serialization
        df_pd = df.to_pandas()
        
        # Handle missing values
        df_pd["year"] = df_pd["year"].fillna(0).astype(int)
        df_pd["author"] = df_pd["author"].fillna("Unknown")
        df_pd["test_id"] = df_pd["test_id"].fillna(0).astype(int)
        
        if format == "simple":
            # Simple format: just the endpoints
            endpoints = []
            for _, row in df_pd.iterrows():
                endpoints.append({
                    "trophic_group": row["trophic_group"],
                    "species": row["species_common_name"],
                    "EC10eq": float(row["EC10eq"]),
                    "test_id": int(row["test_id"]),
                    "year": int(row["year"]),
                    "author": row["author"]
                })
            
            return JSONResponse(content={
                "cas": cas,
                "chemical_name": chemical_name,
                "endpoints": endpoints
            })
        else:
            # Detailed format: organized by trophic group and species
            result = {
                "cas": cas,
                "chemical_name": chemical_name,
                "trophic_groups": {}
            }
            
            # Group by trophic group
            for trophic_group in sorted(df_pd["trophic_group"].unique()):
                df_group = df_pd[df_pd["trophic_group"] == trophic_group]
                result["trophic_groups"][trophic_group] = {}
                
                # Group by species
                for species in sorted(df_group["species_common_name"].unique()):
                    df_species = df_group[df_group["species_common_name"] == species]
                    endpoints = []
                    
                    for _, row in df_species.iterrows():
                        endpoints.append({
                            "EC10eq": float(row["EC10eq"]),
                            "test_id": int(row["test_id"]),
                            "year": int(row["year"]),
                            "author": row["author"]
                        })
                    
                    result["trophic_groups"][trophic_group][species] = endpoints
            
            return JSONResponse(content=result)
            
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des données: {str(e)}"
        )


@app.get("/ec10eq/stats")
async def get_ec10eq_stats(
    cas: str = Query(..., description="Numéro CAS du produit chimique (ex: 60-51-5)")
):
    """
    Retourne les statistiques pour un CAS donné.
    
    **Paramètres:**
    - `cas`: Numéro CAS du produit chimique (requis)
    
    **Retour:**
    - JSON avec les statistiques (nombre de groupes trophiques, espèces, endpoints, etc.)
    """
    try:
        df = load_and_prepare_data(cas)
        
        # Get chemical name
        chemical_name = None
        if "chemical_name" in df.columns:
            chemical_name = df["chemical_name"][0]
        
        # Calculate statistics
        stats = {
            "cas": cas,
            "chemical_name": chemical_name,
            "total_endpoints": len(df),
            "trophic_groups": {
                "count": df["trophic_group"].n_unique(),
                "list": sorted(df["trophic_group"].unique().to_list())
            },
            "species": {
                "count": df["species_common_name"].nunique(),
                "list": sorted(df["species_common_name"].unique().to_list())
            },
            "tests": {
                "count": df["test_id"].n_unique()
            },
            "year": {
                "min": int(df["year"].min()),
                "max": int(df["year"].max())
            },
            "authors": {
                "count": df["author"].n_unique()
            },
            "ec10eq": {
                "min": float(df["EC10eq"].min()),
                "max": float(df["EC10eq"].max()),
                "mean": float(df["EC10eq"].mean()),
                "median": float(df["EC10eq"].median())
            }
        }
        
        return JSONResponse(content=stats)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des statistiques: {str(e)}"
        )


@app.get("/ec10eq/plot/json")
async def get_ec10eq_plot_json(
    cas: str = Query(..., description="Numéro CAS du produit chimique (ex: 60-51-5)"),
    color_by: Optional[str] = Query("trophic_group", description="Mode de coloration: 'trophic_group', 'year', ou 'author'")
):
    """
    Génère un graphique EC10eq et le retourne en JSON (structure Plotly).
    
    Le client peut utiliser Plotly.js pour afficher le graphique côté frontend.
    
    **Paramètres:**
    - `cas`: Numéro CAS du produit chimique (requis)
    - `color_by`: Mode de coloration - 'trophic_group' (défaut), 'year', ou 'author'
    
    **Retour:**
    - JSON avec la structure complète du graphique Plotly
    
    **Exemple d'utilisation côté client (JavaScript):**
    ```javascript
    const response = await fetch('/ec10eq/plot/json?cas=60-51-5');
    const plotData = await response.json();
    Plotly.newPlot('plot-container', plotData.data, plotData.layout);
    ```
    """
    try:
        # Import the plotting function
        sys.path.insert(0, str(current_dir))
        from plot_ec10eq_by_trophic_species import create_ec10eq_plot
        
        df = load_and_prepare_data(cas)
        
        # Get chemical name
        chemical_name = None
        if "chemical_name" in df.columns:
            chemical_name = df["chemical_name"][0]
        
        # Validate color_by
        if color_by not in ["trophic_group", "year", "author"]:
            color_by = "trophic_group"
        
        # Create plot
        fig = create_ec10eq_plot(df, cas, chemical_name, log_scale=True, color_by=color_by)
        
        # Return Plotly JSON structure
        return JSONResponse(content=fig.to_dict())
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la génération du graphique: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Endpoint de santé pour vérifier que l'API fonctionne"""
    return {
        "status": "healthy",
        "data_file_exists": os.path.exists(DATA_PATH),
        "data_path": DATA_PATH
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        log_level="info"
    )

