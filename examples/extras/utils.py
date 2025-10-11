# © 2023 BrainGnosis Inc. All rights reserved.

"""
Utility functions for inventory system state validation and schema creation.

This module contains helper functions for creating tailored pydantic schemas,
converting between data structures, and setting up state validation objectives.
"""

from typing import Dict, Any
from datetime import datetime
from omnibar.objectives import StateEqualityObjective, PartialStateEqualityObjective

# Import schemas and models from the other modules
from .schemas import (
    ComplexMultiLocationFinalState,
    WarehouseStateSchema,
    ShowroomStateSchema,
    ItemStateSchema,
    ShipmentRequestStateSchema,
    SystemSummarySchema,
    InventorySystemStateSchema
)
from .models import Item, Warehouse, Showroom, ShipmentRequest


def create_complex_multi_location_schema():
    """Create highly specific schema for complex multi-location scenario final state validation."""
    return ComplexMultiLocationFinalState


def create_state_objective_for_operation(operation_type: str) -> PartialStateEqualityObjective:
    """Create a PartialStateEqualityObjective for complex multi-location crisis scenarios."""
    # Always use complex multi-location crisis scenario validation
    return PartialStateEqualityObjective(
        name="complex_crisis_management_validation",
        description="Validates complex multi-location crisis scenario with partial scoring across all 3 showrooms and multiple item types",
        goal=create_complex_multi_location_schema(),
        output_key="system_state"
    )


def convert_item_to_state_schema(item: Item) -> Dict[str, Any]:
    """Convert Item dataclass to state schema dictionary."""
    return {
        "item_id": item.item_id,
        "name": item.name,
        "quantity": item.quantity,
        "unit_price": item.unit_price,
        "category": item.category,
        "expiry_date": item.expiry_date.isoformat() if item.expiry_date else None
    }


def convert_warehouse_to_state_schema(warehouse: Warehouse) -> Dict[str, Any]:
    """Convert Warehouse dataclass to state schema dictionary."""
    return {
        "location_id": warehouse.warehouse_id,
        "name": warehouse.name,
        "location_address": warehouse.location,
        "capacity": warehouse.capacity,
        "current_quantity": warehouse.current_quantity,
        "available_capacity": warehouse.available_capacity,
        "utilization_rate": warehouse.current_quantity / warehouse.capacity if warehouse.capacity > 0 else 0.0,
        "items": {item_id: convert_item_to_state_schema(item) for item_id, item in warehouse.items.items()},
        "warehouse_type": "distribution",
        "operational_status": "active"
    }


def convert_showroom_to_state_schema(showroom: Showroom) -> Dict[str, Any]:
    """Convert Showroom dataclass to state schema dictionary."""
    return {
        "location_id": showroom.showroom_id,
        "name": showroom.name,
        "location_address": showroom.location,
        "capacity": showroom.capacity,
        "current_quantity": showroom.current_quantity,
        "available_capacity": showroom.available_capacity,
        "utilization_rate": showroom.current_quantity / showroom.capacity if showroom.capacity > 0 else 0.0,
        "items": {item_id: convert_item_to_state_schema(item) for item_id, item in showroom.items.items()},
        "associated_warehouse_id": showroom.associated_warehouse_id,
        "showroom_type": "retail",
        "public_access": True
    }


def convert_shipment_request_to_state_schema(request: ShipmentRequest) -> Dict[str, Any]:
    """Convert ShipmentRequest dataclass to state schema dictionary."""
    return {
        "request_id": request.request_id,
        "item_requests": request.item_requests,
        "destination_warehouse": request.destination_warehouse,
        "requested_date": request.requested_date.isoformat(),
        "status": request.status
    }





