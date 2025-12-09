# OpenChemFacts Backend

FastAPI backend for the OpenChemFacts platform, providing access to ecotoxicology data and generating scientific visualizations.

## Role

This backend serves as the data and computation layer for the OpenChemFacts platform. It provides:

- **Data Access**: RESTful API to query ecotoxicology datasets stored in Parquet format
- **Scientific Visualizations**: Generation of Species Sensitivity Distribution (SSD) plots and EC10eq analysis
- **Data Processing**: Statistical calculations including HC20 (Hazard Concentration for 20% of species) and multi-substance comparisons

## Technical Architecture

### Core Components

```
app/
├── main.py          # FastAPI application setup, CORS, security middleware
├── api.py           # API route definitions and request handling
├── data_loader.py   # Data loading from Parquet files with caching
├── models.py        # Pydantic models for request/response validation
├── security.py      # Rate limiting and security configurations
└── middleware.py    # Security headers, request size limits, logging
```

### Data Layer

- **Storage**: Ecotoxicology data stored as Parquet files in `data/`
- **Processing**: Pandas/Polars for data manipulation
- **Caching**: LRU cache for efficient data loading and reuse

### API Layer

- **Framework**: FastAPI with automatic OpenAPI documentation
- **Security**: CORS, rate limiting, security headers, request size limits
- **Endpoints**: 
  - Data queries (`/api/summary`, `/api/search`, `/api/cas/list`)
  - Visualization data (`/api/plot/ssd/{cas}`, `/api/plot/ec10eq/{cas}`)
  - Comparisons (`/api/plot/ssd/comparison`)

### Visualization

- **Library**: Plotly for interactive scientific plots
- **Output**: JSON-serialized Plotly figures consumed by frontend
- **Types**: SSD curves, EC10eq distributions, multi-substance comparisons

## Project Structure

```
openchemfacts_backend/
├── app/                    # Application code
├── data/                   # Parquet data files
│   └── graph/             # Visualization logic modules
├── scripts/               # Deployment and utility scripts
├── tests/                 # Test suite
├── requirements.txt       # Python dependencies
└── Procfile              # Scalingo deployment configuration
```

## Deployment

Deployed on Scalingo. The application automatically configures CORS based on the `ALLOWED_ORIGINS` environment variable.

## Technology Stack

- **Python 3.11+**
- **FastAPI**: Web framework
- **Pandas/Polars**: Data processing
- **Plotly**: Scientific visualizations
- **Pydantic**: Data validation

## License

This OpenChemFacts database is made available under the Open Database License: http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual contents of the database are licensed under the Database Contents License: http://opendatacommons.org/licenses/dbcl/1.0/

The complete legal texts of both licenses are available in the project root:
- `LICENSE_ODBL.txt` - Open Database License (ODbL) v1.0
- `LICENSE_DBCL.txt` - Database Contents License (DbCL) v1.0

For more information about your rights and obligations under these licenses, please refer to the full license texts or visit [Open Data Commons](https://opendatacommons.org/licenses/).