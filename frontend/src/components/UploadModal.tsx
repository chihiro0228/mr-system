"use client";

import { useState, useRef, useCallback } from "react";
import axios from "axios";
import { Product, API_BASE_URL } from "@/types";

interface UploadModalProps {
  onClose: () => void;
  onUploadSuccess: (product: Product) => void;
}

interface ImagePreview {
  file: File;
  preview: string;
}

export default function UploadModal({ onClose, onUploadSuccess }: UploadModalProps) {
  const [images, setImages] = useState<ImagePreview[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateAndAddFiles = useCallback((files: FileList | File[]) => {
    const newImages: ImagePreview[] = [];
    const errors: string[] = [];

    Array.from(files).forEach((file) => {
      if (!file.type.startsWith("image/")) {
        errors.push(`${file.name}: 画像ファイルではありません`);
        return;
      }
      if (file.size > 10 * 1024 * 1024) {
        errors.push(`${file.name}: 10MBを超えています`);
        return;
      }
      // Check for duplicates
      if (images.some(img => img.file.name === file.name && img.file.size === file.size)) {
        return; // Skip duplicates silently
      }
      newImages.push({
        file,
        preview: URL.createObjectURL(file)
      });
    });

    if (errors.length > 0) {
      setError(errors.join("\n"));
    } else {
      setError(null);
    }

    if (newImages.length > 0) {
      setImages(prev => [...prev, ...newImages]);
    }
  }, [images]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndAddFiles(e.target.files);
    }
    // Reset input to allow selecting same files again
    e.target.value = "";
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndAddFiles(e.dataTransfer.files);
    }
  }, [validateAndAddFiles]);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  };

  const removeImage = (index: number) => {
    setImages(prev => {
      const newImages = [...prev];
      URL.revokeObjectURL(newImages[index].preview);
      newImages.splice(index, 1);
      return newImages;
    });
  };

  const handleUpload = async () => {
    if (images.length === 0) {
      setError("画像を選択してください");
      return;
    }

    setUploading(true);
    setError(null);

    const formData = new FormData();
    images.forEach((img) => {
      formData.append("files", img.file);
    });

    try {
      const response = await axios.post<Product>(
        `${API_BASE_URL}/upload`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );
      // Cleanup previews
      images.forEach(img => URL.revokeObjectURL(img.preview));
      onUploadSuccess(response.data);
      onClose();
    } catch (err: unknown) {
      console.error(err);
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail || "アップロードに失敗しました");
      } else {
        setError("アップロードに失敗しました");
      }
    } finally {
      setUploading(false);
    }
  };

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      onClick={handleBackdropClick}
    >
      <div className="bg-white rounded-xl p-6 w-full max-w-lg shadow-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold text-gray-800">商品画像をアップロード</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl"
            aria-label="閉じる"
          >
            ×
          </button>
        </div>

        {/* Drop Zone */}
        <div
          onClick={() => fileInputRef.current?.click()}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition ${
            dragOver
              ? "border-blue-500 bg-blue-50"
              : "border-gray-300 hover:border-blue-500"
          }`}
        >
          <div className="text-gray-400">
            <div className="text-4xl mb-2">📷</div>
            <p className="font-medium">クリックまたはドラッグ&ドロップ</p>
            <p className="text-sm">複数の画像を選択できます</p>
            <p className="text-xs mt-1">JPG, PNG, GIF (各10MB以下)</p>
          </div>
        </div>

        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          multiple
          onChange={handleFileChange}
          className="hidden"
        />

        {/* Image Previews */}
        {images.length > 0 && (
          <div className="mt-4">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm text-gray-600">
                選択中: {images.length}枚
              </span>
              <button
                onClick={() => {
                  images.forEach(img => URL.revokeObjectURL(img.preview));
                  setImages([]);
                }}
                className="text-sm text-red-500 hover:text-red-700"
              >
                すべて削除
              </button>
            </div>
            <div className="grid grid-cols-4 gap-2">
              {images.map((img, index) => (
                <div key={index} className="relative group">
                  <img
                    src={img.preview}
                    alt={`Preview ${index + 1}`}
                    className="w-full aspect-square object-cover rounded-lg"
                  />
                  {index === 0 && (
                    <span className="absolute top-1 left-1 bg-blue-600 text-white text-xs px-1.5 py-0.5 rounded">
                      メイン
                    </span>
                  )}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      removeImage(index);
                    }}
                    className="absolute top-1 right-1 bg-red-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs opacity-0 group-hover:opacity-100 transition"
                    aria-label="削除"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {error && (
          <p className="text-red-500 text-sm mt-2 whitespace-pre-line">{error}</p>
        )}

        {uploading && (
          <div className="mt-4">
            <div className="text-sm text-gray-600 mb-2">
              画像を解析中... ({images.length}枚)
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div className="bg-blue-600 h-2 rounded-full animate-pulse w-3/4"></div>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              商品情報の抽出と価格検索を行っています
            </p>
          </div>
        )}

        <div className="flex gap-3 mt-6">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
            disabled={uploading}
          >
            キャンセル
          </button>
          <button
            onClick={handleUpload}
            disabled={images.length === 0 || uploading}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {uploading ? "解析中..." : `アップロード (${images.length}枚)`}
          </button>
        </div>
      </div>
    </div>
  );
}
