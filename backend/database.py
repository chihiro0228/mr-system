import sqlite3
import os
from typing import List, Dict, Optional

# Check if PostgreSQL is available (production)
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    import psycopg
    from psycopg.rows import dict_row
    USE_POSTGRES = True
else:
    USE_POSTGRES = False
    # Use parent directory for shared database (local development)
    DB_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DB_NAME = os.path.join(DB_DIR, "products.db")


def get_connection():
    """Get database connection based on environment"""
    if USE_POSTGRES:
        # psycopg3 can use DATABASE_URL directly
        conn = psycopg.connect(DATABASE_URL)
        return conn
    else:
        return sqlite3.connect(DB_NAME)


def init_db():
    conn = get_connection()
    c = conn.cursor()

    if USE_POSTGRES:
        # PostgreSQL schema
        c.execute('''CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            product_name TEXT,
            volume TEXT,
            manufacturer TEXT,
            seller TEXT,
            price_info TEXT,
            price_tax_excluded TEXT,
            product_url TEXT,
            image_path TEXT,
            ingredients TEXT,
            category TEXT DEFAULT 'Other',
            appeals TEXT,
            nutrition_energy TEXT,
            nutrition_protein TEXT,
            nutrition_fat TEXT,
            nutrition_carbs TEXT,
            nutrition_sugar TEXT,
            nutrition_fiber TEXT,
            nutrition_salt TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS product_images (
            id SERIAL PRIMARY KEY,
            product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
            image_path TEXT,
            is_primary BOOLEAN DEFAULT FALSE,
            display_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
    else:
        # SQLite schema
        c.execute('''CREATE TABLE IF NOT EXISTS products
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      product_name TEXT,
                      volume TEXT,
                      manufacturer TEXT,
                      price_info TEXT,
                      image_path TEXT,
                      ingredients TEXT)''')

        c.execute('''CREATE TABLE IF NOT EXISTS product_images
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      product_id INTEGER,
                      image_path TEXT,
                      is_primary BOOLEAN DEFAULT 0,
                      display_order INTEGER DEFAULT 0,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE)''')

    conn.commit()
    conn.close()

    # Run migration for SQLite
    if not USE_POSTGRES:
        migrate_db()


def migrate_db():
    """Migrate database to new schema with category, appeals, timestamps, nutrition, and tax-excluded price"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Check if migration needed
    c.execute("PRAGMA table_info(products)")
    columns = [col[1] for col in c.fetchall()]

    if 'category' not in columns:
        print("Migrating database to new schema...")

        # Create new table with enhanced schema
        c.execute('''CREATE TABLE products_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT,
            volume TEXT,
            manufacturer TEXT,
            price_info TEXT,
            image_path TEXT,
            ingredients TEXT,
            category TEXT DEFAULT 'Other',
            appeals TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

        # Copy existing data
        c.execute('''INSERT INTO products_new
                     (id, product_name, volume, manufacturer, price_info, image_path, ingredients)
                     SELECT id, product_name, volume, manufacturer, price_info, image_path, ingredients
                     FROM products''')

        # Drop old table and rename
        c.execute('DROP TABLE products')
        c.execute('ALTER TABLE products_new RENAME TO products')

        print("Migration completed successfully!")

    # Add nutrition and price_tax_excluded fields if not exist
    if 'nutrition_energy' not in columns:
        print("Adding nutrition fields...")
        try:
            c.execute('ALTER TABLE products ADD COLUMN nutrition_energy TEXT')
            c.execute('ALTER TABLE products ADD COLUMN nutrition_protein TEXT')
            c.execute('ALTER TABLE products ADD COLUMN nutrition_fat TEXT')
            c.execute('ALTER TABLE products ADD COLUMN nutrition_carbs TEXT')
            c.execute('ALTER TABLE products ADD COLUMN nutrition_sugar TEXT')
            c.execute('ALTER TABLE products ADD COLUMN nutrition_fiber TEXT')
            c.execute('ALTER TABLE products ADD COLUMN nutrition_salt TEXT')
            c.execute('ALTER TABLE products ADD COLUMN price_tax_excluded TEXT')
            print("Nutrition fields added successfully!")
        except sqlite3.OperationalError:
            pass  # Columns already exist

    # Add seller and product_url fields if not exist
    if 'seller' not in columns:
        print("Adding seller and product_url fields...")
        try:
            c.execute('ALTER TABLE products ADD COLUMN seller TEXT')
            c.execute('ALTER TABLE products ADD COLUMN product_url TEXT')
            print("Seller and product_url fields added successfully!")
        except sqlite3.OperationalError:
            pass  # Columns already exist

    conn.commit()
    conn.close()


