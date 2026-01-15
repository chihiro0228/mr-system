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

export type ProductCategory = "Chocolate" | "Gummy" | "Cookie" | "Snack" | "Donut" | "Jelly" | "Other";

export const CATEGORIES: ProductCategory[] = ["Chocolate", "Gummy", "Cookie", "Snack", "Donut", "Jelly", "Other"];

// API Base URL: Use environment variable in production, fallback to dynamic detection for local dev
export const API_BASE_URL = (() => {
  // Server-side rendering
  if (typeof window === 'undefined') {
    return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  }
  // Client-side: Check environment variable first
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  // Fallback for local development: Use PC's IP for mobile access
  return window.location.hostname !== 'localhost'
    ? `http://${window.location.hostname}:8000`
    : "http://localhost:8000";
})();
