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

def get_urls(totalPages):
    urls=[]
    
    for i in range(1, 426+1):
        if i<=381:
            urls.append(f"https://www.cdkeys.com/pc?locale=all&p={i}")
            pass
        if i<=57:
            urls.append(f"https://www.cdkeys.com/playstation-network-psn?locale=all&p=1")
        if i<=426:
            urls.append(f"https://www.cdkeys.com/playstation-network-psn?locale=all&p=1%27")
            pass
        
    return urls

async def get_page_data(session, url):
    try:
    
        
        header = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
        }
        async with session.get(url, headers = header) as r:
            
            return await r.text
    
    except:
        
        return 0

async def get_all(session, urls):
    tasks=[]
    results=[]
    i=0
    for url in urls:
        i+=1
        task=asyncio.create_task(get_page_data(session, url))
        tasks.append(task)
        if len(tasks)%5==0:
            await asyncio.sleep(2)
    results=await asyncio.gather(*tasks)
    return results

async def parse_and_save(results):
    gamesPrices={"pc":[], "ps4":[], "xbx":[]}
    
    if len(results)<=0:
        return

    for html in results:
        soup=BeautifulSoup(html, "html.parser")

        games=soup.findAll("div", {"class":"product-item-details"})

        for game in games:
            try:

                try:
                    name=game.find("a", class_="product-item-link").text
                    price=float(game.find("span", {"class":"special-price"}).find("span", {"class":"price"}).text)
                except:
                    price=float(game.find("span", {"class":"old-price"}).find("span", {"class":"price"}).text)

                gamePrice={
                    'name':re.sub('[^A-Za-z0-9 ]+', '', name),
                    'price':price
                }

                if "pc" in soup.find("span", {"class":"base"}).text.lower():
                    gamesPrices['pc'].append(gamePrice)
                elif "ps4" in soup.find("span", {"class":"base"}).text.lower():
                    gamesPrices['ps4'].append(gamePrice)
                elif "xbx" in soup.find("span", {"class":"base"}).text.lower():
                    gamesPrices['xbx'].append(gamePrice)

            except Exception as e:
                print(traceback.format_exc())

    await saveGamesCdkeys(gamesPrices)

async def saveGamesCdkeys(allGames):

    if len(allGames)<=0:
        logging.info('CDkeys not working')
    else:
        logging.info(f'Scraped {len(allGames["ps4"])+len(allGames["xbx"])+len(allGames["pc"])} games of CDkeys')

    Database().insert_many_games(allGames['ps4'], 'cdkeys_ps4')
    Database().insert_many_games(allGames['xbx'], 'cdkeys_xbx')
    Database().insert_many_games(allGames['pc'], 'cdkeys_pc')

async def dbCdkeys():
    ssl_context=ssl.create_default_context(cafile=certifi.where())
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    async with aiohttp.ClientSession(connector=connector) as session:
        print("Scraping Cdkeys...")
        start_time=time.time()

        urls=get_urls(381)
        results=await get_all(session, urls)
        await parse_and_save(results)
        print("Cdkeys Scraped")
        print("it takes Cdkeys: ",time.time()-start_time, "secs to scrape all games")

if __name__=='__main__':
    asyncio.get_event_loop().run_until_complete(dbCdkeys())