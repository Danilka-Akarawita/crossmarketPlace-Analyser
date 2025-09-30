import pytest
from unittest.mock import MagicMock, patch
from scraperAbans import LenovoScraper
from pathlib import Path

@pytest.fixture
def scraper():
    """Fixture to create and clean up scraper instance."""
    lenovoscraper = LenovoScraper()
    yield lenovoscraper
    if hasattr(lenovoscraper, "driver"):
        lenovoscraper.close_driver()


@patch("scraperAbans.LenovoScraper.search_and_scrape")
def test_search_and_scrape_returns_expected(mock_scrape, scraper):
    """
    Test that search_and_scrape returns the expected product data structure.
    """
    # Mocked return value
    mock_scrape.return_value = {
        "price": 999.99,
        "in_stock": True,
        "rating": 4.5,
        "review_count": "(12)",
        "specs": {"ram": "16GB", "storage": "512GB SSD"},
    }

    result = scraper.search_and_scrape("lenovo_ideapad_5", sheduler=False)

    assert isinstance(result, dict)
    assert "price" in result
    assert "in_stock" in result
    assert "rating" in result
    assert "review_count" in result
    assert "specs" in result

    
    assert result["price"] == 999.99
    assert result["in_stock"] is True
    assert result["rating"] == 4.5
    assert result["review_count"] == "(12)"
    assert result["specs"]["ram"] == "16GB"


def test_scraper_handles_empty_result(scraper):
    """
    Ensure scraper gracefully handles empty/invalid product keys.
    """
    # Monkeypatch the method that hits the site
    scraper.search_and_scrape = MagicMock(return_value={})

    result = scraper.search_and_scrape("non_existing_model")

    assert result == {}
    scraper.search_and_scrape.assert_called_once_with("non_existing_model")


@patch("scraperAbans.LenovoScraper.search_and_scrape")
def test_scraper_handles_exceptions(mock_scrape, scraper):
    """
    Ensure scraper raises or logs error properly when scraping fails.
    """
    mock_scrape.side_effect = Exception("Network error")

    with pytest.raises(Exception) as exc:
        scraper.search_and_scrape("lenovo_ideapad_5")

    assert "Network error" in str(exc.value)
    

def test_parse_product_page_integration():
    scraper = LenovoScraper()
    scraper.setup_driver() 
    result = scraper.search_and_scrape("lenovo_ideapad_5", sheduler=False)

    assert isinstance(result, dict)
    assert "price" in result
    assert result["price"] > 0
    assert result["in_stock"] in (True, False)
    assert "specs" in result
    assert "ram" in result["specs"]

    scraper.close_driver()  