def create_complex_multi_location_state_dict(inventory_manager, operation_success: bool = True) -> Dict[str, Any]:
    """Create state dictionary for crisis management scenario validation."""
    
    # Get current showroom states
    sr001 = inventory_manager.showrooms.get("SR001")
    sr002 = inventory_manager.showrooms.get("SR002") 
    sr003 = inventory_manager.showrooms.get("SR003")
    
    # Count items by type across all locations
    def count_item_in_showroom(showroom, item_id: str) -> int:
        if not showroom or item_id not in showroom.items:
            return 0
        return showroom.items[item_id].quantity
    
    # Calculate progress on each order based on requirements
    # ORDER A: SR001 needs 12 laptops + 8 chairs + 4 stands  
    sr001_laptops = count_item_in_showroom(sr001, "ITEM001")
    sr001_chairs = count_item_in_showroom(sr001, "ITEM002") 
    sr001_stands = count_item_in_showroom(sr001, "ITEM003")
    order_a_progress = min(1.0, (min(sr001_laptops/12, 1.0) + min(sr001_chairs/8, 1.0) + min(sr001_stands/4, 1.0)) / 3)
    
    # ORDER B: SR002 needs 15 laptops + 10 lamps + 6 chairs, SR003 needs 8 laptops + 12 chairs + 5 stands + 4 lamps
    sr002_laptops = count_item_in_showroom(sr002, "ITEM001")
    sr002_chairs = count_item_in_showroom(sr002, "ITEM002")
    sr002_lamps = count_item_in_showroom(sr002, "ITEM004")
    sr003_laptops = count_item_in_showroom(sr003, "ITEM001")
    sr003_chairs = count_item_in_showroom(sr003, "ITEM002")
    sr003_stands = count_item_in_showroom(sr003, "ITEM003")
    sr003_lamps = count_item_in_showroom(sr003, "ITEM004")
    
    # Calculate Order B progress (2 showrooms)
    sr002_progress = (min(sr002_laptops/15, 1.0) + min(sr002_chairs/6, 1.0) + min(sr002_lamps/10, 1.0)) / 3
    sr003_progress = (min(sr003_laptops/8, 1.0) + min(sr003_chairs/12, 1.0) + min(sr003_stands/5, 1.0) + min(sr003_lamps/4, 1.0)) / 4
    order_b_progress = (sr002_progress + sr003_progress) / 2
    
    # ORDER C: Equal distribution + notebooks (simplified to just notebooks placed)
    sr001_notebooks = count_item_in_showroom(sr001, "ITEM005")
    sr002_notebooks = count_item_in_showroom(sr002, "ITEM005")
    sr003_notebooks = count_item_in_showroom(sr003, "ITEM005")
    order_c_progress = (min(sr001_notebooks/3, 1.0) + min(sr002_notebooks/5, 1.0) + min(sr003_notebooks/2, 1.0)) / 3
    
    # Calculate total items and operations
    total_items_placed = sum(sr.current_quantity for sr in [sr001, sr002, sr003] if sr)
    total_operations = len(inventory_manager.operation_log)
    
    # Calculate efficiency (items placed per operation, normalized)
    efficiency_score = min(1.0, total_items_placed / max(1, total_operations * 10)) if total_operations > 0 else 0.0
    
    # Check constraint adherence
    respected_capacity = True
    respected_operations = True
    
    # Check if any operations failed due to constraints in logs
    for log_entry in inventory_manager.operation_log:
        if not log_entry.get("success", True):
            error_msg = log_entry.get("error", "").lower()
            if "capacity" in error_msg or "insufficient" in error_msg:
                respected_capacity = False
            if "constraint violation" in error_msg:
                respected_operations = False
    
    # Validate item types exist with correct details
    def validate_item_details(showroom, item_id: str, expected_name: str, expected_category: str) -> bool:
        if not showroom or item_id not in showroom.items:
            return True  # No items to validate
        item = showroom.items[item_id]
        return item.name == expected_name and item.category == expected_category
    
    # Check all showrooms for correct item types
    laptop_details_valid = all([
        validate_item_details(sr001, "ITEM001", "Laptop Computer", "electronics"),
        validate_item_details(sr002, "ITEM001", "Laptop Computer", "electronics"),
        validate_item_details(sr003, "ITEM001", "Laptop Computer", "electronics")
    ])
    
    chair_details_valid = all([
        validate_item_details(sr001, "ITEM002", "Office Chair", "furniture"),
        validate_item_details(sr002, "ITEM002", "Office Chair", "furniture"),
        validate_item_details(sr003, "ITEM002", "Office Chair", "furniture")
    ])
    
    lamp_details_valid = all([
        validate_item_details(sr001, "ITEM004", "Desk Lamp", "furniture"),
        validate_item_details(sr002, "ITEM004", "Desk Lamp", "furniture"),
        validate_item_details(sr003, "ITEM004", "Desk Lamp", "furniture")
    ])
    
    stand_details_valid = all([
        validate_item_details(sr001, "ITEM003", "Monitor Stand", "furniture"),
        validate_item_details(sr002, "ITEM003", "Monitor Stand", "furniture"),
        validate_item_details(sr003, "ITEM003", "Monitor Stand", "furniture")
    ])
    
    return {
        "operation_type": "complex_business_scenario",
        "success": operation_success,
        "scenario_type": "crisis_supply_chain_management",
        
        # Priority management
        "order_a_attempted": total_operations > 0,  # Any operations means Order A was attempted
        "order_a_progress": order_a_progress,
        "order_b_attempted": order_b_progress > 0,
        "order_b_progress": order_b_progress, 
        "order_c_attempted": order_c_progress > 0,
        "order_c_progress": order_c_progress,
        
        # Constraint handling
        "respected_capacity_limits": respected_capacity,
        "respected_operational_limits": respected_operations,
        "intelligent_resource_allocation": total_items_placed > 20,  # Got significant items placed
        
        # System utilization
        "total_items_placed": total_items_placed,
        "total_operations_performed": total_operations,
        "efficiency_score": efficiency_score,
        
        # Crisis management indicators
        "handled_bottlenecks": total_items_placed > 10,  # Successfully worked around constraints
        "multi_step_planning": total_operations > 5,  # Showed multi-step approach
        "priority_adherence": order_a_progress >= order_b_progress,  # Order A got more attention
        
        # Association validations
        "sr001_associated_with_wh001": sr001.associated_warehouse_id == "WH001" if sr001 else False,
        "sr002_associated_with_wh002": sr002.associated_warehouse_id == "WH002" if sr002 else False,
        "sr003_associated_with_wh003": sr003.associated_warehouse_id == "WH003" if sr003 else False,
        
        # Item type validations
        "laptop_item_details_valid": laptop_details_valid,
        "chair_item_details_valid": chair_details_valid,
        "lamp_item_details_valid": lamp_details_valid,
        "stand_item_details_valid": stand_details_valid
    }


