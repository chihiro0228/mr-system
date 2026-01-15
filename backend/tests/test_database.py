import pytest
import sqlite3
import os
import sys
import time
import uuid

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database


@pytest.fixture(autouse=True)
def setup_test_db():
    """Setup test database before each test"""
    # Use unique database name per test to avoid locking issues
    test_db = f"test_products_{uuid.uuid4().hex[:8]}.db"
    database.DB_NAME = test_db

    # Initialize fresh database
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


class TestDatabaseInit:
    def test_init_db_creates_table(self):
        """Test that init_db creates the products table"""
        conn = sqlite3.connect(database.DB_NAME)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products'")
        result = c.fetchone()
        conn.close()

        assert result is not None
        assert result[0] == "products"

    def test_init_db_has_correct_columns(self):
        """Test that products table has all required columns"""
        conn = sqlite3.connect(database.DB_NAME)
        c = conn.cursor()
        c.execute("PRAGMA table_info(products)")
        columns = [col[1] for col in c.fetchall()]
        conn.close()

        required_columns = [
            "id", "product_name", "volume", "manufacturer",
            "price_info", "image_path", "ingredients",
            "category", "appeals", "created_at", "updated_at"
        ]

        for col in required_columns:
            assert col in columns, f"Missing column: {col}"


class TestAddProduct:
    def test_add_product_returns_id(self):
        """Test that add_product returns a valid ID"""
        data = {
            "product_name": "Test Product",
            "volume": "100g",
            "manufacturer": "Test Corp",
            "ingredients": ["A", "B", "C"],
            "appeals": ["無添加"],
            "category": "Snack"
        }

        product_id = database.add_product(data)

        assert product_id is not None
        assert product_id > 0

    def test_add_product_stores_data(self):
        """Test that add_product correctly stores data"""
        data = {
            "product_name": "Test Product",
            "volume": "200ml",
            "manufacturer": "Test Corp",
            "ingredients": ["Ingredient1", "Ingredient2"],
            "appeals": ["低糖質", "高タンパク"],
            "category": "Supplements"
        }

        product_id = database.add_product(data)
        product = database.get_product_by_id(product_id)

        assert product is not None
        assert product["product_name"] == "Test Product"
        assert product["volume"] == "200ml"
        assert product["manufacturer"] == "Test Corp"
        assert product["category"] == "Supplements"
        assert "Ingredient1" in product["ingredients"]
        assert "低糖質" in product["appeals"]

    def test_add_product_with_empty_lists(self):
        """Test adding product with empty ingredients and appeals"""
        data = {
            "product_name": "Simple Product",
            "volume": "50g",
            "manufacturer": "Simple Corp",
            "ingredients": [],
            "appeals": [],
            "category": "Other"
        }

        product_id = database.add_product(data)
        product = database.get_product_by_id(product_id)

        assert product is not None
        assert product["ingredients"] == []
        assert product["appeals"] == []


class TestGetProduct:
    def test_get_product_by_id_found(self):
        """Test getting existing product by ID"""
        data = {"product_name": "Find Me", "category": "Snack"}
        product_id = database.add_product(data)

        product = database.get_product_by_id(product_id)

        assert product is not None
        assert product["product_name"] == "Find Me"

    def test_get_product_by_id_not_found(self):
        """Test getting non-existent product returns None"""
        product = database.get_product_by_id(99999)

        assert product is None

    def test_get_all_products(self):
        """Test getting all products"""
        # Add multiple products
        database.add_product({"product_name": "Product 1", "category": "Snack"})
        database.add_product({"product_name": "Product 2", "category": "Noodles"})
        database.add_product({"product_name": "Product 3", "category": "Other"})

        products = database.get_all_products()

        assert len(products) == 3

    def test_get_products_by_category(self):
        """Test filtering products by category"""
        database.add_product({"product_name": "Snack 1", "category": "Snack"})
        database.add_product({"product_name": "Snack 2", "category": "Snack"})
        database.add_product({"product_name": "Noodle 1", "category": "Noodles"})

        snacks = database.get_products_by_category("Snack")
        noodles = database.get_products_by_category("Noodles")

        assert len(snacks) == 2
        assert len(noodles) == 1


class TestUpdateProduct:
    def test_update_product_success(self):
        """Test successful product update"""
        data = {"product_name": "Original Name", "category": "Snack"}
        product_id = database.add_product(data)

        update_data = {
            "product_name": "Updated Name",
            "volume": "150g",
            "manufacturer": "New Corp",
            "price_info": "500 JPY",
            "category": "Noodles",
            "ingredients": ["New Ingredient"],
            "appeals": ["新登場"]
        }

        success = database.update_product(product_id, update_data)
        updated = database.get_product_by_id(product_id)

        assert success is True
        assert updated["product_name"] == "Updated Name"
        assert updated["volume"] == "150g"
        assert updated["category"] == "Noodles"

    def test_update_product_with_none_values(self):
        """Test updating product when ingredients/appeals are None"""
        data = {
            "product_name": "Test",
            "ingredients": ["A", "B"],
            "appeals": ["X"],
            "category": "Snack"
        }
        product_id = database.add_product(data)

        # Update with None values (simulating partial update)
        update_data = {
            "product_name": "Updated",
            "ingredients": None,
            "appeals": None,
            "category": "Snack"
        }

        success = database.update_product(product_id, update_data)
        updated = database.get_product_by_id(product_id)

        assert success is True
        assert updated["ingredients"] == []
        assert updated["appeals"] == []

    def test_update_nonexistent_product(self):
        """Test updating non-existent product returns False"""
        update_data = {"product_name": "Ghost", "category": "Other"}
        success = database.update_product(99999, update_data)

        assert success is False


class TestDeleteProduct:
    def test_delete_product_success(self):
        """Test successful product deletion"""
        data = {"product_name": "Delete Me", "category": "Snack"}
        product_id = database.add_product(data)

        success = database.delete_product(product_id)
        deleted = database.get_product_by_id(product_id)

        assert success is True
        assert deleted is None

    def test_delete_nonexistent_product(self):
        """Test deleting non-existent product returns False"""
        success = database.delete_product(99999)

        assert success is False
