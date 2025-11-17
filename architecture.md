# Architecture du Backend OpenChemFacts

## Vue d'ensemble

```mermaid
graph TB
    FE[Frontend] -->|HTTP| API[FastAPI<br/>/api/*]
    API --> LOADER[data_loader.py<br/>@lru_cache]
    API --> PLOT[plotting_functions.py]
    LOADER --> DATA[(Parquet<br/>results_ecotox_*.parquet)]
    PLOT --> DATA
    PLOT -->|Plotly JSON| API
    API -->|JSON| FE
    
    style API fill:#4A90E2,color:#fff
    style PLOT fill:#FF6B6B,color:#fff
    style DATA fill:#FFD93D,color:#000
```

## Endpoints API

| Méthode | Endpoint | Description | Réponse |
|---------|----------|-------------|---------|
| `GET` | `/health` | Santé de l'API | `{"status": "ok"}` |
| `GET` | `/api/summary` | Résumé des données | `{rows, columns, columns_names}` |
| `GET` | `/api/by_column?column=X` | Valeurs uniques d'une colonne | `{column, unique_values, count}` |
| `GET` | `/api/cas/list` | Liste des CAS disponibles | `{count, cas_numbers, cas_with_names}` |
| `GET` | `/api/plot/ssd/{cas}` | Graphique SSD + HC20 | Plotly figure JSON |
| `GET` | `/api/plot/ec10eq/{cas}` | Graphique EC10eq par taxon/espèce | Plotly figure JSON |
| `POST` | `/api/plot/ssd/comparison` | Comparaison SSD (max 3) | Plotly figure JSON |

**Body pour POST `/api/plot/ssd/comparison`:**
```json
{"cas_list": ["CAS1", "CAS2", "CAS3"]}
```

## Utilisation Frontend

### CORS
- Origines: `ALLOWED_ORIGINS` (défaut: `https://openchemfacts.com,https://openchemfacts.lovable.app`)
- Méthodes/Headers: Tous autorisés

### Affichage des graphiques Plotly

**Streamlit:**
```python
import plotly.graph_objects as go
fig_dict = requests.get(f"{API_URL}/api/plot/ssd/{cas}").json()
st.plotly_chart(go.Figure(fig_dict))
```

**JavaScript:**
```javascript
const figJson = await fetch(`${API_URL}/api/plot/ssd/${cas}`).then(r => r.json());
Plotly.newPlot('plot-div', figJson.data, figJson.layout);
```

### Codes d'erreur
- `404`: CAS non trouvé
- `400`: Paramètres invalides
- `500`: Erreur serveur
- `503`: Fonctions non disponibles