def create_complete_system_state_dict(inventory_manager) -> Dict[str, Any]:
    """Create complete system state dictionary for JSON serialization and validation."""
    status = inventory_manager.get_inventory_status()
    timestamp = datetime.now().isoformat()
    
    # Convert all entities to state schema format
    warehouses_state = {wh_id: convert_warehouse_to_state_schema(wh) 
                       for wh_id, wh in inventory_manager.warehouses.items()}
    
    showrooms_state = {sr_id: convert_showroom_to_state_schema(sr)
                      for sr_id, sr in inventory_manager.showrooms.items()}
    
    active_shipments = {req_id: convert_shipment_request_to_state_schema(req)
                       for req_id, req in inventory_manager.shipment_requests.items()
                       if req.status in ["pending", "approved", "shipped"]}
    
    # Calculate system summary
    total_items = status["summary"]["total_items"] 
    total_capacity = status["summary"]["total_capacity"]
    total_available = total_capacity - total_items
    overall_utilization = total_items / total_capacity if total_capacity > 0 else 0.0
    
    # Calculate total inventory value
    total_value = 0.0
    for warehouse in inventory_manager.warehouses.values():
        for item in warehouse.items.values():
            total_value += item.quantity * item.unit_price
    for showroom in inventory_manager.showrooms.values():
        for item in showroom.items.values():
            total_value += item.quantity * item.unit_price
    
    summary_state = {
        "total_items": total_items,
        "total_capacity": total_capacity,
        "total_available_capacity": total_available,
        "overall_utilization_rate": round(overall_utilization, 4),
        "total_value": round(total_value, 2)
    }
    
    return {
        "system_id": "INVENTORY_SYS_001",
        "timestamp": timestamp,
        "total_warehouses": len(inventory_manager.warehouses),
        "total_showrooms": len(inventory_manager.showrooms),
        "warehouses": warehouses_state,
        "showrooms": showrooms_state,
        "active_shipment_requests": active_shipments,
        "summary": summary_state,
        "system_status": "operational"
    }
