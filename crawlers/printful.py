import requests
import logging
from datetime import datetime
from typing import List, Tuple, Optional
from models.order import StandardizedOrder, Customer, OrderItem
from .base import BaseCrawler

logger = logging.getLogger("pod_crawler.printful")

class PrintfulCrawler(BaseCrawler):
    def __init__(self, api_token: str):
        super().__init__(api_token)
        self.base_url = "https://api.printful.com"
        # Fixed EUR to USD conversion rate - update this regularly in production
        self.eur_to_usd_rate = 1.08  # Example rate as of March 2025

    def get_orders(self, start_date: datetime, end_date: datetime) -> List[StandardizedOrder]:
        endpoint = f"{self.base_url}/orders"
        params = {
            "offset": 0,
            "limit": 100,
            "from": int(start_date.timestamp()),
            "to": int(end_date.timestamp())
        }

        logger.info(f"Fetching Printful orders from {start_date} to {end_date}")
        logger.info(f"Request URL: {endpoint}")
        logger.info(f"Request params: {params}")

        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            logger.debug(f"Response data type: {type(data)}")
            if isinstance(data, dict) and 'result' in data:
                orders = data.get("result", [])
                logger.info(f"Retrieved {len(orders)} orders from Printful API")
                
                # DEBUG: log first order to see structure
                if orders and len(orders) > 0:
                    logger.debug(f"First order sample: {orders[0]}")
            else:
                logger.warning(f"Unexpected response format from Printful API: {type(data)}")
                orders = []

            standardized_orders = []
            for order in orders:
                try:
                    standardized_order = self._convert_to_standardized(order)
                    standardized_orders.append(standardized_order)
                except Exception as e:
                    order_id = order['id'] if isinstance(order, dict) and 'id' in order else 'unknown'
                    logger.error(f"Error processing Printful order {order_id}: {str(e)}", exc_info=True)
                    continue

            return standardized_orders
        except Exception as e:
            logger.error(f"Error fetching Printful orders: {str(e)}", exc_info=True)
            return []

    def _convert_to_standardized(self, order: dict) -> StandardizedOrder:
        order_id = order.get('id', 'unknown')
        logger.debug(f"Converting Printful order {order_id} to standardized format")
        
        # Printful uses EUR by default
        original_currency = "EUR"
        
        # Extract customer information with fallbacks for missing fields
        recipient = order.get('recipient', {})
        customer = Customer(
            name=f"{recipient.get('name', '')} {recipient.get('last_name', '')}".strip(),
            email=recipient.get('email', ''),
            address=recipient.get('address1', ''),
            city=recipient.get('city', ''),
            country=recipient.get('country_code', ''),
            zip_code=recipient.get('zip', '')
        )

        # Extract order items and convert prices from EUR to USD
        items = []
        order_items = order.get('items', [])
        
        if isinstance(order_items, list):
            for item in order_items:
                if not isinstance(item, dict):
                    logger.warning(f"Skipping non-dict item in order {order_id}: {item}")
                    continue
                    
                eur_price = float(item.get('price', 0))
                usd_price = self._convert_eur_to_usd(eur_price)
                
                order_item = OrderItem(
                    product_name=item.get('name', 'Unknown Product'),
                    quantity=item.get('quantity', 1),
                    price=usd_price,
                    variant=item.get('variant', ''),
                    size=item.get('size', ''),
                    color=item.get('color', '')
                )
                items.append(order_item)
        else:
            logger.warning(f"Expected list for items in order {order_id}, got {type(order_items)}")

        # Get costs from the costs object if available
        costs = order.get('costs', {})
        
        # Calculate costs with fallbacks and convert to USD
        subtotal_eur = 0
        shipping_cost_eur = 0
        
        if isinstance(costs, dict):
            # Get subtotal and shipping directly from the costs breakdown
            subtotal_eur = float(costs.get('subtotal', 0))
            shipping_cost_eur = float(costs.get('shipping', 0))
            total_eur = float(costs.get('total', 0))
            
            # Convert to USD
            subtotal = self._convert_eur_to_usd(subtotal_eur)
            shipping_cost = self._convert_eur_to_usd(shipping_cost_eur)
            final_price = self._convert_eur_to_usd(total_eur)
        else:
            # Fallback to calculated values if costs object is not available
            subtotal = sum(item.price * item.quantity for item in items)
            shipping_cost = 0  # Can't determine shipping cost
            final_price = subtotal  # Best estimate without shipping
            
        total_cost = subtotal + shipping_cost
            
        logger.debug(f"Printful Order {order_id}: EUR to USD - Subtotal: €{subtotal_eur:.2f} -> ${subtotal:.2f}, Shipping: €{shipping_cost_eur:.2f} -> ${shipping_cost:.2f}, Final: ${final_price:.2f}")

        # Create standardized order
        standardized_order = StandardizedOrder(
            platform="printful",
            order_id=str(order_id),
            order_date=datetime.fromtimestamp(order.get('created', datetime.now().timestamp())),
            customer=customer,
            items=items,
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            total_cost=total_cost,
            final_price=final_price,
            status=order.get('status', 'pending'),
            tracking_number=order.get('tracking_number', ''),
            raw_data=order
        )
        
        return standardized_order
        
    def _convert_eur_to_usd(self, amount_eur: float) -> float:
        """Convert amount from EUR to USD using fixed rate"""
        return round(amount_eur * self.eur_to_usd_rate, 2) 