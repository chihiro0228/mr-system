from typing import Optional, List, Dict
from duckduckgo_search import DDGS
import re
import time


def find_price(query: str) -> Optional[str]:
    """
    Search for product price using DuckDuckGo.
    Returns formatted price string or "Price not found".
    """
    print(f"Searching for price: {query}")

    try:
        # Enhanced query for Japanese e-commerce
        search_query = f"{query} 価格 通販"

        with DDGS() as ddgs:
            # Search with Japan region
            results = list(ddgs.text(search_query, region='jp-jp', max_results=5))

            if not results:
                return "Price not found"

            # Extract prices from results
            prices = []
            for result in results:
                snippet = result.get('body', '') + ' ' + result.get('title', '')
                extracted_prices = extract_prices_from_text(snippet)
                prices.extend(extracted_prices)

            if prices:
                # Return average price
                avg_price = sum(prices) / len(prices)
                return f"{int(avg_price)}円"

            return "Price not found"

    except Exception as e:
        print(f"Price search error: {e}")
        return "Price search failed"


def find_tax_excluded_price(query: str) -> Optional[str]:
    """
    Search for tax-excluded price using DuckDuckGo.
    Returns formatted price string or None.
    """
    print(f"Searching for tax-excluded price: {query}")

    try:
        # Query specifically for tax-excluded price
        search_query = f"{query} 税抜き 価格"

        with DDGS() as ddgs:
            results = list(ddgs.text(search_query, region='jp-jp', max_results=5))

            if not results:
                # Try alternative query
                search_query = f"{query} 本体価格"
                results = list(ddgs.text(search_query, region='jp-jp', max_results=5))

            if not results:
                return None

            # Extract prices from results
            prices = []
            for result in results:
                snippet = result.get('body', '') + ' ' + result.get('title', '')
                # Look for tax-excluded patterns
                extracted_prices = extract_tax_excluded_prices(snippet)
                prices.extend(extracted_prices)

            if prices:
                avg_price = sum(prices) / len(prices)
                return f"{int(avg_price)}円(税抜)"

            return None

    except Exception as e:
        print(f"Tax-excluded price search error: {e}")
        return None


def find_all_prices(product_name: str, manufacturer: str = "") -> Dict[str, Optional[str]]:
    """
    Search for both regular and tax-excluded prices.
    Returns dict with 'price_info' and 'price_tax_excluded'.
    """
    query = f"{product_name} {manufacturer}".strip()

    result = {
        "price_info": find_price(query),
        "price_tax_excluded": find_tax_excluded_price(query)
    }

    return result


def extract_tax_excluded_prices(text: str) -> List[float]:
    """
    Extract tax-excluded price values from text.
    Patterns: 税抜XXX円, 本体価格XXX円, (税抜)XXX円
    """
    prices = []

    # Patterns for tax-excluded prices
    patterns = [
        r'税抜[^\d]*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*円?',  # 税抜1,234円
        r'本体[^\d]*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*円?',  # 本体価格1,234円
        r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*円?\s*[\(（]税抜',  # 1,234円(税抜)
        r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*円?\s*[\+＋]税',  # 1,234円+税
    ]

    for pattern in patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            try:
                price_str = match.group(1).replace(',', '')
                price = float(price_str)
                if 100 <= price <= 100000:
                    prices.append(price)
            except ValueError:
                continue

    return prices

def extract_prices_from_text(text: str) -> List[float]:
    """
    Extract price values from text.
    Patterns: ¥XXX, XXX円, XXX,XXX円
    """
    prices = []

    # Patterns for Japanese price formats
    patterns = [
        r'¥\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',  # ¥1,234
        r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*円',  # 1,234円
        r'(\d{3,})\s*円',  # 1234円 (no comma)
    ]

    for pattern in patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            try:
                # Remove commas and convert to float
                price_str = match.group(1).replace(',', '')
                price = float(price_str)

                # Filter reasonable price range (100-100000 JPY)
                if 100 <= price <= 100000:
                    prices.append(price)
            except ValueError:
                continue

    return prices

def find_price_from_sites(product_name: str, manufacturer: str) -> Optional[str]:
    """
    Enhanced search targeting specific e-commerce sites.
    """
    # Target sites for better price accuracy
    sites = [
        'amazon.co.jp',
        'rakuten.co.jp',
        'kakaku.com',
        'yahoo.co.jp'
    ]

    all_prices = []

    for site in sites:
        query = f"site:{site} {product_name} {manufacturer} 価格"
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, region='jp-jp', max_results=2))
                for result in results:
                    snippet = result.get('body', '') + ' ' + result.get('title', '')
                    prices = extract_prices_from_text(snippet)
                    all_prices.extend(prices)
            time.sleep(0.5)  # Rate limiting
        except:
            continue

    if all_prices:
        avg_price = sum(all_prices) / len(all_prices)
        return f"{int(avg_price)} JPY (avg from {len(all_prices)} sources)"

    return None


