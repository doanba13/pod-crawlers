import json
import os
from datetime import datetime
from typing import List
from models.order import StandardizedOrder

class OrderStorage:
    def __init__(self, base_path: str):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)

    def save_orders(self, orders: List[StandardizedOrder], platform: str):
        """
        Save orders to a JSON file organized by date and platform
        """
        if not orders:
            return

        # Group orders by date
        orders_by_date = {}
        for order in orders:
            date_str = order.order_date.strftime("%Y-%m-%d")
            if date_str not in orders_by_date:
                orders_by_date[date_str] = []
            orders_by_date[date_str].append(order)

        # Save orders for each date
        for date_str, date_orders in orders_by_date.items():
            # Create platform-specific directory
            platform_dir = os.path.join(self.base_path, platform)
            os.makedirs(platform_dir, exist_ok=True)

            # Create filename with date
            filename = f"{date_str}.json"
            filepath = os.path.join(platform_dir, filename)

            # Convert orders to JSON-serializable format
            orders_data = [order.model_dump() for order in date_orders]

            # Save to file
            with open(filepath, 'w') as f:
                json.dump(orders_data, f, indent=2, default=str) 