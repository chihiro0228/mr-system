"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";
import { Toast, useToast } from "@/components/Toast";
import ImageGallery from "@/components/ImageGallery";
import { Product, API_BASE_URL, CATEGORIES } from "@/types";

export default function ProductDetailPage({ params }: { params: { id: string } }) {
  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const router = useRouter();
  const { toast, showToast, hideToast } = useToast();

  useEffect(() => {
    fetchProduct();
  }, [params.id]);

  const fetchProduct = async () => {
    try {
      const res = await axios.get<Product>(`${API_BASE_URL}/products/${params.id}`);
      setProduct(res.data);
      setError(null);
    } catch (err: unknown) {
      if (axios.isAxiosError(err) && err.response?.status === 404) {
        setError("商品が見つかりません");
      } else {
        setError("商品の読み込みに失敗しました");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm("この商品を削除しますか？")) return;

    setIsDeleting(true);
    try {
      await axios.delete(`${API_BASE_URL}/products/${params.id}`);
      showToast("商品を削除しました", "success");
      setTimeout(() => router.push("/"), 1000);
    } catch (err) {
      showToast("削除に失敗しました", "error");
      setIsDeleting(false);
    }
  };

  const handleUpdateSuccess = () => {
    fetchProduct();
    setIsEditing(false);
    showToast("商品情報を更新しました", "success");
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

  if (error || !product) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50">
        <div className="text-xl text-red-600 mb-4">{error}</div>
        <button
          onClick={() => router.push("/")}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg"
        >
          ギャラリーに戻る
        </button>
      </div>
    );
  }

  // Use image_paths if available, otherwise fallback to single image_path
  const productImages = product.image_paths && product.image_paths.length > 0
    ? product.image_paths
    : product.image_path
      ? [product.image_path]
      : [];

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto mb-6">
        <button
          onClick={() => router.push("/")}
          className="text-blue-600 hover:text-blue-700 flex items-center gap-2"
        >
          ← ギャラリーに戻る
        </button>
      </div>

      <div className="max-w-6xl mx-auto bg-white rounded-xl shadow-lg overflow-hidden">
        <div className="grid md:grid-cols-2 gap-8 p-8">
          {/* Image Gallery */}
          <ImageGallery
            images={productImages}
            productName={product.product_name}
          />

          <div className="flex flex-col">
            <div className="mb-4">
              <span className="inline-block px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-semibold">
                {product.category}
              </span>
            </div>

            <h1 className="text-3xl font-bold text-gray-800 mb-2">
              {product.product_name}
            </h1>

            <p className="text-lg text-gray-600 mb-2">
              製造者: {product.manufacturer}
            </p>

            {product.seller && (
              <p className="text-lg text-gray-600 mb-4">
                販売者: {product.seller}
              </p>
            )}

            {/* Price Section */}
            <div className="mb-6 bg-gray-50 rounded-lg p-4">
              <div className="flex items-baseline gap-4">
                <div>
                  <div className="text-sm text-gray-500 mb-1">価格</div>
                  <div className="text-2xl font-bold text-green-600">
                    {product.price_info}
                  </div>
                </div>
                {product.price_tax_excluded && (
                  <div>
                    <div className="text-sm text-gray-500 mb-1">税抜価格</div>
                    <div className="text-lg text-gray-700">
                      {product.price_tax_excluded}
                    </div>
                  </div>
                )}
              </div>
              {product.product_url && (
                <a
                  href={product.product_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-3 inline-flex items-center gap-1 text-blue-600 hover:text-blue-800 text-sm"
                >
                  商品ページを見る →
                </a>
              )}
            </div>

            <div className="mb-6">
              <div className="text-sm text-gray-500 mb-1">内容量</div>
              <div className="text-lg text-gray-800">{product.volume}</div>
            </div>

            {product.appeals && product.appeals.length > 0 && (
              <div className="mb-6">
                <div className="text-sm text-gray-500 mb-2">訴求ポイント</div>
                <div className="flex flex-wrap gap-2">
                  {product.appeals.map((appeal, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm"
                    >
                      {appeal}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Nutrition Info */}
            {product.nutrition && Object.values(product.nutrition).some(v => v) && (
              <div className="mb-6">
                <div className="text-sm text-gray-500 mb-2">栄養成分</div>
                <div className="bg-gray-50 rounded-lg p-4 grid grid-cols-2 gap-2 text-sm">
                  {product.nutrition.energy && (
                    <div><span className="text-gray-500">エネルギー:</span> {product.nutrition.energy}</div>
                  )}
                  {product.nutrition.protein && (
                    <div><span className="text-gray-500">タンパク質:</span> {product.nutrition.protein}</div>
                  )}
                  {product.nutrition.fat && (
                    <div><span className="text-gray-500">脂質:</span> {product.nutrition.fat}</div>
                  )}
                  {product.nutrition.carbs && (
                    <div><span className="text-gray-500">炭水化物:</span> {product.nutrition.carbs}</div>
                  )}
                  {product.nutrition.sugar && (
                    <div><span className="text-gray-500">糖質:</span> {product.nutrition.sugar}</div>
                  )}
                  {product.nutrition.fiber && (
                    <div><span className="text-gray-500">食物繊維:</span> {product.nutrition.fiber}</div>
                  )}
                  {product.nutrition.salt && (
                    <div><span className="text-gray-500">食塩相当量:</span> {product.nutrition.salt}</div>
                  )}
                </div>
              </div>
            )}

            {product.ingredients && product.ingredients.length > 0 && (
              <div className="mb-6">
                <div className="text-sm text-gray-500 mb-2">原材料</div>
                <div className="bg-gray-50 rounded-lg p-4 max-h-48 overflow-y-auto">
                  <p className="text-sm text-gray-700">
                    {product.ingredients.join(", ")}
                  </p>
                </div>
              </div>
            )}

            <div className="mt-auto pt-6 flex gap-3">
              <button
                onClick={() => setIsEditing(true)}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                編集
              </button>
              <button
                onClick={handleDelete}
                disabled={isDeleting}
                className="px-4 py-2 border border-red-600 text-red-600 rounded-lg hover:bg-red-50 disabled:opacity-50"
              >
                {isDeleting ? "削除中..." : "削除"}
              </button>
            </div>
          </div>
        </div>
      </div>

      {isEditing && (
        <EditProductModal
          product={product}
          onClose={() => setIsEditing(false)}
          onUpdate={handleUpdateSuccess}
        />
      )}

      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={hideToast}
        />
      )}
    </div>
  );
}

interface EditProductModalProps {
  product: Product;
  onClose: () => void;
  onUpdate: () => void;
}

function EditProductModal({ product, onClose, onUpdate }: EditProductModalProps) {
  const [formData, setFormData] = useState({
    product_name: product.product_name || "",
    volume: product.volume || "",
    manufacturer: product.manufacturer || "",
    seller: product.seller || "",
    category: product.category || "Other",
    price_info: product.price_info || "",
    price_tax_excluded: product.price_tax_excluded || "",
    product_url: product.product_url || "",
    appeals: product.appeals?.join(", ") || "",
    ingredients: product.ingredients?.join(", ") || ""
  });
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.product_name.trim()) {
      setError("商品名は必須です");
      return;
    }

    setIsSaving(true);
    setError(null);

    try {
      const updateData = {
        ...formData,
        appeals: formData.appeals.split(",").map(s => s.trim()).filter(s => s),
        ingredients: formData.ingredients.split(",").map(s => s.trim()).filter(s => s)
      };

      await axios.put(`${API_BASE_URL}/products/${product.id}`, updateData);
      onUpdate();
    } catch (err) {
      console.error("Update failed", err);
      setError("更新に失敗しました");
    } finally {
      setIsSaving(false);
    }
  };

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div
      className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4"
      onClick={handleBackdropClick}
    >
      <div className="bg-white rounded-xl w-full max-w-2xl p-6 max-h-[90vh] overflow-y-auto">
        <h2 className="text-2xl font-bold mb-6">商品情報の編集</h2>

        {error && (
          <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-lg">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              商品名 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.product_name}
              onChange={(e) => setFormData({...formData, product_name: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              カテゴリー
            </label>
            <select
              value={formData.category}
              onChange={(e) => setFormData({...formData, category: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {CATEGORIES.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                製造者
              </label>
              <input
                type="text"
                value={formData.manufacturer}
                onChange={(e) => setFormData({...formData, manufacturer: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                販売者
              </label>
              <input
                type="text"
                value={formData.seller}
                onChange={(e) => setFormData({...formData, seller: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              内容量
            </label>
            <input
              type="text"
              value={formData.volume}
              onChange={(e) => setFormData({...formData, volume: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                価格
              </label>
              <input
                type="text"
                value={formData.price_info}
                onChange={(e) => setFormData({...formData, price_info: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                税抜価格
              </label>
              <input
                type="text"
                value={formData.price_tax_excluded}
                onChange={(e) => setFormData({...formData, price_tax_excluded: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              商品URL
            </label>
            <input
              type="url"
              value={formData.product_url}
              onChange={(e) => setFormData({...formData, product_url: e.target.value})}
              placeholder="https://..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              訴求ポイント (カンマ区切り)
            </label>
            <input
              type="text"
              value={formData.appeals}
              onChange={(e) => setFormData({...formData, appeals: e.target.value})}
              placeholder="高タンパク, 低カロリー, 無添加"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              原材料 (カンマ区切り)
            </label>
            <textarea
              value={formData.ingredients}
              onChange={(e) => setFormData({...formData, ingredients: e.target.value})}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
              disabled={isSaving}
            >
              キャンセル
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              disabled={isSaving}
            >
              {isSaving ? "保存中..." : "保存"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
