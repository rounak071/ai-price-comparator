
from urllib.parse import quote_plus


def compare_prices(product_name):
    """Create shopping search links for a product."""

    query = quote_plus(product_name.strip())

    if not query:
        return []

    return [
        {
            "store": "Amazon India",
            "search_url": f"https://www.amazon.in/s?k={query}",
        },
        {
            "store": "Flipkart",
            "search_url": f"https://www.flipkart.com/search?q={query}",
        },
        {
            "store": "Google Shopping",
            "search_url": f"https://www.google.com/search?tbm=shop&q={query}",
        },
    ]
