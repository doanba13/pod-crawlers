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
            try:
                standardized_order = self._convert_to_standardized(order)
                standardized_orders.append(standardized_order)
            except Exception as e:
                print(f"Error processing order {order.get('id')}: {str(e)}")
                continue

        return standardized_orders

    def _convert_to_standardized(self, order: dict) -> StandardizedOrder:
        # Extract customer information with fallbacks for missing fields
        shipping = order.get('shipping', {})
        customer = Customer(
            name=f"{shipping.get('first_name', '')} {shipping.get('last_name', '')}".strip(),
            email=order.get('email', ''),
            address=shipping.get('address1', ''),
            city=shipping.get('city', ''),
            country=shipping.get('country', ''),
            zip_code=shipping.get('zip', '')
        )

        # Extract order items with fallbacks
        items = []
        for item in order.get('line_items', []):
            order_item = OrderItem(
                product_name=item.get('title', 'Unknown Product'),
                quantity=item.get('quantity', 1),
                price=float(item.get('price', 0)),
                variant=item.get('variant_title'),
                size=item.get('size'),
                color=item.get('color')
            )
            items.append(order_item)

        # Calculate costs with fallbacks
        subtotal = float(order.get('subtotal', 0))
        shipping_cost = float(order.get('shipping_cost', 0))
        total_cost = float(order.get('total_price', subtotal + shipping_cost))

        # Convert created_at to datetime with fallback
        created_at = order.get('created_at')
        if created_at:
            try:
                order_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                order_date = datetime.now()
        else:
            order_date = datetime.now()

        return StandardizedOrder(
            platform="printify",
            order_id=str(order.get('id', '')),
            order_date=order_date,
            customer=customer,
            items=items,
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            total_cost=total_cost,
            status=order.get('status', 'unknown'),
            tracking_number=order.get('tracking_number'),
            raw_data=order
        ) 