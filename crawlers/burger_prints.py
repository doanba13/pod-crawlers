import requests
import logging
from datetime import datetime
from typing import List
from models.order import StandardizedOrder, Customer, OrderItem
from .base import BaseCrawler

logger = logging.getLogger("pod_crawler.burger_prints")

class BurgerPrintsCrawler(BaseCrawler):
    def __init__(self, api_token: str):
        super().__init__(api_token)
        self.base_url = "https://api.burgerprints.com/v2"
        self.headers = {
            'api-key': api_token  # Only use the api-key header
        }

    def get_orders(self, start_date: datetime, end_date: datetime) -> List[StandardizedOrder]:
        endpoint = f"{self.base_url}/order"
        logger.info(f"Fetching orders from {start_date} to {end_date}")
        logger.info(f"Request URL: {endpoint}")

        try:
            # Get all orders from the API
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            # Handle different response formats
            if isinstance(data, list):
                all_orders = data
            elif isinstance(data, dict) and 'data' in data:
                all_orders = data.get("data", [])
            else:
                logger.warning(f"Unexpected response format: {type(data)}")
                all_orders = []
                
            logger.info(f"Retrieved {len(all_orders)} orders from Burger Prints API")
            
            # Filter orders by date
            filtered_orders = []
            for order in all_orders:
                order_date = self._parse_order_date(order)
                if order_date and start_date <= order_date <= end_date:
                    filtered_orders.append(order)
            
            logger.info(f"Filtered to {len(filtered_orders)} orders within date range {start_date.date()} to {end_date.date()}")
            
            # Convert to standardized format
            standardized_orders = []
            for order in filtered_orders:
                try:
                    standardized_order = self._convert_to_standardized(order)
                    standardized_orders.append(standardized_order)
                except Exception as e:
                    order_id = order.get('id', 'unknown')
                    logger.error(f"Error processing order {order_id}: {str(e)}", exc_info=True)
                    continue

            return standardized_orders
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching orders: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching orders: {str(e)}", exc_info=True)
            raise

    def _parse_order_date(self, order: dict) -> datetime:
        """Extract and parse the order date"""
        created_date = order.get('created_date')
        if not created_date:
            logger.warning(f"No created_date field for order {order.get('id', 'unknown')}")
            return None
            
        try:
            # Format is 'YYYYMMDDTHHmmssZ' (e.g., '20250322T233223Z')
            # Parse to standard format
            year = int(created_date[0:4])
            month = int(created_date[4:6])
            day = int(created_date[6:8])
            hour = int(created_date[9:11])
            minute = int(created_date[11:13])
            second = int(created_date[13:15])
            
            return datetime(year, month, day, hour, minute, second)
        except (ValueError, IndexError) as e:
            logger.warning(f"Error parsing date '{created_date}' for order {order.get('id', 'unknown')}: {str(e)}")
            return None

    def _convert_to_standardized(self, order: dict) -> StandardizedOrder:
        order_id = order.get('id', 'unknown')
        logger.debug(f"Converting order {order_id} to standardized format")
        
        # Extract customer information from shipping address
        shipping = order.get('shipping', {})
        if isinstance(shipping, dict) and 'address' in shipping:
            address = shipping.get('address', {})
            customer = Customer(
                name=shipping.get('name', ''),
                email=shipping.get('email', ''),
                address=address.get('line1', ''),
                city=address.get('city', ''),
                country=address.get('country', ''),
                zip_code=address.get('postal_code', '')
            )
        else:
            # Fallback for missing shipping info
            customer = Customer(
                name='',
                email='',
                address='',
                city='',
                country='',
                zip_code=''
            )

        # Extract order items
        items = []
        items_amount_total = 0.0
        for item in order.get('items', []):
            product_name = f"{item.get('base_short_code', '')} - {item.get('size_name', '')}"
            # Get item amount (final price for this item)
            item_amount = float(item.get('amount', 0))
            items_amount_total += item_amount
            
            order_item = OrderItem(
                product_name=product_name if product_name.strip() else 'Unknown Product',
                quantity=int(item.get('quantity', 1)),
                price=float(item.get('price', 0)),
                variant=item.get('size_name'),
                size=item.get('size_name'),
                color='',  # Color info not available
                sku=item.get('catalog_sku'),
                product_id=item.get('id'),
                raw_data=item  # Store the complete raw item data
            )
            items.append(order_item)

        # Calculate costs with fallbacks
        subtotal = float(order.get('sub_amount', 0))
        shipping_cost = float(order.get('shipping_fee', 0))
        total_cost = float(order.get('amount', subtotal + shipping_cost))
        
        # Use the total amount from items as the final price
        final_price = items_amount_total
        logger.debug(f"Order {order_id}: final_price from items.amount total: {final_price}")

        # Convert created_date to datetime
        order_date = self._parse_order_date(order) or datetime.now()

        # Get tracking info
        tracking_number = None
        trackings = order.get('trackings', [])
        if trackings and isinstance(trackings, list) and len(trackings) > 0:
            tracking_number = trackings[0].get('code')

        # Create standardized order
        standardized_order = StandardizedOrder(
            platform="burger_prints",
            order_id=str(order_id),
            order_date=order_date,
            customer=customer,
            items=items,
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            total_cost=total_cost,
            final_price=final_price,
            status=order.get('status', 'unknown'),
            tracking_number=tracking_number,
            raw_data=order
        )
        
        return standardized_order 