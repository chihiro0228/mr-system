import pytest
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.extractor import (
    extract_volume,
    extract_manufacturer,
    extract_ingredients,
    extract_appeals,
    extract_nutritional_features,
    classify_category,
    extract_product_name
)


class TestExtractVolume:
    def test_extract_volume_grams(self):
        """Test extracting volume in grams"""
        text = "内容量 100g お菓子"
        result = extract_volume([], text)
        assert "100" in result and "g" in result

    def test_extract_volume_ml(self):
        """Test extracting volume in milliliters"""
        text = "ドリンク 500ml 清涼飲料水"
        result = extract_volume([], text)
        assert "500" in result

    def test_extract_volume_pieces(self):
        """Test extracting volume as piece count"""
        text = "12個入り お菓子セット"
        result = extract_volume([], text)
        assert "12" in result

    def test_extract_volume_not_found(self):
        """Test when volume is not found"""
        text = "商品名だけ"
        result = extract_volume([], text)
        assert result == "Unknown"


class TestExtractManufacturer:
    def test_extract_manufacturer_kabushiki(self):
        """Test extracting manufacturer with 株式会社"""
        text = "製造者: 山田食品株式会社 東京都"
        result = extract_manufacturer([], text)
        assert "山田食品" in result or "株式会社" in result

    def test_extract_manufacturer_from_block(self):
        """Test extracting from text blocks"""
        blocks = ["商品名", "ABC株式会社", "原材料"]
        result = extract_manufacturer(blocks, "")
        assert "ABC株式会社" in result

    def test_extract_manufacturer_not_found(self):
        """Test when manufacturer is not found"""
        text = "商品情報のみ"
        result = extract_manufacturer([], text)
        assert result == "Unknown Manufacturer"


class TestExtractIngredients:
    def test_extract_ingredients_japanese_comma(self):
        """Test extracting ingredients with Japanese comma"""
        text = "原材料名: 小麦粉、砂糖、卵、バター"
        result = extract_ingredients([], text)

        assert len(result) > 0
        assert "小麦粉" in result
        assert "砂糖" in result

    def test_extract_ingredients_regular_comma(self):
        """Test extracting ingredients with regular comma"""
        text = "原材料: 塩,胡椒,にんにく"
        result = extract_ingredients([], text)

        assert len(result) > 0

    def test_extract_ingredients_not_found(self):
        """Test when no ingredients found"""
        text = "商品説明のみ"
        result = extract_ingredients([], text)

        assert result == []

    def test_extract_ingredients_limit(self):
        """Test that ingredients are limited to 15 items"""
        many_ingredients = "、".join([f"原料{i}" for i in range(20)])
        text = f"原材料名: {many_ingredients}"
        result = extract_ingredients([], text)

        assert len(result) <= 15


class TestExtractAppeals:
    def test_extract_appeals_sugar_free(self):
        """Test extracting sugar-related claims"""
        text = "糖質オフ ダイエット食品"
        result = extract_appeals([], text)

        assert "糖質オフ" in result

    def test_extract_appeals_additive_free(self):
        """Test extracting additive-free claims"""
        text = "無添加 自然派 オーガニック"
        result = extract_appeals([], text)

        assert "無添加" in result
        assert "オーガニック" in result

    def test_extract_appeals_multiple(self):
        """Test extracting multiple appeals"""
        text = "低カロリー 高タンパク 食物繊維"
        result = extract_appeals([], text)

        assert "低カロリー" in result
        assert "高タンパク" in result
        assert "食物繊維" in result

    def test_extract_appeals_none_found(self):
        """Test when no appeals found"""
        text = "普通の商品です"
        result = extract_appeals([], text)

        # May return empty or have nutritional features
        assert isinstance(result, list)


class TestExtractNutritionalFeatures:
    def test_high_protein(self):
        """Test detecting high protein"""
        text = "たんぱく質: 15g"
        result = extract_nutritional_features(text)

        assert "高タンパク" in result

    def test_low_calorie(self):
        """Test detecting low calorie"""
        text = "エネルギー: 50kcal"
        result = extract_nutritional_features(text)

        assert "低カロリー" in result

    def test_low_sugar(self):
        """Test detecting low sugar"""
        text = "糖質: 3g"
        result = extract_nutritional_features(text)

        assert "低糖質" in result

    def test_high_fiber(self):
        """Test detecting high fiber"""
        text = "食物繊維: 8g"
        result = extract_nutritional_features(text)

        assert "食物繊維豊富" in result

    def test_no_features(self):
        """Test when no nutritional features detected"""
        text = "普通の栄養成分"
        result = extract_nutritional_features(text)

        assert isinstance(result, list)


class TestClassifyCategory:
    def test_classify_snack(self):
        """Test classifying as Snack"""
        text = "ポテトチップス うすしお味"
        result = classify_category([], text)

        assert result == "Snack"

    def test_classify_noodles(self):
        """Test classifying as Noodles"""
        text = "インスタントラーメン 豚骨味"
        result = classify_category([], text)

        assert result == "Noodles"

    def test_classify_supplements(self):
        """Test classifying as Supplements"""
        text = "プロテイン ホエイ100%"
        result = classify_category([], text)

        assert result == "Supplements"

    def test_classify_other(self):
        """Test classifying as Other"""
        text = "特に分類できない商品"
        result = classify_category([], text)

        assert result == "Other"


class TestExtractProductName:
    def test_extract_product_name_first_block(self):
        """Test extracting product name from first valid block"""
        blocks = ["商品名テスト", "原材料名: xxx", "製造者: yyy"]
        result = extract_product_name(blocks, "")

        assert result == "商品名テスト"

    def test_extract_product_name_skip_labels(self):
        """Test skipping label blocks"""
        blocks = ["原材料名", "内容量", "実際の商品名"]
        result = extract_product_name(blocks, "")

        assert result == "実際の商品名"

    def test_extract_product_name_fallback(self):
        """Test fallback when no valid name found"""
        blocks = ["AB"]  # Too short
        result = extract_product_name(blocks, "")

        assert result == "AB"  # Falls back to first block

    def test_extract_product_name_empty(self):
        """Test with empty blocks"""
        blocks = []
        result = extract_product_name(blocks, "")

        assert result == "Unknown Product"
