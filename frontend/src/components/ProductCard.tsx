"use client";

import Link from "next/link";
import { Product, API_BASE_URL } from "@/types";

interface ProductCardProps {
  product: Product;
}

// Cloudinary画像を最適化（サムネイル生成）
function getOptimizedImageUrl(url: string | undefined, width: number = 400): string {
  if (!url) return "";

  // Cloudinary URLの場合、変換パラメータを追加
  if (url.includes("res.cloudinary.com") && url.includes("/upload/")) {
    // /upload/ の後に変換パラメータを挿入
    return url.replace(
      "/upload/",
      `/upload/w_${width},q_auto,f_auto/`
    );
  }

  return url.startsWith("http") ? url : `${API_BASE_URL}${url}`;
}

export default function ProductCard({ product }: ProductCardProps) {
  const imageUrl = getOptimizedImageUrl(product.image_path, 400);

  const appealsArray = Array.isArray(product.appeals)
    ? product.appeals.slice(0, 2)
    : [];

  return (
    <Link href={`/products/${product.id}`}>
      <div className="bg-white rounded-xl shadow-lg overflow-hidden cursor-pointer group transition hover:shadow-xl">
        <div className="relative aspect-square overflow-hidden bg-gray-100">
          {/* Using regular img tag instead of Next.js Image to avoid loading issues */}
          <img
            src={imageUrl}
            alt={product.product_name || "Product image"}
            className="w-full h-full object-cover group-hover:scale-105 transition duration-300"
            loading="lazy"
            decoding="async"
            onError={(e) => {
              // Fallback if image fails to load
              e.currentTarget.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='400'%3E%3Crect width='400' height='400' fill='%23f3f4f6'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' font-family='sans-serif' font-size='24' fill='%239ca3af'%3ENo Image%3C/text%3E%3C/svg%3E";
            }}
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
            <div className="absolute bottom-4 left-4 right-4 text-white">
              <h3 className="font-bold text-lg truncate">
                {product.product_name || "Unknown Product"}
              </h3>
              <p className="text-sm opacity-90">
                {product.manufacturer || "Unknown Manufacturer"}
              </p>
              <p className="text-sm font-semibold mt-1">
                {product.price_info || "Price TBD"}
              </p>
              {appealsArray.length > 0 && (
                <div className="flex gap-1 mt-2 flex-wrap">
                  {appealsArray.map((appeal, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-0.5 bg-white/20 rounded text-xs"
                    >
                      {appeal}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
          <div className="absolute top-2 right-2 bg-blue-600 text-white text-xs px-2 py-1 rounded">
            {product.category || "Other"}
          </div>
        </div>
      </div>
    </Link>
  );
}
