"""
Jumia Phone Price Dashboard Generator
Creates a beautiful HTML dashboard from your scraped data
"""

import pandas as pd
import glob
import webbrowser
import os
from datetime import datetime

print("=" * 60)
print("📊 JUMIA PHONE PRICE DASHBOARD GENERATOR")
print("=" * 60)

# Step 1: Find the latest CSV file in output folder
print("\n🔍 Looking for CSV files in output folder...")
csv_files = glob.glob('output/jumia_phones_*.csv')

if not csv_files:
    print("❌ No CSV files found in output folder!")
    print("   Make sure you've run the scraper first:")
    print("   python jumia_auto_scraper.py")
    exit()

# Get the most recent file
latest_file = max(csv_files, key=os.path.getctime)
print(f"✅ Found file: {os.path.basename(latest_file)}")

# Step 2: Load the data
print("\n📂 Loading data...")
df = pd.read_csv(latest_file)
print(f"✅ Loaded {len(df)} products")

# Step 3: Clean the data (remove obvious errors)
print("\n🧹 Cleaning data...")
# Remove the crazy 13.5 million phone (probably error)
df_clean = df[df['price'] < 5000000].copy()
print(f"✅ After cleaning: {len(df_clean)} products")
print(f"   Removed {len(df) - len(df_clean)} outliers")

# Step 4: Calculate statistics
total_products = len(df_clean)
min_price = df_clean['price'].min()
max_price = df_clean['price'].max()
avg_price = df_clean['price'].mean()
median_price = df_clean['price'].median()
products_on_sale = df_clean['original_price'].notna().sum()
avg_discount = df_clean['discount_percent'].mean()

# Step 5: Create price ranges for distribution
bins = [0, 50000, 100000, 200000, 500000, float('inf')]
labels = ['< ₦50k', '₦50k-100k', '₦100k-200k', '₦200k-500k', '> ₦500k']
df_clean['price_range'] = pd.cut(df_clean['price'], bins=bins, labels=labels)
price_distribution = df_clean['price_range'].value_counts().sort_index()

# Step 6: Get cheapest and most expensive phones
cheapest_phones = df_clean.nsmallest(10, 'price')[['name', 'price', 'rating', 'discount_percent']]
expensive_phones = df_clean.nlargest(10, 'price')[['name', 'price', 'rating', 'discount_percent']]

