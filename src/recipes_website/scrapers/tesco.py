import json
import os
import time

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService


class Scraper:
    def __init__(self, platform: str = "win"):
        """
        Initialize the Scraper with platform-specific configurations and load site configurations.
        :param platform: 'win' for Windows or 'lin' for Linux.
        """
        self.platform = platform
        # print(os.getcwd())
        # Load site configurations from JSON file
        with open("config/site_config.json", "r") as file:
            self.sites_config = json.load(file)

        self.active_site = None  # This will store the currently active site config
        self.browser = None  # Store the browser instance

    def set_active_site(self, site_name: str):
        """
        Set the active site configuration based on the site name.
        """
        if site_name in self.sites_config:
            self.active_site = self.sites_config[site_name]
        else:
            raise ValueError(f"Site '{site_name}' not found in the configuration.")

    def _create_browser(self) -> webdriver.Edge:
        """
        Internal method to create and configure the Edge WebDriver.
        """
        options = EdgeOptions()
        options.headless = False
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--disable-extensions")

        service = EdgeService()
        browser = webdriver.Edge(service=service, options=options)
        browser.maximize_window()  # Maximize the browser window
        return browser

    def get_html(self, url: str, wait_time: int = 0, keep_browser_open: bool = False) -> str:
        """
        Retrieve the HTML source of a given URL.
        
        :param url: The URL to fetch.
        :param wait_time: Time to wait for the page to load.
        :param keep_browser_open: Whether to keep the browser open after the method.
        :return: HTML source as a string.
        """
        if not self.browser:
            self.browser = self._create_browser()
        
        self.browser.get(url)
        time.sleep(wait_time)
        html_source = self.browser.page_source
        
        if not keep_browser_open:
            self.browser.quit()  # Close the browser unless specified to keep it open

        return html_source

    def fetch_all_soup(self, url: str, wait_time: int = 0, keep_browser_open: bool = False) -> BeautifulSoup:
        """
        Fetch all HTML soup code from a given URL.
        
        :param url: The URL to fetch.
        :param wait_time: Time to wait for the page to load.
        :param keep_browser_open: Whether to keep the browser open after fetching.
        :return: BeautifulSoup object containing the parsed HTML.
        """
        html_source = self.get_html(url, wait_time, keep_browser_open)
        soup = BeautifulSoup(html_source, "html.parser")
        return soup

    def get_hrefs(self, soup: BeautifulSoup, tag: str = None, class_name: str = None) -> list:
        """
        Extract hrefs from the specified tag and class name. If tag and class_name are not provided, 
        it will retrieve all hrefs from anchor tags on the page.
        
        :param soup: BeautifulSoup object.
        :param tag: Optional HTML tag to search for. Default is None, which searches for all anchor tags.
        :param class_name: Optional class name of the tag. Default is None, which ignores class.
        :return: List of hrefs.
        """
        if tag is None and class_name is None:
            # If no tag and class_name are provided, find all anchor tags with hrefs
            return [a['href'] for a in soup.find_all('a') if 'href' in a.attrs]
        elif tag is not None and class_name is None:
            # If only tag is provided, find all elements with that tag
            return [a['href'] for a in soup.find_all(tag) if 'href' in a.attrs]
        elif tag is not None and class_name is not None:
            # If both tag and class_name are provided, find elements with that tag and class
            return [a['href'] for a in soup.find_all(tag, class_=class_name) if 'href' in a.attrs]

        
    def save_data(self, df: pd.DataFrame, filename: str):
        """
        Save the scraped DataFrame to a CSV file.
        """
        df.to_csv(filename, index=False)
        print(f"Data saved to {filename}")


