import json
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
        # Load site configurations from JSON file
        with open("../config/site_config.json", "r") as file:
            self.sites_config = json.load(file)

        self.active_site = None  # This will store the currently active site config

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
        return browser

    def scrape_tesco(self, num_pages: int = 1, max_retries: int = 3, wait_time: int = 0) -> pd.DataFrame:
        """
        General method to scrape data from the currently active site and return a DataFrame.
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
                    browser = self._create_browser()
                    try:
                        browser.get(url)
                        time.sleep(wait_time)
                        html_source = browser.page_source
                        soup = BeautifulSoup(html_source, "html.parser")
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

                    except WebDriverException as e:
                        print(
                            f"Error loading page {page} in category {category}: {e}. Retrying {attempt + 1}/{max_retries}..."
                        )
                        attempt += 1
                        time.sleep(wait_time)

                    finally:
                        browser.quit()

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

    def save_data(self, df: pd.DataFrame, filename: str):
        """
        Save the scraped DataFrame to a CSV file.
        """
        df.to_csv(filename, index=False)
        print(f"Data saved to {filename}")


# Example usage:
scraper = Scraper(platform="win")
scraper.set_active_site("tesco")
tesco_data = scraper.scrape_tesco(num_pages=1)
scraper.save_data(tesco_data, "tesco_promotions.csv")
