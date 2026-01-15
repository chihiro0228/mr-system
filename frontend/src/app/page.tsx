"use client";

import { useState, useEffect, useMemo } from "react";
import axios from "axios";
import ProductCard from "@/components/ProductCard";
import UploadModal from "@/components/UploadModal";
import SearchBar from "@/components/SearchBar";
import { Toast, useToast } from "@/components/Toast";
import { Product, Category, API_BASE_URL } from "@/types";

export default function Home() {
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>("All");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { toast, showToast, hideToast } = useToast();

  useEffect(() => {
    fetchInitialData();
  }, []);

  const fetchInitialData = async () => {
    try {
      const [productsRes, categoriesRes] = await Promise.all([
        axios.get<Product[]>(`${API_BASE_URL}/products`),
        axios.get<Category[]>(`${API_BASE_URL}/categories`)
      ]);

      setProducts(productsRes.data);
      setCategories([{ value: "All", label: "All" }, ...categoriesRes.data]);
      setError(null);
    } catch (err) {
      console.error(err);
      setError("データの読み込みに失敗しました");
      showToast("データの読み込みに失敗しました", "error");
    } finally {
      setLoading(false);
    }
  };

  const filteredProducts = useMemo(() => {
    let result = products;

    if (selectedCategory !== "All") {
      result = result.filter(p => p.category === selectedCategory);
    }

    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      result = result.filter(p =>
        p.product_name?.toLowerCase().includes(query) ||
        p.manufacturer?.toLowerCase().includes(query) ||
        p.appeals?.some(a => a.toLowerCase().includes(query))
      );
    }

    return result;
  }, [products, selectedCategory, searchQuery]);

  const handleUploadSuccess = (newProduct: Product) => {
    setProducts((prev) => [...prev, newProduct]);
    showToast("商品を追加しました", "success");
  };

  const handleSearch = (query: string) => {
    setSearchQuery(query);
  };

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

  if (error && products.length === 0) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50">
        <div className="text-xl text-red-600 mb-4">{error}</div>
        <button
          onClick={fetchInitialData}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          再試行
        </button>
      </div>
    );
  }

  return (
    <main className="min-h-screen p-8 bg-gray-50">
      <header className="mb-8">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-800">Product Gallery</h1>
          <button
            onClick={() => setIsModalOpen(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition shadow-lg flex items-center gap-2"
          >
            <span>+</span>
            <span>新規アップロード</span>
          </button>
        </div>

        <div className="mb-4">
          <SearchBar onSearch={handleSearch} />
        </div>

        <div className="flex gap-2 flex-wrap">
          {categories.map((cat) => (
            <button
              key={cat.value}
              onClick={() => setSelectedCategory(cat.value)}
              className={`px-4 py-2 rounded-lg transition ${
                selectedCategory === cat.value
                  ? "bg-blue-600 text-white"
                  : "bg-white text-gray-700 hover:bg-gray-100 border border-gray-300"
              }`}
            >
              {cat.label}
              {cat.value !== "All" && (
                <span className="ml-2 text-xs opacity-75">
                  ({products.filter(p => p.category === cat.value).length})
                </span>
              )}
            </button>
          ))}
        </div>
      </header>

      <div className="mb-6 text-sm text-gray-600">
        表示中: {filteredProducts.length} / {products.length} 商品
        {searchQuery && (
          <span className="ml-2 text-blue-600">
            (検索: "{searchQuery}")
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
        {filteredProducts.map((p) => (
          <ProductCard key={p.id} product={p} />
        ))}
        {filteredProducts.length === 0 && (
          <div className="col-span-full text-center text-gray-400 py-20">
            {products.length === 0
              ? "商品がありません。アップロードしてください。"
              : searchQuery
                ? `"${searchQuery}" に一致する商品がありません。`
                : `${selectedCategory} カテゴリーの商品がありません。`
            }
          </div>
        )}
      </div>

      {isModalOpen && (
        <UploadModal
          onClose={() => setIsModalOpen(false)}
          onUploadSuccess={handleUploadSuccess}
        />
      )}

      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={hideToast}
        />
      )}
    </main>
  );
}
