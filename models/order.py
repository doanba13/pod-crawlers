from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class Customer(BaseModel):
    name: Optional[str] = "Unknown Customer"
    email: Optional[str] = ""
    address: Optional[str] = ""
    city: Optional[str] = ""
    country: Optional[str] = ""
    zip_code: Optional[str] = ""

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