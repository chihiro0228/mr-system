"use client";

import { useEffect, useState } from "react";

export default function TestPage() {
  const [count, setCount] = useState(0);
  const [message, setMessage] = useState("JavaScriptが読み込まれていません");

  useEffect(() => {
    setMessage("✓ JavaScriptが実行されました！");

    // 1秒ごとにカウントアップ
    const interval = setInterval(() => {
      setCount((prev) => prev + 1);
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 p-8">
      <div className="max-w-2xl mx-auto bg-white rounded-2xl shadow-xl p-8">
        <h1 className="text-4xl font-bold text-gray-800 mb-6">
          🧪 動作確認ページ
        </h1>

        <div className="space-y-6">
          <div className="p-4 bg-blue-50 rounded-lg">
            <p className="text-lg font-semibold text-gray-700">ステータス:</p>
            <p className="text-2xl text-blue-600 mt-2">{message}</p>
          </div>

          <div className="p-4 bg-green-50 rounded-lg">
            <p className="text-lg font-semibold text-gray-700">カウンター:</p>
            <p className="text-5xl font-bold text-green-600 mt-2">{count}秒</p>
            <p className="text-sm text-gray-500 mt-2">
              このカウンターが動いていれば、JavaScriptは正常に動作しています
            </p>
          </div>

          <button
            onClick={() => alert("ボタンが押されました！")}
            className="w-full bg-purple-600 text-white py-4 px-6 rounded-lg text-lg font-semibold hover:bg-purple-700 transition"
          >
            クリックしてテスト
          </button>

          <div className="p-4 bg-yellow-50 rounded-lg border-2 border-yellow-200">
            <p className="text-sm text-gray-600">
              <strong>確認事項:</strong>
              <br />
              ✓ 「JavaScriptが実行されました」と表示されている
              <br />
              ✓ カウンターが1秒ごとに増えている
              <br />
              ✓ ボタンを押すとアラートが表示される
              <br />
              <br />
              これらすべてが動作していれば、アプリは正常です！
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
