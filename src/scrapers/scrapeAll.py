from scrapers import scrapeAllkeysPC, scrapeAllkeysXBX, scrapePsStore, scrapeSteam, scrapeXbxStore
import asyncio
import traceback
import config

async def scrape():
        
        try:
                
                tasks=[]

                task3=asyncio.create_task(scrapeXbxStore.dbXBX())
                tasks.append(task3)
                task1=asyncio.create_task(scrapeAllkeysPC.dbAllkeysPC())
                tasks.append(task1)
                task4=asyncio.create_task(scrapePsStore.dbPlayStation())
                tasks.append(task4)
                task5=asyncio.create_task(scrapeSteam.dbSteam())
                tasks.append(task5)
                task6 = asyncio.create_task(scrapeAllkeysXBX.dbAllkeysXBX())
                tasks.append(task6)
                
                await asyncio.gather(*tasks)
      
        except:
                print(traceback.format_exc())
                pass
       