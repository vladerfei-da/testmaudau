from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import os
from pathlib import Path
import random

class RozetkaHTMLSaver:
    def __init__(self, output_folder="maudau_pobut_prannia"):
        self.base_url = "https://maudau.com.ua/category/zasoby-dlia-prannia/"
        self.output_folder = output_folder
        Path(output_folder).mkdir(parents=True, exist_ok=True)
        self.driver = None
    
    def setup_driver(self):
        """Налаштування браузера"""
        options = Options()
        # options.add_argument('--headless')  # Розкоментуйте для фонового режиму
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
        })
        print("✅ Браузер запущено\n")
    
    def get_page_url(self, page_num):
        if page_num == 1:
            return self.base_url
        return f"{self.base_url}page={page_num}/"
    
    def wait_for_cloudflare(self):
        """Очікування Cloudflare"""
        print("   🛡️  Очікування Cloudflare...")
        start = time.time()
        
        while time.time() - start < 60:
            page_source = self.driver.page_source
            if "Трохи зачекайте" not in page_source and "Just a moment" not in page_source:
                if len(page_source) > 5000:
                    print("   ✅ Cloudflare пройдено!")
                    return True
            time.sleep(2)
        
        print("   ⚠️  Cloudflare timeout")
        return False
    
    def save_html(self, page_num):
        """Завантажує і зберігає HTML"""
        url = self.get_page_url(page_num)
        
        try:
            print(f"📄 Сторінка {page_num}")
            print(f"   URL: {url}")
            
            # Завантажуємо сторінку
            self.driver.get(url)
            time.sleep(1)
            
            # Cloudflare
            if "Cloudflare" in self.driver.page_source or "Трохи зачекайте" in self.driver.page_source:
                if not self.wait_for_cloudflare():
                    print("   ❌ Не пройшли Cloudflare\n")
                    return False
            
            # Додаткова пауза
            time.sleep(3)
            
            # Прокрутка сторінки для завантаження контенту
            print("   📜 Прокрутка...")
            total_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # Повільна прокрутка вниз
            for i in range(0, total_height, 500):
                self.driver.execute_script(f"window.scrollTo(0, {i});")
                time.sleep(0.3)
            
            # Пауза внизу
            time.sleep(1)
            
            # Прокрутка вгору
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            # Отримуємо HTML
            html = self.driver.page_source
            
            # Зберігаємо
            filename = os.path.join(self.output_folder, f"page_{page_num:03d}.html")
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html)
            
            print(f"   ✅ Збережено: {filename}")
            print(f"   📊 Розмір: {len(html):,} байт\n")
            return True
            
        except Exception as e:
            print(f"   ❌ Помилка: {e}\n")
            return False
    
    def scrape_pages(self, start=2, end=70, delay_min=15, delay_max=25):
        """Основний метод"""
        print("="*70)
        print("🍷 MAUDAU HTML SAVER")
        print("="*70)
        print(f"📄 Сторінки: {start}-{end}")
        print(f"📁 Папка: {self.output_folder}")
        print(f"⏱️  Затримка: {delay_min}-{delay_max}с")
        print("="*70 + "\n")
        
        try:
            self.setup_driver()
            
            # Прогрів
            print("🔥 Прогрів браузера...\n")
            self.driver.get("https://maudau.com.ua")
            time.sleep(5)
            
            if "Cloudflare" in self.driver.page_source or "Трохи зачекайте" in self.driver.page_source:
                print("🛡️  Проходимо Cloudflare на головній...\n")
                self.wait_for_cloudflare()
                time.sleep(3)
            
            print("✅ Готово! Починаємо збереження...\n")
            print("="*70 + "\n")
            
            ok = 0
            fail = 0
            
            for page in range(start, end + 1):
                if self.save_html(page):
                    ok += 1
                else:
                    fail += 1
                    with open(os.path.join(self.output_folder, 'failed.txt'), 'a') as f:
                        f.write(f"{page}\n")
                
                # Затримка між сторінками
                if page < end:
                    delay = random.uniform(delay_min, delay_max)
                    print(f"⏳ Пауза {delay:.1f}с...\n")
                    time.sleep(delay)
            
        except KeyboardInterrupt:
            print("\n⚠️  Зупинено користувачем")
        except Exception as e:
            print(f"\n❌ Критична помилка: {e}")
        finally:
            if self.driver:
                print("\n🔒 Закриття браузера...")
                self.driver.quit()
            
            print("\n" + "="*70)
            print("📊 РЕЗУЛЬТАТ")
            print("="*70)
            print(f"✅ Успішно: {ok}")
            print(f"❌ Помилок: {fail}")
            print(f"📁 {os.path.abspath(self.output_folder)}")
            print("="*70)

# Запуск
if __name__ == "__main__":
    saver = RozetkaHTMLSaver(output_folder="maudau_pobut_prannia")
    
    # Завантаження сторінок 2-51
    print("📥 ЗАВАНТАЖЕННЯ СТОРІНОК \n")
    saver.scrape_pages(start=2, end=70, delay_min=2, delay_max=5)