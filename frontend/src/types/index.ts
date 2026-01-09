export interface NutritionInfo {
  energy?: string;
  protein?: string;
  fat?: string;
  carbs?: string;
  sugar?: string;
  fiber?: string;
  salt?: string;
}

export interface Product {
  id: number;
  product_name: string;
  volume: string;
  manufacturer: string;
  seller?: string;  // 販売者
  ingredients: string[];
  appeals: string[];
  price_info: string;
  price_tax_excluded?: string;
  product_url?: string;  // 商品ページURL
  category: string;
  image_path: string;
  image_paths?: string[];
  nutrition?: NutritionInfo;
  created_at?: string;
  updated_at?: string;
}

export interface Category {
  value: string;
  label: string;
}

export type ProductCategory = "グミ" | "サプリメント" | "Snack" | "Noodles" | "Other";

export const CATEGORIES: ProductCategory[] = ["グミ", "サプリメント", "Snack", "Noodles", "Other"];

// Use PC's IP for mobile access, localhost for desktop
export const API_BASE_URL = typeof window !== 'undefined' && window.location.hostname !== 'localhost'
  ? `http://${window.location.hostname}:8000`
  : "http://localhost:8000";
