"""
Gemini API integration for product data extraction from images
"""
import os
import json
import base64
from typing import Dict, List, Optional

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Warning: google-generativeai not installed. Run: pip install google-generativeai")

# Configure Gemini API
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

if GEMINI_AVAILABLE and GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


EXTRACTION_PROMPT = """
この商品画像を分析し、以下の情報をJSON形式で抽出してください。
情報が見つからない場合はnullを設定してください。

抽出する情報：
1. product_name: 商品名（パッケージに書かれている正式名称）
2. manufacturer: 製造者の会社名（「製造者:」「製造元:」の後に記載）
3. seller: 販売者の会社名（「販売者:」「販売元:」の後に記載、製造者と異なる場合のみ）
4. volume: 内容量（例: "100g", "500ml"）
5. ingredients: 原材料名のリスト（配列形式）
6. nutrition: 栄養成分表示
   - energy: エネルギー（例: "100kcal"）
   - protein: タンパク質（例: "5.0g"）
   - fat: 脂質（例: "3.0g"）
   - carbs: 炭水化物（例: "15.0g"）
   - sugar: 糖質（例: "10.0g"）
   - fiber: 食物繊維（例: "2.0g"）
   - salt: 食塩相当量（例: "0.5g"）
7. appeals: 訴求ポイント・特徴のリスト（例: ["無添加", "国産", "低糖質", "高タンパク"]）
8. category: 商品カテゴリ（以下から最も適切なものを1つ選択）
   - "Chocolate": チョコレート、チョコ菓子
   - "Gummy": グミ、ソフトキャンディ
   - "Cookie": クッキー、ビスケット、焼き菓子
   - "Snack": スナック菓子、ポテトチップス、せんべい
   - "Donut": ドーナツ
   - "Jelly": ゼリー、プリン、ムース
   - "Noodle": 麺類、ラーメン、うどん、そば
   - "Supplement": サプリメント、ビタミン剤、健康食品
   - "Beverage": 飲料、ドリンク、ジュース
   - "Protein": プロテイン、プロテインバー
   - "Other": 上記に該当しないもの

必ず以下のJSON形式で回答してください：
```json
{
  "product_name": "商品名",
  "manufacturer": "製造者名",
  "seller": "販売者名",
  "volume": "内容量",
  "ingredients": ["原材料1", "原材料2"],
  "nutrition": {
    "energy": "100kcal",
    "protein": "5.0g",
    "fat": "3.0g",
    "carbs": "15.0g",
    "sugar": "10.0g",
    "fiber": "2.0g",
    "salt": "0.5g"
  },
  "appeals": ["特徴1", "特徴2"],
  "category": "カテゴリ名（英語）"
}
```
"""


def extract_with_gemini(image_paths: List[str]) -> Dict:
    """
    Extract product data from images using Gemini API

    Args:
        image_paths: List of paths to product images

    Returns:
        Dictionary containing extracted product data
    """
    if not GEMINI_AVAILABLE:
        print("Gemini API not available, using mock data")
        return _get_mock_data()

    if not GEMINI_API_KEY:
        print("GEMINI_API_KEY not set, using mock data")
        return _get_mock_data()

    try:
        # Use Gemini Pro Vision model
        model = genai.GenerativeModel('gemini-2.0-flash')

        # Prepare images
        image_parts = []
        for image_path in image_paths:
            if os.path.exists(image_path):
                with open(image_path, 'rb') as f:
                    image_data = f.read()
                    # Determine MIME type
                    ext = os.path.splitext(image_path)[1].lower()
                    mime_type = {
                        '.jpg': 'image/jpeg',
                        '.jpeg': 'image/jpeg',
                        '.png': 'image/png',
                        '.gif': 'image/gif',
                        '.webp': 'image/webp'
                    }.get(ext, 'image/jpeg')

                    image_parts.append({
                        'mime_type': mime_type,
                        'data': image_data
                    })

        if not image_parts:
            print("No valid images found")
            return _get_mock_data()

        # Create content with images and prompt
        content = image_parts + [EXTRACTION_PROMPT]

        # Generate response
        response = model.generate_content(content)
        response_text = response.text

        # Parse JSON from response
        extracted_data = _parse_gemini_response(response_text)
        return extracted_data

    except Exception as e:
        print(f"Gemini API error: {e}")
        return _get_mock_data()


def _parse_gemini_response(response_text: str) -> Dict:
    """Parse JSON from Gemini response"""
    try:
        # Try to extract JSON from markdown code block
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            json_str = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            json_str = response_text[json_start:json_end].strip()
        else:
            # Try to find JSON object directly
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            json_str = response_text[json_start:json_end]

        data = json.loads(json_str)

        # Normalize the data
        product_name = data.get("product_name") or "Unknown Product"
        return {
            "product_name": product_name,
            "manufacturer": data.get("manufacturer") or "Unknown Manufacturer",
            "seller": data.get("seller"),
            "volume": data.get("volume") or "Unknown",
            "ingredients": data.get("ingredients") or [],
            "nutrition": data.get("nutrition") or {},
            "appeals": data.get("appeals") or [],
            "category": _normalize_category(data.get("category"), product_name)
        }

    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print(f"Response text: {response_text[:500]}")
        return _get_mock_data()


