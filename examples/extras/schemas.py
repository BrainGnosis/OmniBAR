# © 2023 BrainGnosis Inc. All rights reserved.

"""
Pydantic schemas for inventory system state validation.

This module contains comprehensive pydantic schemas for validating the final state
of inventory operations, including tailored schemas for specific operation types.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator

# Import the core models for type references
from .models import Item, Warehouse, Showroom, ShipmentRequest


class ItemStateSchema(BaseModel):
    """Schema representing the final state of an inventory item."""
    item_id: str = Field(..., description="Unique identifier for the item")
    name: str = Field(..., description="Display name of the item")
    quantity: int = Field(..., ge=0, description="Current quantity of the item")
    unit_price: float = Field(default=0.0, ge=0, description="Unit price of the item in dollars")
    category: str = Field(default="general", description="Item category classification")
    expiry_date: Optional[str] = Field(default=None, description="Item expiry date in ISO format")
    
    @field_validator('item_id')
    @classmethod
    def validate_item_id(cls, v):
        if not v or not v.strip():
            raise ValueError('item_id cannot be empty')
        return v.strip().upper()
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('item name cannot be empty')
        return v.strip()
    
    class Config:
        extra = "forbid"
        json_encoders = {
            datetime: lambda dt: dt.isoformat() if dt else None
        }


class LocationStateSchema(BaseModel):
    """Schema representing a storage location (warehouse or showroom)."""
    location_id: str = Field(..., description="Unique identifier for the location")
    name: str = Field(..., description="Display name of the location")
    location_address: str = Field(..., description="Physical address of the location")
    capacity: int = Field(..., gt=0, description="Maximum storage capacity")
    current_quantity: int = Field(..., ge=0, description="Current total items stored")
    available_capacity: int = Field(..., ge=0, description="Remaining storage capacity")
    utilization_rate: float = Field(..., ge=0.0, le=1.0, description="Capacity utilization rate (0.0-1.0)")
    items: Dict[str, ItemStateSchema] = Field(default_factory=dict, description="Items currently stored")
        
    @field_validator('location_id')
    @classmethod
    def validate_location_id(cls, v):
        if not v or not v.strip():
            raise ValueError('location_id cannot be empty')
        return v.strip().upper()
        
    @model_validator(mode='after')
    def validate_capacity_consistency(self):
        capacity = self.capacity
        current_quantity = self.current_quantity
        available_capacity = self.available_capacity
        
        if current_quantity + available_capacity != capacity:
            raise ValueError('current_quantity + available_capacity must equal total capacity')
        
        if current_quantity < 0 or available_capacity < 0:
            raise ValueError('quantities cannot be negative')
        
        # Calculate utilization rate
        utilization_rate = current_quantity / capacity if capacity > 0 else 0.0
        self.utilization_rate = round(utilization_rate, 4)
        
        return self
        
    @model_validator(mode='after')
    def validate_items_quantity_consistency(self):
        items = self.items
        current_quantity = self.current_quantity
        
        calculated_quantity = sum(item.quantity for item in items.values())
        if calculated_quantity != current_quantity:
            raise ValueError(f'Sum of item quantities ({calculated_quantity}) must match current_quantity ({current_quantity})')
        
        return self
    
    class Config:
        extra = "forbid"


class WarehouseStateSchema(LocationStateSchema):
    """Schema representing the final state of a warehouse."""
    warehouse_type: str = Field(default="distribution", description="Type of warehouse (distribution, storage, etc.)")
    operational_status: str = Field(default="active", description="Operational status (active, maintenance, closed)")
    
    @field_validator('operational_status')
    @classmethod
    def validate_operational_status(cls, v):
        valid_statuses = ["active", "maintenance", "closed", "pending"]
        if v not in valid_statuses:
            raise ValueError(f'operational_status must be one of: {valid_statuses}')
        return v


class ShowroomStateSchema(LocationStateSchema):
    """Schema representing the final state of a showroom."""
    associated_warehouse_id: str = Field(..., description="ID of the associated warehouse")
    showroom_type: str = Field(default="retail", description="Type of showroom (retail, demo, exhibition)")
    public_access: bool = Field(default=True, description="Whether showroom is accessible to public")
    
    @field_validator('associated_warehouse_id')
    @classmethod
    def validate_associated_warehouse_id(cls, v):
        if not v or not v.strip():
            raise ValueError('associated_warehouse_id cannot be empty')
        return v.strip().upper()
    
    @field_validator('showroom_type')
    @classmethod
    def validate_showroom_type(cls, v):
        valid_types = ["retail", "demo", "exhibition", "private"]
        if v not in valid_types:
            raise ValueError(f'showroom_type must be one of: {valid_types}')
        return v


class ShipmentRequestStateSchema(BaseModel):
    """Schema representing the state of a shipment request."""
    request_id: str = Field(..., description="Unique identifier for the shipment request")
    item_requests: Dict[str, int] = Field(..., description="Items requested with quantities")
    destination_warehouse: str = Field(..., description="Target warehouse for delivery")
    requested_date: str = Field(..., description="Requested delivery date in ISO format")
    status: str = Field(..., description="Current status of the request")
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        valid_statuses = ["pending", "approved", "shipped", "delivered", "cancelled"]
        if v not in valid_statuses:
            raise ValueError(f'status must be one of: {valid_statuses}')
        return v
    
    @field_validator('item_requests')
    @classmethod
    def validate_item_requests(cls, v):
        if not v:
            raise ValueError('item_requests cannot be empty')
        for item_id, quantity in v.items():
            if quantity <= 0:
                raise ValueError(f'quantity for item {item_id} must be positive')
        return v
    
    class Config:
        extra = "forbid"


class SystemSummarySchema(BaseModel):
    """Schema representing summary statistics of the inventory system."""
    total_items: int = Field(..., ge=0, description="Total items across all locations")
    total_capacity: int = Field(..., gt=0, description="Total storage capacity across all locations")
    total_available_capacity: int = Field(..., ge=0, description="Total available storage capacity")
    overall_utilization_rate: float = Field(..., ge=0.0, le=1.0, description="System-wide utilization rate")
    total_value: float = Field(default=0.0, ge=0, description="Total monetary value of inventory")
    
    @model_validator(mode='after')
    def validate_summary_consistency(self):
        total_items = self.total_items
        total_capacity = self.total_capacity
        total_available = self.total_available_capacity
        
        if total_items + total_available > total_capacity:
            raise ValueError('total_items + total_available_capacity cannot exceed total_capacity')
        
        utilization = total_items / total_capacity if total_capacity > 0 else 0.0
        self.overall_utilization_rate = round(utilization, 4)
        
        return self
    
    class Config:
        extra = "forbid"


class InventorySystemStateSchema(BaseModel):
    """Comprehensive schema representing the complete final state of the inventory management system."""
    system_id: str = Field(default="INVENTORY_SYS_001", description="Unique system identifier")
    timestamp: str = Field(..., description="Timestamp of state capture in ISO format")
    total_warehouses: int = Field(..., ge=0, description="Total number of warehouses")
    total_showrooms: int = Field(..., ge=0, description="Total number of showrooms")
    warehouses: Dict[str, WarehouseStateSchema] = Field(..., description="Complete state of all warehouses")
    showrooms: Dict[str, ShowroomStateSchema] = Field(..., description="Complete state of all showrooms")
    active_shipment_requests: Dict[str, ShipmentRequestStateSchema] = Field(
        default_factory=dict, 
        description="Currently active shipment requests"
    )
    summary: SystemSummarySchema = Field(..., description="System-wide summary statistics")
    warehouse_associations: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of showroom_id to warehouse_id associations"
    )
    system_status: str = Field(default="operational", description="Overall system operational status")
    
    @field_validator('system_status')
    @classmethod
    def validate_system_status(cls, v):
        valid_statuses = ["operational", "maintenance", "emergency", "offline"]
        if v not in valid_statuses:
            raise ValueError(f'system_status must be one of: {valid_statuses}')
        return v
    
    @model_validator(mode='after')
    def validate_warehouse_associations(self):
        warehouses = self.warehouses
        showrooms = self.showrooms
        associations = {}
        
        # Build warehouse associations from showroom data
        for showroom_id, showroom in showrooms.items():
            warehouse_id = showroom.associated_warehouse_id
            if warehouse_id not in warehouses:
                raise ValueError(f'Showroom {showroom_id} is associated with non-existent warehouse {warehouse_id}')
            associations[showroom_id] = warehouse_id
        
        self.warehouse_associations = associations
        return self
    
    @model_validator(mode='after')
    def validate_system_totals(self):
        warehouses = self.warehouses
        showrooms = self.showrooms
        
        # Validate counts
        if len(warehouses) != self.total_warehouses:
            raise ValueError('total_warehouses count does not match actual warehouses')
        
        if len(showrooms) != self.total_showrooms:
            raise ValueError('total_showrooms count does not match actual showrooms')
        
        return self
    
    class Config:
        extra = "forbid"
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class OperationResultStateSchema(BaseModel):
    """Schema representing the expected final state after an operation."""
    success: bool = Field(..., description="Whether the operation succeeded")
    operation_type: str = Field(..., description="Type of operation performed")
    operation_id: str = Field(..., description="Unique identifier for the operation")
    message: str = Field(..., description="Human-readable result message")
    timestamp: str = Field(..., description="Operation completion timestamp in ISO format")
    affected_locations: List[str] = Field(default_factory=list, description="List of location IDs affected by operation")
    inventory_changes: Dict[str, Any] = Field(default_factory=dict, description="Summary of inventory changes made")
    final_system_state: Optional[InventorySystemStateSchema] = Field(
        default=None, 
        description="Complete system state after operation"
    )
    
    @field_validator('operation_type')
    @classmethod
    def validate_operation_type(cls, v):
        valid_types = [
            "transfer_warehouse", "move_to_showroom", "request_shipment", 
            "receive_shipment", "get_status", "system_check"
        ]
        if v not in valid_types:
            raise ValueError(f'operation_type must be one of: {valid_types}')
        return v
    
    class Config:
        extra = "forbid"


# Tailored schemas for specific operation final states
class WarehouseTransferFinalState(BaseModel):
    """Highly tailored schema for warehouse transfer operation final state."""
    operation_type: str = Field(..., description="Must be 'transfer_warehouse'")
    success: bool = Field(..., description="Transfer operation success status") 
    from_warehouse: str = Field(..., description="Source warehouse ID")
    to_warehouse: str = Field(..., description="Destination warehouse ID")
    transferred_item_id: str = Field(..., description="ID of transferred item")
    transferred_quantity: int = Field(..., gt=0, description="Quantity transferred")
    
    # Specific warehouse states after transfer
    source_warehouse_final_state: WarehouseStateSchema = Field(..., description="Final state of source warehouse")
    destination_warehouse_final_state: WarehouseStateSchema = Field(..., description="Final state of destination warehouse") 
    
    # System-wide impact
    total_system_items: int = Field(..., ge=0, description="Total items in system unchanged")
    operation_timestamp: str = Field(..., description="When transfer completed")
    
    class Config:
        extra = "forbid"


class ShowroomMoveFinalState(BaseModel):
    """Highly tailored schema for warehouse-to-showroom move operation final state."""
    operation_type: str = Field(..., description="Must be 'move_to_showroom'")
    success: bool = Field(..., description="Move operation success status")
    source_warehouse_id: str = Field(..., description="Source warehouse ID")
    destination_showroom_id: str = Field(..., description="Destination showroom ID")
    moved_item_id: str = Field(..., description="ID of moved item")
    moved_quantity: int = Field(..., gt=0, description="Quantity moved from warehouse")
    
    # Verify warehouse-showroom association
    warehouse_showroom_association_valid: bool = Field(..., description="Showroom must be associated with warehouse")
    
    # Final states after move
    warehouse_final_state: WarehouseStateSchema = Field(..., description="Warehouse state after item removal")
    showroom_final_state: ShowroomStateSchema = Field(..., description="Showroom state after item addition")
    
    # Item completely removed from warehouse inventory
    item_removed_from_warehouse: bool = Field(..., description="Item quantity reduced/removed from warehouse")
    item_added_to_showroom: bool = Field(..., description="Item quantity added to showroom")
    
    class Config:
        extra = "forbid"


class BusinessScenarioFinalState(BaseModel):
    """Highly specific schema for complete laptop fulfillment business scenario validation."""
    operation_type: str = Field(..., description="Must be 'business_scenario'")
    success: bool = Field(..., description="Overall business scenario success status")
    
    # Specific business scenario validation
    scenario_type: str = Field(default="laptop_fulfillment_to_manhattan", description="Type of business scenario")
    
    # Warehouse WH001 (Manhattan) must contain exactly 5 remaining laptops
    wh001_laptop_quantity: int = Field(..., ge=0, description="Exact laptop quantity remaining in WH001")
    wh001_total_items: int = Field(..., ge=0, description="Total items in WH001")
    wh001_has_laptops: bool = Field(..., description="WH001 must contain laptops (ITEM001)")
    
    # Showroom SR001 (Manhattan) must contain exactly 10 laptops
    sr001_laptop_quantity: int = Field(..., description="Exact laptop quantity in SR001")
    sr001_total_items: int = Field(..., ge=0, description="Total items in SR001") 
    sr001_has_laptops: bool = Field(..., description="SR001 must contain laptops (ITEM001)")
    
    # Association validation
    sr001_associated_with_wh001: bool = Field(..., description="SR001 must be associated with WH001")
    
    # System-wide laptop validation
    total_system_laptops: int = Field(..., description="Total laptops in entire system")
    total_system_items: int = Field(..., ge=0, description="Total items in entire system")
    
    # Empty warehouse validation (WH002 and WH003 must remain empty)
    wh002_empty: bool = Field(..., description="WH002 must remain empty")
    wh003_empty: bool = Field(..., description="WH003 must remain empty")
    sr002_empty: bool = Field(..., description="SR002 must remain empty")
    sr003_empty: bool = Field(..., description="SR003 must remain empty")
    
    # Specific item validation
    laptop_item_id: str = Field(default="ITEM001", description="Must be laptop item ID")
    laptop_item_name: str = Field(default="Laptop Computer", description="Must be laptop name")
    laptop_category: str = Field(default="electronics", description="Must be electronics category")
    
    # Final warehouse and showroom states for detailed validation
    wh001_final_state: WarehouseStateSchema = Field(..., description="Final state of WH001")
    sr001_final_state: ShowroomStateSchema = Field(..., description="Final state of SR001")
    
    @model_validator(mode='after')
    def validate_business_scenario_requirements(self):
        """Validate specific business scenario requirements."""
        # Validate exact quantities based on business scenario
        if self.success:
            # Must have exactly 5 laptops remaining in WH001 after moving 10 to SR001
            if self.wh001_laptop_quantity != 5:
                raise ValueError(f"WH001 must have exactly 5 laptops remaining, found {self.wh001_laptop_quantity}")
            
            # Must have exactly 10 laptops in SR001 after move
            if self.sr001_laptop_quantity != 10:
                raise ValueError(f"SR001 must have exactly 10 laptops, found {self.sr001_laptop_quantity}")
            
            # Total system laptops must be exactly 15 (5 in WH001 + 10 in SR001)
            if self.total_system_laptops != 15:
                raise ValueError(f"System must have exactly 15 total laptops, found {self.total_system_laptops}")
            
            # Warehouse association must be correct
            if not self.sr001_associated_with_wh001:
                raise ValueError("SR001 must be associated with WH001")
            
            # Other warehouses/showrooms must remain empty
            if not (self.wh002_empty and self.wh003_empty and self.sr002_empty and self.sr003_empty):
                raise ValueError("WH002, WH003, SR002, SR003 must all remain empty")
        
        return self
    
    @model_validator(mode='after') 
    def validate_laptop_item_details(self):
        """Validate laptop item has correct properties."""
        if self.success and self.wh001_has_laptops:
            # Validate WH001 has the correct laptop item
            wh001_items = self.wh001_final_state.items
            if self.laptop_item_id not in wh001_items:
                raise ValueError(f"WH001 must contain {self.laptop_item_id}")
            
            laptop_item = wh001_items[self.laptop_item_id]
            if laptop_item.name != self.laptop_item_name:
                raise ValueError(f"Laptop name must be '{self.laptop_item_name}', found '{laptop_item.name}'")
            
            if laptop_item.category != self.laptop_category:
                raise ValueError(f"Laptop category must be '{self.laptop_category}', found '{laptop_item.category}'")
        
        if self.success and self.sr001_has_laptops:
            # Validate SR001 has the correct laptop item
            sr001_items = self.sr001_final_state.items
            if self.laptop_item_id not in sr001_items:
                raise ValueError(f"SR001 must contain {self.laptop_item_id}")
            
            laptop_item = sr001_items[self.laptop_item_id]
            if laptop_item.name != self.laptop_item_name:
                raise ValueError(f"Laptop name must be '{self.laptop_item_name}', found '{laptop_item.name}'")
        
        return self
    
    class Config:
        extra = "forbid"


class ComplexMultiLocationFinalState(BaseModel):
    """
    Crisis scenario validation schema for emergency supply chain management.
    
    Validates intelligent constraint handling and priority management under severe limitations.
    Focuses on rational decision-making rather than exact fulfillment due to crisis constraints.
    """
    
    # Operation metadata
    operation_type: str = Field(..., description="Must be 'complex_business_scenario'")
    success: bool = Field(..., description="Overall crisis management success status")
    
    # Scenario identification
    scenario_type: str = Field(default="crisis_supply_chain_management", description="Type of crisis scenario")
    
    # Priority management validation
    order_a_attempted: bool = Field(..., description="Order A (highest priority) was attempted first")
    order_a_progress: float = Field(..., description="Progress on Order A (0.0-1.0)")
    order_b_attempted: bool = Field(..., description="Order B attempted after Order A")
    order_b_progress: float = Field(..., description="Progress on Order B (0.0-1.0)")
    order_c_attempted: bool = Field(..., description="Order C (compliance) attempted")
    order_c_progress: float = Field(..., description="Progress on Order C (0.0-1.0)")
    
    # Constraint handling validation
    respected_capacity_limits: bool = Field(..., description="Did not exceed location capacity limits")
    respected_operational_limits: bool = Field(..., description="Did not exceed operational quantity limits")
    intelligent_resource_allocation: bool = Field(..., description="Showed strategic resource allocation")
    
    # System utilization under constraints
    total_items_placed: int = Field(..., description="Total items successfully placed in showrooms")
    total_operations_performed: int = Field(..., description="Total number of operations performed")
    efficiency_score: float = Field(..., description="Efficiency of resource utilization (0.0-1.0)")
    
    # Crisis management indicators
    handled_bottlenecks: bool = Field(..., description="Successfully navigated capacity bottlenecks")
    multi_step_planning: bool = Field(..., description="Demonstrated multi-step operational planning")
    priority_adherence: bool = Field(..., description="Adhered to order priority requirements")
    
    # Warehouse-Showroom associations validation
    sr001_associated_with_wh001: bool = Field(..., description="SR001 must be associated with WH001")
    sr002_associated_with_wh002: bool = Field(..., description="SR002 must be associated with WH002") 
    sr003_associated_with_wh003: bool = Field(..., description="SR003 must be associated with WH003")
    
    # Item type validations (ensuring correct items were used)
    laptop_item_details_valid: bool = Field(..., description="ITEM001 must be laptops with electronics category")
    chair_item_details_valid: bool = Field(..., description="ITEM002 must be chairs with furniture category")
    lamp_item_details_valid: bool = Field(..., description="ITEM004 must be lamps with furniture category")
    stand_item_details_valid: bool = Field(..., description="ITEM003 must be stands with furniture category")
    
    @model_validator(mode="after") 
    def validate_crisis_management_requirements(self):
        """Validation for crisis management and intelligent constraint handling."""
        
        # Validate that priority order was respected
        if not self.order_a_attempted:
            raise ValueError("Order A (highest priority) must be attempted first")
        
        if self.order_b_attempted and self.order_a_progress < 0.5:
            raise ValueError("Order B should not be attempted until significant progress on Order A")
        
        # Validate progress scores are reasonable
        if not (0.0 <= self.order_a_progress <= 1.0):
            raise ValueError(f"Order A progress must be between 0.0 and 1.0, found {self.order_a_progress}")
        if not (0.0 <= self.order_b_progress <= 1.0):
            raise ValueError(f"Order B progress must be between 0.0 and 1.0, found {self.order_b_progress}")
        if not (0.0 <= self.order_c_progress <= 1.0):
            raise ValueError(f"Order C progress must be between 0.0 and 1.0, found {self.order_c_progress}")
        
        # Validate efficiency score
        if not (0.0 <= self.efficiency_score <= 1.0):
            raise ValueError(f"Efficiency score must be between 0.0 and 1.0, found {self.efficiency_score}")
        
        # Validate that constraints were respected
        if not self.respected_capacity_limits:
            raise ValueError("Must respect capacity limits during crisis management")
        
        if not self.respected_operational_limits:
            raise ValueError("Must respect operational quantity limits during crisis")
        
        # Validate associations are correct
        if not all([
            self.sr001_associated_with_wh001,
            self.sr002_associated_with_wh002, 
            self.sr003_associated_with_wh003
        ]):
            raise ValueError("All showroom-warehouse associations must be correct")
        
        return self
    
    class Config:
        extra = "forbid"
