"""
Create a simple HTML dashboard from Jumia data
"""

import pandas as pd
import glob
import webbrowser
import os
from datetime import datetime

# Find the latest CSV file
csv_files = glob.glob('output/jumia_phones_*.csv')
if not csv_files:
    print("❌ No CSV files found in output folder")
    exit()

latest_file = max(csv_files, key=os.path.getctime)
print(f"📁 Using file: {latest_file}")

# Load the data
df = pd.read_csv(latest_file)
print(f"📊 Loaded {len(df)} products")

# Clean the data (remove crazy outliers if needed)
# If price > 10 million, might be error
df_clean = df[df['price'] < 5000000]  # Remove prices over 5 million
print(f"🧹 After cleaning: {len(df_clean)} products (removed {len(df)-len(df_clean)} outliers)")

# Create HTML
html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Jumia Phone Price Dashboard</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        h1 {{
            color: #f68b1e;
            border-bottom: 3px solid #f68b1e;
            padding-bottom: 10px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin: 30px 0;
        }}
        .card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .card h3 {{
            margin: 0 0 10px 0;
            color: #666;
            font-size: 14px;
            text-transform: uppercase;
        }}
        .card .value {{
            font-size: 28px;
            font-weight: bold;
            color: #f68b1e;
        }}
        .card .small {{
            font-size: 14px;
            color: #999;
            margin-top: 5px;
        }}
        table {{
            width: 100%;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin: 20px 0;
        }}
        th {{
            background: #f68b1e;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #eee;
        }}
        tr:hover {{
            background: #f9f9f9;
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
        }}
        .footer {{
            margin-top: 30px;
            text-align: center;
            color: #999;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📱 Jumia Nigeria - Mobile Phone Prices</h1>
        <p>Data scraped: {datetime.now().strftime('%B %d, %Y at %H:%M')}</p>
        
        <div class="stats-grid">
            <div class="card">
                <h3>Total Products</h3>
                <div class="value">{len(df_clean)}</div>
                <div class="small">phones analyzed</div>
            </div>
            <div class="card">
                <h3>Price Range</h3>
                <div class="value">₦{df_clean['price'].min():,.0f} - ₦{df_clean['price'].max():,.0f}</div>
                <div class="small">min - max</div>
            </div>
            <div class="card">
                <h3>Average Price</h3>
                <div class="value">₦{df_clean['price'].mean():,.0f}</div>
                <div class="small">per phone</div>
            </div>
            <div class="card">
                <h3>On Sale</h3>
                <div class="value">{df_clean['original_price'].notna().sum()}</div>
                <div class="small">products with discounts</div>
            </div>
        </div>
        
        <h2>💰 Cheapest 10 Phones</h2>
        <table>
            <tr>
                <th>Product Name</th>
                <th>Price (₦)</th>
                <th>Rating</th>
                <th>Discount</th>
            </tr>
"""

# Add cheapest 10 phones
for _, row in df_clean.nsmallest(10, 'price').iterrows():
    name = row['name'][:60] + '...' if len(str(row['name'])) > 60 else row['name']
    discount = f"{row['discount_percent']}%" if pd.notna(row['discount_percent']) else '-'
    rating = f"{row['rating']}★" if pd.notna(row['rating']) else '-'
    
    html_content += f"""
            <tr>
                <td>{name}</td>
                <td class="price">₦{row['price']:,.0f}</td>
                <td class="rating">{rating}</td>
                <td>{discount}</td>
            </tr>
    """

html_content += """
        </table>
        
        <h2>💰 Most Expensive 10 Phones</h2>
        <table>
            <tr>
                <th>Product Name</th>
                <th>Price (₦)</th>
                <th>Rating</th>
                <th>Discount</th>
            </tr>
"""

# Add most expensive 10 phones
for _, row in df_clean.nlargest(10, 'price').iterrows():
    name = row['name'][:60] + '...' if len(str(row['name'])) > 60 else row['name']
    discount = f"{row['discount_percent']}%" if pd.notna(row['discount_percent']) else '-'
    rating = f"{row['rating']}★" if pd.notna(row['rating']) else '-'
    
    html_content += f"""
            <tr>
                <td>{name}</td>
                <td class="price high-price">₦{row['price']:,.0f}</td>
                <td class="rating">{rating}</td>
                <td>{discount}</td>
            </tr>
    """

html_content += f"""
        </table>
        
        <h2>📊 Price Distribution</h2>
        <table>
            <tr>
                <th>Price Range</th>
                <th>Count</th>
                <th>Percentage</th>
            </tr>
"""

# Calculate price ranges
bins = [0, 50000, 100000, 200000, 500000, float('inf')]
labels = ['< ₦50k', '₦50k-100k', '₦100k-200k', '₦200k-500k', '> ₦500k']
df_clean['price_range'] = pd.cut(df_clean['price'], bins=bins, labels=labels)
range_counts = df_clean['price_range'].value_counts().sort_index()

for range_name, count in range_counts.items():
    percentage = (count / len(df_clean)) * 100
    html_content += f"""
            <tr>
                <td>{range_name}</td>
                <td>{count}</td>
                <td>{percentage:.1f}%</td>
            </tr>
    """

html_content += f"""
        </table>
        
        <div class="footer">
            <p>Data scraped from Jumia Nigeria | {len(df_clean)} products analyzed</p>
            <p>₦13.5M phone removed as probable data error</p>
        </div>
    </div>
</body>
</html>
"""

# Save the HTML file
output_file = 'output/dashboard.html'
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"✅ Dashboard created: {output_file}")

# Open in browser
webbrowser.open('file://' + os.path.abspath(output_file))
print("🚀 Dashboard opened in your browser")