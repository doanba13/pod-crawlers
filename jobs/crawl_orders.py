import os
import schedule
import time
from datetime import datetime
from dotenv import load_dotenv
from crawlers.printful import PrintfulCrawler
from crawlers.printify import PrintifyCrawler
from crawlers.burger_prints import BurgerPrintsCrawler
from storage.order_storage import OrderStorage

def crawl_orders():
    # Load environment variables
    load_dotenv()
    
    # Initialize storage
    storage = OrderStorage(os.getenv('STORAGE_PATH', './data/orders'))

    # Initialize crawlers
    printful_crawler = PrintfulCrawler(os.getenv('PRINTFUL_API_TOKEN'))
    printify_crawler = PrintifyCrawler(os.getenv('PRINTIFY_API_TOKEN'))
    burger_prints_crawler = BurgerPrintsCrawler(os.getenv('BURGER_PRINTS_API_TOKEN'))

    # Get yesterday's date range
    start_date, end_date = printful_crawler._get_yesterday_range()

    try:
        # Fetch orders from each platform
        printful_orders = printful_crawler.get_orders(start_date, end_date)
        storage.save_orders(printful_orders, "printful")
        print(f"Saved {len(printful_orders)} Printful orders")

        # Note: For Printify, you need to set the shop ID first
        # printify_crawler.set_shop_id("your_shop_id")
        # printify_orders = printify_crawler.get_orders(start_date, end_date)
        # storage.save_orders(printify_orders, "printify")
        # print(f"Saved {len(printify_orders)} Printify orders")

        burger_prints_orders = burger_prints_crawler.get_orders(start_date, end_date)
        storage.save_orders(burger_prints_orders, "burger_prints")
        print(f"Saved {len(burger_prints_orders)} Burger Prints orders")

    except Exception as e:
        print(f"Error occurred while crawling orders: {str(e)}")

def main():
    # Schedule the job to run daily at 1 AM
    schedule.every().day.at("01:00").do(crawl_orders)

    # Run the job immediately on startup
    crawl_orders()

    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main() 