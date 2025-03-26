from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List
from models.order import StandardizedOrder

class BaseCrawler(ABC):
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.base_url = None
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }

    @abstractmethod
    def get_orders(self, start_date: datetime, end_date: datetime) -> List[StandardizedOrder]:
        """
        Fetch orders from the platform for the given date range
        and convert them to standardized format
        """
        pass

    def _get_yesterday_range(self) -> tuple[datetime, datetime]:
        """Helper method to get yesterday's date range"""
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        start_date = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
        return start_date, end_date 