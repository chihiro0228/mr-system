"use client";

import { useEffect, useState } from "react";

export default function TestAPI() {
  const [result, setResult] = useState<string>("テスト開始...");

  useEffect(() => {
    const testAPI = async () => {
      try {
        setResult("APIを呼び出し中...");

        const response = await fetch("http://localhost:8000/products");
        const data = await response.json();

        setResult(`成功！商品数: ${data.length}\n\n${JSON.stringify(data, null, 2)}`);
      } catch (error) {
        setResult(`エラー: ${error}`);
      }
    };

    testAPI();
  }, []);

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">API テスト</h1>
      <pre className="bg-gray-100 p-4 rounded overflow-auto max-h-96">
        {result}
      </pre>
    </div>
  );
}
