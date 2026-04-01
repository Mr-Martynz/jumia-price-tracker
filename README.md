# 📱 Jumia Nigeria Price Tracker

A production-ready web scraping pipeline that extracts product data from Jumia Nigeria and generates interactive price analysis dashboards.

## 🎯 Project Overview

This project demonstrates a complete data pipeline:
- **Web Scraping**: Automated extraction of product data using Python/BeautifulSoup
- **Data Processing**: Cleaning, transformation, and analysis with Pandas
- **Interactive Dashboard**: JavaScript-powered dashboard with real-time filtering, sorting, and visualization
- **Multi-format Export**: CSV, JSON, and HTML outputs

## 🛠️ Tech Stack

| Category | Technologies |
|----------|--------------|
| Web Scraping | Python, Requests, BeautifulSoup4 |
| Data Processing | Pandas, NumPy |
| Visualization | Chart.js, HTML/CSS/JavaScript |
| Version Control | Git, GitHub |

## ✨ Features

- ✅ **Fully Automated** - No hardcoded selectors, adapts to page structure
- ✅ **Real-time Search** - Filter products instantly
- ✅ **Brand Filtering** - Filter by Samsung, iPhone, Tecno, etc.
- ✅ **Price Range Slider** - Interactive min/max price selection
- ✅ **Sortable Tables** - Click headers to sort by any column
- ✅ **Interactive Charts** - Bar charts that update with filters
- ✅ **Multi-format Export** - CSV, JSON, and HTML outputs

## 📊 Sample Output

The dashboard shows:
- Total products analyzed
- Price range and averages
- Price distribution by range
- Products on sale
- Top cheapest and most expensive products
- Brand distribution charts

## 🚀 How to Run

### Prerequisites
```bash
pip install requests beautifulsoup4 pandas