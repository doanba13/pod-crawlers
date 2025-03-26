import requests
import logging
from datetime import datetime
from typing import List
from models.order import StandardizedOrder, Customer, OrderItem
from .base import BaseCrawler

logger = logging.getLogger("pod_crawler.printify")

class PrintifyCrawler(BaseCrawler):
    def __init__(self, api_token: str):
        super().__init__(api_token)
        self.base_url = "https://api.printify.com/v1"
        self.shop_id = None

    def get_shop_id(self):
        """Get the first shop ID from the Printify account"""
        if self.shop_id:
            return self.shop_id

        logger.info("Making API request to get Printify shops")
        endpoint = f"{self.base_url}/shops.json"
        
        try:
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            logger.debug(f"Received shop data type: {type(data)}")
            
            # Handle the case where the response is a list directly
            if isinstance(data, list):
                shops = data
            else:
                # Handle the case where the response has a 'data' property
                shops = data.get("data", [])
                
            logger.debug(f"Shops data: {shops}")
            
            if not shops:
                logger.error("No shops found in the Printify account")
                raise ValueError("No shops found in the Printify account")
            
            # Use the first shop - shops could be a list of dictionaries with 'id'
            first_shop = shops[0]
            if isinstance(first_shop, dict):
                self.shop_id = str(first_shop.get("id"))
            else:
                logger.error(f"Invalid shop format: {first_shop}")
                raise ValueError(f"Invalid shop format: {first_shop}")
                
            logger.info(f"Selected shop ID: {self.shop_id}")
            return self.shop_id
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching shops: {str(e)}")
            raise
        except ValueError as e:
            logger.error(f"Value error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching shops: {str(e)}")
            raise

    def set_shop_id(self, shop_id: str):
        """Manually set a shop ID if needed"""
        self.shop_id = shop_id

    def get_orders(self, start_date: datetime, end_date: datetime) -> List[StandardizedOrder]:
        # Get the shop ID if not already set
        shop_id = self.get_shop_id()
        logger.info(f"Getting orders for shop ID: {shop_id}")

        endpoint = f"{self.base_url}/shops/{shop_id}/orders.json"
        params = {
            "limit": 100,
            "created_at_min": start_date.isoformat(),
            "created_at_max": end_date.isoformat()
        }
        
        logger.info(f"Request params: {params}")
        logger.info(f"Request URL: {endpoint}")

        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            logger.debug(f"Response data type: {type(data)}")
            
            # Handle different response formats
            if isinstance(data, list):
                orders = data
            elif isinstance(data, dict) and 'data' in data:
                orders = data.get("data", [])
            else:
                logger.warning(f"Unexpected response format: {type(data)}")
                orders = []
                
            logger.info(f"Retrieved {len(orders)} orders from Printify")
            
            standardized_orders = []
            for order in orders:
                try:
                    standardized_order = self._convert_to_standardized(order)
                    standardized_orders.append(standardized_order)
                except Exception as e:
                    logger.error(f"Error processing order {order.get('id')}: {str(e)}")
                    continue

            return standardized_orders
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching orders: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching orders: {str(e)}")
            raise

    def _convert_to_standardized(self, order: dict) -> StandardizedOrder:
        order_id = order.get('id', 'unknown')
        logger.debug(f"Converting order {order_id} to standardized format")
        
        # Extract customer information from address_to
        address_to = order.get('address_to', {})
        customer = Customer(
            name=f"{address_to.get('first_name', '')} {address_to.get('last_name', '')}".strip(),
            email=order.get('email', ''),
            address=address_to.get('address1', ''),
            city=address_to.get('city', ''),
            country=address_to.get('country', ''),
            zip_code=address_to.get('zip', '')
        )

        # Extract order items from raw_data.line_items
        items = []
        for item in order.get('line_items', []):
            metadata = item.get('metadata', {})
            # Extract size and color from variant_label (format: "Color / Size")
            variant_label = metadata.get('variant_label', '')
            color, size = variant_label.split(' / ') if ' / ' in variant_label else (variant_label, variant_label)
            
            # Convert prices from cents to dollars/euros
            item_cost = item.get('cost', 0)
            # Printify prices are in cents, divide by 100 to get dollars/euros
            item_price = float(item_cost) / 100.0 if item_cost else 0
            
            order_item = OrderItem(
                product_name=metadata.get('title', 'Unknown Product'),
                quantity=item.get('quantity', 1),
                price=item_price,
                variant=metadata.get('variant_label'),
                size=size,
                color=color,
                sku=metadata.get('sku'),
                product_id=item.get('product_id'),
                variant_id=item.get('variant_id'),
                print_provider_id=item.get('print_provider_id'),
                blueprint_id=item.get('blueprint_id'),
                print_area_width=item.get('print_area_width'),
                print_area_height=item.get('print_area_height'),
                raw_data=item  # Store the complete raw item data
            )
            items.append(order_item)

        # Calculate costs with fallbacks - convert from cents to dollars/euros
        subtotal_cents = order.get('subtotal', 0)
        subtotal = float(subtotal_cents) / 100.0 if subtotal_cents else 0
        
        total_price_cents = order.get('total_price', 0)
        total_price = float(total_price_cents) / 100.0 if total_price_cents else 0
        
        shipping_cost_cents = order.get('total_shipping', 0)
        shipping_cost = float(shipping_cost_cents) / 100.0 if shipping_cost_cents else 0

        tax_cents = order.get('total_tax', 0)
        tax = float(tax_cents) / 100.0 if tax_cents else 0
        
        # Calculate final price (total_price + total_shipping + total_tax)
        final_price = total_price + shipping_cost + tax
        logger.debug(f"Order {order_id}: final_price calculation: {total_price} + {shipping_cost} + {tax} = {final_price}")

        # Convert created_at to datetime with fallback
        created_at = order.get('created_at')
        if created_at:
            try:
                order_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except (ValueError, AttributeError) as e:
                logger.warning(f"Error parsing date for order {order_id}: {str(e)}")
                order_date = datetime.now()
        else:
            order_date = datetime.now()

        # Create standardized order with all fields
        standardized_order = StandardizedOrder(
            platform="printify",
            order_id=str(order_id),
            order_date=order_date,
            customer=customer,
            items=items,
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            total_cost=total_price,
            final_price=final_price,
            status=order.get('status', 'unknown'),
            tracking_number=order.get('tracking_number'),
            raw_data=order
        )
        
        return standardized_order 