class TescoScraper(Scraper):
    def __init__(self, platform: str = "win"):
        super().__init__(platform)

    def scrape_tesco(self, num_pages: int = 1, max_retries: int = 3, wait_time: int = 0, keep_browser_open: bool = False) -> pd.DataFrame:
        """
        General method to scrape data from Tesco and return a DataFrame.
        """
        if not self.active_site:
            raise ValueError("No active site set. Please set the active site using set_active_site().")

        names, current_prices, regular_prices, discounts, validity_dates = [], [], [], [], []
        main_http = self.active_site["main_http"]
        links = self.active_site["links"]
        suffix = self.active_site["suffix"]

        for category in links:
            for page in range(1, num_pages + 1):
                url = f"{main_http}{category}/{suffix}{page}"
                attempt, success = 0, False

                while attempt < max_retries and not success:
                    soup = self.fetch_all_soup(url, wait_time, keep_browser_open)
                    product_list = soup.find_all("ul", {"class": "product-list grid"})

                    if not product_list:
                        print(f"No products found in category {category} on page {page}.")
                        break

                    for product in product_list[0].find_all("li", {"class": "product-list--list-item"}):
                        # Product name
                        name = product.find("span", {"class": "styled__Text-sc-1i711qa-1 xZAYu ddsweb-link__text"})
                        names.append(name.get_text() if name else "-")
                        # Current price with Clubcard
                        current_price = product.find(
                            "p",
                            {
                                "class": "text__StyledText-sc-1jpzi8m-0 dxeTiV ddsweb-text styled__ContentText-sc-1d7lp92-8 jJQEMH ddsweb-value-bar__content-text"
                            },
                        )
                        current_prices.append(
                            current_price.get_text().split("€")[0].strip() if current_price else "-"
                        )
                        # Regular price
                        regular_price = product.find(
                            "p",
                            {
                                "class": "styled__StyledHeading-sc-119w3hf-2 jWPEtj styled__Text-sc-8qlq5b-1 lnaeiZ beans-price__text"
                            },
                        )
                        regular_prices.append(
                            regular_price.get_text().split("€")[0].strip() if regular_price else "-"
                        )
                        # Discount and validity
                        discount_text = product.find("p", {"class": "ddsweb-value-bar__terms"})
                        if discount_text:
                            validity_date = (
                                discount_text.get_text().split("do")[-1].strip()
                                if "do" in discount_text.get_text()
                                else "-"
                            )
                            discounts.append(
                                discount_text.get_text().split("Clubcard")[-1].split("€")[0].strip()
                                if "Clubcard" in discount_text.get_text()
                                else "-"
                            )
                            validity_dates.append(validity_date)
                        else:
                            discounts.append("-")
                            validity_dates.append("-")

                    success = True

        df = pd.DataFrame(
            {
                "Polozka": names,
                "Nova Cena": current_prices,
                "Stara Cena": regular_prices,
                "Zlava": discounts,
                "Platnost": validity_dates,
                "Obchod": [self.active_site["main_http"]] * len(names),
            }
        )
        return df
    
    def scrape_item_info(self, url: str, wait_time: int = 3, keep_browser_open: bool = False) -> pd.DataFrame:
        # Initialize lists to hold the scraped data
        names, current_prices, regular_prices, discounts, validity_dates = [], [], [], [], []
        descriptions, ingredients, allergens, manufacturer_info, distributor_info = [], [], [], [], []
        categories = []

        try:
            # Fetch soup with the option to keep the browser open
            soup = self.fetch_all_soup(url, wait_time, keep_browser_open)
            
            # Product name
            name_element = soup.find("h1", class_="product-details-tile__title")  # Updated class name
            names.append(name_element.get_text(strip=True) if name_element else "-")

            # Current price
            current_price_element = soup.find("span", class_="price-value")
            current_prices.append(current_price_element.get_text(strip=True) if current_price_element else "-")

            # Regular price
            regular_price_element = soup.find("div", class_="price-per-sellable-unit--price-per-item")
            regular_prices.append(regular_price_element.get_text(strip=True) if regular_price_element else "-")

            # Discount and validity
            discount_element = soup.find("span", class_="offer-text")
            if discount_element:
                discount_text = discount_element.get_text(strip=True)
                discounts.append(discount_text.split("bežná cena")[0].strip() if "bežná cena" in discount_text else "-")
                validity_dates.append(discount_element.find_next("span", class_="dates").get_text(strip=True))
            else:
                discounts.append("-")
                validity_dates.append("-")

            # Description
            description_element = soup.find("div", class_="product-info-block--product-description")
            if description_element:
                descriptions.append(description_element.find("ul").get_text(strip=True))
            else:
                descriptions.append("-")

            # Ingredients
            ingredients_element = soup.find("div", class_="product-info-block--ingredients")
            if ingredients_element:
                ingredients.append(ingredients_element.find("p").get_text(strip=True))
            else:
                ingredients.append("-")

            # Allergens
            allergens_element = soup.find("div", class_="product-info-block--allergens")
            if allergens_element:
                allergens.append(allergens_element.find("ul").get_text(strip=True))
            else:
                allergens.append("-")

            # Manufacturer information
            manufacturer_element = soup.find("div", class_="product-info-block--manufacturer-address")
            if manufacturer_element:
                manufacturer_info.append(manufacturer_element.get_text(strip=True))
            else:
                manufacturer_info.append("-")

            # Distributor information
            distributor_element = soup.find("div", class_="product-info-block--distributor-address")
            if distributor_element:
                distributor_info.append(distributor_element.get_text(strip=True))
            else:
                distributor_info.append("-")

            # Find the specific <li> tag for the category link
            list_item = soup.find('li', class_='styled__ListItem-sc-li57wm-3 gesMp ddsweb-breadcrumb__list-item')
            if list_item:
                print(list_item)
                anchor = list_item.find('a')
                category_link = anchor['href'] if anchor else "-"
                categories.append(category_link)
            else:
                categories.append("-")

        except WebDriverException as e:
            print(f"Error scraping item info: {e}")

        # Create a DataFrame from the collected data
        df = pd.DataFrame({
            "Product Name": names,
            "Current Price": current_prices,
            "Regular Price": regular_prices,
            "Discount": discounts,
            "Validity Date": validity_dates,
            "Description": descriptions,
            "Ingredients": ingredients,
            "Allergens": allergens,
            "Manufacturer Info": manufacturer_info,
            "Distributor Info": distributor_info,
            "Category Link": categories  # Added category link to DataFrame
        })
        
        return df