def add_product(data: Dict) -> int:
    conn = get_connection()
    c = conn.cursor()

    # Serialize lists to strings
    ingredients_str = ",".join(data.get("ingredients", []))
    appeals_str = ",".join(data.get("appeals", []))
    category = data.get("category", "Other")

    # Get nutrition data
    nutrition = data.get("nutrition", {})

    if USE_POSTGRES:
        c.execute("""INSERT INTO products
                     (product_name, volume, manufacturer, seller, price_info, image_path, ingredients, category, appeals,
                      nutrition_energy, nutrition_protein, nutrition_fat, nutrition_carbs,
                      nutrition_sugar, nutrition_fiber, nutrition_salt, price_tax_excluded, product_url)
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                     RETURNING id""",
                  (data.get("product_name"),
                   data.get("volume"),
                   data.get("manufacturer"),
                   data.get("seller"),
                   data.get("price_info"),
                   data.get("image_path"),
                   ingredients_str,
                   category,
                   appeals_str,
                   nutrition.get("energy"),
                   nutrition.get("protein"),
                   nutrition.get("fat"),
                   nutrition.get("carbs"),
                   nutrition.get("sugar"),
                   nutrition.get("fiber"),
                   nutrition.get("salt"),
                   data.get("price_tax_excluded"),
                   data.get("product_url")))
        p_id = c.fetchone()[0]
    else:
        c.execute("""INSERT INTO products
                     (product_name, volume, manufacturer, seller, price_info, image_path, ingredients, category, appeals,
                      nutrition_energy, nutrition_protein, nutrition_fat, nutrition_carbs,
                      nutrition_sugar, nutrition_fiber, nutrition_salt, price_tax_excluded, product_url)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  (data.get("product_name"),
                   data.get("volume"),
                   data.get("manufacturer"),
                   data.get("seller"),
                   data.get("price_info"),
                   data.get("image_path"),
                   ingredients_str,
                   category,
                   appeals_str,
                   nutrition.get("energy"),
                   nutrition.get("protein"),
                   nutrition.get("fat"),
                   nutrition.get("carbs"),
                   nutrition.get("sugar"),
                   nutrition.get("fiber"),
                   nutrition.get("salt"),
                   data.get("price_tax_excluded"),
                   data.get("product_url")))
        p_id = c.lastrowid

    conn.commit()
    conn.close()
    return p_id


# ===== Product Images Functions =====

def add_product_image(product_id: int, image_path: str, is_primary: bool = False, display_order: int = 0) -> int:
    """Add image to product"""
    conn = get_connection()
    c = conn.cursor()

    if USE_POSTGRES:
        # If this is primary, unset other primaries
        if is_primary:
            c.execute("UPDATE product_images SET is_primary = FALSE WHERE product_id = %s", (product_id,))

        c.execute("""INSERT INTO product_images (product_id, image_path, is_primary, display_order)
                     VALUES (%s, %s, %s, %s) RETURNING id""",
                  (product_id, image_path, is_primary, display_order))
        image_id = c.fetchone()[0]
    else:
        # If this is primary, unset other primaries
        if is_primary:
            c.execute("UPDATE product_images SET is_primary = 0 WHERE product_id = ?", (product_id,))

        c.execute("""INSERT INTO product_images (product_id, image_path, is_primary, display_order)
                     VALUES (?, ?, ?, ?)""",
                  (product_id, image_path, is_primary, display_order))
        image_id = c.lastrowid

    conn.commit()
    conn.close()
    return image_id


def _convert_datetime_fields(row: Dict) -> Dict:
    """Convert datetime fields to ISO format strings"""
    if row.get("created_at") and hasattr(row["created_at"], "isoformat"):
        row["created_at"] = row["created_at"].isoformat()
    if row.get("updated_at") and hasattr(row["updated_at"], "isoformat"):
        row["updated_at"] = row["updated_at"].isoformat()
    return row


def get_product_images(product_id: int) -> List[Dict]:
    """Get all images for a product"""
    conn = get_connection()

    if USE_POSTGRES:
        with conn.cursor(row_factory=dict_row) as c:
            c.execute("""SELECT * FROM product_images WHERE product_id = %s
                         ORDER BY is_primary DESC, display_order ASC""", (product_id,))
            rows = [_convert_datetime_fields(dict(row)) for row in c.fetchall()]
        conn.close()
        return rows
    else:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("""SELECT * FROM product_images WHERE product_id = ?
                     ORDER BY is_primary DESC, display_order ASC""", (product_id,))
        rows = c.fetchall()
        conn.close()
        return [dict(row) for row in rows]


def delete_product_image(image_id: int) -> bool:
    """Delete a product image"""
    conn = get_connection()
    c = conn.cursor()

    if USE_POSTGRES:
        c.execute("DELETE FROM product_images WHERE id = %s", (image_id,))
        success = c.rowcount > 0
    else:
        c.execute("DELETE FROM product_images WHERE id = ?", (image_id,))
        success = c.rowcount > 0

    conn.commit()
    conn.close()
    return success


def reorder_product_images(product_id: int, image_ids: List[int]) -> bool:
    """Reorder images for a product"""
    conn = get_connection()
    c = conn.cursor()

    if USE_POSTGRES:
        for order, image_id in enumerate(image_ids):
            c.execute("UPDATE product_images SET display_order = %s, is_primary = %s WHERE id = %s AND product_id = %s",
                      (order, order == 0, image_id, product_id))
    else:
        for order, image_id in enumerate(image_ids):
            c.execute("UPDATE product_images SET display_order = ?, is_primary = ? WHERE id = ? AND product_id = ?",
                      (order, 1 if order == 0 else 0, image_id, product_id))

    conn.commit()
    conn.close()
    return True


def _parse_product(row) -> Dict:
    """Parse product row and add related data"""
    if USE_POSTGRES:
        p = dict(row)
    else:
        p = dict(row)

    # Parse comma-separated fields
    if p.get("ingredients"):
        p["ingredients"] = p["ingredients"].split(",")
    else:
        p["ingredients"] = []

    if p.get("appeals"):
        p["appeals"] = p["appeals"].split(",")
    else:
        p["appeals"] = []

    # Build nutrition object
    p["nutrition"] = {
        "energy": p.pop("nutrition_energy", None),
        "protein": p.pop("nutrition_protein", None),
        "fat": p.pop("nutrition_fat", None),
        "carbs": p.pop("nutrition_carbs", None),
        "sugar": p.pop("nutrition_sugar", None),
        "fiber": p.pop("nutrition_fiber", None),
        "salt": p.pop("nutrition_salt", None),
    }

    # Convert datetime objects to strings (PostgreSQL returns datetime objects)
    _convert_datetime_fields(p)

    # Get associated images
    images = get_product_images(p["id"])
    p["image_paths"] = [img["image_path"] for img in images]

    # Fallback to legacy image_path if no images in new table
    if not p["image_paths"] and p.get("image_path"):
        p["image_paths"] = [p["image_path"]]

    return p


def get_all_products() -> List[Dict]:
    conn = get_connection()

    if USE_POSTGRES:
        with conn.cursor(row_factory=dict_row) as c:
            c.execute("SELECT * FROM products ORDER BY created_at DESC")
            rows = [dict(row) for row in c.fetchall()]  # Convert to dicts before closing
    else:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM products ORDER BY created_at DESC")
        rows = [dict(row) for row in c.fetchall()]

    conn.close()
    products = [_parse_product(row) for row in rows]
    return products


def get_product_by_id(product_id: int) -> Optional[Dict]:
    """Get single product by ID"""
    conn = get_connection()
    row = None

    if USE_POSTGRES:
        with conn.cursor(row_factory=dict_row) as c:
            c.execute("SELECT * FROM products WHERE id = %s", (product_id,))
            result = c.fetchone()
            if result:
                row = dict(result)  # Convert to dict before closing connection
    else:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        result = c.fetchone()
        if result:
            row = dict(result)

    conn.close()

    if row:
        return _parse_product(row)
    return None


def update_product(product_id: int, data: Dict) -> bool:
    """Update existing product"""
    conn = get_connection()
    c = conn.cursor()

    # Serialize lists to strings (handle None values)
    ingredients = data.get("ingredients") or []
    appeals = data.get("appeals") or []
    ingredients_str = ",".join(ingredients) if ingredients else ""
    appeals_str = ",".join(appeals) if appeals else ""

    # Get nutrition data
    nutrition = data.get("nutrition", {}) or {}

    if USE_POSTGRES:
        c.execute("""UPDATE products SET
                     product_name=%s, volume=%s, manufacturer=%s, seller=%s, price_info=%s, price_tax_excluded=%s,
                     product_url=%s, category=%s, appeals=%s, ingredients=%s,
                     nutrition_energy=%s, nutrition_protein=%s, nutrition_fat=%s, nutrition_carbs=%s,
                     nutrition_sugar=%s, nutrition_fiber=%s, nutrition_salt=%s,
                     updated_at=CURRENT_TIMESTAMP
                     WHERE id=%s""",
                  (data.get("product_name"),
                   data.get("volume"),
                   data.get("manufacturer"),
                   data.get("seller"),
                   data.get("price_info"),
                   data.get("price_tax_excluded"),
                   data.get("product_url"),
                   data.get("category", "Other"),
                   appeals_str,
                   ingredients_str,
                   nutrition.get("energy"),
                   nutrition.get("protein"),
                   nutrition.get("fat"),
                   nutrition.get("carbs"),
                   nutrition.get("sugar"),
                   nutrition.get("fiber"),
                   nutrition.get("salt"),
                   product_id))
    else:
        c.execute("""UPDATE products SET
                     product_name=?, volume=?, manufacturer=?, seller=?, price_info=?, price_tax_excluded=?,
                     product_url=?, category=?, appeals=?, ingredients=?,
                     nutrition_energy=?, nutrition_protein=?, nutrition_fat=?, nutrition_carbs=?,
                     nutrition_sugar=?, nutrition_fiber=?, nutrition_salt=?,
                     updated_at=CURRENT_TIMESTAMP
                     WHERE id=?""",
                  (data.get("product_name"),
                   data.get("volume"),
                   data.get("manufacturer"),
                   data.get("seller"),
                   data.get("price_info"),
                   data.get("price_tax_excluded"),
                   data.get("product_url"),
                   data.get("category", "Other"),
                   appeals_str,
                   ingredients_str,
                   nutrition.get("energy"),
                   nutrition.get("protein"),
                   nutrition.get("fat"),
                   nutrition.get("carbs"),
                   nutrition.get("sugar"),
                   nutrition.get("fiber"),
                   nutrition.get("salt"),
                   product_id))

    conn.commit()
    success = c.rowcount > 0
    conn.close()
    return success


def delete_product(product_id: int) -> bool:
    """Delete product"""
    conn = get_connection()
    c = conn.cursor()

    if USE_POSTGRES:
        c.execute("DELETE FROM products WHERE id = %s", (product_id,))
    else:
        c.execute("DELETE FROM products WHERE id = ?", (product_id,))

    conn.commit()
    success = c.rowcount > 0
    conn.close()
    return success


def get_products_by_category(category: str) -> List[Dict]:
    """Get products filtered by category"""
    conn = get_connection()

    if USE_POSTGRES:
        with conn.cursor(row_factory=dict_row) as c:
            c.execute("SELECT * FROM products WHERE category = %s ORDER BY created_at DESC", (category,))
            rows = [dict(row) for row in c.fetchall()]  # Convert to dicts before closing
    else:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM products WHERE category = ? ORDER BY created_at DESC", (category,))
        rows = [dict(row) for row in c.fetchall()]

    conn.close()
    products = [_parse_product(row) for row in rows]
    return products