def is_japanese_or_trusted_url(url: str) -> bool:
    """
    Check if URL is from Japanese domain or trusted international sites.
    """
    trusted_patterns = [
        '.jp',           # Japanese TLD
        '.co.jp',        # Japanese commercial
        'amazon.com',    # Amazon global (often redirects to .co.jp)
    ]

    blocked_patterns = [
        '.cn',           # China
        'baidu.com',     # Chinese search engine
        'zhidao.baidu',  # Chinese Q&A site
        'alibaba.com',   # Chinese e-commerce
        'taobao.com',    # Chinese e-commerce
        'aliexpress.com',# Chinese e-commerce
        '.ru',           # Russia
        '.kr',           # Korea (unless specifically needed)
    ]

    url_lower = url.lower()

    # Block untrusted domains
    for blocked in blocked_patterns:
        if blocked in url_lower:
            return False

    # Prefer trusted domains
    for trusted in trusted_patterns:
        if trusted in url_lower:
            return True

    # Allow other URLs but with lower priority (return True for now)
    return True


def find_product_url(product_name: str, manufacturer: str = "") -> Optional[str]:
    """
    Search for official product page URL.
    Priority: Official site > Amazon > Rakuten > Yahoo
    """
    print(f"Searching for product URL: {product_name} {manufacturer}")

    query = f"{product_name} {manufacturer}".strip()

    try:
        with DDGS() as ddgs:
            # First, try to find official manufacturer site
            if manufacturer:
                official_query = f"{query} 公式 商品"
                results = list(ddgs.text(official_query, region='jp-jp', max_results=5))

                for result in results:
                    url = result.get('href', '')
                    # Check if it's likely an official site (not e-commerce) and is Japanese/trusted
                    if url and is_japanese_or_trusted_url(url) and not any(ec in url.lower() for ec in ['amazon', 'rakuten', 'yahoo', 'kakaku', 'mercari', 'yodobashi']):
                        # Prefer manufacturer name in URL
                        manufacturer_lower = manufacturer.lower().replace(' ', '')
                        if manufacturer_lower in url.lower().replace('-', '').replace('_', ''):
                            return url

                # Return first non-ecommerce result if no manufacturer match
                for result in results:
                    url = result.get('href', '')
                    if url and is_japanese_or_trusted_url(url) and not any(ec in url.lower() for ec in ['amazon', 'rakuten', 'yahoo', 'kakaku', 'mercari']):
                        return url

            # Fallback: Search e-commerce sites
            ecommerce_sites = [
                ('amazon.co.jp', 'Amazon'),
                ('rakuten.co.jp', 'Rakuten'),
                ('shopping.yahoo.co.jp', 'Yahoo')
            ]

            for site_domain, site_name in ecommerce_sites:
                site_query = f"site:{site_domain} {query}"
                try:
                    results = list(ddgs.text(site_query, region='jp-jp', max_results=1))
                    if results:
                        url = results[0].get('href', '')
                        if url and is_japanese_or_trusted_url(url):
                            return url
                    time.sleep(0.3)
                except:
                    continue

            return None

    except Exception as e:
        print(f"Product URL search error: {e}")
        return None


def find_all_product_info(product_name: str, manufacturer: str = "") -> Dict[str, Optional[str]]:
    """
    Search for price info, tax-excluded price, and product URL.
    Returns dict with 'price_info', 'price_tax_excluded', and 'product_url'.
    """
    query = f"{product_name} {manufacturer}".strip()

    result = {
        "price_info": find_price(query),
        "price_tax_excluded": find_tax_excluded_price(query),
        "product_url": find_product_url(product_name, manufacturer)
    }

    return result
