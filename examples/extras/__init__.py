# © 2023 BrainGnosis Inc. All rights reserved.

"""
Extras package for inventory management system components.

This package contains reusable components for inventory management:
- models: Core dataclasses (Item, Warehouse, Showroom, ShipmentRequest)
- schemas: Pydantic validation schemas for state validation
- utils: Helper functions and schema creation utilities

These components can be easily imported and reused in Jupyter notebooks or other examples.
"""

# Import all the core components for easy access
from .models import Item, Warehouse, Showroom, ShipmentRequest
from .schemas import (
    ItemStateSchema,
    LocationStateSchema,
    WarehouseStateSchema,
    ShowroomStateSchema,
    ShipmentRequestStateSchema,
    SystemSummarySchema,
    InventorySystemStateSchema,
    ComplexMultiLocationFinalState
)
from .utils import (
    create_complex_multi_location_schema,
    create_state_objective_for_operation,
    convert_item_to_state_schema,
    convert_warehouse_to_state_schema,
    convert_showroom_to_state_schema,
    convert_shipment_request_to_state_schema,
    create_complete_system_state_dict,
    create_complex_multi_location_state_dict
)

__all__ = [
    # Models
    'Item',
    'Warehouse', 
    'Showroom',
    'ShipmentRequest',
    
    # Schemas
    'ItemStateSchema',
    'LocationStateSchema',
    'WarehouseStateSchema',
    'ShowroomStateSchema',
    'ShipmentRequestStateSchema',
    'SystemSummarySchema',
    'InventorySystemStateSchema',
    'ComplexMultiLocationFinalState',
    
    # Utils
    'create_complex_multi_location_schema', 
    'create_state_objective_for_operation',
    'convert_item_to_state_schema',
    'convert_warehouse_to_state_schema',
    'convert_showroom_to_state_schema',
    'convert_shipment_request_to_state_schema',
    'create_complete_system_state_dict',
    'create_complex_multi_location_state_dict'
]
