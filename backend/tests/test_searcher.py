import pytest
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.searcher import extract_prices_from_text


class TestExtractPricesFromText:
    def test_extract_yen_symbol(self):
        """Test extracting prices with yen symbol"""
        text = "商品価格 ¥1,234 送料別"
        result = extract_prices_from_text(text)

        assert 1234 in result

    def test_extract_en_suffix(self):
        """Test extracting prices with 円 suffix"""
        text = "特価 980円 税込"
        result = extract_prices_from_text(text)

        assert 980 in result

    def test_extract_comma_separated(self):
        """Test extracting comma-separated prices"""
        text = "定価 2,500円"
        result = extract_prices_from_text(text)

        assert 2500 in result

    def test_extract_multiple_prices(self):
        """Test extracting multiple prices"""
        text = "通常価格 1,000円 セール価格 800円"
        result = extract_prices_from_text(text)

        assert len(result) >= 2
        assert 1000 in result
        assert 800 in result

    def test_filter_unreasonable_prices(self):
        """Test that unreasonable prices are filtered"""
        text = "商品コード 12345 価格 50円 高額商品 500000円"
        result = extract_prices_from_text(text)

        # 50円 is below 100, should be filtered
        # 500000円 is above 100000, should be filtered
        assert 50 not in result
        assert 500000 not in result

    def test_valid_price_range(self):
        """Test valid price range (100-100000 JPY)"""
        text = "安い商品 100円 普通商品 5000円 高い商品 99999円"
        result = extract_prices_from_text(text)

        assert 100 in result
        assert 5000 in result
        assert 99999 in result

    def test_no_prices_found(self):
        """Test when no prices found"""
        text = "価格情報なし"
        result = extract_prices_from_text(text)

        assert result == []

    def test_decimal_prices(self):
        """Test extracting decimal prices"""
        text = "価格 ¥1,234.56"
        result = extract_prices_from_text(text)

        # Should extract as float
        assert any(abs(p - 1234.56) < 1 for p in result)
