import os
import logging
import schedule
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from crawlers.printful import PrintfulCrawler
from crawlers.printify import PrintifyCrawler
from crawlers.burger_prints import BurgerPrintsCrawler
from storage.order_storage import OrderStorage

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("pod_crawler.log")
    ]
)

logger = logging.getLogger("pod_crawler")

def crawl_orders():
    logger.info("Starting order crawl job")
    
    # Load environment variables
    load_dotenv()
    
    # Initialize storage
    storage_path = os.getenv('STORAGE_PATH', './data/orders')
    logger.info(f"Using storage path: {storage_path}")
    storage = OrderStorage(storage_path)

    # Get yesterday's date range
    start_date, end_date = get_yesterday_range()
    logger.info(f"Fetching orders from {start_date} to {end_date}")

    # Process Printful orders
    try:
        printful_token = os.getenv('PRINTFUL_API_TOKEN')
        if not printful_token:
            logger.warning("Printful API token not found, skipping Printful orders")
        else:
            logger.info("Fetching Printful orders")
            printful_crawler = PrintfulCrawler(printful_token)
            printful_orders = printful_crawler.get_orders(start_date, end_date)
            storage.save_orders(printful_orders, "printful")
            logger.info(f"Saved {len(printful_orders)} Printful orders")
    except Exception as e:
        logger.error(f"Error fetching Printful orders: {str(e)}")

    # Process Printify orders
    try:
        printify_token = os.getenv('PRINTIFY_API_TOKEN')
        if not printify_token:
            logger.warning("Printify API token not found, skipping Printify orders")
        else:
            logger.info("Fetching Printify orders")
            printify_crawler = PrintifyCrawler(printify_token)
            
            # Will automatically get the first shop ID
            try:
                logger.info("Attempting to fetch shop list from Printify")
                shop_id = printify_crawler.get_shop_id()
                logger.info(f"Successfully retrieved shop ID: {shop_id}")
                
                logger.info(f"Fetching orders for shop {shop_id} from {start_date} to {end_date}")
                printify_orders = printify_crawler.get_orders(start_date, end_date)
                logger.info(f"Retrieved {len(printify_orders)} orders from Printify")
                
                storage.save_orders(printify_orders, "printify")
                logger.info(f"Saved {len(printify_orders)} Printify orders to {storage_path}/printify/")
            except Exception as e:
                logger.error(f"Error with Printify shop: {str(e)}", exc_info=True)
    except Exception as e:
        logger.error(f"Error fetching Printify orders: {str(e)}", exc_info=True)

    # Process Burger Prints orders
    try:
        burger_prints_token = os.getenv('BURGER_PRINTS_API_TOKEN')
        if not burger_prints_token:
            logger.warning("Burger Prints API token not found, skipping Burger Prints orders")
        else:
            logger.info("Fetching Burger Prints orders")
            burger_prints_crawler = BurgerPrintsCrawler(burger_prints_token)
            burger_prints_orders = burger_prints_crawler.get_orders(start_date, end_date)
            storage.save_orders(burger_prints_orders, "burger_prints")
            logger.info(f"Saved {len(burger_prints_orders)} Burger Prints orders")
    except Exception as e:
        logger.error(f"Error fetching Burger Prints orders: {str(e)}")

    logger.info("Order crawl job completed")

def get_yesterday_range():
    """Helper method to get yesterday's date range"""
    # For testing purposes, use a wide date range to capture more orders
    start_date = datetime(2020, 1, 1)  # Start from Jan 1, 2020
    end_date = datetime.now()  # Until now
    return start_date, end_date

def main():
    # For testing purposes, just run once and exit
    logger.info("Running single crawler job for testing")
    crawl_orders()
    logger.info("Test run completed - exiting")
    
    # Uncomment for normal operation with scheduling
    # schedule.every().day.at("01:00").do(crawl_orders)
    # logger.info("Scheduled crawler job to run daily at 01:00")
    # 
    # # Run the job immediately on startup
    # logger.info("Running initial crawler job")
    # crawl_orders()
    # 
    # # Keep the script running
    # logger.info("Crawler script is now running")
    # try:
    #     while True:
    #         schedule.run_pending()
    #         time.sleep(60)
    # except KeyboardInterrupt:
    #     logger.info("Crawler script stopped")

if __name__ == "__main__":
    main() 