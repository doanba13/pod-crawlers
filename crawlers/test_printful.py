import os
import sys
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from crawlers.printful import PrintfulCrawler

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("test_printful")

def main():
    # Load environment variables from .env file
    load_dotenv()
    
    # Get API token from environment variable
    api_token = os.getenv("PRINTFUL_API_TOKEN")
    if not api_token:
        logger.error("PRINTFUL_API_TOKEN environment variable not found")
        sys.exit(1)
    
    # Create crawler instance
    crawler = PrintfulCrawler(api_token)
    
    # Set date range for orders (last 30 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    logger.info(f"Testing Printful crawler with date range: {start_date} to {end_date}")
    
    # Get orders from Printful
    orders = crawler.get_orders(start_date, end_date)
    
    # Display results
    logger.info(f"Retrieved {len(orders)} standardized orders from Printful")
    
    # Show sample of the first order (if any)
    if orders:
        sample_order = orders[0]
        logger.info(f"Sample order:")
        logger.info(f"  Order ID: {sample_order.order_id}")
        logger.info(f"  Date: {sample_order.order_date}")
        logger.info(f"  Customer: {sample_order.customer.name} ({sample_order.customer.email})")
        logger.info(f"  Items: {len(sample_order.items)}")
        for i, item in enumerate(sample_order.items):
            logger.info(f"    Item {i+1}: {item.quantity}x {item.product_name} - ${item.price:.2f}")
        logger.info(f"  Total: ${sample_order.final_price:.2f}")
    else:
        logger.warning("No orders retrieved")

if __name__ == "__main__":
    main() 