from bs4 import BeautifulSoup
import os
import json
import csv
from pathlib import Path
import re

class RozetkaParser:
    def __init__(self, html_folder=r"D:\testmaudau\rozetka_pobut_prannia", output_folder=r"D:\testmaudau\parsed_data_rozetka"):
        self.html_folder = html_folder
        self.output_folder = output_folder
        Path(output_folder).mkdir(parents=True, exist_ok=True)
        self.products = []
    
    def clean_price(self, text):
        if not text:
            return None
        text = text.replace('\u00a0', '').replace(' ', '')
        m = re.search(r'(\d+)', text)
        return int(m.group(1)) if m else None

    def parse_product(self, article):
        try:
            data = {}
            
            title_link = article.select_one('a.tile-title')
            if title_link:
                data['title'] = title_link.get_text(strip=True)
                data['url'] = title_link.get('href', '')
                if data['url'] and not data['url'].startswith('http'):
                    data['url'] = 'https://rozetka.com.ua' + data['url']
            else:
                data['title'] = None
                data['url'] = None
            
            img = article.select_one('img.tile-image')
            data['image'] = img.get('src', '') if img else None
            
            price_elem = article.select_one('div.price')
            data['price'] = self.clean_price(price_elem.get_text(strip=True)) if price_elem else None
            
            old_price_elem = article.select_one('div.old-price')
            data['old_price'] = self.clean_price(old_price_elem.get_text(strip=True)) if old_price_elem else None
            
            rating_elem = article.select_one('div.stars__rating')
            if rating_elem:
                style = rating_elem.get('style', '')
                rating_match = re.search(r'calc\((\d+)%', style)
                data['rating'] = round(int(rating_match.group(1)) / 20, 1) if rating_match else None
            else:
                data['rating'] = None
            
            reviews_elem = article.select_one('span.rating-block-content')
            if reviews_elem:
                reviews_match = re.search(r'(\d+)', reviews_elem.get_text(strip=True))
                data['reviews_count'] = int(reviews_match.group(1)) if reviews_match else None
            else:
                data['reviews_count'] = None
            
            status_elem = article.select_one('rz-tile-sell-status')
            data['availability'] = status_elem.get_text(strip=True) if status_elem else 'Невідомо'
            
            badges = article.select('rz-promo-label')
            data['badges'] = [b.get_text(strip=True) for b in badges] if badges else []
            
            data['brand'] = data['title'].split()[0] if data.get('title') else None
            
            if data.get('old_price') and data.get('price'):
                data['discount_percent'] = round((1 - data['price'] / data['old_price']) * 100)
            else:
                data['discount_percent'] = None
            
            return data
            
        except Exception as e:
            print(f"⚠️ Помилка парсингу товару: {e}")
            return None
    
    def parse_html_file(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                html = f.read()
            
            soup = BeautifulSoup(html, 'html.parser')
            products = soup.select('article[class*="tile"]')
            if not products:
                products = soup.select('rz-product-tile article')
            
            page_products = []
            for product in products:
                parsed = self.parse_product(product)
                if parsed and parsed.get('title'):
                    page_products.append(parsed)
            return page_products
            
        except Exception as e:
            print(f"❌ Помилка читання файлу: {e}")
            return []
    
    def parse_all_files(self):
        html_files = sorted([f for f in os.listdir(self.html_folder) if f.endswith('.html')])
        if not html_files:
            print("❌ HTML файли не знайдено!")
            return
        
        print(f"📄 Знайдено файлів: {len(html_files)}\n")
        
        for filename in html_files:
            filepath = os.path.join(self.html_folder, filename)
            print(f"📄 Парсинг: {filename}")
            
            products = self.parse_html_file(filepath)
            if products:
                self.products.extend(products)
                print(f"   ✅ Товарів: {len(products)}")
            else:
                print(f"   ⚠️ Товарів не знайдено")
    
    def remove_duplicates(self):
        seen = set()
        unique = []
        for p in self.products:
            url = p.get('url')
            if url and url not in seen:
                seen.add(url)
                unique.append(p)
        self.products = unique
    
    def save_to_json(self, filename="pobut_prannia.json"):
        filepath = os.path.join(self.output_folder, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.products, f, ensure_ascii=False, indent=2)
        print("JSON OK:", filepath)
    
    def save_to_csv(self, filename="pobut_prannia.csv"):
        if not self.products:
            return
        filepath = os.path.join(self.output_folder, filename)
        
        fields = ['title','brand','price','old_price','discount_percent',
                  'rating','reviews_count','availability','url','image','badges']
        
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
            w.writeheader()
            for p in self.products:
                row = p.copy()
                row['badges'] = ', '.join(row['badges']) if row.get('badges') else ''
                w.writerow(row)
        
        print("CSV OK:", filepath)

    def save_to_txt(self, filename="pobut_prannia.txt"):
        filepath = os.path.join(self.output_folder, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            for i, p in enumerate(self.products, 1):
                f.write("="*70 + "\n")
                f.write(f"ТОВАР #{i}\n")
                f.write("="*70 + "\n")
                f.write(f"Назва: {p.get('title')}\n")
                f.write(f"Бренд: {p.get('brand')}\n")
                f.write(f"Ціна: {p.get('price')}\n")
                if p.get('old_price'):
                    f.write(f"Стара ціна: {p.get('old_price')}\n")
                    f.write(f"Знижка: {p.get('discount_percent')}%\n")
                f.write(f"Рейтинг: {p.get('rating')}\n")
                f.write(f"Відгуків: {p.get('reviews_count')}\n")
                f.write(f"Наявність: {p.get('availability')}\n")
                f.write(f"URL: {p.get('url')}\n\n")
        print("TXT OK:", filepath)


if __name__ == "__main__":
    parser = RozetkaParser()
    parser.parse_all_files()
    parser.remove_duplicates()
    parser.save_to_json()
    parser.save_to_csv()
    parser.save_to_txt()
    print("Готово!")
