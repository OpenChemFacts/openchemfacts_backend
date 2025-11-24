# API EC10eq - Documentation

Ce document décrit l'utilisation de l'API backend et du frontend pour visualiser les données EC10eq par groupe trophique et espèce.

## Fichiers

1. **`api_ec10eq_backend.py`** - API FastAPI pour exposer les données EC10eq
2. **`frontend_ec10eq_plot.js`** - Bibliothèque JavaScript pour afficher les graphiques
3. **`frontend_ec10eq_example.html`** - Exemple d'utilisation du frontend

## Installation Backend

### Dépendances

```bash
pip install fastapi uvicorn polars plotly numpy
```

### Lancement du serveur

```bash
# Développement
uvicorn api_ec10eq_backend:app --host 0.0.0.0 --port 8000 --reload

# Production
uvicorn api_ec10eq_backend:app --host 0.0.0.0 --port $PORT
```

L'API sera accessible à :
- Documentation interactive : `http://localhost:8000/docs`
- Documentation alternative : `http://localhost:8000/redoc`
- Endpoint racine : `http://localhost:8000/`

## Endpoints API

### 1. GET `/ec10eq/data`

Récupère les données EC10eq pour un CAS donné.

**Paramètres :**
- `cas` (requis) : Numéro CAS (ex: `60-51-5`)
- `format` (optionnel) : `detailed` (défaut) ou `simple`

**Exemple :**
```bash
curl "http://localhost:8000/ec10eq/data?cas=60-51-5"
```

**Réponse (format detailed) :**
```json
{
  "cas": "60-51-5",
  "chemical_name": "O,O-Dimethyl S-[2-(methylamino)-2-oxoethyl]phosphorodithioic acid ester",
  "trophic_groups": {
    "algae": {
      "Green Algae": [
        {
          "EC10eq": 0.3,
          "test_id": 123456,
          "year": 2016,
          "author": "Author Name"
        }
      ]
    }
  }
}
```

### 2. GET `/ec10eq/stats`

Récupère les statistiques pour un CAS donné.

**Paramètres :**
- `cas` (requis) : Numéro CAS

**Exemple :**
```bash
curl "http://localhost:8000/ec10eq/stats?cas=60-51-5"
```

**Réponse :**
```json
{
  "cas": "60-51-5",
  "chemical_name": "...",
  "total_endpoints": 220,
  "trophic_groups": {
    "count": 6,
    "list": ["algae", "amphibians", "crustaceans", "fish", "insects", "molluscs"]
  },
  "species": {
    "count": 41,
    "list": ["..."]
  },
  "ec10eq": {
    "min": 0.01,
    "max": 100.0,
    "mean": 5.5,
    "median": 2.3
  }
}
```

### 3. GET `/ec10eq/plot/json`

Génère un graphique Plotly et le retourne en JSON.

**Paramètres :**
- `cas` (requis) : Numéro CAS
- `color_by` (optionnel) : `trophic_group` (défaut), `year`, ou `author`

**Exemple :**
```bash
curl "http://localhost:8000/ec10eq/plot/json?cas=60-51-5&color_by=trophic_group"
```

**Réponse :**
Structure JSON complète du graphique Plotly (compatible avec Plotly.js).

## Utilisation Frontend

### Méthode 1 : Utilisation directe avec Plotly.js

```html
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</head>
<body>
    <div id="plot-container"></div>
    <script>
        async function loadPlot() {
            const response = await fetch('/ec10eq/plot/json?cas=60-51-5');
            const plotData = await response.json();
            Plotly.newPlot('plot-container', plotData.data, plotData.layout);
        }
        loadPlot();
    </script>
</body>
</html>
```

### Méthode 2 : Utilisation avec la bibliothèque frontend

```html
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="frontend_ec10eq_plot.js"></script>
</head>
<body>
    <div id="plot-container"></div>
    <script>
        // Charger le graphique
        EC10eqPlotter.renderPlot('plot-container', '60-51-5', {
            colorBy: 'trophic_group',
            apiBaseUrl: 'http://localhost:8000'
        });
        
        // Ou récupérer les statistiques
        EC10eqPlotter.fetchStats('60-51-5', 'http://localhost:8000')
            .then(stats => console.log(stats));
    </script>
</body>
</html>
```

### Méthode 3 : Utiliser l'exemple HTML

Ouvrez simplement `frontend_ec10eq_example.html` dans un navigateur (après avoir démarré le serveur backend).

## API Frontend JavaScript

### `EC10eqPlotter.renderPlot(containerId, casNumber, options)`

Affiche un graphique dans un conteneur HTML.

**Paramètres :**
- `containerId` (string) : ID de l'élément HTML
- `casNumber` (string) : Numéro CAS
- `options` (object, optionnel) :
  - `colorBy` : `'trophic_group'`, `'year'`, ou `'author'`
  - `apiBaseUrl` : URL de base de l'API

**Exemple :**
```javascript
EC10eqPlotter.renderPlot('my-plot', '60-51-5', {
    colorBy: 'year',
    apiBaseUrl: 'http://localhost:8000'
});
```

### `EC10eqPlotter.fetchData(casNumber, format, apiBaseUrl)`

Récupère les données brutes.

**Exemple :**
```javascript
const data = await EC10eqPlotter.fetchData('60-51-5', 'detailed', 'http://localhost:8000');
```

### `EC10eqPlotter.fetchStats(casNumber, apiBaseUrl)`

Récupère les statistiques.

**Exemple :**
```javascript
const stats = await EC10eqPlotter.fetchStats('60-51-5', 'http://localhost:8000');
```

### `EC10eqPlotter.updatePlot(containerId, casNumber, options)`

Met à jour un graphique existant.

**Exemple :**
```javascript
EC10eqPlotter.updatePlot('my-plot', '60-51-5', { colorBy: 'author' });
```

## Configuration

### Variables d'environnement

- `EC10EQ_DATA_PATH` : Chemin vers le fichier parquet (défaut: `results_ecotox_EC10_list_per_species.parquet`)
- `PORT` : Port du serveur (défaut: 8000)

### CORS

Par défaut, CORS est configuré pour autoriser toutes les origines (`*`). En production, modifiez `allow_origins` dans `api_ec10eq_backend.py` pour spécifier les domaines autorisés.

## Exemples d'utilisation

### Python (requests)

```python
import requests

# Récupérer les données
response = requests.get('http://localhost:8000/ec10eq/data?cas=60-51-5')
data = response.json()

# Récupérer le graphique
response = requests.get('http://localhost:8000/ec10eq/plot/json?cas=60-51-5')
plot_data = response.json()
```

### JavaScript (fetch)

```javascript
// Récupérer les données
const data = await fetch('http://localhost:8000/ec10eq/data?cas=60-51-5')
    .then(res => res.json());

// Récupérer le graphique
const plotData = await fetch('http://localhost:8000/ec10eq/plot/json?cas=60-51-5')
    .then(res => res.json());
Plotly.newPlot('container', plotData.data, plotData.layout);
```

## Déploiement

### Scalingo

Ajoutez dans `Procfile` :
```
web: uvicorn api_ec10eq_backend:app --host 0.0.0.0 --port $PORT
```

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "api_ec10eq_backend:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Support

Pour toute question ou problème, consultez la documentation interactive de l'API à `/docs` une fois le serveur démarré.