# Step 7: Generate HTML
print("\n🎨 Generating HTML dashboard...")

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jumia Nigeria - Mobile Phone Price Dashboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}
        
        body {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}
        
        .header p {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            padding: 40px;
            background: #f8f9fa;
        }}
        
        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
        }}
        
        .stat-card h3 {{
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }}
        
        .stat-card .value {{
            font-size: 2.2em;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 5px;
        }}
        
        .stat-card .subtitle {{
            color: #999;
            font-size: 0.9em;
        }}
        
        .section {{
            padding: 40px;
            border-top: 1px solid #eee;
        }}
        
        .section h2 {{
            color: #2c3e50;
            margin-bottom: 30px;
            font-size: 1.8em;
            position: relative;
        }}
        
        .section h2:after {{
            content: '';
            position: absolute;
            bottom: -10px;
            left: 0;
            width: 60px;
            height: 4px;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            border-radius: 2px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        
        th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.9em;
            letter-spacing: 0.5px;
            padding: 15px;
            text-align: left;
        }}
        
        td {{
            padding: 15px;
            border-bottom: 1px solid #eee;
            color: #2c3e50;
        }}
        
        tr:hover {{
            background: #f8f9fa;
        }}
        
        .price {{
            font-weight: bold;
            color: #27ae60;
        }}
        
        .high-price {{
            color: #e74c3c;
        }}
        
        .rating {{
            color: #f39c12;
            font-weight: bold;
        }}
        
        .discount {{
            background: #27ae60;
            color: white;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            display: inline-block;
        }}
        
        .price-range-bar {{
            margin-top: 30px;
        }}
        
        .range-item {{
            display: flex;
            align-items: center;
            margin-bottom: 15px;
        }}
        
        .range-label {{
            width: 100px;
            font-weight: 600;
            color: #2c3e50;
        }}
        
        .range-bar-container {{
            flex: 1;
            height: 30px;
            background: #f0f0f0;
            border-radius: 15px;
            margin: 0 15px;
            overflow: hidden;
        }}
        
        .range-bar {{
            height: 100%;
            background: linear-gradient(90deg, #f093fb, #f5576c);
            border-radius: 15px;
            transition: width 0.3s ease;
        }}
        
        .range-count {{
            width: 80px;
            color: #666;
            font-weight: 600;
        }}
        
        .footer {{
            background: #2c3e50;
            color: white;
            text-align: center;
            padding: 20px;
            font-size: 0.9em;
        }}
        
        .footer a {{
            color: #f093fb;
            text-decoration: none;
        }}
        
        .footer a:hover {{
            text-decoration: underline;
        }}
        
        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 1.8em;
            }}
            
            .stats-grid {{
                grid-template-columns: 1fr;
                padding: 20px;
            }}
            
            .section {{
                padding: 20px;
            }}
            
            table {{
                font-size: 0.9em;
            }}
            
            td, th {{
                padding: 10px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📱 Jumia Nigeria Mobile Phones</h1>
            <p>Real-time Market Analysis Dashboard</p>
            <p style="font-size: 0.9em; margin-top: 10px;">Data scraped: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>Total Products</h3>
                <div class="value">{total_products}</div>
                <div class="subtitle">phones analyzed</div>
            </div>
            
            <div class="stat-card">
                <h3>Price Range</h3>
                <div class="value">₦{min_price:,.0f} - ₦{max_price:,.0f}</div>
                <div class="subtitle">lowest to highest</div>
            </div>
            
            <div class="stat-card">
                <h3>Average Price</h3>
                <div class="value">₦{avg_price:,.0f}</div>
                <div class="subtitle">median: ₦{median_price:,.0f}</div>
            </div>
            
            <div class="stat-card">
                <h3>On Sale</h3>
                <div class="value">{products_on_sale}</div>
                <div class="subtitle">{products_on_sale/total_products*100:.1f}% of products</div>
            </div>
        </div>
        
        <div class="section">
            <h2>💰 Price Distribution</h2>
            <div class="price-range-bar">
"""

# Add price distribution bars
for range_name, count in price_distribution.items():
    percentage = (count / total_products) * 100
    html_content += f"""
                <div class="range-item">
                    <span class="range-label">{range_name}</span>
                    <div class="range-bar-container">
                        <div class="range-bar" style="width: {percentage}%;"></div>
                    </div>
                    <span class="range-count">{count} ({percentage:.1f}%)</span>
                </div>
"""

html_content += f"""
            </div>
        </div>
        
        <div class="section">
            <h2>💎 Top 10 Cheapest Phones</h2>
            <table>
                <thead>
                    <tr>
                        <th>Product Name</th>
                        <th>Price (₦)</th>
                        <th>Rating</th>
                        <th>Discount</th>
                    </tr>
                </thead>
                <tbody>
"""

# Add cheapest phones
for _, row in cheapest_phones.iterrows():
    name = row['name'][:60] + '...' if len(str(row['name'])) > 60 else row['name']
    rating = f"{row['rating']} ★" if pd.notna(row['rating']) else 'No rating'
    discount = f"{row['discount_percent']:.0f}% off" if pd.notna(row['discount_percent']) else '-'
    
    html_content += f"""
                    <tr>
                        <td>{name}</td>
                        <td class="price">₦{row['price']:,.0f}</td>
                        <td class="rating">{rating}</td>
                        <td>{discount}</td>
                    </tr>
"""

html_content += f"""
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <h2>👑 Top 10 Most Expensive Phones</h2>
            <table>
                <thead>
                    <tr>
                        <th>Product Name</th>
                        <th>Price (₦)</th>
                        <th>Rating</th>
                        <th>Discount</th>
                    </tr>
                </thead>
                <tbody>
"""

# Add expensive phones
for _, row in expensive_phones.iterrows():
    name = row['name'][:60] + '...' if len(str(row['name'])) > 60 else row['name']
    rating = f"{row['rating']} ★" if pd.notna(row['rating']) else 'No rating'
    discount = f"{row['discount_percent']:.0f}% off" if pd.notna(row['discount_percent']) else '-'
    
    html_content += f"""
                    <tr>
                        <td>{name}</td>
                        <td class="high-price">₦{row['price']:,.0f}</td>
                        <td class="rating">{rating}</td>
                        <td>{discount}</td>
                    </tr>
"""

html_content += f"""
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <h2>📊 Key Insights</h2>
            <table>
                <tr>
                    <td><strong>Most Popular Price Range:</strong></td>
                    <td>{price_distribution.idxmax()} ({price_distribution.max()} phones, {price_distribution.max()/total_products*100:.1f}%)</td>
                </tr>
                <tr>
                    <td><strong>Average Discount on Sale Items:</strong></td>
                    <td>{avg_discount:.0f}%</td>
                </tr>
                <tr>
                    <td><strong>Phones with Ratings:</strong></td>
                    <td>{df_clean['rating'].notna().sum()} ({df_clean['rating'].notna().sum()/total_products*100:.1f}%)</td>
                </tr>
                <tr>
                    <td><strong>Price Gap (Cheapest vs Most Expensive):</strong></td>
                    <td>₦{max_price - min_price:,.0f}</td>
                </tr>
            </table>
        </div>
        
        <div class="footer">
            <p>Built with Python, BeautifulSoup, and Love ❤️</p>
            <p>Data scraped from Jumia Nigeria | {total_products} products analyzed</p>
            <p><a href="#">View on GitHub</a> | <a href="#">Download CSV</a></p>
        </div>
    </div>
</body>
</html>
"""

# Step 8: Save the HTML file
output_file = 'output/dashboard.html'
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"✅ Dashboard saved to: {output_file}")

# Step 9: Open in browser
print("\n🚀 Opening dashboard in your browser...")
webbrowser.open('file://' + os.path.abspath(output_file))

print("\n" + "=" * 60)
print("✅ DASHBOARD CREATED SUCCESSFULLY!")
print("=" * 60)
print("\n📁 Your files:")
print(f"   • Data: {latest_file}")
print(f"   • Dashboard: {output_file}")
print("\n💡 Next steps:")
print("   1. Share this dashboard with potential employers")
print("   2. Add more features (charts, filters, etc.)")
print("   3. Deploy online with GitHub Pages")