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
import json

folder = os.path.dirname(os.path.realpath(__file__)).replace('\src', '').replace('\scrapers', '')


async def dbXBX():
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    async with aiohttp.ClientSession(connector=connector) as session:
        print("Scraping XBX...")
        start_time = time.time()
        urls = get_urls()
        results = await get_all(session, urls)
        await parse_and_save(results)
        print("XBX Scraped")
        print("it takes XBX: ", time.time() -
              start_time, "secs to scrape all games")

def get_urls():
    urls = []
    for i in range(1, 177):
        urls.append(f"https://xbdeals.net/in-store/all-games/{i}")
    return urls

async def get_page_data(session, url):
    async with session.get(url) as r:
        if r.status == 200:
            return await r.text()
        else:
            return False

async def get_all(session, urls):
    tasks = []
    results = []
    for url in urls:
        task = asyncio.create_task(get_page_data(session, url))
        tasks.append(task)
        if len(tasks) % 3 == 0:
            await asyncio.sleep(2)
    results = await asyncio.gather(*tasks)

    return results

async def parse_and_save(results):
    gamesPrices = []

    for html in results:
        if not html:
            continue

        soup = BeautifulSoup(html, "html.parser")
        GamesPage = soup.find_all("a", class_="game-collection-item-link")

        for game in GamesPage:
            try:

                name = game.find('span', class_="game-collection-item-details-title").text
                name = re.sub('[^A-Za-z0-9 ]+', '', name)
                platform = game.find('span', class_="game-collection-item-top-platform").text

                if 'crossgen' in name.lower() or 'cross-gen' in name.lower() or 'xbox one  xbox series xs' in name.lower() or 'xbox one and xbox series xs' in name.lower():
                    platform = 'xbox one / xbox series x|s'
    
                price = game.find("div", class_="game-collection-item-prices").find('span').text
                regular_price = price

                try:
                    price = float(game.find("div", class_="game-collection-item-prices").find('span').text.replace("₹", "").replace(",", "").strip())

                    regular_price = price
                    price = round((price - (0.5 * price)) + (0.5 * (price - (0.5 * price))), 2)
                except:
                    price = game.find("div", class_="game-collection-item-prices").find('span').text.strip()

                gamePrice = {
                    'name': name,
                    'streamstop_price': price,
                    'price': regular_price,
                    'platform': platform
                }

                gamesPrices.append(gamePrice)
            except Exception as e:
                print(traceback.format_exc())

    await saveGamesXBX(gamesPrices)

async def saveGamesXBX(allGames):
    Database().insert_many_games(allGames, 'xbx')
    logging.info(f'Scraped {len(allGames)} games of XBXstore')

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(dbXBX())
