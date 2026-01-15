"use client";

import { useState, useEffect } from "react";

export default function SimplePage() {
  const [status, setStatus] = useState("初期化中...");
  const [products, setProducts] = useState<any[]>([]);

  useEffect(() => {
    console.log("useEffect が実行されました");
    setStatus("データを取得中...");

    fetch("http://localhost:8000/products")
      .then((res) => {
        console.log("レスポンス受信:", res.status);
        return res.json();
      })
      .then((data) => {
        console.log("データ受信:", data);
        setProducts(data);
        setStatus(`成功！商品数: ${data.length}`);
      })
      .catch((err) => {
        console.error("エラー:", err);
        setStatus(`エラー: ${err.message}`);
      });
  }, []);

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-4">シンプルテスト</h1>
      <p className="text-xl mb-4">ステータス: {status}</p>

      {products.length > 0 && (
        <div className="bg-gray-100 p-4 rounded">
          <h2 className="font-bold mb-2">商品一覧:</h2>
          {products.map((p) => (
            <div key={p.id} className="mb-2 p-2 bg-white rounded">
              <p className="font-bold">{p.product_name}</p>
              <p className="text-sm text-gray-600">{p.manufacturer}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
