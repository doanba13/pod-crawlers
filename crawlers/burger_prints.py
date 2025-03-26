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
            try:
                standardized_order = self._convert_to_standardized(order)
                standardized_orders.append(standardized_order)
            except Exception as e:
                print(f"Error processing order {order.get('id')}: {str(e)}")
                continue

        return standardized_orders

    def _convert_to_standardized(self, order: dict) -> StandardizedOrder:
        # Extract customer information with fallbacks for missing fields
        customer_data = order.get('customer', {})
        shipping_data = order.get('shipping', {})
        
        customer = Customer(
            name=f"{customer_data.get('first_name', '')} {customer_data.get('last_name', '')}".strip(),
            email=customer_data.get('email', ''),
            address=shipping_data.get('address', ''),
            city=shipping_data.get('city', ''),
            country=shipping_data.get('country', ''),
            zip_code=shipping_data.get('zip', '')
        )

        # Extract order items with fallbacks
        items = []
        for item in order.get('items', []):
            order_item = OrderItem(
                product_name=item.get('product_name', 'Unknown Product'),
                quantity=item.get('quantity', 1),
                price=float(item.get('price', 0)),
                variant=item.get('variant_name'),
                size=item.get('size'),
                color=item.get('color')
            )
            items.append(order_item)

        # Calculate costs with fallbacks
        subtotal = float(order.get('subtotal', 0))
        shipping_cost = float(order.get('shipping_cost', 0))
        total_cost = float(order.get('total', subtotal + shipping_cost))

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
            platform="burger_prints",
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