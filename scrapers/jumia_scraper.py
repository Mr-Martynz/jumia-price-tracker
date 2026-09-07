"""
Jumia Product Scraper
Scrapes product data from a specific category page.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
from datetime import datetime

def clean_price(price_text):
    """Converts a price string like '₦ 250,000' to a float 250000.0."""
    if not price_text or price_text == 'N/A':
        return None
    # Remove the Naira symbol and commas, then convert to float
    cleaned = price_text.replace('₦', '').replace(',', '').strip()
    try:
        return float(cleaned)
    except ValueError:
        return None

def scrape_jumia_category(category_url, pages=1):
    """
    Scrapes product data from a Jumia category URL.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    all_products = []

    print(f"🌐 Starting scrape for: {category_url}")

    for page in range(1, pages + 1):
        # Jumia often uses '?page=' for pagination
        page_url = f"{category_url}?page={page}"
        print(f"   📄 Fetching page {page}...")

        try:
            response = requests.get(page_url, headers=headers, timeout=10)
            response.raise_for_status()  # Raise an error for bad status codes

            soup = BeautifulSoup(response.content, 'html.parser')

            # --- ADAPT THIS SECTION ---
            # **CRITICAL:** You must inspect Jumia's HTML to get the right selectors.
            # Right-click on a product and "Inspect" to find the correct class names.
            # Common product container classes on Jumia are 'prd _fb col c-prd' or 'sku -gallery'.
            product_articles = soup.find_all('article', class_='prd _fb col c-prd')

            if not product_articles:
                print("   ⚠️ No products found. Check your CSS selector.")
                break

            for article in product_articles:
                # Extract Name
                name_tag = article.find('h3', class_='name')
                name = name_tag.text.strip() if name_tag else 'N/A'

                # Extract Current Price
                price_tag = article.find('div', class_='prc')
                price_text = price_tag.text.strip() if price_tag else 'N/A'
                price = clean_price(price_text)

                # Extract Original Price (if on sale)
                old_price_tag = article.find('div', class_='old')
                old_price_text = old_price_tag.text.strip() if old_price_tag else 'N/A'
                old_price = clean_price(old_price_text)

                # Extract Product Link
                link_tag = article.find('a', class_='core')
                link = link_tag['href'] if link_tag and link_tag.has_attr('href') else 'N/A'
                # Ensure the link is absolute
                if link != 'N/A' and not link.startswith('http'):
                    link = 'https://www.jumia.com.ng' + link

                # Extract Rating (if available)
                rating_tag = article.find('div', class_='stars _s')
                rating_text = rating_tag.text.strip() if rating_tag else 'No rating'

                product_data = {
                    'product_name': name,
                    'price_ngn': price,
                    'original_price_ngn': old_price,
                    'product_url': link,
                    'rating': rating_text,
                    'scrape_date': datetime.now().strftime('%Y-%m-%d'),
                    'source_site': 'Jumia'
                }
                all_products.append(product_data)

            # Be respectful to the server
            time.sleep(2)

        except requests.exceptions.RequestException as e:
            print(f"   ❌ Error fetching page {page}: {e}")
            break

    print(f"✅ Scraping complete. Found {len(all_products)} products.")
    return all_products

if __name__ == "__main__":
    # --- START HERE: Define the category you want to scrape ---
    # Example: Jumia's "Mobile Phones" category
    TARGET_URL = "https://www.jumia.com.ng/mlp/mobile-phones/"
    NUMBER_OF_PAGES = 2  # Start small for testing

    scraped_data = scrape_jumia_category(TARGET_URL, pages=NUMBER_OF_PAGES)

    if scraped_data:
        # Create a DataFrame
        df = pd.DataFrame(scraped_data)

        # Create output directory if it doesn't exist
        output_dir = '../data'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Save to CSV with a timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{output_dir}/jumia_phones_{timestamp}.csv'
        df.to_csv(filename, index=False)
        print(f"💾 Data saved to {filename}")

        # Display a quick summary
        print("\n📊 First 5 products:")
        print(df[['product_name', 'price_ngn', 'rating']].head())
    else:
        print("❌ No data scraped.")