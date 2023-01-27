import logging
import os
from dotenv import load_dotenv
load_dotenv()

mongoConn = os.getenv('MONGO_CONN')

logging.basicConfig(
    filename="priceTracker.log",
    level=logging.INFO,
    format='%(asctime)s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
