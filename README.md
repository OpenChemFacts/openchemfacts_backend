# OpenChemFacts API

FastAPI backend for accessing ecotoxicology (ecotox) data and generating Species Sensitivity Distribution (SSD) plots.

## Description

This API provides access to ecotoxicology data stored in Parquet files and generates interactive visualizations with Plotly:
- Species Sensitivity Distribution (SSD) and HC20 calculation
- EC10eq results by taxon and species
- Comparison of multiple substances

## Prerequisites

- Python 3.11+
- Git

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd openchemfacts_backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Verify data files are present:
```bash
ls data/results_ecotox_*.parquet
```

## Quick Start

### Start the server

**Linux/macOS:**
```bash
chmod +x scripts/start_local.sh
./scripts/start_local.sh
```

**Windows:**
```batch
scripts\start_local.bat
```

The server starts on `http://localhost:8000` with auto-reload enabled.

### Verify the server is running

**Linux/macOS:**
```bash
./scripts/check_server.sh
```

**Windows:**
```batch
scripts\check_server.bat
```

Or manually: open `http://localhost:8000/health` in your browser.

### Stop the server

Press `Ctrl+C` in the terminal where the server is running.

## API Endpoints

### Health
- `GET /health` - API health check

### Data
- `GET /api/summary` - Data summary (rows, columns, column names)
- `GET /api/by_column?column=<column_name>` - Unique values of a column
- `GET /api/cas/list` - List of all available CAS numbers with chemical names

### Plots
- `GET /api/plot/ssd/{cas}` - SSD plot and HC20 for a chemical
  - Example: `GET /api/plot/ssd/335104-84-2`
  - Returns: Plotly figure JSON

- `GET /api/plot/ec10eq/{cas}` - EC10eq results by taxon and species
  - Example: `GET /api/plot/ec10eq/335104-84-2`
  - Returns: Plotly figure JSON

- `POST /api/plot/ssd/comparison` - Compare multiple SSD curves (max 3)
  - Body: `{"cas_list": ["CAS1", "CAS2", "CAS3"]}`
  - Returns: Plotly figure JSON

## Interactive Documentation

Once the API is running, access:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Project Structure

```
openchemfacts_backend/
├── app/
│   ├── main.py          # FastAPI application
│   ├── api.py           # API routes
│   ├── data_loader.py   # Data loading
│   └── models.py        # Pydantic models
├── data/
│   └── results_ecotox_*.parquet  # Ecotoxicology data
├── scripts/             # Utility scripts
├── tests/               # Test suite
├── Documentation/       # Detailed documentation
├── Procfile             # Scalingo configuration
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Deployment

The application can be deployed on Scalingo. For detailed deployment instructions, see `Documentation/06_Deploiement_Scalingo.md`.

Quick deployment:
```bash
git push scalingo main
```

## Environment Variables

- `ALLOWED_ORIGINS`: Allowed CORS origins (comma-separated)
  - Default: `https://openchemfacts.com,https://openchemfacts.lovable.app`

## Documentation

For detailed documentation, see the `Documentation/` folder:
- Installation and configuration: `Documentation/03_Installation_Configuration.md`
- API usage: `Documentation/04_Utilisation_API.md`
- Deployment: `Documentation/06_Deploiement_Scalingo.md`
- Development: `Documentation/05_Developpement_Local.md`

## Support

For questions or issues, consult the Scalingo documentation: https://doc.scalingo.com
