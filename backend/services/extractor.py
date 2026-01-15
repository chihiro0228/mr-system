from typing import Dict, List
import re

# Try to import easyocr, but don't fail if it's not available
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    print("Warning: easyocr not installed. Using mock data extraction.")
    EASYOCR_AVAILABLE = False

# Global reader instance (initialized once for performance)
reader = None

def get_reader():
    """Lazy initialization of EasyOCR reader"""
    global reader
    if not EASYOCR_AVAILABLE:
        return None
    if reader is None:
        print("Initializing EasyOCR reader...")
        reader = easyocr.Reader(['ja', 'en'], gpu=False)
        print("EasyOCR reader initialized!")
    return reader

def extract_product_data(image_path: str) -> Dict:
    """
    Extracts product information from Japanese package images.
    Returns: {
        product_name: str,
        volume: str,
        manufacturer: str,
        ingredients: List[str],
        appeals: List[str],
        category: str
    }
    """
    print(f"Extracting data from {image_path}...")

    # If easyocr is not available, return mock data
    if not EASYOCR_AVAILABLE:
        print("Using mock data (easyocr not available)")
        return {
            "product_name": "Sample Product (OCR not available)",
            "volume": "100g",
            "manufacturer": "Sample Manufacturer",
            "ingredients": ["Ingredient A", "Ingredient B", "Ingredient C"],
            "appeals": ["無添加", "国産"],
            "category": "Other"
        }

    try:
        reader = get_reader()
        if reader is None:
            raise Exception("OCR reader not available")

        # Perform OCR
        result = reader.readtext(image_path)

        # Extract all text blocks
        text_blocks = [detection[1] for detection in result]
        full_text = " ".join(text_blocks)

        print(f"Extracted text blocks: {len(text_blocks)}")

        # Extract structured data
        extracted = {
            "product_name": extract_product_name(text_blocks, full_text),
            "volume": extract_volume(text_blocks, full_text),
            "manufacturer": extract_manufacturer(text_blocks, full_text),
            "ingredients": extract_ingredients(text_blocks, full_text),
            "appeals": extract_appeals(text_blocks, full_text),
            "category": classify_category(text_blocks, full_text)
        }

        print(f"Extracted data: {extracted}")
        return extracted

    except Exception as e:
        print(f"OCR extraction error: {e}")
        # Return default values on error
        return {
            "product_name": "Unknown Product",
            "volume": "Unknown",
            "manufacturer": "Unknown Manufacturer",
            "ingredients": [],
            "appeals": [],
            "category": "Other"
        }

def extract_product_name(text_blocks: List[str], full_text: str) -> str:
    """
    Extract product name - typically the largest/first text block.
    Strategy: First non-label text block, or longest block in upper portion.
    """
    # Filter out common label keywords
    label_keywords = ['原材料名', '内容量', '製造者', '販売者', '賞味期限',
                      '保存方法', '栄養成分', 'Ingredients', 'Volume', '名称']

    candidates = []
    for block in text_blocks[:5]:  # Focus on first 5 blocks
        if not any(keyword in block for keyword in label_keywords):
            if len(block) > 2:  # Meaningful length
                candidates.append(block)

    return candidates[0] if candidates else (text_blocks[0] if text_blocks else "Unknown Product")

def extract_volume(text_blocks: List[str], full_text: str) -> str:
    """
    Extract volume/quantity.
    Patterns: XXXg, XXXml, XXX個, XXX枚, etc.
    """
    # Pattern for volume: number + unit
    volume_patterns = [
        r'(\d+(?:\.\d+)?)\s*(?:g|グラム)',
        r'(\d+(?:\.\d+)?)\s*(?:ml|mL|ミリリットル)',
        r'(\d+(?:\.\d+)?)\s*(?:kg|キログラム)',
        r'(\d+(?:\.\d+)?)\s*(?:L|リットル)',
        r'(\d+)\s*(?:個|枚|本|袋)',
        r'内容量[:\s]*(\d+(?:\.\d+)?)\s*(?:g|ml|個|枚)',
    ]

    for pattern in volume_patterns:
        match = re.search(pattern, full_text)
        if match:
            return match.group(0)

    return "Unknown"

def extract_manufacturer(text_blocks: List[str], full_text: str) -> str:
    """
    Extract manufacturer.
    Look for patterns: 製造者, 販売者, 株式会社, Co.,Ltd.
    """
    manufacturer_patterns = [
        r'製造者[:\s]*([\u4E00-\u9FFF\u3040-\u309F\u30A0-\u30FFa-zA-Z0-9\s]+(?:株式会社|有限会社|合同会社)?)',
        r'販売者[:\s]*([\u4E00-\u9FFF\u3040-\u309F\u30A0-\u30FFa-zA-Z0-9\s]+(?:株式会社|有限会社|合同会社)?)',
        r'([\u4E00-\u9FFF\u3040-\u309F\u30A0-\u30FFa-zA-Z0-9\s]+(?:株式会社|有限会社|合同会社|Co\.,Ltd\.|Inc\.))',
    ]

    for pattern in manufacturer_patterns:
        match = re.search(pattern, full_text)
        if match:
            return match.group(1).strip()

    # Fallback: look for blocks with company keywords
    for block in text_blocks:
        if '株式会社' in block or 'Co.,Ltd' in block or '有限会社' in block:
            return block.strip()

    return "Unknown Manufacturer"

