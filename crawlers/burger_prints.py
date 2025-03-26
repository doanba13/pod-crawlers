import requests
from datetime import datetime
from typing import List
from models.order import StandardizedOrder, Customer, OrderItem
from .base import BaseCrawler

class BurgerPrintsCrawler(BaseCrawler):
    def __init__(self, api_token: str):
        super().__init__(api_token)
        self.base_url = "https://api.burgerprints.com/v1"

    def get_orders(self, start_date: datetime, end_date: datetime) -> List[StandardizedOrder]:
        endpoint = f"{self.base_url}/orders"
        params = {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "limit": 100
        }

        response = requests.get(endpoint, headers=self.headers, params=params)
        response.raise_for_status()
        data = response.json()

        standardized_orders = []
        for order in data.get("orders", []):
            standardized_order = self._convert_to_standardized(order)
            standardized_orders.append(standardized_order)

        return standardized_orders

    def _convert_to_standardized(self, order: dict) -> StandardizedOrder:
        # Extract customer information
        customer = Customer(
            name=f"{order['customer']['first_name']} {order['customer']['last_name']}",
            email=order['customer']['email'],
            address=order['shipping']['address'],
            city=order['shipping']['city'],
            country=order['shipping']['country'],
            zip_code=order['shipping']['zip']
        )

        # Extract order items
        items = []
        for item in order['items']:
            order_item = OrderItem(
                product_name=item['product_name'],
                quantity=item['quantity'],
                price=float(item['price']),
                variant=item.get('variant_name'),
                size=item.get('size'),
                color=item.get('color')
            )
            items.append(order_item)

        # Calculate costs
        subtotal = float(order['subtotal'])
        shipping_cost = float(order['shipping_cost'])
        total_cost = float(order['total'])

        return StandardizedOrder(
            platform="burger_prints",
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