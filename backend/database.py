import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Optional
import os

# Get database URL from environment
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_connection():
    """Get database connection"""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def init_db():
    """Initialize database - tables are created in Supabase"""
    # Tables are already created in Supabase via SQL Editor
    # This function now just verifies connection
    try:
        conn = get_connection()
        conn.close()
        print("Database connection successful!")
    except Exception as e:
        print(f"Database connection error: {e}")
        raise

def add_product(data: Dict) -> int:
    conn = get_connection()
    c = conn.cursor()

    # Serialize lists to strings
    ingredients_str = ",".join(data.get("ingredients", []))
    appeals_str = ",".join(data.get("appeals", []))
    category = data.get("category", "Other")

    # Get nutrition data
    nutrition = data.get("nutrition", {})

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

    p_id = c.fetchone()["id"]
    conn.commit()
    conn.close()
    return p_id


# ===== Product Images Functions =====

def add_product_image(product_id: int, image_path: str, is_primary: bool = False, display_order: int = 0) -> int:
    """Add image to product"""
    conn = get_connection()
    c = conn.cursor()

    # If this is primary, unset other primaries
    if is_primary:
        c.execute("UPDATE product_images SET is_primary = false WHERE product_id = %s", (product_id,))

    c.execute("""INSERT INTO product_images (product_id, image_path, is_primary, display_order)
                 VALUES (%s, %s, %s, %s) RETURNING id""",
              (product_id, image_path, is_primary, display_order))

    image_id = c.fetchone()["id"]
    conn.commit()
    conn.close()
    return image_id


def get_product_images(product_id: int) -> List[Dict]:
    """Get all images for a product"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""SELECT * FROM product_images WHERE product_id = %s
                 ORDER BY is_primary DESC, display_order ASC""", (product_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_product_image(image_id: int) -> bool:
    """Delete a product image"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM product_images WHERE id = %s", (image_id,))
    conn.commit()
    success = c.rowcount > 0
    conn.close()
    return success


def reorder_product_images(product_id: int, image_ids: List[int]) -> bool:
    """Reorder images for a product"""
    conn = get_connection()
    c = conn.cursor()
    for order, image_id in enumerate(image_ids):
        c.execute("UPDATE product_images SET display_order = %s, is_primary = %s WHERE id = %s AND product_id = %s",
                  (order, order == 0, image_id, product_id))
    conn.commit()
    conn.close()
    return True

def _parse_product(row: Dict) -> Dict:
    """Parse product row and add related data"""
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

    # Get associated images
    images = get_product_images(p["id"])
    p["image_paths"] = [img["image_path"] for img in images]

    # Fallback to legacy image_path if no images in new table
    if not p["image_paths"] and p.get("image_path"):
        p["image_paths"] = [p["image_path"]]

    return p


def get_all_products() -> List[Dict]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM products ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()

    products = [_parse_product(dict(row)) for row in rows]
    return products

def get_product_by_id(product_id: int) -> Optional[Dict]:
    """Get single product by ID"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    row = c.fetchone()
    conn.close()

    if row:
        return _parse_product(dict(row))
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

    conn.commit()
    success = c.rowcount > 0
    conn.close()
    return success

def delete_product(product_id: int) -> bool:
    """Delete product"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM products WHERE id = %s", (product_id,))
    conn.commit()
    success = c.rowcount > 0
    conn.close()
    return success

def get_products_by_category(category: str) -> List[Dict]:
    """Get products filtered by category"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM products WHERE category = %s ORDER BY id DESC", (category,))
    rows = c.fetchall()
    conn.close()

    products = [_parse_product(dict(row)) for row in rows]
    return products