def extract_ingredients(text_blocks: List[str], full_text: str) -> List[str]:
    """
    Extract ingredients list.
    Look for: 原材料名: item1, item2, item3 / item1、item2、item3
    """
    # Find ingredients section
    ingredient_pattern = r'原材料名?[:\s]*([\u4E00-\u9FFF\u3040-\u309F\u30A0-\u30FFa-zA-Z0-9、,\(\)\s]+)'
    match = re.search(ingredient_pattern, full_text)

    if match:
        ingredients_text = match.group(1)
        # Split by Japanese comma (、) or regular comma
        ingredients = re.split('[、,]', ingredients_text)
        # Clean up
        ingredients = [ing.strip() for ing in ingredients if ing.strip() and len(ing.strip()) > 1]
        return ingredients[:15]  # Limit to 15 ingredients

    return []

def extract_appeals(text_blocks: List[str], full_text: str) -> List[str]:
    """
    Extract appeals (package claims + nutritional features).
    Look for:
    1. Package claims: 糖質オフ, 無添加, 低カロリー, etc.
    2. Nutritional features from 栄養成分表示
    """
    appeals = []

    # 1. Package claims keywords
    claim_keywords = [
        '糖質オフ', '糖質ゼロ', '低糖質', '糖質制限',
        '無添加', '保存料無添加', '着色料無添加',
        '低カロリー', 'カロリーオフ', 'ノンカロリー',
        '高タンパク', 'タンパク質', 'プロテイン',
        '低脂肪', '脂質ゼロ', 'ノンファット',
        '食物繊維', '乳酸菌', 'ビタミン', 'ミネラル',
        'オーガニック', '有機', '国産', '無農薬',
        'グルテンフリー', 'アレルゲンフリー',
        '機能性表示食品', '特定保健用食品', 'トクホ'
    ]

    for keyword in claim_keywords:
        if keyword in full_text:
            appeals.append(keyword)

    # 2. Nutritional features extraction
    nutritional_features = extract_nutritional_features(full_text)
    appeals.extend(nutritional_features)

    return list(set(appeals))  # Remove duplicates

def extract_nutritional_features(full_text: str) -> List[str]:
    """
    Extract nutritional features from 栄養成分表示.
    Identify high/low values compared to typical ranges.
    """
    features = []

    # Protein patterns
    protein_pattern = r'たんぱく質[:\s]*(\d+(?:\.\d+)?)\s*g'
    match = re.search(protein_pattern, full_text)
    if match:
        protein = float(match.group(1))
        if protein >= 10:  # High protein threshold (per 100g)
            features.append('高タンパク')

    # Calorie patterns
    calorie_pattern = r'エネルギー[:\s]*(\d+(?:\.\d+)?)\s*kcal'
    match = re.search(calorie_pattern, full_text)
    if match:
        calories = float(match.group(1))
        if calories <= 100:  # Low calorie threshold (per 100g)
            features.append('低カロリー')

    # Sugar patterns
    sugar_pattern = r'糖質[:\s]*(\d+(?:\.\d+)?)\s*g'
    match = re.search(sugar_pattern, full_text)
    if match:
        sugar = float(match.group(1))
        if sugar <= 5:  # Low sugar threshold
            features.append('低糖質')

    # Fiber patterns
    fiber_pattern = r'食物繊維[:\s]*(\d+(?:\.\d+)?)\s*g'
    match = re.search(fiber_pattern, full_text)
    if match:
        fiber = float(match.group(1))
        if fiber >= 5:  # High fiber threshold
            features.append('食物繊維豊富')

    return features

def classify_category(text_blocks: List[str], full_text: str) -> str:
    """
    Classify product into category based on keywords.
    Categories: Snack, Noodles, Supplements, Other
    """
    category_keywords = {
        'Snack': ['スナック', 'お菓子', 'チップス', 'クッキー', 'ビスケット',
                  'チョコレート', 'キャンディ', 'グミ', 'ポテト', 'せんべい'],
        'Noodles': ['麺', 'ラーメン', 'うどん', 'そば', 'パスタ', 'スパゲッティ',
                    'インスタント麺', 'カップ麺', 'ヌードル', '中華麺'],
        'Supplements': ['サプリメント', 'プロテイン', 'ビタミン', 'ミネラル',
                       '健康食品', '栄養補助食品', '機能性表示食品', 'サプリ']
    }

    for category, keywords in category_keywords.items():
        for keyword in keywords:
            if keyword in full_text:
                return category

    return 'Other'
