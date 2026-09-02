@echo off
cd /d C:\Users\mnonu\nigeria-price-tracker
venv\Scripts\python.exe jumia_auto_scraper.py
git add data\jumia_prices.db
git commit -m "auto: daily price scrape %date%"
git push origin master