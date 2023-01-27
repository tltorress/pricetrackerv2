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

def get_urls():
    urls=[]
    
    for i in range(1, 326):
        urls.append(f"https://psdeals.net/in-store/all-games/{i}")
    return urls

async def get_page_data(session, url, n):
    header = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
    }
    async with session.get(url, headers=header) as r:
        return await r.text()

async def get_all(session, urls):
    tasks=[]
    results=[]
    i=0
    n=0
    for url in urls:
        i+=1
        task=asyncio.create_task(get_page_data(session, url, i))
        tasks.append(task)
        if len(tasks)%3==0:
            await asyncio.sleep(2)
    results=await asyncio.gather(*tasks)
    return results

async def parse_and_save(results):
    gamesPrices=[]
    ids = []
    
    for html in results:
        soup=BeautifulSoup(html, "html.parser")
        games=soup.find_all("a", class_="game-collection-item-link")
        ids = []

        for game in games:
            
            
            try:
                
                name = game.find('span', class_="game-collection-item-details-title").text
                _id = game.find('span', {"itemprop":'sku'}).text

                if _id in ids:
                    continue
                
                ids.append(_id)

                try:
                    price = float(game.find("div", class_="game-collection-item-prices").find('span').text.replace("Rs", "").replace(",", "").replace(".", ",").strip()   )
                           
                except:
                    price = game.find("div", class_="game-collection-item-prices").find('span').text

                

                gamePrice={
                    '_id':_id,
                    'name':re.sub('[^A-Za-z0-9 ]+', '', name),
                    'price':price
                }

                
                gamesPrices.append(gamePrice)
            except Exception as e:
                print(traceback.format_exc())
    
    await saveGamesPS4(gamesPrices)

async def saveGamesPS4(allGames):

    logging.info(f'Scraped {len(allGames)} games of PSstore')

    Database().insert_many_games(allGames, 'ps4')

async def dbPlayStation():
    ssl_context=ssl.create_default_context(cafile=certifi.where())
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    async with aiohttp.ClientSession(connector=connector) as session:
        print("Scraping PS...")
        start_time=time.time()

        urls=get_urls()
        results=await get_all(session, urls)
        await parse_and_save(results)
        print("PS Scraped")
        print("it takes PS: ",time.time()-start_time, "secs to scrape all games")


if __name__=='__main__':
    asyncio.get_event_loop().run_until_complete(dbPlayStation())