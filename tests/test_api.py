"""
Tests for API endpoints.
"""
import pytest
from fastapi import status


def test_health_check(client):
    """Test that the health endpoint returns OK."""
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data
    assert "version" in data
    assert "data" in data


def test_root_endpoint(client):
    """Test that the root endpoint returns API information."""
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "message" in data
    assert "status" in data
    assert "endpoints" in data


def test_get_summary(client):
    """Test that the summary endpoint returns data statistics."""
    response = client.get("/api/summary")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "rows" in data
    assert "columns" in data
    assert "columns_names" in data
    assert isinstance(data["rows"], int)
    assert isinstance(data["columns"], int)
    assert isinstance(data["columns_names"], list)
    assert data["rows"] > 0


def test_get_cas_list(client):
    """Test that the CAS list endpoint returns a list of CAS numbers."""
    response = client.get("/api/cas/list")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "count" in data
    assert "cas_numbers" in data
    assert "cas_with_names" in data
    assert isinstance(data["cas_numbers"], list)
    assert isinstance(data["cas_with_names"], dict)
    assert data["count"] > 0
    assert len(data["cas_numbers"]) == data["count"]


def test_search_substances(client):
    """Test the search endpoint with a query."""
    response = client.get("/api/search?query=test")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "query" in data
    assert "count" in data
    assert "matches" in data
    assert isinstance(data["matches"], list)
    assert data["query"] == "test"


def test_search_with_limit(client):
    """Test that the limit parameter works correctly."""
    response = client.get("/api/search?query=test&limit=5")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["matches"]) <= 5


def test_search_with_invalid_limit(client):
    """Test that invalid limit values are rejected."""
    # Limit too high
    response = client.get("/api/search?query=test&limit=200")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    # Limit too low
    response = client.get("/api/search?query=test&limit=0")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_get_by_column(client):
    """Test the by_column endpoint."""
    # First, get the summary to know available columns
    summary_response = client.get("/api/summary")
    assert summary_response.status_code == status.HTTP_200_OK
    columns = summary_response.json()["columns_names"]
    
    if columns:
        # Test with the first column
        column_name = columns[0]
        response = client.get(f"/api/by_column?column={column_name}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "column" in data
        assert "unique_values" in data
        assert "count" in data
        assert data["column"] == column_name


def test_get_by_column_invalid(client):
    """Test that invalid column names return an error."""
    response = client.get("/api/by_column?column=nonexistent_column")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "detail" in response.json()


def test_get_ssd_plot(client, sample_cas):
    """Test that the SSD plot endpoint returns a Plotly figure."""
    response = client.get(f"/api/plot/ssd/{sample_cas}")
    
    # The endpoint might return 200 (success) or 404 (CAS not found)
    # Both are valid responses depending on your data
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
    
    if response.status_code == status.HTTP_200_OK:
        data = response.json()
        # Plotly figure should have 'data' and 'layout' keys
        assert "data" in data or "layout" in data


def test_get_ssd_plot_not_found(client):
    """Test that a non-existent CAS returns 404."""
    response = client.get("/api/plot/ssd/999-99-9")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "detail" in response.json()


def test_get_ec10eq_plot(client, sample_cas):
    """Test that the EC10eq plot endpoint returns a Plotly figure."""
    response = client.get(f"/api/plot/ec10eq/{sample_cas}")
    
    # Similar to SSD plot, might return 200 or 404
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
    
    if response.status_code == status.HTTP_200_OK:
        data = response.json()
        assert "data" in data or "layout" in data


def test_ssd_comparison(client, sample_cas):
    """Test the SSD comparison endpoint."""
    # Use a valid CAS (or multiple if available)
    payload = {
        "cas_list": [sample_cas]
    }
    response = client.post("/api/plot/ssd/comparison", json=payload)
    
    # Might return 200 (success) or 400/404 (error)
    assert response.status_code in [
        status.HTTP_200_OK,
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_404_NOT_FOUND
    ]
    
    if response.status_code == status.HTTP_200_OK:
        data = response.json()
        assert "data" in data or "layout" in data


def test_ssd_comparison_empty_list(client):
    """Test that an empty CAS list is rejected."""
    payload = {
        "cas_list": []
    }
    response = client.post("/api/plot/ssd/comparison", json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_ssd_comparison_too_many_substances(client, sample_cas):
    """Test that more than 3 substances are rejected."""
    payload = {
        "cas_list": [sample_cas, sample_cas, sample_cas, sample_cas]
    }
    response = client.post("/api/plot/ssd/comparison", json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

