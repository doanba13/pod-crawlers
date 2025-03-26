import requests
from datetime import datetime
from typing import List
from models.order import StandardizedOrder, Customer, OrderItem
from .base import BaseCrawler

class PrintifyCrawler(BaseCrawler):
    def __init__(self, api_token: str):
        super().__init__(api_token)
        self.base_url = "https://api.printify.com/v1"
        self.shop_id = None  # This needs to be set before making requests

    def set_shop_id(self, shop_id: str):
        self.shop_id = shop_id

    def get_orders(self, start_date: datetime, end_date: datetime) -> List[StandardizedOrder]:
        if not self.shop_id:
            raise ValueError("Shop ID must be set before fetching orders")

        endpoint = f"{self.base_url}/shops/{self.shop_id}/orders.json"
        params = {
            "limit": 100,
            "created_at_min": start_date.isoformat(),
            "created_at_max": end_date.isoformat()
        }

        response = requests.get(endpoint, headers=self.headers, params=params)
        response.raise_for_status()
        data = response.json()

        standardized_orders = []
        for order in data.get("data", []):
            standardized_order = self._convert_to_standardized(order)
            standardized_orders.append(standardized_order)

        return standardized_orders

    def _convert_to_standardized(self, order: dict) -> StandardizedOrder:
        # Extract customer information
        customer = Customer(
            name=f"{order['shipping']['first_name']} {order['shipping']['last_name']}",
            email=order['email'],
            address=order['shipping']['address1'],
            city=order['shipping']['city'],
            country=order['shipping']['country'],
            zip_code=order['shipping']['zip']
        )

        # Extract order items
        items = []
        for item in order['line_items']:
            order_item = OrderItem(
                product_name=item['title'],
                quantity=item['quantity'],
                price=float(item['price']),
                variant=item.get('variant_title'),
                size=item.get('size'),
                color=item.get('color')
            )
            items.append(order_item)

        # Calculate costs
        subtotal = float(order['subtotal'])
        shipping_cost = float(order['shipping_cost'])
        total_cost = float(order['total_price'])

        return StandardizedOrder(
            platform="printify",
            order_id=str(order['id']),
            order_date=datetime.fromisoformat(order['created_at'].replace('Z', '+00:00')),
            customer=customer,
            items=items,
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            total_cost=total_cost,
            status=order['status'],
            tracking_number=order.get('tracking_number'),
            raw_data=order
        ) 