"use client";

import { useState } from "react";
import { API_BASE_URL } from "@/types";

interface ImageGalleryProps {
  images: string[];
  productName: string;
}

export default function ImageGallery({ images, productName }: ImageGalleryProps) {
  const [selectedIndex, setSelectedIndex] = useState(0);

  // Ensure we have at least one image
  if (!images || images.length === 0) {
    return (
      <div className="aspect-square relative bg-gray-100 rounded-lg overflow-hidden flex items-center justify-center">
        <div className="text-gray-400 text-center">
          <div className="text-4xl mb-2">📷</div>
          <p>画像なし</p>
        </div>
      </div>
    );
  }

  const getImageUrl = (path: string) => {
    if (path.startsWith("http")) {
      return path;
    }
    return `${API_BASE_URL}${path}`;
  };

  const currentImage = images[selectedIndex];

  return (
    <div className="space-y-3">
      {/* Main Image */}
      <div className="aspect-square relative bg-gray-100 rounded-lg overflow-hidden">
        <img
          src={getImageUrl(currentImage)}
          alt={`${productName} - ${selectedIndex + 1}`}
          className="w-full h-full object-contain"
        />
        {images.length > 1 && (
          <div className="absolute bottom-2 right-2 bg-black/50 text-white text-xs px-2 py-1 rounded">
            {selectedIndex + 1} / {images.length}
          </div>
        )}
      </div>

      {/* Thumbnails */}
      {images.length > 1 && (
        <div className="flex gap-2 overflow-x-auto pb-2">
          {images.map((image, index) => (
            <button
              key={index}
              onClick={() => setSelectedIndex(index)}
              className={`flex-shrink-0 w-16 h-16 rounded-lg overflow-hidden border-2 transition ${
                selectedIndex === index
                  ? "border-blue-600 ring-2 ring-blue-200"
                  : "border-gray-200 hover:border-gray-400"
              }`}
            >
              <img
                src={getImageUrl(image)}
                alt={`${productName} thumbnail ${index + 1}`}
                className="w-full h-full object-cover"
              />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
