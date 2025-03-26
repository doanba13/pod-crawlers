from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class Customer(BaseModel):
    name: str
    email: str
    address: str
    city: str
    country: str
    zip_code: str

class OrderItem(BaseModel):
    product_name: str
    quantity: int
    price: float
    variant: Optional[str] = None
    size: Optional[str] = None
    color: Optional[str] = None

class StandardizedOrder(BaseModel):
    platform: str  # printful, printify, or burger_prints
    order_id: str
    order_date: datetime
    customer: Customer
    items: List[OrderItem]
    subtotal: float
    shipping_cost: float
    total_cost: float
    status: str
    tracking_number: Optional[str] = None
    raw_data: dict  # Store the original response data 