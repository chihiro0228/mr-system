from dotenv import load_dotenv
load_dotenv()  # Load .env file before other imports

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import shutil
import os
from typing import List
import schemas
import database
from services import searcher
from services.gemini_extractor import extract_with_gemini
from services.image_uploader import get_image_url, USE_CLOUDINARY

# Create uploads directory (for local development or temporary storage)
PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(PARENT_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# CORS configuration from environment
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "*").split(",")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    database.init_db()
    yield
    # Shutdown (cleanup if needed)


app = FastAPI(lifespan=lifespan, debug=os.environ.get("DEBUG", "false").lower() == "true")

# Configure CORS
if ALLOWED_ORIGINS == ["*"]:
    # Development mode - allow all origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # Production mode - restrict to specific origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

# Mount static files only for local development
if not USE_CLOUDINARY:
    app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.get("/")
def read_root():
    return {"message": "Product Reference API", "cloudinary": USE_CLOUDINARY}

@app.get("/test")
def test_endpoint():
    return {"status": "ok", "data": [{"id": 1}]}


@app.post("/upload", response_model=schemas.Product)
async def upload_images(files: List[UploadFile] = File(...)):
    """
    Upload multiple images for a single product.
    First image is set as primary.
    """
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")

        # Save all uploaded files
        saved_paths = []
        image_urls = []

        for file in files:
            # Save to local storage first (needed for Gemini processing)
            file_location = f"{UPLOAD_DIR}/{file.filename}"
            with open(file_location, "wb+") as file_object:
                shutil.copyfileobj(file.file, file_object)
            saved_paths.append(file_location)

            # Get the final URL (Cloudinary or local)
            image_url = get_image_url(file_location, file.filename)
            image_urls.append(image_url)

        # 1. Extract Data from images using Gemini
        extracted_data = extract_with_gemini(saved_paths)

        # Set first image as legacy image_path for backward compatibility
        extracted_data["image_path"] = image_urls[0] if image_urls else None

        # 2. Search for prices and product URL
        product_name = extracted_data.get("product_name", "")
        manufacturer = extracted_data.get("manufacturer", "")
        product_info = searcher.find_all_product_info(product_name, manufacturer)
        extracted_data["price_info"] = product_info.get("price_info", "Price not found")
        extracted_data["price_tax_excluded"] = product_info.get("price_tax_excluded")
        extracted_data["product_url"] = product_info.get("product_url")

        # 3. Save product to DB
        p_id = database.add_product(extracted_data)

        # 4. Save images to product_images table
        for i, image_url in enumerate(image_urls):
            database.add_product_image(
                product_id=p_id,
                image_path=image_url,
                is_primary=(i == 0),
                display_order=i
            )

        # Clean up local files if using Cloudinary
        if USE_CLOUDINARY:
            for path in saved_paths:
                try:
                    os.remove(path)
                except:
                    pass

        # Return complete product
        return database.get_product_by_id(p_id)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/products")
def get_products():
    """Get all products"""
    try:
        products = database.get_all_products()
        print(f"DEBUG: Fetched {len(products)} products from database")
        return products
    except Exception as e:
        print(f"ERROR in get_products: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/products/{product_id}", response_model=schemas.Product)
def get_product(product_id: int):
    """Get single product by ID"""
    product = database.get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.put("/products/{product_id}", response_model=schemas.Product)
def update_product(product_id: int, product_update: schemas.ProductUpdate):
    """Update product"""
    # Get existing product
    existing = database.get_product_by_id(product_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Product not found")

    # Merge updates
    update_data = product_update.model_dump(exclude_unset=True)
    merged = {**existing, **update_data}

    # Convert category enum to string if present
    if "category" in merged and hasattr(merged["category"], "value"):
        merged["category"] = merged["category"].value

    # Update in database
    success = database.update_product(product_id, merged)
    if not success:
        raise HTTPException(status_code=500, detail="Update failed")

    return database.get_product_by_id(product_id)

@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    """Delete product"""
    success = database.delete_product(product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"status": "deleted", "id": product_id}

@app.get("/products/category/{category}", response_model=List[schemas.Product])
def get_products_by_category(category: schemas.ProductCategory):
    """Get products filtered by category"""
    return database.get_products_by_category(category.value)

@app.get("/categories")
def get_categories():
    """Get all available categories"""
    return [{"value": cat.value, "label": cat.value} for cat in schemas.ProductCategory]


# ===== Data Migration Endpoint =====

@app.post("/products/import")
def import_product(product_data: schemas.ProductImport):
    """Import product data (for migration from local to cloud)"""
    try:
        data = product_data.model_dump()
        p_id = database.add_product(data)
        return {"status": "imported", "id": p_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== Image Management Endpoints =====

@app.post("/products/{product_id}/images")
async def add_product_images(product_id: int, files: List[UploadFile] = File(...)):
    """Add images to existing product"""
    # Check product exists
    product = database.get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    try:
        added_images = []
        existing_images = database.get_product_images(product_id)
        next_order = len(existing_images)

        for i, file in enumerate(files):
            # Save to local storage first
            file_location = f"{UPLOAD_DIR}/{file.filename}"
            with open(file_location, "wb+") as file_object:
                shutil.copyfileobj(file.file, file_object)

            # Get the final URL
            image_url = get_image_url(file_location, file.filename)

            image_id = database.add_product_image(
                product_id=product_id,
                image_path=image_url,
                is_primary=False,
                display_order=next_order + i
            )
            added_images.append({"id": image_id, "image_path": image_url})

            # Clean up local file if using Cloudinary
            if USE_CLOUDINARY:
                try:
                    os.remove(file_location)
                except:
                    pass

        return {"added": added_images}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/products/{product_id}/images/{image_id}")
def delete_product_image(product_id: int, image_id: int):
    """Delete an image from a product"""
    # Verify the image belongs to the product
    images = database.get_product_images(product_id)
    if not any(img["id"] == image_id for img in images):
        raise HTTPException(status_code=404, detail="Image not found for this product")

    success = database.delete_product_image(image_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete image")

    return {"status": "deleted", "image_id": image_id}


@app.put("/products/{product_id}/images/reorder")
def reorder_product_images(product_id: int, request: schemas.ImageReorderRequest):
    """Reorder images for a product"""
    # Verify product exists
    product = database.get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    success = database.reorder_product_images(product_id, request.image_ids)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to reorder images")

    return {"status": "reordered", "order": request.image_ids}


@app.get("/products/{product_id}/images")
def get_product_images_endpoint(product_id: int):
    """Get all images for a product"""
    product = database.get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    images = database.get_product_images(product_id)
    return images
