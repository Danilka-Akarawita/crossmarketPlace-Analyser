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
import re


class BaseScraper:
    def __init__(self):
        self.driver = None

    def setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        # chrome_options.add_argument("--headless")  #
        self.driver = webdriver.Chrome(options=chrome_options)

    def close_driver(self):
        if self.driver:
            self.driver.quit()


class HpScraper(BaseScraper):
    BASE_URL = "https://laptopcare.lk"

    def search_and_scrape(self, model_name: str, scheduler: bool) -> Optional[Dict]:
        self.driver.get(self.BASE_URL)

        search_box = WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='s']"))
        )

        try:
            category_dropdown = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "select[name='term']"))
            )
            from selenium.webdriver.support.ui import Select

            Select(category_dropdown).select_by_value("laptop")
        except:
            pass

        # Type model name
        search_box.clear()
        search_box.send_keys(model_name)
        search_box.send_keys("\ue007")

        # Click search button instead of hitting Enter
        # submit_button = WebDriverWait(self.driver, 5).until(
        #     EC.element_to_be_clickable((By.CSS_SELECTOR, "div.search-button input[type='submit']"))
        # )
        # submit_button.click()

        try:
            first_product = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, ".products section.product a")
                )
            )
            url = first_product.get_attribute("href")
            self.driver.get(url)
            print("Navigating to:", url)
            time.sleep(3)

            if scheduler:
                return self.scrape_price_and_reviews()
            else:
                return self.scrape_product_page()
        except Exception as e:
            print("No products found for model:", model_name, e)
            return None

    def scrape_product_page(self) -> Dict:
        soup = BeautifulSoup(self.driver.page_source, "html.parser")

        # Title
        try:
            name = soup.find("h1", class_="product_title").text.strip()
        except:
            name = None

        # Price
        try:
            raw_price = soup.select_one(
                "p.price span.woocommerce-Price-amount"
            ).get_text(strip=True)
            price = self.clean_price(raw_price)
        except:
            price = None

        try:
            discount = soup.select_one(
                "p.price del .woocommerce-Price-amount"
            ).get_text(strip=True)
        except:
            discount = None

        # Stock availability
        try:
            stock_status = soup.select_one("p.stock, .availability")
            if (
                stock_status
                and "out of stock" in stock_status.get_text(strip=True).lower()
            ):
                availability = AvailabilityStatus.OUT_OF_STOCK.value
            else:
                availability = AvailabilityStatus.IN_STOCK.value
        except:
            availability = AvailabilityStatus.OUT_OF_STOCK.value

        # Specs (from short description <ul><li>)
        specs = {}
        try:
            short_desc = soup.select_one(
                "div.woocommerce-product-details__short-description ul"
            )
            if short_desc:
                for li in short_desc.find_all("li"):
                    text = li.get_text(" ", strip=True)
                    if ":" in text:
                        key, val = text.split(":", 1)
                        specs[key.strip()] = val.strip()
                    else:
                        specs[f"feature_{len(specs)+1}"] = text
        except:
            pass

        # Images
        images = []
        try:
            gallery = soup.select("div.woocommerce-product-gallery__image a img")
            for img in gallery:
                src = img.get("src")
                if src and src not in images:
                    images.append(src)
        except:
            pass

        return {
            "title": name,
            "price": price,
            "discount": discount,
            "specs": specs,
            "in_stock": availability,
            "images": images,
        }

    def clean_price(self, price_str: str) -> float:
        if not price_str:
            return None
        cleaned = re.sub(r"[^\d.]", "", price_str)
        try:
            return float(cleaned)
        except ValueError:
            return None

    def scrape_price_and_reviews(self) -> Dict:
        """Light scrape: only price, discount, stock"""
        soup = BeautifulSoup(self.driver.page_source, "html.parser")

        try:
            raw_price = soup.select_one(
                "p.price span.woocommerce-Price-amount"
            ).get_text(strip=True)
            price = self.clean_price(raw_price)
        except:
            price = None

        try:
            discount = soup.select_one(
                "p.price del .woocommerce-Price-amount"
            ).get_text(strip=True)
        except:
            discount = None

        try:
            stock_status = soup.select_one("p.stock")
            if (
                stock_status
                and "out of stock" in stock_status.get_text(strip=True).lower()
            ):
                availability = AvailabilityStatus.OUT_OF_STOCK.value
            else:
                availability = AvailabilityStatus.IN_STOCK.value
        except:
            availability = AvailabilityStatus.OUT_OF_STOCK.value

        return {
            "price": price,
            "discount": discount,
            "in_stock": availability,
        }


class LenovoScraper(BaseScraper):
    BASE_URL = "https://www.lenovo.com"

    def search_and_scrape(self, model_name: str, scheduler: bool) -> Optional[Dict]:
        self.driver.get(f"{self.BASE_URL}/us/en")

        # Wait for search box
        search_box = WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.ID, "commonHeaderSearch"))
        )
        search_box.clear()
        search_box.send_keys(model_name)
        search_box.send_keys("\ue007")  # Press Enter

        # Wait for first product
        try:
            first_product = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "li.product_item .product_title a")
                )
            )
            url = first_product.get_attribute("href")
            self.driver.get(url)
            print("Navigating to:", url)
            time.sleep(3)  # wait for JS content to load

            if scheduler:
                return self.scrape_price_and_reviews()
            else:
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
            price = price_span.text.strip()
            discount_span = soup.find("span", class_="price-save-mt")
            discount = discount_span.text.strip() if discount_span else None
        except:
            price = None

        # Rating
        try:
            rating = soup.select_one(".card-review-inline .bv_text").get_text(
                strip=True
            )
        except:
            rating = None

        # Review count
        try:
            review_count = soup.select_one(
                ".card-review-inline .bv_numReviews_component_container .bv_text"
            ).get_text(strip=True)
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
            "in_stock": availability,
        }

    def scrape_price_and_reviews(self) -> Dict:
        """Light scrape: only price, discount, rating, review count, availability."""
        time.sleep(2)  # let JS load
        soup = BeautifulSoup(self.driver.page_source, "html.parser")

        try:
            price_span = soup.find("span", class_="price")
            price = price_span.text.strip() if price_span else None
            discount_span = soup.find("span", class_="price-save-mt")
            discount = discount_span.text.strip() if discount_span else None
        except:
            price = discount = None

        # Rating + reviews
        try:
            rating = soup.select_one(".card-review-inline .bv_text").get_text(
                strip=True
            )
        except:
            rating = None
        try:
            review_count = soup.select_one(
                ".card-review-inline .bv_numReviews_component_container .bv_text"
            ).get_text(strip=True)
        except:
            review_count = None

        # Stock
        try:
            stock_button = soup.select_one("button.buyNowBtn, button.outOfStock")
            if stock_button and "out of stock" in stock_button.text.lower():
                availability = AvailabilityStatus.OUT_OF_STOCK.value
            else:
                availability = AvailabilityStatus.IN_STOCK.value
        except:
            availability = AvailabilityStatus.OUT_OF_STOCK.value

        return {
            "price": price,
            "discount": discount,
            "rating": rating,
            "review_count": review_count,
            "in_stock": availability,
        }


# if __name__ == "__main__":
#     model = 'HP ProBook 450 G10'
#     scraper = HpScraper()
#     scraper.setup_driver()
#     data = scraper.search_and_scrape(model, scheduler=False)
#     print(data)
#     scraper.close_driver()
