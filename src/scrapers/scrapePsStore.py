from bs4 import BeautifulSoup
import time
import asyncio
import aiohttp
import ssl
import certifi
import os
from database_handler import Database
import logging
import config
import traceback
import re

folder = os.path.dirname(os.path.realpath(__file__)).replace('\src', '').replace('\scrapers', '')

async def dbPlayStation():
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    async with aiohttp.ClientSession(connector=connector) as session:
        print("Scraping PS...")
        start_time = time.time()

        urls = get_urls()
        results = await get_all(session, urls)
        await parse_and_save(results)
        print("PS Scraped")
        print("it takes PS: ", time.time() - start_time, "secs to scrape all games")

def get_urls():
    urls = []

    for i in range(1, 231):
        urls.append(f"https://psdeals.net/in-store/all-games/{i}?platforms=ps4%2Cps5")
    return urls

async def get_page_data(session, url, n):
    header = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
    }
    async with session.get(url, headers=header) as r:
        return await r.text()

async def get_all(session, urls):
    tasks = []
    results = []
    i = 0
    n = 0
    for url in urls:
        i += 1
        task = asyncio.create_task(get_page_data(session, url, i))
        tasks.append(task)
        if len(tasks) % 3 == 0:
            await asyncio.sleep(2)
    results = await asyncio.gather(*tasks)
    return results

async def parse_and_save(results):
    gamesPrices = []
    ids = []

    for html in results:
        soup = BeautifulSoup(html, "html.parser")
        games = soup.find_all("a", class_="game-collection-item-link")
        ids = []

        for game in games:
            try:
                name = game.find('span', class_="game-collection-item-details-title").text
                price = game.find("div", class_="game-collection-item-prices").find('span').text
                regular_price = price
                platform = game.find('span', class_="game-collection-item-top-platform").text

                try:
                    price = float(price.replace("Rs", "").replace(",", "").replace(".", ",").strip())

                    regular_price = price
                    plusPrice = round(((price - (price * 0.55)) + ((price - (price * 0.55)) * 0.50)) * 1.6, 2)
                    proPrice = round(((price - (price * 0.35)) + ((price - (price * 0.35)) * 0.30)) * 1.6, 2)
                except Exception as e:
                    print(e)
                    proPrice = price
                    plusPrice = price 

                if price == 0:
                    continue

                if re.search(r'[\w\s]+ \+ [\w\s]+', name):
                    continue

                if 'crossgen bundle' in name.lower():
                    name.lower().replace("crossgen bundle", '')

                if 'ps4' in name.lower() or 'for ps4' in name.lower():
                    name.lower().replace('ps4', '').replace('for ps4', '')

                #REPLACE ROMAN NUMBERS FROM NAME
                name = re.sub(r'\bM{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})\b', lambda x: str(roman_to_int(x.group(0))), name)
            
                gamePrice = {
                    'name': re.sub('[^A-Za-z0-9 ]+', '', name),
                    'price': regular_price,
                    'plusPrice': plusPrice,
                    'proPrice': proPrice,
                    "platform": platform
                }

                gamesPrices.append(gamePrice)

            except Exception as e:
                print(traceback.format_exc())

    await saveGamesPS4(gamesPrices)

async def saveGamesPS4(allGames):
    Database().insert_many_games(allGames, 'ps4')
    logging.info(f'Scraped {len(allGames)} games of PSstore')

def roman_to_int(roman):

                if roman == '':
                    return ''

                roman_dict = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
                result = 0
                for i in range(len(roman)):
                    if i > 0 and roman_dict[roman[i]] > roman_dict[roman[i-1]]:
                        result += roman_dict[roman[i]] - 2 * roman_dict[roman[i-1]]
                    else:
                        result += roman_dict[roman[i]]
                return result

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(dbPlayStation())
