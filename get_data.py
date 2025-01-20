import asyncio
import websockets
import json
import requests
import time
import logging
import sqlite3
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque

from getprice import get_price

conn = sqlite3.connect('coins.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS coins
             (coin_name text, mint text, found_time text,init_cap real, five_min_cap real, ten_min_cap real,if_done text)''')

logging.basicConfig(filename='log.text', filemode='a', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

coin_detail = 'https://frontend-api-v2.pump.fun/coins/mint'
coin_creator = 'https://frontend-api-v2.pump.fun/coins/user-created-coins/creator?offset=0&limit=10&includeNsfw=false'

async def subscribe():
    uri = "wss://pumpportal.fun/api/data"
    async with websockets.connect(uri) as websocket:
        payload = {
            "method": "subscribeNewToken",
        }
        await websocket.send(json.dumps(payload))
        async for message in websocket:
            result = json.loads(message)
            print(result)
            coin_info = {}
            try:
                logging.error(f"Begin to filter {result['mint']}")
                uri = result['uri']
                mint = result['mint']
                bondingCurveKey = result['bondingCurveKey']
                vSolInBondingCurve = result['vSolInBondingCurve']
                vTokensInBondingCurve = result['vTokensInBondingCurve']
                creator = result['traderPublicKey']
                current_price=f"{(vSolInBondingCurve/vTokensInBondingCurve):.10f}"
                coin_name = result['symbol']
                marketCapSol= result['marketCapSol']
                # price_dic = await get_price(mint,bondingCurveKey)
                # price = price_dic['price']
                now = datetime.now()
                current_time = now.strftime('%Y-%m-%d %H:%M')
                filter_result,cap_num = coin_filter(mint)
                if filter_result:
                    c.execute(f"INSERT INTO coins VALUES ('{coin_name}', '{mint}', '{current_time}', '{current_price}', 0.0,0.0,'{creator}','no')")
                    conn.commit()
                    logging.error(f"Found coin : {str(coin_info)}")
            except KeyError:
                continue


def coin_filter(mint):
    try:
        coin_detail_response = requests.get(coin_detail.replace('mint', mint))
    except:
        return False
    coin_detail_json = coin_detail_response.json()
    creator = coin_detail_json['creator']
    twitter = coin_detail_json['twitter']
    telegram = coin_detail_json['telegram']
    website = coin_detail_json['website']
    usd_market_cap = coin_detail_json['usd_market_cap']
    # 条件1 twitter website telegram 只要有一个值为空就pass掉
    if not bool(website) or not bool(twitter):
        return False, 0

    if 'x.com' not in twitter:
        return False, 0

    # if 't.me' not in telegram:
    #     return False,0
    
    if "." not in website :
        return False,0

    # 条件2， 判断网站是不是io或者com的，并且要是二级域名以下
    if not filter_website(website):
        logging.error(f"website not in whitelist {website}")
        return False,0

    # 条件3 判断发币次数是否大于1
    if not filter_creator(creator):
        logging.error(f"creator create coin more than 1 {creator}")
        return False,0

    # 条件4 爬取网站，看看网站的内容和深度
    # 爬取网站
    result = crawl_website(website)
    print(f"webstde crawl result{website} {str(result)}")
    # result['max_depth']
    # result['total_pages']
    # result['unique_urls']

    return True,usd_market_cap

def filter_website(website):
    bad_domains = ['twitter.com','x.com','tiktok.com','facebook.com','github.com']
    # 判断是否是io或者com域名
    website = website.replace("https://","")
    website = website.replace("http://","")
    clean_domain = website.split('/')[0]
    if clean_domain.endswith('.com') or clean_domain.endswith('.io') :
        # 判断是否是顶级，一级或者二级域名
        if website.count('.')<3:
            #过滤掉一些完整
            for bad_domain in bad_domains:
                if bad_domain in website:
                    return False
            return True
        return False
    else:
        return False

def filter_creator(creator):
    url = coin_creator.replace('creator',creator)
    response = requests.get(url)
    result = response.json()
    if len(result)>1:
        return False
    else:
        return True

def is_valid_url(url):
    """Check if a URL is valid and belongs to the same domain."""
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)

def crawl_website(start_url, max_depth=3):
    """Crawl a website and determine its depth and page count.
    Args:
        start_url (str): The starting URL of the website.
        max_depth (int): Maximum depth to crawl.
    Returns:
        dict: A dictionary with depth, total pages, and unique URLs.
    """
    visited = set()  # To track visited URLs
    queue = deque([(start_url, 0)])  # Queue for BFS with (url, depth)
    max_reached_depth = 0
    page_count = 0

    while queue:
        url, depth = queue.popleft()

        if depth > max_depth or url in visited:
            continue

        try:
            response = requests.get(url, timeout=5)
            if response.status_code != 200:
                continue

            visited.add(url)
            page_count += 1
            max_reached_depth = max(max_reached_depth, depth)

            soup = BeautifulSoup(response.text, "html.parser")
            for a_tag in soup.find_all("a", href=True):
                next_url = urljoin(url, a_tag["href"])
                print(a_tag["href"])
                if 'github.com' in a_tag["href"]:
                    print("found github")
                if is_valid_url(next_url) and urlparse(next_url).netloc == urlparse(start_url).netloc:
                    queue.append((next_url, depth + 1))

        except Exception as e:
            print(f"Error accessing {url}: {e}")

    return {
        "max_depth": max_reached_depth,
        "total_pages": page_count,
        "unique_urls": len(visited),
    }

if __name__=="__main__":
    while True:
        try:
            asyncio.get_event_loop().run_until_complete(subscribe())  # 尝试运行函数
        except Exception as e:
            logging.error(str(e),exc_info=True)
            time.sleep(10)








