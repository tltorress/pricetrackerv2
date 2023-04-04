from bs4 import BeautifulSoup
import time
import asyncio
import aiohttp
import certifi
import ssl
import os
from database_handler import Database
import logging
import config
import traceback
import re

folder = os.path.dirname(os.path.realpath(__file__)).replace(
    '\src', '').replace('\scrapers', '')

async def dbSteam():
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    async with aiohttp.ClientSession(connector=connector) as session:
        print("Scraping Steam...")
        start_time = time.time()
        urls = get_urls()
        results = await get_all(session, urls)
        await parse_and_save(results)
        print("Steam Scraped")
        print("it takes Steam: ", time.time() - start_time, "secs to scrape all games")

def get_urls():
    urls = []
    for i in range(0, 29300, 50):
        urls.append(f"https://store.steampowered.com/search/results/?query&start={i}&count=50&dynamic_data=&force_infinite=1&category1=998&os=win&filter=globaltopsellers&snr=1_7_7_globaltopsellers_7&infinite=1")
    return urls

async def get_page_data(session, url):
    async with session.get(url) as r:
        return await r.json()

async def get_all(session, urls):
    tasks = []
    results = []
    for url in urls:
        task = asyncio.create_task(get_page_data(session, url))
        tasks.append(task)
        if len(tasks) % 5 == 0:
            await asyncio.sleep(0.5)
    results = await asyncio.gather(*tasks)
    return results

async def parse_and_save(results):
    gamesPrices = []


    for html in results:
        data = html["results_html"]
        soup = BeautifulSoup(data, "html.parser")
        games = soup.find_all("a")

        for game in games:
            try:
                name = game.find("div", class_='col search_name ellipsis').find("span").text
                name = re.sub(r'[^a-zA-Z0-9\s]', '', name)
                name = re.sub(r'\bM{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})\b', lambda x: str(roman_to_int(x.group(0))), name)
                price = game.find("div", {"class": "search_price"}).text.strip()
                regular_price = price

                try:
                    price = float(price.split("₹")[-1].strip().replace(",", '').replace(".", ","))
                    

                    regular_price = price
                    price = round(price + 0.25 * price, 2)
                    if price < 400:
                        price = 400
                except:
                    pass

                gamePrice = {
                    'name': re.sub('[^A-Za-z0-9 ]+', '', name),
                    'streamstop_price': price,
                    'price': regular_price
                }

                gamesPrices.append(gamePrice)

            except Exception as e:
                print(traceback.format_exc())

    await saveGames(gamesPrices)

async def saveGames(allGames):
    Database().insert_many_games(allGames, 'steam')
    logging.info(f'Scraped {len(allGames)} games of Steam')

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
    asyncio.get_event_loop().run_until_complete(dbSteam())
