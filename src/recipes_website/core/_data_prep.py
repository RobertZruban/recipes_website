import re

from bs4 import BeautifulSoup


def match_urls(urls: list, pattern:str) -> list:
    """
    """
    matching_urls = [url for url in urls if isinstance(url, str) and re.match(pattern, url)]
    return matching_urls


def get_max_page_number(pagination_items: list) -> int:
    """
    Extracts the maximum page number from the pagination buttons in a list of <li> elements.
    
    :param pagination_items: List of BeautifulSoup <li> elements (ResultSet).
    :return: Maximum page number.
    """
    # Extract page numbers from the 'href' attribute and convert them to integers
    page_numbers = []
    for item in pagination_items:
        # Find the <a> tag inside each <li>
        a_tag = item.find('a', href=re.compile(r"page=(\d+)"))
        if a_tag:
            href = a_tag.get("href", "")
            match = re.search(r"page=(\d+)", href)
            if match:
                page_numbers.append(int(match.group(1)))
    
    # Return the maximum page number, or 1 if no pages were found
    return max(page_numbers) if page_numbers else 1