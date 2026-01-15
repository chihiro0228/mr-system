from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class ProductCategory(str, Enum):
    CHOCOLATE = "Chocolate"
    GUMMY = "Gummy"
    COOKIE = "Cookie"
    SNACK = "Snack"
    DONUT = "Donut"
    JELLY = "Jelly"
    NOODLE = "Noodle"
    SUPPLEMENT = "Supplement"
    BEVERAGE = "Beverage"
    PROTEIN = "Protein"
    OTHER = "Other"


class NutritionInfo(BaseModel):
    """Nutrition information"""
    energy: Optional[str] = None      # kcal
    protein: Optional[str] = None     # g
    fat: Optional[str] = None         # g
    carbs: Optional[str] = None       # g
    sugar: Optional[str] = None       # g
    fiber: Optional[str] = None       # g
    salt: Optional[str] = None        # g


class ProductImage(BaseModel):
    """Product image"""
    id: int
    image_path: str
    is_primary: bool = False
    display_order: int = 0


class ProductBase(BaseModel):
    product_name: Optional[str] = None
    volume: Optional[str] = None
    manufacturer: Optional[str] = None
    seller: Optional[str] = None  # 販売者
    ingredients: Optional[List[str]] = None
    appeals: Optional[List[str]] = None
    price_info: Optional[str] = None
    price_tax_excluded: Optional[str] = None
    product_url: Optional[str] = None  # 商品ページURL
    nutrition: Optional[NutritionInfo] = None
    category: Optional[ProductCategory] = ProductCategory.OTHER
    image_path: Optional[str] = None  # Legacy single image
    image_paths: Optional[List[str]] = None  # Multiple images


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    """Allow partial updates"""
    product_name: Optional[str] = None
    volume: Optional[str] = None
    manufacturer: Optional[str] = None
    seller: Optional[str] = None
    ingredients: Optional[List[str]] = None
    appeals: Optional[List[str]] = None
    price_info: Optional[str] = None
    price_tax_excluded: Optional[str] = None
    product_url: Optional[str] = None
    nutrition: Optional[NutritionInfo] = None
    category: Optional[ProductCategory] = None


class Product(ProductBase):
    id: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = {"from_attributes": True}


class ImageReorderRequest(BaseModel):
    """Request to reorder images"""
    image_ids: List[int]


class ProductImport(BaseModel):
    """For importing product data from local to cloud"""
    product_name: Optional[str] = None
    volume: Optional[str] = None
    manufacturer: Optional[str] = None
    seller: Optional[str] = None
    ingredients: Optional[List[str]] = None
    appeals: Optional[List[str]] = None
    price_info: Optional[str] = None
    price_tax_excluded: Optional[str] = None
    product_url: Optional[str] = None
    nutrition: Optional[NutritionInfo] = None
    category: Optional[str] = "Other"
    image_path: Optional[str] = None
