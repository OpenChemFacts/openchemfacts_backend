# OpenChemFacts Backend API

Backend API for the OpenChemFacts platform - an open-data platform dedicated to the assessment of chemicals' ecotoxicity.

## Architecture

The project follows a modular FastAPI architecture:

```
openchemfacts_backend/
├── app/                    # Main application code
│   ├── main.py            # FastAPI application setup and configuration
│   ├── api.py             # API routes and endpoints
│   ├── config.py          # Configuration settings (CORS, API settings)
│   ├── data_loader.py     # Data loading utilities
│   ├── models.py          # Pydantic models for request/response validation
│   ├── security.py        # Security and rate limiting
│   └── middleware.py      # Custom middleware (security headers, request size limits)
├── data/                   # Data files and processing scripts
│   ├── graph/             # Data visualization and processing modules
│   │   ├── EC10 details/  # EC10eq data processing
│   │   ├── SSD/           # Species Sensitivity Distribution processing
│   │   └── SSD comparison/# Comparison data processing
│   └── *.parquet          # Data files (ecotoxicology datasets)
├── Documentation/         # Gitbook documentation
├── scripts/               # Utility scripts (deployment, testing, local development)
├── tests/                 # Test suite
└── requirements.txt       # Python dependencies
```

### Key Components

- **FastAPI Application** (`app/main.py`): Main application instance with CORS, security middleware, and route registration
- **API Routes** (`app/api.py`): RESTful endpoints for data access (summary, search, CAS list, SSD data, EC10eq data, comparisons)
- **Data Layer** (`app/data_loader.py`): Handles loading and caching of parquet data files
- **Security** (`app/security.py`, `app/middleware.py`): Rate limiting, security headers, and request validation
- **Configuration** (`app/config.py`): Centralized configuration management

## License

This OpenChemFacts database is made available under the **Open Database License**: http://opendatacommons.org/licenses/odbl/1.0/

Any rights in individual contents of the database are licensed under the **Database Contents License**: http://opendatacommons.org/licenses/dbcl/1.0/

See `LICENSE_ODBL.txt` and `LICENSE_DBCL.txt` for full license text.
