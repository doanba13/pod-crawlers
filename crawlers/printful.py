import requests
from datetime import datetime
from typing import List
from models.order import StandardizedOrder, Customer, OrderItem
from .base import BaseCrawler

class PrintfulCrawler(BaseCrawler):
    def __init__(self, api_token: str):
        super().__init__(api_token)
        self.base_url = "https://api.printful.com"

    def get_orders(self, start_date: datetime, end_date: datetime) -> List[StandardizedOrder]:
        endpoint = f"{self.base_url}/orders"
        params = {
            "offset": 0,
            "limit": 100,
            "from": int(start_date.timestamp()),
            "to": int(end_date.timestamp())
        }

        response = requests.get(endpoint, headers=self.headers, params=params)
        response.raise_for_status()
        data = response.json()

        standardized_orders = []
        for order in data.get("result", []):
            try:
                standardized_order = self._convert_to_standardized(order)
                standardized_orders.append(standardized_order)
            except Exception as e:
                print(f"Error processing order {order.get('id')}: {str(e)}")
                continue

        return standardized_orders

    def _convert_to_standardized(self, order: dict) -> StandardizedOrder:
        # Extract customer information with fallbacks for missing fields
        recipient = order.get('recipient', {})
        customer = Customer(
            name=f"{recipient.get('name', '')} {recipient.get('surname', '')}".strip(),
            email=recipient.get('email', ''),
            address=recipient.get('address1', ''),
            city=recipient.get('city', ''),
            country=recipient.get('country_code', ''),
            zip_code=recipient.get('zip', '')
        )

        # Extract order items
        items = []
        for item in order.get('items', []):
            order_item = OrderItem(
                product_name=item.get('name', 'Unknown Product'),
                quantity=item.get('quantity', 1),
                price=float(item.get('price', 0)),
                variant=item.get('variant_name'),
                size=item.get('size'),
                color=item.get('color')
            )
            items.append(order_item)

        # Calculate costs with fallbacks
        subtotal = sum(item.price * item.quantity for item in items)
        shipping_cost = float(order.get('shipping_cost', 0))
        total_cost = subtotal + shipping_cost

        return StandardizedOrder(
            platform="printful",
            order_id=str(order.get('id', '')),
            order_date=datetime.fromtimestamp(order.get('created', datetime.now().timestamp())),
            customer=customer,
            items=items,
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            total_cost=total_cost,
            status=order.get('status', 'unknown'),
            tracking_number=order.get('tracking_number'),
            raw_data=order
        ) 