from scrapers.scrapeAll import scrape
import asyncio
import logging
import config

async def main():
    while True:

        await scrape()

        await asyncio.sleep(600)

if __name__=='__main__':
    asyncio.run(main())