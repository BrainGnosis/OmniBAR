# © 2023 BrainGnosis Inc. All rights reserved.

"""
Core dataclasses for the inventory management system.

This module contains the fundamental data structures used throughout the 
inventory management system, including items, warehouses, showrooms, and shipment requests.
"""

from typing import Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Item:
    """Represents an inventory item."""
    item_id: str
    name: str
    quantity: int
    unit_price: float = 0.0
    category: str = "general"
    expiry_date: Optional[datetime] = None

    def __post_init__(self):
        if isinstance(self.expiry_date, str):
            self.expiry_date = datetime.fromisoformat(self.expiry_date)


@dataclass
class Warehouse:
    """Represents a warehouse with direct item storage and capacity."""
    warehouse_id: str
    name: str
    location: str
    capacity: int
    items: Dict[str, Item] = field(default_factory=dict)
    
    @property
    def current_quantity(self) -> int:
        """Get total quantity of items in this warehouse."""
        return sum(item.quantity for item in self.items.values())
    
    @property
    def available_capacity(self) -> int:
        """Get remaining capacity in this warehouse."""
        return max(0, self.capacity - self.current_quantity)
    
    def get_total_capacity(self) -> int:
        """Get total capacity of this warehouse."""
        return self.capacity
    
    def get_total_items(self) -> int:
        """Get total items in this warehouse."""
        return self.current_quantity


@dataclass
class Showroom:
    """Represents a showroom associated with a specific warehouse."""
    showroom_id: str
    name: str
    location: str
    associated_warehouse_id: str
    capacity: int
    items: Dict[str, Item] = field(default_factory=dict)
    
    @property
    def current_quantity(self) -> int:
        """Get total quantity of items in this showroom."""
        return sum(item.quantity for item in self.items.values())
    
    @property
    def available_capacity(self) -> int:
        """Get remaining capacity in this showroom."""
        return max(0, self.capacity - self.current_quantity)


@dataclass
class ShipmentRequest:
    """Represents a shipment request."""
    request_id: str
    item_requests: Dict[str, int]  # item_id -> quantity
    destination_warehouse: str
    requested_date: datetime
    status: str = "pending"  # pending, approved, shipped, delivered, cancelled
