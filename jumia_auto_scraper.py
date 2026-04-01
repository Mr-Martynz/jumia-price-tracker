"""
FULLY AUTOMATED JUMIA NIGERIA SCRAPER
No hardcoded selectors - adapts to ANY Jumia page structure
Just give it a URL and it works
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import json
from datetime import datetime
import os
from urllib.parse import urljoin

class JumiaAutoScraper:
    """
    Scrapes ANY Jumia Nigeria page automatically
    Finds products, prices, names, ratings, shipping info
    """
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
    def fetch_page(self, url):
        """Fetch a page with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"   📡 Attempt {attempt + 1} to fetch page...")
                response = self.session.get(url, timeout=15)
                response.raise_for_status()
                
                # Check if we got blocked
                if "Access Denied" in response.text or "captcha" in response.text.lower():
                    print("   ⚠️ Possible block detected, retrying with different headers...")
                    # Rotate user agent
                    self.headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                    self.session.headers.update(self.headers)
                    continue
                    
                return response.text
                
            except requests.exceptions.RequestException as e:
                print(f"   ⚠️ Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(3)
                else:
                    raise Exception(f"Failed to fetch page after {max_retries} attempts: {e}")
    
    def analyze_page_structure(self, soup):
        """
        AUTOMATICALLY analyze the page structure
        Finds where products are stored without hardcoding
        """
        print("\n   🔍 Analyzing page structure...")
        
        structure = {
            'product_containers': [],
            'price_patterns': [],
            'name_patterns': [],
            'total_products': 0
        }
        
        # METHOD 1: Look for common Jumia patterns
        print("   Looking for Jumia-specific patterns...")
        
        # Jumia often uses 'article' tags with specific classes
        jumia_patterns = [
            ('article', ['prd', 'product', 'item']),
            ('div', ['sku', 'gallery', 'product']),
            ('div', ['info', 'details']),
            ('a', ['core', 'link'])
        ]
        
        for tag, classes in jumia_patterns:
            elements = soup.find_all(tag)
            for element in elements:
                if element.has_attr('class'):
                    element_classes = ' '.join(element['class']).lower()
                    # Check if any target class is in this element
                    for target in classes:
                        if target in element_classes:
                            structure['product_containers'].append(element)
                            break
        
        # METHOD 2: Look for data attributes (modern websites use these)
        print("   Looking for data attributes...")
        data_attrs = soup.find_all(attrs={
            'data-component': re.compile(r'.*'),
            'data-product': re.compile(r'.*'),
            'data-sku': re.compile(r'.*')
        })
        structure['product_containers'].extend(data_attrs)
        
        # METHOD 3: Find by price proximity (anything near ₦ symbol)
        print("   Looking for price patterns...")
        price_indicators = soup.find_all(string=re.compile(r'₦|N\s*\d+'))
        for indicator in price_indicators[:10]:  # Check first 10
            parent = indicator.parent
            # Go up until we find a container that might hold a product
            for _ in range(5):  # Check up to 5 levels up
                if parent and parent not in structure['product_containers']:
                    # Check if this parent seems like a product container
                    text_length = len(parent.get_text(strip=True))
                    if 50 < text_length < 1000:  # Product containers have moderate text
                        structure['product_containers'].append(parent)
                        break
                if parent:
                    parent = parent.parent
                else:
                    break
        
        # Remove duplicates while preserving order
        seen = set()
        unique_containers = []
        for container in structure['product_containers']:
            container_id = id(container)
            if container_id not in seen:
                seen.add(container_id)
                unique_containers.append(container)
        
        structure['product_containers'] = unique_containers
        structure['total_products'] = len(unique_containers)
        
        print(f"   ✅ Found {len(unique_containers)} potential product containers")
        return structure
    
    def extract_any_price(self, text):
        """
        Find ANY price format in text
        Handles: ₦1,234, N1234, 1,234.56, etc.
        """
        if not text:
            return None
            
        # Convert to string if needed
        text = str(text)
        
        # Pattern 1: ₦ with numbers
        naira_pattern = r'₦\s*([\d,]+(?:\.\d{2})?)'
        match = re.search(naira_pattern, text)
        if match:
            price_str = match.group(1).replace(',', '')
            try:
                return float(price_str)
            except:
                pass
        
        # Pattern 2: N with numbers (alternative notation)
        n_pattern = r'N\s*([\d,]+(?:\.\d{2})?)'
        match = re.search(n_pattern, text)
        if match:
            price_str = match.group(1).replace(',', '')
            try:
                return float(price_str)
            except:
                pass
        
        # Pattern 3: Just numbers with commas (likely a price)
        number_pattern = r'([\d,]+(?:\.\d{2})?)'
        matches = re.findall(number_pattern, text)
        for match in matches:
            # Clean and check if it's a reasonable price
            clean_num = match.replace(',', '')
            try:
                num = float(clean_num)
                if 100 < num < 1000000:  # Nigerian product prices are between ₦100 and ₦1M
                    return num
            except:
                continue
        
        return None
    
    def extract_product_name(self, container):
        """
        Intelligently find the product name
        """
        # Try headings first
        headings = container.find_all(['h1', 'h2', 'h3', 'h4', 'strong'])
        for heading in headings:
            text = heading.get_text(strip=True)
            # Product names are usually 10+ chars and don't contain prices
            if len(text) > 10 and '₦' not in text and 'N' not in text:
                # Check if it's mostly letters (not just numbers)
                if sum(c.isalpha() for c in text) > len(text) * 0.3:
                    return text
        
        # Try links (product names are often in links)
        links = container.find_all('a', href=True)
        for link in links:
            text = link.get_text(strip=True)
            if len(text) > 15 and '₦' not in text:
                return text
        
        # Try any element with product-related class
        for element in container.find_all(class_=re.compile(r'name|title|product', re.I)):
            text = element.get_text(strip=True)
            if len(text) > 10:
                return text
        
        # Last resort: get the longest text that's not full of numbers
        all_text = container.get_text(strip=True).split('\n')
        longest = ''
        for line in all_text:
            line = line.strip()
            if len(line) > len(longest) and len(line) < 200 and '₦' not in line:
                # Check if it's not mostly numbers
                if sum(c.isdigit() for c in line) < len(line) * 0.3:
                    longest = line
        
        return longest if longest else None
    
    def extract_product_url(self, container, base_url):
        """
        Find the product URL
        """
        links = container.find_all('a', href=True)
        for link in links:
            href = link['href']
            # Look for product links (usually contain product identifiers)
            if '/product/' in href or '/p-' in href or 'catalog' in href:
                return urljoin(base_url, href)
        
        # If no obvious product link, take first substantial link
        for link in links:
            href = link['href']
            if href and not href.startswith('#') and len(href) > 10:
                return urljoin(base_url, href)
        
        return None
    
    def extract_rating(self, container):
        """
        Extract product rating if available
        """
        # Look for stars or rating text
        rating_patterns = [
            r'(\d+(?:\.\d+)?)\s*out of\s*5',
            r'(\d+(?:\.\d+)?)\s*stars?',
            r'rating[:\s]*(\d+(?:\.\d+)?)',
            r'(\d+)%\s*positive'
        ]
        
        text = container.get_text()
        for pattern in rating_patterns:
            match = re.search(pattern, text, re.I)
            if match:
                try:
                    return float(match.group(1))
                except:
                    pass
        
        # Look for star images/classes
        stars = container.find_all(class_=re.compile(r'star|rating', re.I))
        if stars:
            # Count filled stars
            star_text = ' '.join([s.get('class', [''])[0] for s in stars])
            filled = len(re.findall(r'filled|active|full', star_text))
            if filled > 0:
                return filled
        
        return None
    
    def extract_shipping_info(self, container):
        """
        Extract shipping/delivery info
        """
        shipping_texts = container.find_all(string=re.compile(r'delivery|shipping|free|express', re.I))
        shipping = []
        for text in shipping_texts[:3]:  # Limit to 3 matches
            text = text.strip()
            if len(text) < 100:  # Avoid huge blocks
                shipping.append(text)
        
        return ' | '.join(shipping) if shipping else None
    
    def extract_original_price(self, container):
        """
        Extract original price (if on sale)
        """
        # Look for struck-through prices
        strike = container.find_all(['span', 'div'], class_=re.compile(r'old|was|before|strike', re.I))
        for element in strike:
            price = self.extract_any_price(element.get_text())
            if price:
                return price
        
        # Look for "was" text
        was_text = container.find_all(string=re.compile(r'was\s*₦|was\s*N', re.I))
        for text in was_text:
            price = self.extract_any_price(text)
            if price:
                return price
        
        return None
    
    def extract_discount(self, container):
        """
        Extract discount percentage
        """
        discount_text = container.find_all(string=re.compile(r'-?\d+%\s*off', re.I))
        for text in discount_text:
            match = re.search(r'(\d+)%\s*off', text, re.I)
            if match:
                return int(match.group(1))
        
        # Look for percentage in classes
        for element in container.find_all(class_=re.compile(r'percent|discount', re.I)):
            text = element.get_text()
            match = re.search(r'(\d+)%', text)
            if match:
                return int(match.group(1))
        
        return None
    
    def scrape_page(self, url, max_products=50):
        """
        Main scraping method - fully automated
        """
        print(f"\n{'='*60}")
        print(f"🛒 JUMIA AUTOMATIC SCRAPER")
        print(f"{'='*60}")
        print(f"📌 URL: {url}")
        
        # Fetch the page
        print("\n📡 Fetching page...")
        html = self.fetch_page(url)
        soup = BeautifulSoup(html, 'html.parser')
        print("✅ Page fetched successfully")
        
        # Analyze page structure
        structure = self.analyze_page_structure(soup)
        containers = structure['product_containers']
        
        if not containers:
            print("\n❌ Could not find any products on this page")
            print("   This might happen if Jumia has changed their structure")
            print("   Trying emergency extraction method...")
            
            # Emergency: look for ANYTHING with price-like text
            all_elements = soup.find_all(['div', 'article', 'li'])
            for element in all_elements:
                if '₦' in element.get_text():
                    containers.append(element)
                    if len(containers) >= 10:
                        break
        
        print(f"\n📦 Found {len(containers)} potential products")
        
        # Extract data from each container
        products = []
        print("\n🔍 Extracting product data...")
        
        for i, container in enumerate(containers[:max_products]):
            if i % 10 == 0 and i > 0:
                print(f"   Processed {i}/{min(len(containers), max_products)} products...")
            
            try:
                # Get all text for debugging
                preview = container.get_text(strip=True)[:100].replace('\n', ' ')
                
                product = {
                    'name': self.extract_product_name(container),
                    'price': self.extract_any_price(container.get_text()),
                    'url': self.extract_product_url(container, url),
                    'rating': self.extract_rating(container),
                    'shipping': self.extract_shipping_info(container),
                    'original_price': self.extract_original_price(container),
                    'discount_percent': self.extract_discount(container),
                    'scrape_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'source_url': url
                }
                
                # Only add if we have at least name and price
                if product['name'] and product['price']:
                    # Clean name (remove extra whitespace)
                    product['name'] = ' '.join(product['name'].split())
                    products.append(product)
                    
            except Exception as e:
                print(f"   ⚠️ Error extracting product {i+1}: {e}")
                continue
        
        print(f"\n✅ Successfully extracted {len(products)} products with complete data")
        return products
    
    def scrape_multiple_pages(self, base_url, num_pages=3):
        """
        Scrape multiple pages automatically
        """
        all_products = []
        
        for page in range(1, num_pages + 1):
            print(f"\n{'='*60}")
            print(f"📄 PAGE {page} OF {num_pages}")
            print(f"{'='*60}")
            
            # Construct page URL (Jumia uses ?page=)
            if '?' in base_url:
                page_url = f"{base_url}&page={page}"
            else:
                page_url = f"{base_url}?page={page}"
            
            products = self.scrape_page(page_url)
            all_products.extend(products)
            
            # Be respectful between pages
            if page < num_pages:
                print(f"\n⏳ Waiting 3 seconds before next page...")
                time.sleep(3)
        
        return all_products
    
    def save_results(self, products, filename=None):
        """
        Save results in multiple formats
        """
        if not products:
            print("❌ No products to save")
            return
        
        df = pd.DataFrame(products)
        
        # Remove duplicates based on URL and price
        if 'url' in df.columns:
            df = df.drop_duplicates(subset=['url', 'price'], keep='first')
        
        # Sort by price
        df = df.sort_values('price', ascending=True)
        
        # Create output directory
        output_dir = 'output'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if not filename:
            filename = f"jumia_phones_{timestamp}"
        
        # Save as CSV
        csv_file = f"{output_dir}/{filename}.csv"
        df.to_csv(csv_file, index=False)
        print(f"\n💾 CSV saved: {csv_file}")
        
        # Save as Excel
        try:
            excel_file = f"{output_dir}/{filename}.xlsx"
            df.to_excel(excel_file, index=False)
            print(f"💾 Excel saved: {excel_file}")
        except:
            print("⚠️ Could not save Excel (openpyxl may not be installed)")
        
        # Save as JSON
        json_file = f"{output_dir}/{filename}.json"
        df.to_json(json_file, orient='records', indent=2)
        print(f"💾 JSON saved: {json_file}")
        
        return df
    
    def analyze_results(self, df):
        """
        Generate insights from scraped data
        """
        print(f"\n{'='*60}")
        print("📊 ANALYSIS RESULTS")
        print(f"{'='*60}")
        
        print(f"\n📈 Total Products: {len(df)}")
        print(f"💰 Price Range: ₦{df['price'].min():,.0f} - ₦{df['price'].max():,.0f}")
        print(f"📊 Average Price: ₦{df['price'].mean():,.0f}")
        print(f"📉 Median Price: ₦{df['price'].median():,.0f}")
        
        # Price distribution
        print(f"\n📊 Price Distribution:")
        bins = [0, 50000, 100000, 200000, 500000, 1000000]
        labels = ['< ₦50k', '₦50k-100k', '₦100k-200k', '₦200k-500k', '> ₦500k']
        
        df['price_range'] = pd.cut(df['price'], bins=bins, labels=labels)
        price_dist = df['price_range'].value_counts().sort_index()
        for range_name, count in price_dist.items():
            percentage = (count / len(df)) * 100
            print(f"   {range_name}: {count} products ({percentage:.1f}%)")
        
        # Products with ratings
        if 'rating' in df.columns:
            rated_products = df[df['rating'].notna()]
            print(f"\n⭐ Products with ratings: {len(rated_products)}/{len(df)}")
            if len(rated_products) > 0:
                print(f"   Average rating: {rated_products['rating'].mean():.1f}/5")
        
        # Products on sale
        if 'original_price' in df.columns:
            on_sale = df[df['original_price'].notna()]
            print(f"\n🏷️ Products on sale: {len(on_sale)}/{len(df)}")
            if len(on_sale) > 0:
                avg_discount = on_sale['discount_percent'].mean()
                print(f"   Average discount: {avg_discount:.0f}%")
        
        # Top 5 cheapest
        print(f"\n💎 Top 5 Cheapest Products:")
        cheapest = df.nsmallest(5, 'price')[['name', 'price']]
        for idx, row in cheapest.iterrows():
            name = row['name'][:50] + '...' if len(row['name']) > 50 else row['name']
            print(f"   • {name}")
            print(f"     ₦{row['price']:,.0f}")
        
        # Top 5 most expensive
        print(f"\n👑 Top 5 Most Expensive Products:")
        expensive = df.nlargest(5, 'price')[['name', 'price']]
        for idx, row in expensive.iterrows():
            name = row['name'][:50] + '...' if len(row['name']) > 50 else row['name']
            print(f"   • {name}")
            print(f"     ₦{row['price']:,.0f}")
        
        return df

def main():
    """
    Run the scraper with your specific URL
    """
    # YOUR URL
    TARGET_URL = "https://www.jumia.com.ng/mobile-phones/?srsltid=AfmBOoqKDbb6nyDTisu1FR1udGnNMVYEd10R9gIbqjUjNvJ95uVQufGp"
    
    # Create scraper
    scraper = JumiaAutoScraper()
    
    try:
        # OPTION 1: Scrape just one page
        print("\n🚀 STARTING SCRAPER...")
        products = scraper.scrape_page(TARGET_URL, max_products=50)
        
        # OPTION 2: Scrape multiple pages (uncomment to use)
        # products = scraper.scrape_multiple_pages(TARGET_URL, num_pages=3)
        
        if products:
            # Save results
            df = scraper.save_results(products)
            
            # Analyze results
            scraper.analyze_results(df)
            
            print(f"\n{'='*60}")
            print("✅ SCRAPING COMPLETE!")
            print(f"{'='*60}")
            print("\n📁 Check the 'output' folder for your files:")
            print("   • CSV file - for Excel/analysis")
            print("   • JSON file - for web apps/dashboards")
            print("   • Excel file - for easy viewing")
            
        else:
            print("\n❌ No products found. This could mean:")
            print("   1. Jumia has changed their structure")
            print("   2. The page requires JavaScript")
            print("   3. You're being blocked")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting tips:")
        print("1. Check your internet connection")
        print("2. Try a different URL")
        print("3. Jumia might be blocking automated requests")

if __name__ == "__main__":
    main()