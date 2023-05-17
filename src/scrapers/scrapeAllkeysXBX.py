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

async def dbAllkeysXBX():
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    connector = aiohttp.TCPConnector(force_close=True, ssl=ssl_context)
    async with aiohttp.ClientSession(connector=connector) as session:
        print("Scraping AllkeyXBX...")
        start_time = time.time()
        urls = get_urls()
        results = await get_all(session, urls)
        await parse_and_save(results)
        print("AllkeyXBX Scraped")
        print("it takes AllkeyXBX: ", time.time() - start_time, "secs to scrape all games")

def get_urls():
    urls = []
    for i in range(1, 150):
        urls.append(f"https://cheapdigitaldownload.com/catalog/category-xbox-games-all/page-{i}/")
    return urls

async def get_page_data(session, url):
    header = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',}
    async with session.get(url, headers=header) as r:
        return await r.text()

async def get_all(session, urls):
    tasks = []
    results = []
    for url in urls:
        task = asyncio.create_task(get_page_data(session, url))
        tasks.append(task)
        await asyncio.sleep(2.5)
    results = await asyncio.gather(*tasks)
    return results

async def parse_and_save(results):
    gamesPrices = []

    for html in results:
        soup = BeautifulSoup(html, "html.parser")
        GamesPage = soup.find_all("li", class_="search-results-row")

        for game in GamesPage:

            try:
                name = game.find("h2", class_="search-results-row-game-title").text
                platform = game.find('div', class_="search-results-row-game-infos").text.replace(' game', '')

                try:
                    price = round(float(game.find("div", class_="search-results-row-price").text.strip().replace("$", "")) / 0.013, 2)

                    regular_price = price
                    price = round((price - (0.5 * price)) + (0.5 * (price - (0.5 * price))), 2)
                    streamstop_priceNPR= price*2
                    streamstop_priceUSD=round(price/65,2)
                except:
                    price = game.find("div", class_="search-results-row-price").text
                    regular_price = price
                    streamstop_priceNPR= price*2
                    streamstop_priceUSD=round(price/65,2)


                gamePrice = {
                    "name": re.sub('[^A-Za-z0-9 ]+', '', name),
                    "streamstop_price": price,
                    'streamstop_priceNPR': streamstop_priceNPR,
                    'streamstop_priceUSD': streamstop_priceUSD,
                    "price":regular_price
                }

                gamesPrices.append(gamePrice)
            except Exception as e:
                print(traceback.format_exc())

    await saveGames(gamesPrices)

async def saveGames(allGames):
    Database().insert_many_games(allGames, 'allkeys_xbx')
    logging.info(f'Scraped {len(allGames)} games of AllkeysXBX')

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(dbAllkeysXBX())
