from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
from typing import Dict, Optional
from models import AvailabilityStatus
import time

class BaseScraper:
    def __init__(self):
        self.driver = None

    def setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        # chrome_options.add_argument("--headless")  # Optional
        self.driver = webdriver.Chrome(options=chrome_options)

    def close_driver(self):
        if self.driver:
            self.driver.quit()

class LenovoScraper(BaseScraper):
    BASE_URL = "https://www.lenovo.com"

    def search_and_scrape(self, model_name: str) -> Optional[Dict]:
        self.driver.get(f"{self.BASE_URL}/us/en")
        
        # Wait for search box
        search_box = WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.ID, "commonHeaderSearch"))
        )
        search_box.clear()
        search_box.send_keys(model_name)
        search_box.send_keys(u'\ue007')  # Press Enter

        # Wait for first product
        try:
            first_product = WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "li.product_item .product_title a")))
            url = first_product.get_attribute("href")
            self.driver.get(url)
            print("Navigating to:", url)
            time.sleep(3)  # wait for JS content to load

            return self.scrape_product_page()
        except:
            print("No products found for model:", model_name)
            return None

    def scrape_product_page(self) -> Dict:
        soup = BeautifulSoup(self.driver.page_source, "html.parser")

        # Product title
        try:
            name = soup.find("h1", class_="product_summary").text.strip()
        except:
            name = None

        # Price
        try:
            price_span = soup.find("span", class_="price")
            price=price_span.text.strip()
            discount_span = soup.find("span", class_="price-save-mt")
            discount = discount_span.text.strip() if discount_span else None
        except:
            price = None

        # Rating
        try:
            rating = soup.select_one(".card-review-inline .bv_text").get_text(strip=True)
        except:
            rating = None

        # Review count
        try:
            review_count = soup.select_one(".card-review-inline .bv_numReviews_component_container .bv_text").get_text(strip=True)
        except:
            review_count = None

        # Specs
        specs = {}
        spec_items = soup.select("div.specs_list div.specs_item")

        for item in spec_items:
            name_tag = item.find("div", class_="item_name")
            content_tag = item.find("div", class_="item_content")
            if name_tag and content_tag:
                specs[name_tag.text.strip()] = content_tag.text.strip()
        try:
            stock_button = soup.select_one("button.buyNowBtn, button.outOfStock")
            if stock_button and "out of stock" in stock_button.text.lower():
                availability = AvailabilityStatus.OUT_OF_STOCK.value
                
            else:
                availability = AvailabilityStatus.IN_STOCK.value
        except:
            availability = AvailabilityStatus.OUT_OF_STOCK.value
        return {
            "title": name,
            "price": price,
            "discount": discount,
            "rating": rating,
            "review_count": review_count,
            "specs": specs,
            "in_stock": availability
        }


# if __name__ == "__main__":
#     model = 'ThinkPad E14 Gen 5 (AMD)'
#     scraper = LenovoScraper()
#     scraper.setup_driver()
#     data = scraper.search_and_scrape(model)
#     print(data)
#     scraper.close_driver()