def _normalize_category(category: Optional[str], product_name: Optional[str] = None) -> str:
    """Normalize category to valid values, also check product name for category hints"""
    # Valid English category names
    valid_categories = [
        "Chocolate", "Gummy", "Cookie", "Snack", "Donut",
        "Jelly", "Noodle", "Supplement", "Beverage", "Protein", "Other"
    ]

    # Map Japanese to English
    category_map = {
        # Japanese mappings
        "チョコレート": "Chocolate",
        "チョコ": "Chocolate",
        "グミ": "Gummy",
        "クッキー": "Cookie",
        "ビスケット": "Cookie",
        "焼き菓子": "Cookie",
        "スナック": "Snack",
        "せんべい": "Snack",
        "ドーナツ": "Donut",
        "ゼリー": "Jelly",
        "プリン": "Jelly",
        "麺類": "Noodle",
        "ラーメン": "Noodle",
        "うどん": "Noodle",
        "そば": "Noodle",
        "サプリメント": "Supplement",
        "健康食品": "Supplement",
        "飲料": "Beverage",
        "ドリンク": "Beverage",
        "ジュース": "Beverage",
        "プロテイン": "Protein",
        "その他": "Other",
        # Old category mappings for backwards compatibility
        "Noodles": "Noodle",
    }

    # Keywords to detect category from product name (Japanese and English)
    name_keywords = {
        "Chocolate": ["チョコ", "chocolate", "Chocolate", "ショコラ"],
        "Gummy": ["グミ", "gummy", "Gummy", "ガム"],
        "Cookie": ["クッキー", "cookie", "Cookie", "ビスケット", "biscuit"],
        "Snack": ["スナック", "snack", "Snack", "チップス", "chips", "せんべい"],
        "Donut": ["ドーナツ", "donut", "Donut", "ドーナッツ"],
        "Jelly": ["ゼリー", "jelly", "Jelly", "プリン", "pudding"],
        "Noodle": ["麺", "ラーメン", "うどん", "そば", "noodle", "Noodle", "ヌードル"],
        "Supplement": ["サプリ", "supplement", "Supplement", "ビタミン", "vitamin"],
        "Beverage": ["飲料", "ドリンク", "ジュース", "beverage", "Beverage", "drink"],
        "Protein": ["プロテイン", "protein", "Protein"],
    }

    # First, try to detect from product name
    if product_name:
        product_name_lower = product_name.lower()
        for cat, keywords in name_keywords.items():
            for keyword in keywords:
                if keyword.lower() in product_name_lower:
                    return cat

    # If category is provided and valid, return it
    if category:
        if category in valid_categories:
            return category
        if category in category_map:
            return category_map[category]

    return "Other"


def _get_mock_data() -> Dict:
    """Return mock data when Gemini is not available"""
    return {
        "product_name": "Sample Product (Gemini not available)",
        "manufacturer": "Sample Manufacturer",
        "seller": None,
        "volume": "100g",
        "ingredients": ["Ingredient A", "Ingredient B", "Ingredient C"],
        "nutrition": {
            "energy": "100kcal",
            "protein": "5.0g",
            "fat": "3.0g",
            "carbs": "15.0g",
            "sugar": "10.0g",
            "fiber": "2.0g",
            "salt": "0.5g"
        },
        "appeals": ["無添加", "国産"],
        "category": "Other"
    }


def merge_extracted_data(data_list: List[Dict]) -> Dict:
    """
    Merge extracted data from multiple images

    Prioritizes non-empty values and combines lists
    """
    if not data_list:
        return _get_mock_data()

    if len(data_list) == 1:
        return data_list[0]

    merged = {
        "product_name": None,
        "manufacturer": None,
        "seller": None,
        "volume": None,
        "ingredients": [],
        "nutrition": {},
        "appeals": [],
        "category": "Other"
    }

    for data in data_list:
        # Take first non-empty value for scalar fields
        if not merged["product_name"] and data.get("product_name"):
            merged["product_name"] = data["product_name"]
        if not merged["manufacturer"] and data.get("manufacturer"):
            merged["manufacturer"] = data["manufacturer"]
        if not merged["seller"] and data.get("seller"):
            merged["seller"] = data["seller"]
        if not merged["volume"] and data.get("volume"):
            merged["volume"] = data["volume"]
        if merged["category"] == "Other" and data.get("category") != "Other":
            merged["category"] = data["category"]

        # Merge lists (unique values)
        for ingredient in data.get("ingredients", []):
            if ingredient and ingredient not in merged["ingredients"]:
                merged["ingredients"].append(ingredient)

        for appeal in data.get("appeals", []):
            if appeal and appeal not in merged["appeals"]:
                merged["appeals"].append(appeal)

        # Merge nutrition (take first non-empty value for each field)
        nutrition = data.get("nutrition", {})
        for key in ["energy", "protein", "fat", "carbs", "sugar", "fiber", "salt"]:
            if not merged["nutrition"].get(key) and nutrition.get(key):
                merged["nutrition"][key] = nutrition[key]

    # Set defaults for empty fields
    if not merged["product_name"]:
        merged["product_name"] = "Unknown Product"
    if not merged["manufacturer"]:
        merged["manufacturer"] = "Unknown Manufacturer"
    if not merged["volume"]:
        merged["volume"] = "Unknown"

    return merged
