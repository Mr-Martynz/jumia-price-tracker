"""
Interactive Jumia Phone Price Dashboard
With sorting, filtering, search, and charts
"""

import pandas as pd
import glob
import webbrowser
import os
import json
from datetime import datetime

print("=" * 60)
print("📊 INTERACTIVE JUMIA PHONE DASHBOARD")
print("=" * 60)

# Find the latest CSV file
print("\n🔍 Looking for data...")
csv_files = glob.glob('output/jumia_phones_*.csv')

if not csv_files:
    print("❌ No CSV files found! Run scraper first.")
    exit()

latest_file = max(csv_files, key=os.path.getctime)
print(f"✅ Found: {os.path.basename(latest_file)}")

# Load and clean data
df = pd.read_csv(latest_file)
df_clean = df[df['price'] < 5000000].copy()  # Remove outliers
print(f"✅ Loaded {len(df_clean)} products")

# Extract brands from product names
def extract_brand(name):
    name = str(name).upper()
    brands = ['SAMSUNG', 'IPHONE', 'APPLE', 'TECNO', 'INFINIX', 'NOKIA', 
              'XIAOMI', 'REDMI', 'HUAWEI', 'OPPO', 'REALME', 'MOTOROLA',
              'GOOGLE', 'PIXEL', 'ONEPLUS', 'SONY', 'LG', 'HTC']
    
    for brand in brands:
        if brand in name:
            return brand.title()
    return 'Other'

df_clean['brand'] = df_clean['name'].apply(extract_brand)

# Prepare data for JavaScript
products_list = []
for _, row in df_clean.iterrows():
    products_list.append({
        'name': str(row['name']),
        'price': float(row['price']),
        'brand': str(row['brand']),
        'rating': float(row['rating']) if pd.notna(row['rating']) else None,
        'discount': float(row['discount_percent']) if pd.notna(row['discount_percent']) else 0,
        'url': str(row['url']) if pd.notna(row['url']) else '#'
    })

# Save as JSON for JavaScript to use
with open('output/products.json', 'w', encoding='utf-8') as f:
    json.dump(products_list, f, indent=2)

# Calculate stats for display
total_products = len(df_clean)
min_price = float(df_clean['price'].min())
max_price = float(df_clean['price'].max())
avg_price = float(df_clean['price'].mean())
brands = sorted(df_clean['brand'].unique().tolist())

print("\n🎨 Generating interactive dashboard...")

