"use client";

import { useState, useEffect } from "react";
import { Product, API_BASE_URL } from "@/types";

export default function WorkingPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_BASE_URL}/products`)
      .then((res) => res.json())
      .then((data) => {
        setProducts(data);
        setError(null);
      })
      .catch((err) => {
        console.error(err);
        setError("エラーが発生しました");
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <div className="text-xl text-gray-600">読み込み中...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-xl text-red-600">{error}</div>
      </div>
    );
  }

  return (
    <main className="min-h-screen p-8 bg-gray-50">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-4">Product Gallery（画像なし版）</h1>
        <p className="text-gray-600">商品数: {products.length}</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {products.map((product) => (
          <div key={product.id} className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition">
            <h2 className="text-xl font-bold text-gray-800 mb-2">
              {product.product_name}
            </h2>

            <div className="space-y-2 text-sm text-gray-600">
              <p><strong>メーカー:</strong> {product.manufacturer}</p>
              <p><strong>容量:</strong> {product.volume}</p>
              <p><strong>価格:</strong> {product.price_info}</p>
              <p><strong>カテゴリ:</strong> {product.category}</p>
            </div>

            {product.appeals && product.appeals.length > 0 && (
              <div className="mt-4 flex gap-2 flex-wrap">
                {product.appeals.map((appeal, idx) => (
                  <span
                    key={idx}
                    className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-semibold"
                  >
                    {appeal}
                  </span>
                ))}
              </div>
            )}

            {product.nutrition && (
              <div className="mt-4 p-3 bg-gray-50 rounded text-xs">
                <p className="font-semibold mb-1">栄養成分:</p>
                <div className="grid grid-cols-2 gap-1">
                  {product.nutrition.energy && <p>エネルギー: {product.nutrition.energy}</p>}
                  {product.nutrition.protein && <p>たんぱく質: {product.nutrition.protein}</p>}
                  {product.nutrition.fat && <p>脂質: {product.nutrition.fat}</p>}
                  {product.nutrition.carbs && <p>炭水化物: {product.nutrition.carbs}</p>}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </main>
  );
}
