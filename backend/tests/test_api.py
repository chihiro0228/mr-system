import pytest
from fastapi.testclient import TestClient
import os
import sys
import time
import uuid

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database
from main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_db():
    """Setup test database before each test"""
    # Use unique database name per test to avoid locking issues
    test_db = f"test_api_{uuid.uuid4().hex[:8]}.db"
    database.DB_NAME = test_db

    database.init_db()

    yield

    # Cleanup after test with retry for Windows file locking
    for _ in range(3):
        try:
            if os.path.exists(test_db):
                os.remove(test_db)
            break
        except PermissionError:
            time.sleep(0.1)


class TestRootEndpoint:
    def test_read_root(self):
        """Test root endpoint returns welcome message"""
        response = client.get("/")

        assert response.status_code == 200
        assert response.json() == {"message": "Product Reference API"}


class TestProductsEndpoint:
    def test_get_products_empty(self):
        """Test getting products when database is empty"""
        response = client.get("/products")

        assert response.status_code == 200
        assert response.json() == []

    def test_get_products_with_data(self):
        """Test getting products after adding data"""
        # Add test product directly to database
        database.add_product({
            "product_name": "Test Product",
            "volume": "100g",
            "manufacturer": "Test Corp",
            "category": "Snack",
            "ingredients": ["A", "B"],
            "appeals": ["無添加"]
        })

        response = client.get("/products")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["product_name"] == "Test Product"


class TestProductByIdEndpoint:
    def test_get_product_by_id_found(self):
        """Test getting existing product by ID"""
        product_id = database.add_product({
            "product_name": "Find Me",
            "category": "Snack"
        })

        response = client.get(f"/products/{product_id}")

        assert response.status_code == 200
        assert response.json()["product_name"] == "Find Me"

    def test_get_product_by_id_not_found(self):
        """Test getting non-existent product returns 404"""
        response = client.get("/products/99999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestUpdateProductEndpoint:
    def test_update_product_success(self):
        """Test successful product update via API"""
        product_id = database.add_product({
            "product_name": "Original",
            "category": "Snack"
        })

        response = client.put(
            f"/products/{product_id}",
            json={
                "product_name": "Updated",
                "volume": "200g"
            }
        )

        assert response.status_code == 200
        assert response.json()["product_name"] == "Updated"
        assert response.json()["volume"] == "200g"

    def test_update_product_not_found(self):
        """Test updating non-existent product returns 404"""
        response = client.put(
            "/products/99999",
            json={"product_name": "Ghost"}
        )

        assert response.status_code == 404

    def test_update_product_category(self):
        """Test updating product category"""
        product_id = database.add_product({
            "product_name": "Test",
            "category": "Snack"
        })

        response = client.put(
            f"/products/{product_id}",
            json={"category": "Noodles"}
        )

        assert response.status_code == 200
        assert response.json()["category"] == "Noodles"


class TestDeleteProductEndpoint:
    def test_delete_product_success(self):
        """Test successful product deletion"""
        product_id = database.add_product({
            "product_name": "Delete Me",
            "category": "Snack"
        })

        response = client.delete(f"/products/{product_id}")

        assert response.status_code == 200
        assert response.json()["status"] == "deleted"

        # Verify deleted
        get_response = client.get(f"/products/{product_id}")
        assert get_response.status_code == 404

    def test_delete_product_not_found(self):
        """Test deleting non-existent product returns 404"""
        response = client.delete("/products/99999")

        assert response.status_code == 404


class TestCategoryEndpoints:
    def test_get_categories(self):
        """Test getting all categories"""
        response = client.get("/categories")

        assert response.status_code == 200
        categories = response.json()

        # Check expected categories exist
        values = [cat["value"] for cat in categories]
        assert "Snack" in values
        assert "Noodles" in values
        assert "Supplements" in values
        assert "Other" in values

    def test_get_products_by_category(self):
        """Test filtering products by category via API"""
        database.add_product({"product_name": "Snack 1", "category": "Snack"})
        database.add_product({"product_name": "Snack 2", "category": "Snack"})
        database.add_product({"product_name": "Noodle 1", "category": "Noodles"})

        response = client.get("/products/category/Snack")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(p["category"] == "Snack" for p in data)
