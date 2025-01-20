import sqlite3
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import threading
import re
import time

# 数据库初始化
def init_db():
    conn = sqlite3.connect("crypto.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cryptos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            website TEXT,
            twitter TEXT,
            telegram TEXT,
            creator TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY,
            website_score INTEGER,
            twitter_score INTEGER,
            telegram_score INTEGER,
            total_score INTEGER
        )
    ''')
    conn.commit()
    conn.close()

# 插入初始币信息
def insert_crypto_data(cryptos):
    conn = sqlite3.connect("crypto.db")
    cursor = conn.cursor()
    for crypto in cryptos:
        cursor.execute('''
            INSERT INTO cryptos (name, website, twitter, telegram, creator)
            VALUES (?, ?, ?, ?, ?)
        ''', (crypto["name"], crypto["website"], crypto["twitter"], crypto["telegram"], crypto["creator"]))
    conn.commit()
    conn.close()

# 从API获取币信息
def fetch_crypto_data(api_url):
    response = requests.get(api_url)
    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to fetch data")
        return []

# 域名评分
def domain_score(website_url):
    domain_weights = {
        ".com": 3,
        ".org": 2,
        ".xyz": -2
    }
    domain = re.search(r"\.\w+$", website_url)
    return domain_weights.get(domain.group(), -3) if domain else -3

# 网站深度评分
def website_score(website_url):
    try:
        response = requests.get(website_url, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            links = soup.find_all("a")
            return 3 if len(links) > 10 else 1
        else:
            return -3
    except:
        return -3

# 多线程爬取并评分
lock = threading.Lock()

def process_crypto(crypto):
    website = crypto[2]
    id = crypto[0]
    website_score_val = domain_score(website) + website_score(website)
    # 模拟其他评分逻辑
    twitter_score = 1  # 暂时用1替代
    telegram_score = 1  # 暂时用1替代
    total_score = website_score_val + twitter_score + telegram_score

    # 写入数据库（加锁防止竞争）
    with lock:
        conn = sqlite3.connect("crypto.db")
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO scores (id, website_score, twitter_score, telegram_score, total_score)
            VALUES (?, ?, ?, ?, ?)
        ''', (id, website_score_val, twitter_score, telegram_score, total_score))
        conn.commit()
        conn.close()

# 获取所有币种信息
def get_all_cryptos():
    conn = sqlite3.connect("crypto.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cryptos")
    result = cursor.fetchall()
    conn.close()
    return result

# 主函数
def main():
    api_url = "https://example.com/api/pump"  # 替换为实际API
    init_db()

    # Step 1: 从API获取数据并存储
    cryptos = fetch_crypto_data(api_url)
    insert_crypto_data(cryptos)

    # Step 2: 多线程爬取和评分
    all_cryptos = get_all_cryptos()
    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(process_crypto, all_cryptos)

    # Step 3: 输出评分结果
    conn = sqlite3.connect("crypto.db")
    cursor = conn.cursor()
    cursor.execute('''
        SELECT cryptos.name, scores.total_score, cryptos.website 
        FROM cryptos 
        JOIN scores ON cryptos.id = scores.id 
        ORDER BY scores.total_score DESC
    ''')
    results = cursor.fetchall()
    conn.close()

    for name, score, website in results[:20]:  # 输出前20个币
        print(f"Name: {name}, Score: {score}, Website: {website}")

if __name__ == "__main__":
    start_time = time.time()
    main()
    print(f"Completed in {time.time() - start_time:.2f} seconds")