# Create HTML with JavaScript interactivity
html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📱 Jumia Phone Price Tracker - Interactive Dashboard</title>
    
    <!-- Chart.js for beautiful charts -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    
    <!-- Font Awesome for icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    
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
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}
        
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            text-align: center;
        }}
        
        .stat-card h3 {{
            color: #666;
            font-size: 0.9em;
            margin-bottom: 10px;
            text-transform: uppercase;
        }}
        
        .stat-card .value {{
            font-size: 1.8em;
            font-weight: bold;
            color: #2c3e50;
        }}
        
        .controls {{
            padding: 20px 30px;
            background: white;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            border-bottom: 1px solid #eee;
        }}
        
        .control-group {{
            display: flex;
            flex-direction: column;
        }}
        
        .control-group label {{
            font-size: 0.9em;
            color: #666;
            margin-bottom: 5px;
            font-weight: 600;
        }}
        
        .control-group input, .control-group select {{
            padding: 10px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 1em;
            transition: all 0.3s;
        }}
        
        .control-group input:focus, .control-group select:focus {{
            outline: none;
            border-color: #667eea;
        }}
        
        .price-range {{
            display: flex;
            gap: 10px;
            align-items: center;
        }}
        
        .price-range input {{
            width: 100%;
        }}
        
        .price-values {{
            display: flex;
            justify-content: space-between;
            font-size: 0.9em;
            color: #666;
            margin-top: 5px;
        }}
        
        .chart-container {{
            padding: 30px;
            background: white;
            height: 400px;
        }}
        
        .table-container {{
            padding: 30px;
            overflow-x: auto;
            max-height: 600px;
            overflow-y: auto;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        
        th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            text-align: left;
            cursor: pointer;
            position: sticky;
            top: 0;
            transition: all 0.3s;
        }}
        
        th:hover {{
            opacity: 0.9;
        }}
        
        th i {{
            margin-left: 5px;
            font-size: 0.8em;
        }}
        
        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
        }}
        
        tr:hover {{
            background: #f8f9fa;
        }}
        
        .price {{
            font-weight: bold;
            color: #27ae60;
        }}
        
        .rating {{
            color: #f39c12;
        }}
        
        .brand-badge {{
            background: #e0e0e0;
            padding: 3px 10px;
            border-radius: 15px;
            font-size: 0.85em;
            display: inline-block;
        }}
        
        .no-results {{
            text-align: center;
            padding: 40px;
            color: #999;
            font-size: 1.2em;
        }}
        
        .footer {{
            background: #2c3e50;
            color: white;
            text-align: center;
            padding: 20px;
            font-size: 0.9em;
        }}
        
        .active-filters {{
            padding: 0 30px 20px 30px;
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }}
        
        .filter-tag {{
            background: #e0e0e0;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.9em;
            display: inline-flex;
            align-items: center;
            gap: 5px;
        }}
        
        .filter-tag i {{
            cursor: pointer;
            color: #999;
        }}
        
        .filter-tag i:hover {{
            color: #e74c3c;
        }}
        
        .btn-reset {{
            background: #667eea;
            color: white;
            border: none;
            padding: 8px 20px;
            border-radius: 20px;
            cursor: pointer;
            font-size: 0.9em;
            transition: all 0.3s;
        }}
        
        .btn-reset:hover {{
            background: #764ba2;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1><i class="fas fa-mobile-alt"></i> Jumia Nigeria Phone Price Tracker</h1>
            <p>Interactive Dashboard • {datetime.now().strftime('%B %d, %Y')}</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>Total Phones</h3>
                <div class="value" id="total-count">{total_products}</div>
            </div>
            <div class="stat-card">
                <h3>Price Range</h3>
                <div class="value">₦{min_price:,.0f} - ₦{max_price:,.0f}</div>
            </div>
            <div class="stat-card">
                <h3>Average Price</h3>
                <div class="value">₦{avg_price:,.0f}</div>
            </div>
            <div class="stat-card">
                <h3>Brands</h3>
                <div class="value">{len(brands)}</div>
            </div>
        </div>
        
        <div class="controls">
            <div class="control-group">
                <label><i class="fas fa-search"></i> Search Products</label>
                <input type="text" id="search-input" placeholder="Type to search... (e.g., Samsung, iPhone)">
            </div>
            
            <div class="control-group">
                <label><i class="fas fa-filter"></i> Filter by Brand</label>
                <select id="brand-select">
                    <option value="all">All Brands</option>
                    {"".join([f'<option value="{brand}">{brand}</option>' for brand in brands])}
                </select>
            </div>
            
            <div class="control-group">
                <label><i class="fas fa-sort"></i> Sort By</label>
                <select id="sort-select">
                    <option value="price-asc">Price: Low to High</option>
                    <option value="price-desc">Price: High to Low</option>
                    <option value="name-asc">Name: A to Z</option>
                    <option value="name-desc">Name: Z to A</option>
                    <option value="rating-desc">Highest Rated</option>
                    <option value="discount-desc">Biggest Discount</option>
                </select>
            </div>
            
            <div class="control-group">
                <label><i class="fas fa-dollar-sign"></i> Price Range</label>
                <div class="price-range">
                    <input type="range" id="price-min" min="{min_price}" max="{max_price}" value="{min_price}">
                    <input type="range" id="price-max" min="{min_price}" max="{max_price}" value="{max_price}">
                </div>
                <div class="price-values">
                    <span>₦<span id="min-price-display">{min_price:,.0f}</span></span>
                    <span>₦<span id="max-price-display">{max_price:,.0f}</span></span>
                </div>
            </div>
        </div>
        
        <div class="active-filters" id="active-filters">
            <button class="btn-reset" onclick="resetFilters()">
                <i class="fas fa-undo"></i> Reset All Filters
            </button>
        </div>
        
        <div class="chart-container">
            <canvas id="priceChart"></canvas>
        </div>
        
        <div class="table-container">
            <table id="products-table">
                <thead>
                    <tr>
                        <th onclick="sortTable('name')">Product Name <i class="fas fa-sort"></i></th>
                        <th onclick="sortTable('price')">Price (₦) <i class="fas fa-sort"></i></th>
                        <th onclick="sortTable('brand')">Brand <i class="fas fa-sort"></i></th>
                        <th onclick="sortTable('rating')">Rating <i class="fas fa-sort"></i></th>
                        <th onclick="sortTable('discount')">Discount <i class="fas fa-sort"></i></th>
                    </tr>
                </thead>
                <tbody id="table-body">
                    <!-- Filled by JavaScript -->
                </tbody>
            </table>
            <div id="no-results" class="no-results" style="display: none;">
                <i class="fas fa-search"></i> No products match your filters
            </div>
        </div>
        
        <div class="footer">
            <p><i class="fas fa-code"></i> Built with Python, BeautifulSoup, and JavaScript | Data from Jumia Nigeria</p>
            <p style="font-size: 0.8em; margin-top: 10px;">Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        </div>
    </div>
    
    <script>
        // Load product data
        const products = {json.dumps(products_list)};
        
        // State
        let currentSort = 'price-asc';
        let currentSearch = '';
        let currentBrand = 'all';
        let minPrice = {min_price};
        let maxPrice = {max_price};
        
        // Initialize chart
        let priceChart = null;
        
        // Format price
        function formatPrice(price) {{
            return '₦' + price.toFixed(0).replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, ',');
        }}
        
        // Filter and sort products
        function getFilteredProducts() {{
            return products.filter(p => {{
                // Search filter
                if (currentSearch && !p.name.toLowerCase().includes(currentSearch.toLowerCase())) {{
                    return false;
                }}
                
                // Brand filter
                if (currentBrand !== 'all' && p.brand !== currentBrand) {{
                    return false;
                }}
                
                // Price filter
                if (p.price < minPrice || p.price > maxPrice) {{
                    return false;
                }}
                
                return true;
            }}).sort((a, b) => {{
                switch(currentSort) {{
                    case 'price-asc': return a.price - b.price;
                    case 'price-desc': return b.price - a.price;
                    case 'name-asc': return a.name.localeCompare(b.name);
                    case 'name-desc': return b.name.localeCompare(a.name);
                    case 'rating-desc': return (b.rating || 0) - (a.rating || 0);
                    case 'discount-desc': return (b.discount || 0) - (a.discount || 0);
                    default: return 0;
                }}
            }});
        }}
        
        // Update table
        function updateTable() {{
            const filtered = getFilteredProducts();
            const tbody = document.getElementById('table-body');
            const noResults = document.getElementById('no-results');
            
            // Update total count
            document.getElementById('total-count').textContent = filtered.length;
            
            if (filtered.length === 0) {{
                tbody.innerHTML = '';
                noResults.style.display = 'block';
                return;
            }}
            
            noResults.style.display = 'none';
            
            tbody.innerHTML = filtered.map(p => `
                <tr>
                    <td>${{p.name.substring(0, 60)}}${{p.name.length > 60 ? '...' : ''}}</td>
                    <td class="price">${{formatPrice(p.price)}}</td>
                    <td><span class="brand-badge">${{p.brand}}</span></td>
                    <td class="rating">${{p.rating ? '⭐'.repeat(Math.round(p.rating)) + ' ' + p.rating.toFixed(1) : 'No rating'}}</td>
                    <td>${{p.discount ? p.discount + '% off' : '-'}}</td>
                </tr>
            `).join('');
            
            updateChart(filtered);
        }}
        
        // Update chart
        function updateChart(filtered) {{
            // Group by brand
            const brandGroups = {{}};
            filtered.forEach(p => {{
                brandGroups[p.brand] = (brandGroups[p.brand] || 0) + 1;
            }});
            
            const brands = Object.keys(brandGroups);
            const counts = Object.values(brandGroups);
            
            if (priceChart) {{
                priceChart.destroy();
            }}
            
            const ctx = document.getElementById('priceChart').getContext('2d');
            priceChart = new Chart(ctx, {{
                type: 'bar',
                data: {{
                    labels: brands,
                    datasets: [{{
                        label: 'Number of Products',
                        data: counts,
                        backgroundColor: 'rgba(102, 126, 234, 0.7)',
                        borderColor: 'rgba(102, 126, 234, 1)',
                        borderWidth: 2,
                        borderRadius: 5
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{
                            display: false
                        }},
                        title: {{
                            display: true,
                            text: 'Products by Brand',
                            font: {{
                                size: 16,
                                weight: 'bold'
                            }}
                        }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            ticks: {{
                                stepSize: 1
                            }}
                        }}
                    }}
                }}
            }});
        }}
        
        // Sort table
        function sortTable(column) {{
            switch(column) {{
                case 'name': currentSort = currentSort === 'name-asc' ? 'name-desc' : 'name-asc'; break;
                case 'price': currentSort = currentSort === 'price-asc' ? 'price-desc' : 'price-asc'; break;
                case 'rating': currentSort = 'rating-desc'; break;
                case 'discount': currentSort = 'discount-desc'; break;
            }}
            updateTable();
        }}
        
        // Reset filters
        function resetFilters() {{
            currentSearch = '';
            currentBrand = 'all';
            minPrice = {min_price};
            maxPrice = {max_price};
            
            document.getElementById('search-input').value = '';
            document.getElementById('brand-select').value = 'all';
            document.getElementById('price-min').value = minPrice;
            document.getElementById('price-max').value = maxPrice;
            document.getElementById('min-price-display').textContent = minPrice.toFixed(0).replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, ',');
            document.getElementById('max-price-display').textContent = maxPrice.toFixed(0).replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, ',');
            
            updateTable();
        }}
        
        // Event listeners
        document.getElementById('search-input').addEventListener('input', (e) => {{
            currentSearch = e.target.value;
            updateTable();
        }});
        
        document.getElementById('brand-select').addEventListener('change', (e) => {{
            currentBrand = e.target.value;
            updateTable();
        }});
        
        document.getElementById('sort-select').addEventListener('change', (e) => {{
            currentSort = e.target.value;
            updateTable();
        }});
        
        document.getElementById('price-min').addEventListener('input', (e) => {{
            minPrice = parseInt(e.target.value);
            document.getElementById('min-price-display').textContent = minPrice.toFixed(0).replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, ',');
            if (minPrice > maxPrice) {{
                maxPrice = minPrice;
                document.getElementById('price-max').value = maxPrice;
                document.getElementById('max-price-display').textContent = maxPrice.toFixed(0).replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, ',');
            }}
            updateTable();
        }});
        
        document.getElementById('price-max').addEventListener('input', (e) => {{
            maxPrice = parseInt(e.target.value);
            document.getElementById('max-price-display').textContent = maxPrice.toFixed(0).replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, ',');
            if (maxPrice < minPrice) {{
                minPrice = maxPrice;
                document.getElementById('price-min').value = minPrice;
                document.getElementById('min-price-display').textContent = minPrice.toFixed(0).replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, ',');
            }}
            updateTable();
        }});
        
        // Initial load
        updateTable();
    </script>
</body>
</html>
"""

# Save the interactive dashboard
output_file = 'output/interactive_dashboard.html'
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"✅ Interactive dashboard saved to: {output_file}")
print("\n🚀 Opening in browser...")
webbrowser.open('file://' + os.path.abspath(output_file))

print("\n" + "=" * 60)
print("✅ INTERACTIVE DASHBOARD READY!")
print("=" * 60)
print("\n✨ Features added:")
print("   • 🔍 Real-time search")
print("   • 🏷️ Brand filtering")
print("   • 💰 Price range slider")
print("   • 📊 Interactive charts")
print("   • 🔄 Click-to-sort tables")
print("   • 🎯 Live updates")