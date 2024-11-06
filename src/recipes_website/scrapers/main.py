from recipes_website.core._data_prep import (
    get_max_page_number,
    match_urls,
)
from tesco import Scraper

# # Example usage:
# scraper = TescoScraper(platform="win")
# scraper.set_active_site("tesco")
# tesco_data = scraper.scrape_tesco(num_pages=5, keep_browser_open=False)  # Change to True to keep the browser open
# scraper.save_data(tesco_data, "tesco_promotions.csv")


# # Example usage for a specific item:
item_url = "https://potravinydomov.itesco.sk/groceries/en-GB/shop/meat-fish-and-delicatessen/all"  # Replace with the actual item URL
# item_info_df = scraper.scrape_item_info(item_url)
# print(item_info_df)


pattern = "/groceries/en-GB/shop/"
pattern_2 = "Go to results page"

# Scraper
scraper = Scraper(platform="win")
soup = scraper.fetch_all_soup(item_url)
hrefs = scraper.get_hrefs(soup=soup)
urls_categories = match_urls(hrefs,pattern=pattern)
cleaned_urls = [url.split('?')[0] for url in urls_categories]

# Get the pagination items (all <li> elements containing pagination links)
pagination_items = soup.find_all("li", class_="pagination-btn-holder")

# Find the maximum page number
max_page = get_max_page_number(pagination_items)





