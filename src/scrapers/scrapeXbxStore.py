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

folder = os.path.dirname(os.path.realpath(__file__)).replace(
    '\src', '').replace('\scrapers', '')


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
    i = 0
    for url in urls:
        i += 1
        task = asyncio.create_task(get_page_data(session, url))
        tasks.append(task)
        if len(tasks) % 3 == 0:
            await asyncio.sleep(2)
    results = await asyncio.gather(*tasks)

    return results


async def parse_and_save(results):
    gamesPrices = []
    ids = []

    i = 0

    for html in results:
        if not html:
            continue

        soup = BeautifulSoup(html, "html.parser")
        GamesPage = soup.find_all("a", class_="game-collection-item-link")

        for game in GamesPage:
            
            try:

                name = game.find(
                    'span', class_="game-collection-item-details-title").text
                try:
                    price = float(game.find("div", class_="game-collection-item-prices").find(
                        'span').text.replace("₹", "").replace(",", "").strip())

                except:
                    price = game.find(
                        "div", class_="game-collection-item-prices").find('span').text.strip()

                gamePrice = {
                    'name': re.sub('[^A-Za-z0-9 ]+', '', name),
                    'price': price
                }

                i+=1
                gamesPrices.append(gamePrice)

            except Exception as e:
                print(traceback.format_exc())
                await asyncio.sleep(2)

    await saveGamesXBX(gamesPrices)


async def saveGamesXBX(allGames):

    Database().insert_many_games(allGames, 'xbx')
    logging.info(f'Scraped {len(allGames)} games of XBXstore')


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

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(dbXBX())
