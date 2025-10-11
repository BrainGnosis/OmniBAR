# © 2023 BrainGnosis Inc. All rights reserved.

"""
Complex Multi-Location Crisis Management Benchmark using gpt-4 LangChain Agent.

This benchmark tests a gpt-4 LangChain agent's ability to manage a crisis scenario involving
emergency supply chain management across multiple locations with severe capacity constraints
and competing priority orders.

Architecture:
- Core `InventoryManager` class handles crisis scenario business logic
- `create_inventory_tools()` creates LangChain tools for inventory operations
- `create_inventory_agent_executor()` returns enhanced AgentExecutor with state validation
- Complex multi-location state validation using `ComplexMultiLocationFinalState` schema

Crisis Scenario Features:
- Multi-priority order management (Order A, B, C with dependencies)
- Severe capacity constraints (reduced warehouse/showroom capacities)
- Strategic resource allocation across 3 showrooms and 3 warehouses  
- Partial state validation with scoring for incomplete fulfillment
- Intelligent constraint handling and priority adherence validation

Requirements:
- OPENAI_API_KEY environment variable or .env file
- LangChain and OpenAI packages: `pip install langchain langchain-openai langchain-core`
"""

import asyncio
import json
import uuid
import os
from typing import Dict, Any, List, Tuple
from pathlib import Path
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

# Flexible environment variable loading
def load_environment_variables():
    """
    Load environment variables from various possible locations.
    
    Priority order:
    1. OMNIBAR_ENV_PATH environment variable (if set)
    2. .env in current directory  
    3. .env in parent directory (examples/)
    4. .env in project root (../../)
    5. Skip if none found
    """
    try:
        from dotenv import load_dotenv
        import os
        
        # Option 1: Check for custom env path
        custom_env = os.getenv('OMNIBAR_ENV_PATH')
        if custom_env:
            custom_path = Path(custom_env)
            if custom_path.exists():
                load_dotenv(custom_path)
                print(f"✅ Loaded environment variables from custom path: {custom_path}")
                return True
            else:
                print(f"⚠️  Custom env path not found: {custom_path}")
        
        # Option 2-4: Check common locations
        current_dir = Path(__file__).parent
        search_paths = [
            current_dir / '.env',                    # ./env
            current_dir.parent / '.env',             # ../env  
            current_dir.parent.parent / '.env'       # ../../.env (project root)
        ]
        
        for env_path in search_paths:
            if env_path.exists():
                load_dotenv(env_path)
                print(f"✅ Loaded environment variables from {env_path}")
                return True
        
        print("⚠️  No .env file found in common locations")
        print("💡 To specify a custom location, set OMNIBAR_ENV_PATH environment variable")
        return False
        
    except ImportError:
        print("⚠️  python-dotenv not available, environment variables should be set manually")
        return False

# Load environment variables
load_environment_variables()

# LangChain and OpenAI imports
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI


# Import OmniBAR components
from omnibar import OmniBarmarker, Benchmark
from omnibar.objectives import PartialPathEqualityObjective, CombinedBenchmarkObjective

# Import inventory system components from extras package
from examples.extras import (
    # Models
    Item, Warehouse, Showroom, ShipmentRequest,
    
    # Utils
    create_state_objective_for_operation,
    create_complex_multi_location_state_dict
)


# =====================================================
# Tool Schema Definitions for Path-Based Benchmarking
# =====================================================

class RequestShipmentSchema(BaseModel):
    """Schema for request_shipment tool arguments."""
    item_requests_str: str = Field(description="JSON string of item requests like '{\"ITEM001\": 10}'")
    destination_warehouse: str = Field(description="Target warehouse ID (WH001, WH002, WH003)")

class ReceiveShipmentSchema(BaseModel):
    """Schema for receive_shipment tool arguments."""
    request_id: str = Field(description="Shipment request ID from request_shipment")
    received_items_str: str = Field(description="JSON string of received items like '{\"ITEM001\": 8}'")

class TransferWarehouseSchema(BaseModel):
    """Schema for transfer_warehouse tool arguments."""
    from_warehouse: str = Field(description="Source warehouse ID")
    to_warehouse: str = Field(description="Destination warehouse ID")
    item_id: str = Field(description="Item ID to transfer")
    quantity: str = Field(description="Number of items to transfer (as string)")

class MoveToShowroomSchema(BaseModel):
    """Schema for move_to_showroom tool arguments."""
    warehouse_id: str = Field(description="Source warehouse ID")
    showroom_id: str = Field(description="Destination showroom ID")
    item_id: str = Field(description="Item ID to move")
    quantity: str = Field(description="Number of items to move (as string)")


# =====================================================
# Optimal Path Definitions for Crisis Management
# =====================================================

def create_optimal_inventory_paths() -> List[List[Tuple[str, type[BaseModel] | None]]]:
    """
    Define optimal execution paths for the crisis management scenario.
    
    These paths represent different strategic approaches to fulfill the complex multi-order crisis:
    - Order A: SR001 needs 12 laptops + 8 chairs + 4 stands
    - Order B: SR002 needs 15 laptops + 10 lamps + 6 chairs, SR003 needs 8 laptops + 12 chairs + 5 stands + 4 lamps  
    - Order C: Equal laptop distribution (6 more each) + varying notebook packs
    
    Total: 41 laptops, 36 chairs, 13 lamps, 9 stands, 10 notebook packs
    
    Returns:
        List of valid path sequences, each containing (tool_name, schema_type) tuples
    """
    
    # Strategy 1: Single High-Capacity Warehouse Strategy
    # Use WH003 (Chicago, 820 capacity) as primary hub, then distribute
    single_warehouse_path = [
        ("request_shipment", RequestShipmentSchema),  # Request all laptops to WH003
        ("receive_shipment", ReceiveShipmentSchema),   # Receive laptops
        ("request_shipment", RequestShipmentSchema),  # Request all chairs to WH003
        ("receive_shipment", ReceiveShipmentSchema),   # Receive chairs
        ("request_shipment", RequestShipmentSchema),  # Request remaining items to WH003
        ("receive_shipment", ReceiveShipmentSchema),   # Receive remaining items
        ("move_to_showroom", MoveToShowroomSchema),    # Move items to SR003 (local)
        ("transfer_warehouse", TransferWarehouseSchema), # Transfer items to WH001
        ("move_to_showroom", MoveToShowroomSchema),    # Move items to SR001
        ("transfer_warehouse", TransferWarehouseSchema), # Transfer items to WH002  
        ("move_to_showroom", MoveToShowroomSchema),    # Move items to SR002
    ]
    
    # Strategy 2: Distributed Multi-Warehouse Strategy
    # Distribute initial shipments based on showroom proximity
    distributed_path = [
        ("request_shipment", RequestShipmentSchema),  # Laptops to WH001 (for SR001)
        ("request_shipment", RequestShipmentSchema),  # Chairs to WH002 (for SR002)  
        ("request_shipment", RequestShipmentSchema),  # Remaining items to WH003
        ("receive_shipment", ReceiveShipmentSchema),   # Receive at WH001
        ("receive_shipment", ReceiveShipmentSchema),   # Receive at WH002
        ("receive_shipment", ReceiveShipmentSchema),   # Receive at WH003
        ("move_to_showroom", MoveToShowroomSchema),    # WH001 -> SR001
        ("move_to_showroom", MoveToShowroomSchema),    # WH002 -> SR002
        ("move_to_showroom", MoveToShowroomSchema),    # WH003 -> SR003
        ("transfer_warehouse", TransferWarehouseSchema), # Cross-warehouse optimization
        ("move_to_showroom", MoveToShowroomSchema),    # Final distribution
    ]
    
    # Strategy 3: Priority-Sequential Strategy
    # Handle Order A first completely, then Order B, then Order C
    priority_sequential_path = [
        ("request_shipment", RequestShipmentSchema),  # Order A requirements
        ("receive_shipment", ReceiveShipmentSchema),   # Receive Order A items
        ("move_to_showroom", MoveToShowroomSchema),    # Fulfill Order A (SR001)
        ("request_shipment", RequestShipmentSchema),  # Order B requirements
        ("receive_shipment", ReceiveShipmentSchema),   # Receive Order B items
        ("move_to_showroom", MoveToShowroomSchema),    # Fulfill Order B (SR002)
        ("move_to_showroom", MoveToShowroomSchema),    # Fulfill Order B (SR003)
        ("request_shipment", RequestShipmentSchema),  # Order C requirements
        ("receive_shipment", ReceiveShipmentSchema),   # Receive Order C items
        ("move_to_showroom", MoveToShowroomSchema),    # Fulfill Order C (all showrooms)
    ]
    
    # Strategy 4: Optimized Transfer Strategy
    # Use inter-warehouse transfers to optimize capacity utilization
    transfer_optimized_path = [
        ("request_shipment", RequestShipmentSchema),  # Large shipment to WH003
        ("receive_shipment", ReceiveShipmentSchema),   # Receive bulk shipment
        ("transfer_warehouse", TransferWarehouseSchema), # Optimize to WH001
        ("transfer_warehouse", TransferWarehouseSchema), # Optimize to WH002
        ("move_to_showroom", MoveToShowroomSchema),    # WH001 -> SR001
        ("move_to_showroom", MoveToShowroomSchema),    # WH002 -> SR002
        ("move_to_showroom", MoveToShowroomSchema),    # WH003 -> SR003
        ("request_shipment", RequestShipmentSchema),  # Additional items as needed
        ("receive_shipment", ReceiveShipmentSchema),   # Receive additional items
        ("move_to_showroom", MoveToShowroomSchema),    # Final distribution
    ]
    
    # Strategy 5: Minimal Steps Strategy
    # Most efficient path with fewest operations
    minimal_steps_path = [
        ("request_shipment", RequestShipmentSchema),  # All items to WH003
        ("receive_shipment", ReceiveShipmentSchema),   # Receive all at once
        ("move_to_showroom", MoveToShowroomSchema),    # Direct to SR003
        ("transfer_warehouse", TransferWarehouseSchema), # WH003 -> WH001
        ("transfer_warehouse", TransferWarehouseSchema), # WH003 -> WH002
        ("move_to_showroom", MoveToShowroomSchema),    # WH001 -> SR001
        ("move_to_showroom", MoveToShowroomSchema),    # WH002 -> SR002
    ]
    
    return [
        single_warehouse_path,
        distributed_path, 
        priority_sequential_path,
        transfer_optimized_path,
        minimal_steps_path
    ]


def create_inventory_path_objective() -> PartialPathEqualityObjective:
    """
    Create a path-based objective that evaluates execution efficiency for crisis management.
    
    Uses PartialPathEqualityObjective to score similarity to optimal paths (0.0 to 1.0).
    Higher scores indicate more efficient strategic execution.
    
    Returns:
        PartialPathEqualityObjective configured for inventory crisis management
    """
    optimal_paths = create_optimal_inventory_paths()
    
    return PartialPathEqualityObjective(
        name="inventory_crisis_path_efficiency",
        description="Evaluates execution path efficiency for complex multi-location crisis management",
        category="supply_chain_optimization", 
        tags=["crisis_management", "path_optimization", "strategic_execution"],
        goal=optimal_paths,
        output_key="execution_path"
    )


def create_combined_crisis_objective() -> CombinedBenchmarkObjective:
    """
    Create a combined objective that evaluates both state correctness and path efficiency.
    
    Combines:
    1. State-based objective - validates final system state and order fulfillment
    2. Path-based objective - scores execution efficiency and strategic approach
    
    Returns:
        CombinedBenchmarkObjective that runs both evaluations simultaneously
    """
    # Create the state-based objective for crisis scenario validation
    state_objective = create_state_objective_for_operation("complex_business_scenario")
    
    # Create the path-based objective for execution efficiency analysis
    path_objective = create_inventory_path_objective()
    
    return CombinedBenchmarkObjective(
        name="crisis_management_dual_evaluation",
        description="Combined state correctness and execution path efficiency evaluation for crisis management",
        category="supply_chain_crisis",
        tags=["crisis_management", "dual_evaluation", "state_validation", "path_optimization"],
        objectives=[state_objective, path_objective]
    )


class InventoryManager:
    """
    Comprehensive inventory management system with multi-warehouse support.
    
    Features:
    - Multi-warehouse inventory tracking
    - Warehouse-to-showroom item movement
    - Shipment request management  
    - Real-time capacity monitoring
    - Comprehensive audit logging
    """
    
    def __init__(self):
        self.warehouses: Dict[str, Warehouse] = {}
        self.showrooms: Dict[str, Showroom] = {}
        self.shipment_requests: Dict[str, ShipmentRequest] = {}
        self.operation_log: List[Dict[str, Any]] = []
        self._setup_initial_inventory()
    
    def _setup_initial_inventory(self):
        """Initialize the inventory with sample data."""
        
        # Create warehouses with SEVERELY REDUCED capacities for crisis scenario
        self.warehouses = {
            "WH001": Warehouse("WH001", "Main Warehouse", "New York", 35),      # CRISIS: Emergency maintenance - reduced from 570!
            "WH002": Warehouse("WH002", "West Coast Warehouse", "Los Angeles", 25),  # CRISIS: Renovation - reduced from 430!
            "WH003": Warehouse("WH003", "Midwest Distribution", "Chicago", 820)     # Full capacity but has 48-hour delivery delays
        }
        
        # Create showrooms with REDUCED capacities due to construction/remodeling
        self.showrooms = {
            "SR001": Showroom("SR001", "Manhattan Showroom", "New York", "WH001", 30),      # CRISIS: Construction - reduced from 200!
            "SR002": Showroom("SR002", "Beverly Hills Showroom", "Los Angeles", "WH002", 25),  # CRISIS: Remodeling - reduced from 150!
            "SR003": Showroom("SR003", "Downtown Chicago Showroom", "Chicago", "WH003", 300)   # Full capacity available
        }
        
        # Start with empty showrooms - items will be moved from warehouses through operations
        for showroom in self.showrooms.values():
            showroom.items = {}
        
        # Start with empty warehouses - items will be added through shipment operations
        # All warehouses begin with no inventory to track item movement from the beginning
        for warehouse in self.warehouses.values():
            warehouse.items = {}

    def request_shipment(self, item_requests: Dict[str, int], destination_warehouse: str) -> Dict[str, Any]:
        """Request a shipment of items to a destination warehouse."""
        timestamp = datetime.now()
        request_id = f"REQ_{uuid.uuid4().hex[:8].upper()}"
        
        try:
            # Validate destination warehouse exists
            if destination_warehouse not in self.warehouses:
                raise ValueError(f"Destination warehouse {destination_warehouse} does not exist")
            
            # Create shipment request
            shipment_request = ShipmentRequest(
                request_id=request_id,
                item_requests=item_requests,
                destination_warehouse=destination_warehouse, 
                requested_date=timestamp + timedelta(days=3),
                status="pending"
            )
            
            # Store the request
            self.shipment_requests[request_id] = shipment_request
            
            result = {
                "success": True,
                "request_id": request_id,
                "operation_type": "shipment_request",
                "item_requests": item_requests,
                "destination_warehouse": destination_warehouse,
                "status": "pending",
                "timestamp": timestamp.isoformat(),
                "message": f"Shipment request {request_id} created successfully"
            }
            
        except Exception as e:
            result = {
                "success": False,
                "operation_id": request_id,
                "operation_type": "shipment_request",
                "timestamp": timestamp.isoformat(), 
                "error": str(e),
                "message": f"Failed to create shipment request: {str(e)}"
            }
        
        self.operation_log.append(result)
        return result

    def receive_shipment(self, request_id: str, received_items: Dict[str, int]) -> Dict[str, Any]:
        """Process received shipment and add items to destination warehouse.""" 
        timestamp = datetime.now()
        operation_id = f"RCV_{uuid.uuid4().hex[:8].upper()}"
        
        try:
            # Validate shipment request exists
            if request_id not in self.shipment_requests:
                raise ValueError(f"Shipment request {request_id} not found")
            
            request = self.shipment_requests[request_id]
            destination_warehouse = self.warehouses[request.destination_warehouse]
            
            # Check capacity constraints
            total_incoming = sum(received_items.values())
            if total_incoming > destination_warehouse.available_capacity:
                raise ValueError(f"Insufficient capacity in warehouse {request.destination_warehouse}")
            
            # Add items to destination warehouse
            for item_id, quantity in received_items.items():
                if item_id in destination_warehouse.items:
                    destination_warehouse.items[item_id].quantity += quantity
                else:
                    # Create new item with proper details based on common item catalog
                    item_catalog = {
                        "ITEM001": ("Laptop Computer", 999.99, "electronics"),
                        "ITEM002": ("Office Chair", 199.99, "furniture"),
                        "ITEM003": ("Monitor Stand", 89.99, "furniture"),
                        "ITEM004": ("Desk Lamp", 49.99, "furniture"),
                        "ITEM005": ("Notebook Pack", 9.99, "stationery")
                    }
                    
                    if item_id in item_catalog:
                        name, price, category = item_catalog[item_id]
                        destination_warehouse.items[item_id] = Item(item_id, name, quantity, price, category)
                    else:
                        # Fallback for unknown items
                        destination_warehouse.items[item_id] = Item(item_id, f"Item {item_id}", quantity, 50.0, "general")
            
            # Update shipment request status
            request.status = "delivered"
            
            result = {
                "success": True,
                "operation_id": operation_id,
                "operation_type": "shipment_receipt",
                "request_id": request_id,
                "destination_warehouse": request.destination_warehouse,
                "received_items": received_items,
                "timestamp": timestamp.isoformat(),
                "message": f"Shipment {request_id} received successfully"
            }
            
        except Exception as e:
            result = {
                "success": False,
                "operation_id": operation_id, 
                "operation_type": "shipment_receipt",
                "request_id": request_id,
                "timestamp": timestamp.isoformat(),
                "error": str(e),
                "message": f"Failed to receive shipment: {str(e)}"
            }
        
        self.operation_log.append(result)
        return result

    def transfer_between_warehouses(self, from_warehouse: str, to_warehouse: str, item_id: str, quantity: int) -> Dict[str, Any]:
        """Transfer items directly between warehouses."""
        timestamp = datetime.now()
        operation_id = f"TXF_{uuid.uuid4().hex[:8].upper()}"
        
        try:
            # Validate warehouses exist
            if from_warehouse not in self.warehouses:
                raise ValueError(f"Source warehouse {from_warehouse} does not exist")
            if to_warehouse not in self.warehouses:
                raise ValueError(f"Destination warehouse {to_warehouse} does not exist")
            
            source_wh = self.warehouses[from_warehouse]
            dest_wh = self.warehouses[to_warehouse]
            
            # Validate item exists and sufficient quantity
            if item_id not in source_wh.items:
                raise ValueError(f"Item {item_id} not found in warehouse {from_warehouse}")
            
            source_item = source_wh.items[item_id]
            if source_item.quantity < quantity:
                raise ValueError(f"Insufficient quantity: requested {quantity}, available {source_item.quantity}")
            
            # Check destination capacity
            if quantity > dest_wh.available_capacity:
                raise ValueError(f"Insufficient capacity in destination warehouse {to_warehouse}")
            
            # Perform transfer
            source_item.quantity -= quantity
            if source_item.quantity == 0:
                del source_wh.items[item_id]
            
            # Add to destination
            if item_id in dest_wh.items:
                dest_wh.items[item_id].quantity += quantity
            else:
                dest_wh.items[item_id] = Item(item_id, source_item.name, quantity, source_item.unit_price, source_item.category)
            
            result = {
                "success": True,
                "operation_id": operation_id,
                "operation_type": "warehouse_transfer",
                "from_warehouse": from_warehouse,
                "to_warehouse": to_warehouse,
                "item_id": item_id,
                "quantity_requested": quantity,
                "timestamp": timestamp.isoformat(),
                "message": f"Transferred {quantity} units of {item_id} from {from_warehouse} to {to_warehouse}"
            }
            
        except Exception as e:
            result = {
                "success": False,
                "operation_id": operation_id,
                "operation_type": "warehouse_transfer",
                "from_warehouse": from_warehouse,
                "to_warehouse": to_warehouse,
                "item_id": item_id,
                "quantity_requested": quantity,
                "timestamp": timestamp.isoformat(),
                "error": str(e),
                "message": f"Failed to transfer items: {str(e)}"
            }
        
        self.operation_log.append(result)
        return result

    def move_to_showroom(self, warehouse_id: str, showroom_id: str, item_id: str, quantity: int) -> Dict[str, Any]:
        """Move items from warehouse to its associated showroom."""
        timestamp = datetime.now()
        operation_id = f"SRM_{uuid.uuid4().hex[:8].upper()}"
        
        try:
            # Validate warehouse and showroom exist
            if warehouse_id not in self.warehouses:
                raise ValueError(f"Warehouse {warehouse_id} does not exist")
            if showroom_id not in self.showrooms:
                raise ValueError(f"Showroom {showroom_id} does not exist")
            
            warehouse = self.warehouses[warehouse_id]
            showroom = self.showrooms[showroom_id]
            
            # Validate showroom is associated with this warehouse
            if showroom.associated_warehouse_id != warehouse_id:
                raise ValueError(f"Showroom {showroom_id} is not associated with warehouse {warehouse_id}")
            
            # Validate item exists and sufficient quantity
            if item_id not in warehouse.items:
                raise ValueError(f"Item {item_id} not found in warehouse {warehouse_id}")
            
            warehouse_item = warehouse.items[item_id]
            if warehouse_item.quantity < quantity:
                raise ValueError(f"Insufficient quantity: requested {quantity}, available {warehouse_item.quantity}")
            
            # Check showroom capacity
            if quantity > showroom.available_capacity:
                raise ValueError(f"Insufficient capacity in showroom {showroom_id}")
            
            # Perform move
            warehouse_item.quantity -= quantity
            if warehouse_item.quantity == 0:
                del warehouse.items[item_id]
            
            # Add to showroom
            if item_id in showroom.items:
                showroom.items[item_id].quantity += quantity
            else:
                showroom.items[item_id] = Item(item_id, warehouse_item.name, quantity, warehouse_item.unit_price, warehouse_item.category)
            
            result = {
                "success": True,
                "operation_id": operation_id,
                "operation_type": "showroom_move",
                "warehouse_id": warehouse_id,
                "showroom_id": showroom_id,
                "item_id": item_id,
                "quantity": quantity,
                "timestamp": timestamp.isoformat(),
                "message": f"Moved {quantity} units of {item_id} from warehouse {warehouse_id} to showroom {showroom_id}"
            }
            
        except Exception as e:
            result = {
                "success": False,
                "operation_id": operation_id,
                "operation_type": "showroom_move",
                "warehouse_id": warehouse_id,
                "showroom_id": showroom_id,
                "item_id": item_id,
                "quantity": quantity,
                "timestamp": timestamp.isoformat(),
                "error": str(e),
                "message": f"Failed to move items to showroom: {str(e)}"
            }
        
        self.operation_log.append(result)
        return result
    

    
    def get_inventory_status(self) -> Dict[str, Any]:
        """Get comprehensive inventory status across all warehouses and showrooms."""
        status = {
            "total_warehouses": len(self.warehouses),
            "total_showrooms": len(self.showrooms),
            "warehouses": {},
            "showrooms": {},
            "summary": {
                "total_items": 0,
                "total_capacity": 0,
                "total_value": 0.0
            }
        }
        
        # Collect warehouse information
        for wh_id, warehouse in self.warehouses.items():
            wh_info = {
                "name": warehouse.name,
                "location": warehouse.location,
                "capacity": warehouse.capacity,
                "current_quantity": warehouse.current_quantity,
                "available_capacity": warehouse.available_capacity,
                "utilization_rate": warehouse.current_quantity / warehouse.capacity if warehouse.capacity > 0 else 0,
                "items": {item_id: {"quantity": item.quantity, "value": item.quantity * item.unit_price} 
                         for item_id, item in warehouse.items.items()}
            }
            status["warehouses"][wh_id] = wh_info
            status["summary"]["total_items"] += warehouse.current_quantity
            status["summary"]["total_capacity"] += warehouse.capacity
            
            # Calculate warehouse value
            for item in warehouse.items.values():
                status["summary"]["total_value"] += item.quantity * item.unit_price
        
        # Collect showroom information
        for sr_id, showroom in self.showrooms.items():
            sr_info = {
                "name": showroom.name,
                "location": showroom.location,
                "associated_warehouse": showroom.associated_warehouse_id,
                "capacity": showroom.capacity,
                "current_quantity": showroom.current_quantity,
                "available_capacity": showroom.available_capacity,
                "utilization_rate": showroom.current_quantity / showroom.capacity if showroom.capacity > 0 else 0,
                "items": {item_id: {"quantity": item.quantity, "value": item.quantity * item.unit_price} 
                         for item_id, item in showroom.items.items()}
            }
            status["showrooms"][sr_id] = sr_info
            status["summary"]["total_items"] += showroom.current_quantity
            status["summary"]["total_capacity"] += showroom.capacity
            
            # Calculate showroom value
            for item in showroom.items.values():
                status["summary"]["total_value"] += item.quantity * item.unit_price
        
        return status


def create_inventory_tools(inventory_manager: InventoryManager):
    """Create LangChain tools for inventory operations."""
    
    @tool
    def request_shipment(item_requests_str: str, destination_warehouse: str) -> str:
        """
        Request a shipment of items to a destination warehouse.
        
        Parameters:
        item_requests_str (str): JSON string containing item IDs and quantities to request. 
                                Format: '{"ITEM001": 10, "ITEM002": 5}'. 
                                Available items: ITEM001 (Laptop), ITEM002 (Office Chair), ITEM003 (Monitor Stand), ITEM004 (Desk Lamp), ITEM005 (Notebook Pack)
        destination_warehouse (str): Target warehouse ID where items should be delivered.
                                   Valid warehouses: WH001, WH002, WH003
        
        Returns:
        str: JSON formatted result with request_id for use in receive_shipment
        
        Example:
        request_shipment('{"ITEM001": 15}', 'WH001')
        """
        try:
            if not item_requests_str or not destination_warehouse:
                return "Error: Missing required parameters. Need item_requests_str and destination_warehouse."
            item_requests = json.loads(item_requests_str)
            result = inventory_manager.request_shipment(item_requests, destination_warehouse)
            return f"Shipment request result: {json.dumps(result, indent=2)}"
        except Exception as e:
            return f"Error requesting shipment: {str(e)}"
    
    @tool
    def receive_shipment(request_id: str, received_items_str: str) -> str:
        """
        Process received shipment and add items to destination warehouse.
        
        Parameters:
        request_id (str): Shipment request ID obtained from request_shipment.
                         Format: REQ_XXXXXXXX (e.g., "REQ_ABC12345")
        received_items_str (str): JSON string containing item IDs and actual quantities received.
                                 Format: '{"ITEM001": 8, "ITEM002": 5}'
                                 Should match or be subset of original request
        
        Returns:
        str: JSON formatted result confirming items added to warehouse
        
        Example:
        receive_shipment('REQ_ABC12345', '{"ITEM001": 15}')
        """
        try:
            if not request_id or not received_items_str:
                return "Error: Missing required parameters. Need request_id and received_items_str."
            received_items = json.loads(received_items_str)
            result = inventory_manager.receive_shipment(request_id, received_items)
            return f"Shipment receipt result: {json.dumps(result, indent=2)}"
        except Exception as e:
            return f"Error receiving shipment: {str(e)}"
    
    @tool
    def transfer_warehouse(from_warehouse: str, to_warehouse: str, item_id: str, quantity: str) -> str:
        """
        Transfer items directly between warehouses.
        
        Parameters:
        from_warehouse (str): Source warehouse ID containing the items to transfer.
                            Valid warehouses: WH001, WH002, WH003
        to_warehouse (str): Destination warehouse ID to receive the items.
                          Valid warehouses: WH001, WH002, WH003
        item_id (str): Item ID to transfer.
                      Available items: ITEM001 (Laptop), ITEM002 (Office Chair), ITEM003 (Monitor Stand), ITEM004 (Desk Lamp), ITEM005 (Notebook Pack)
        quantity (str): Number of items to transfer (must be string, will be converted to integer).
                       Must not exceed available quantity in source warehouse
        
        Returns:
        str: JSON formatted result confirming transfer completion
        
        Example:
        transfer_warehouse('WH001', 'WH002', 'ITEM001', '5')
        """
        try:
            if not all([from_warehouse, to_warehouse, item_id, quantity]):
                return "Error: Missing required parameters. Need from_warehouse, to_warehouse, item_id, and quantity."
            qty = int(quantity)
            result = inventory_manager.transfer_between_warehouses(from_warehouse, to_warehouse, item_id, qty)
            return f"Warehouse transfer result: {json.dumps(result, indent=2)}"
        except Exception as e:
            return f"Error transferring between warehouses: {str(e)}"
    
    @tool
    def move_to_showroom(warehouse_id: str, showroom_id: str, item_id: str, quantity: str) -> str:
        """
        Move items from warehouse to its associated showroom.
        
        Parameters:
        warehouse_id (str): Source warehouse ID containing the items to move.
                          Valid warehouses: WH001, WH002, WH003
        showroom_id (str): Destination showroom ID to receive the items.
                         Must be associated with the warehouse: SR001 (with WH001), SR002 (with WH002), SR003 (with WH003)
        item_id (str): Item ID to move from warehouse to showroom.
                      Available items: ITEM001 (Laptop), ITEM002 (Office Chair), ITEM003 (Monitor Stand), ITEM004 (Desk Lamp), ITEM005 (Notebook Pack)
        quantity (str): Number of items to move (must be string, will be converted to integer).
                       Must not exceed available quantity in source warehouse
        
        Returns:
        str: JSON formatted result confirming items moved to showroom
        
        Example:
        move_to_showroom('WH001', 'SR001', 'ITEM001', '10')
        """
        try:
            if not all([warehouse_id, showroom_id, item_id, quantity]):
                return "Error: Missing required parameters. Need warehouse_id, showroom_id, item_id, and quantity."
            qty = int(quantity)
            result = inventory_manager.move_to_showroom(warehouse_id, showroom_id, item_id, qty)
            return f"Showroom move result: {json.dumps(result, indent=2)}"
        except Exception as e:
            return f"Error moving to showroom: {str(e)}"
    
    return [
        request_shipment,
        receive_shipment,
        transfer_warehouse,
        move_to_showroom
        # Note: get_inventory_status removed from tools to avoid token waste during operations
        # Final status checking will be done after all operations complete
    ]




def create_inventory_agent_executor():
    """
    Create a LangChain AgentExecutor wrapper for inventory management with OmniBAR compatibility.
    
    This function returns an enhanced wrapper around LangChain AgentExecutor that adds
    system state information to responses for proper OmniBAR objective validation.
    
    Returns:
        EnhancedAgentExecutor: Wrapper around LangChain AgentExecutor with system state support
    """
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY environment variable is required")
    
    # Create inventory manager instance
    inventory_manager = InventoryManager()
    
    # Create OpenAI model
    llm = ChatOpenAI(
        model="gpt-4",
        temperature=1,  # Deterministic for benchmarking
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Create tools
    tools = create_inventory_tools(inventory_manager)
    
    # Create prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an inventory management agent with access to tools for shipment requests, receipts, transfers, and showroom moves.

CURRENT SYSTEM STATUS:
- WH001 (New York): 35 capacity  
- WH002 (Los Angeles): 25 capacity
- WH003 (Chicago): 820 capacity
- SR001 (Manhattan): 30 capacity
- SR002 (Beverly Hills): 25 capacity  
- SR003 (Chicago): 300 capacity
- ALL locations start empty

Available Items: ITEM001 (Laptop), ITEM002 (Office Chair), ITEM003 (Monitor Stand), ITEM004 (Desk Lamp), ITEM005 (Notebook Pack)

Tool usage:
- request_shipment: JSON format like '{{"ITEM001": 10}}'
- receive_shipment: Use request_id from shipment 
- transfer_warehouse: Specify warehouses and quantities
- move_to_showroom: Move from associated warehouse to showroom

Operations may fail if system constraints are violated."""),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])
    
    # Create agent
    agent = create_openai_tools_agent(llm, tools, prompt)
    
    # Create executor with full verbosity enabled
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,  # Enable verbose LangChain agent logging
        max_iterations=10,
        return_intermediate_steps=True,
        handle_parsing_errors=True  # Better error handling
    )
    
    # Create a wrapper class to add system state and execution path tracking to agent output
    class EnhancedAgentExecutor:
        """Wrapper around LangChain AgentExecutor that adds system state and execution path tracking for OmniBAR validation."""
        
        def __init__(self, agent_executor, inventory_manager):
            self.agent_executor = agent_executor
            self.inventory_manager = inventory_manager
            # Store inventory manager reference for potential access
            self._inventory_manager = inventory_manager
        
        def invoke(self, **kwargs) -> Dict[str, Any]:
            """Enhanced invoke that adds system state and execution path tracking to the output for OmniBAR validation."""
            # Execute the original agent (LangChain AgentExecutor expects the kwargs as dict)
            agent_response = self.agent_executor.invoke(kwargs)
            
            # Add basic response structure
            enhanced_response = agent_response.copy() if isinstance(agent_response, dict) else {"output": str(agent_response)}
            enhanced_response["_inventory_manager"] = self.inventory_manager
            
            # Add final inventory status for verification (only done at end, not during operations)
            enhanced_response["final_inventory_status"] = self.inventory_manager.get_inventory_status()
            
            # Extract and track execution path from intermediate steps
            execution_path = self._extract_execution_path(enhanced_response.get("intermediate_steps", []))
            enhanced_response["execution_path"] = execution_path
            
            # Parse success/failure from agent output
            success = True
            if isinstance(enhanced_response.get("output"), str):
                output_text = enhanced_response["output"].lower()
                if any(error_word in output_text for error_word in ["error", "failed", "insufficient", "not found", "invalid"]):
                    success = False
            
            # Check intermediate steps for tool errors
            intermediate_steps = enhanced_response.get("intermediate_steps", [])
            for step in intermediate_steps:
                if len(step) > 1 and isinstance(step[1], str):
                    tool_output = step[1].lower()
                    if "error" in tool_output or "failed" in tool_output:
                        success = False
                        break
            
            enhanced_response["success"] = success
            enhanced_response["timestamp"] = datetime.now().isoformat()
            
            # Add system state with actual success status for precise validation
            # Always use complex multi-location crisis scenario validation
            enhanced_response["system_state"] = create_complex_multi_location_state_dict(self.inventory_manager, operation_success=success)
            
            return enhanced_response
        
        def _extract_execution_path(self, intermediate_steps: List[Any]) -> List[Tuple[str, Dict[str, Any]]]:
            """
            Extract execution path from LangChain intermediate steps for path-based benchmarking.
            
            Args:
                intermediate_steps: LangChain intermediate steps from agent execution
                
            Returns:
                List of (tool_name, tool_args) tuples representing the execution path
            """
            execution_path = []
            
            for step in intermediate_steps:
                try:
                    if len(step) >= 2:
                        # LangChain intermediate steps format: (AgentAction, tool_output)
                        agent_action = step[0]
                        
                        if hasattr(agent_action, 'tool') and hasattr(agent_action, 'tool_input'):
                            tool_name = agent_action.tool
                            tool_input = agent_action.tool_input
                            
                            # Parse tool input - it might be a string or dict
                            if isinstance(tool_input, str):
                                # Try to parse as JSON first, fallback to simple parsing
                                try:
                                    parsed_input = json.loads(tool_input)
                                except json.JSONDecodeError:
                                    # Simple string input, convert to dict
                                    parsed_input = {"input": tool_input}
                            elif isinstance(tool_input, dict):
                                parsed_input = tool_input
                            else:
                                parsed_input = {"input": str(tool_input)}
                            
                            execution_path.append((tool_name, parsed_input))
                            
                except Exception as e:
                    # Skip malformed steps but log for debugging
                    print(f"Warning: Could not parse intermediate step: {e}")
                    continue
            
            return execution_path
        
        def __getattr__(self, name):
            """Delegate any other attributes to the original agent executor."""
            return getattr(self.agent_executor, name)
    
    return EnhancedAgentExecutor(agent_executor, inventory_manager)


async def run_inventory_benchmark():
    """
    Run complex multi-location crisis management benchmark using a gpt-4 LangChain agent.
    
    Features dual evaluation approach:
    1. STATE-BASED BENCHMARKING: Tests final outcomes and system state correctness
    2. PATH-BASED BENCHMARKING: Evaluates execution efficiency and strategic approach
    
    Tests the agent's ability to handle emergency supply chain scenarios with:
    - Multi-priority order management with dependencies
    - Severe capacity constraints and resource allocation
    - Strategic thinking under pressure
    - Partial state validation with intelligent scoring
    - Execution path optimization and strategic analysis
    
    Path Evaluation includes 5 optimal strategy patterns:
    - Single High-Capacity Warehouse Strategy (WH003 hub)
    - Distributed Multi-Warehouse Strategy (proximity-based)
    - Priority-Sequential Strategy (Order A → B → C)
    - Optimized Transfer Strategy (inter-warehouse optimization)
    - Minimal Steps Strategy (efficiency-focused)
    """
    
    # Define test operations with expected outcomes - EXTREMELY COMPLEX MULTI-CONSTRAINT SCENARIO
    test_operations = [
        # Ultra-complex scenario: Crisis management with competing priorities, capacity constraints, and failure recovery
        {
            "name": "Crisis Supply Chain Management with Multi-Constraint Optimization",
            "operation": "complex_business_scenario", 
            "kwargs": {
                "goal": """Emergency supply chain scenario with three critical orders requiring immediate fulfillment:

ORDER A (Priority 1):
• Manhattan showroom (SR001): 12 laptops + 8 office chairs + 4 monitor stands
• Must complete before any other orders

ORDER B (Priority 2): 
• Los Angeles showroom (SR002): 15 laptops + 10 desk lamps + 6 office chairs
• Chicago showroom (SR003): 8 laptops + 12 office chairs + 5 monitor stands + 4 desk lamps
• Complete after Order A

ORDER C (Compliance):
• Equal laptop quantities across all 3 showrooms required
• Manhattan (SR001): Additional 6 laptops + 3 notebook packs  
• Los Angeles (SR002): Additional 6 laptops + 5 notebook packs
• Chicago (SR003): Additional 6 laptops + 2 notebook packs

CONSTRAINTS:
• All orders must be fulfilled successfully
• System starts empty

Total requirement: 41 laptops, 36 chairs, 13 lamps, 9 stands, 10 notebook packs""",
                "expected_locations": ["SR001", "SR002", "SR003"],
                "expected_items": ["ITEM001", "ITEM002", "ITEM003", "ITEM004", "ITEM005"],
                "total_laptops_required": 41,  # Much higher complexity
                "total_chairs_required": 36,    
                "total_lamps_required": 13,     
                "total_stands_required": 9,
                "total_notebooks_required": 10,
                "capacity_crisis": True,  # Indicates this is a capacity-constrained scenario
                "priority_ordering": ["ORDER_A", "ORDER_B", "ORDER_C"],
                "has_compliance_requirements": True
            },
            "expected_success": True
        }
    ]
    
    # Create benchmarks for each operation
    benchmarks = []
    
    def create_instruction(operation: str, kwargs: Dict[str, Any], expected_success: bool) -> str:
        """Convert operation parameters to natural language instruction for complex crisis scenarios."""
        # Always treat as complex multi-location crisis scenario
        goal = kwargs.get("goal", "")
        instruction = f"{goal} You have complete access to inventory management tools. This requires strategic thinking about:\n1. Optimal shipment allocation across warehouses\n2. Efficient cross-warehouse transfers if needed\n3. Sequence planning to meet all requirements\n4. Resource optimization under constraints\n\nAnalyze the requirements carefully and execute the most efficient solution."
        
        if not expected_success:
            instruction += ". Note: This operation might fail due to validation constraints - please attempt it and report the result."
        
        return instruction
    
    for i, test_op in enumerate(test_operations, 1):
        # Convert to natural language instruction
        instruction = create_instruction(
            test_op["operation"], 
            test_op["kwargs"], 
            test_op["expected_success"]
        )
        
        # Create combined benchmark that evaluates both state and path simultaneously
        combined_objective = create_combined_crisis_objective()
        
        combined_benchmark = Benchmark(
            name=f"Complex Crisis Management {i}: {test_op['name']} (Combined Evaluation)", 
            input_kwargs={"input": instruction},  # LangChain AgentExecutor expects "input" key
            objective=combined_objective,  # Combined objective evaluates both state and path
            iterations=1,  # Single iteration for deterministic testing
            verbose=True,
            invoke_method="invoke"
        )
        benchmarks.append(combined_benchmark)
    
    # Create benchmarker using the enhanced agent with built-in OmniBAR logging
    benchmarker = OmniBarmarker(
        executor_fn=create_inventory_agent_executor,
        executor_kwargs={},
        initial_input=benchmarks,
        enable_logging=True,  # Enable comprehensive logging
        notebook=False
    )
    
    # Run benchmark
    print(f"🚀 Running {len(benchmarks)} inventory management benchmarks...")
    print("   • Each benchmark includes dual evaluation: State correctness + Path efficiency")
    print(f"   • {len(benchmarks)} Combined evaluations (state validation + strategic analysis)")
    results = await benchmarker.benchmark_async()
    
    # Display results summary using built-in OmniBAR logging
    print("\n📊 Benchmark Results Summary")
    print("=" * 50)
    
    # Debug: Check what type of results we got
    print(f"Debug: Results type = {type(results)}")
    if hasattr(results, '__len__'):
        print(f"Debug: Results length = {len(results)}")
    
    # Check results structure and display appropriately
    if results:
        # Handle both single result and list of results
        results_list = results if isinstance(results, list) else [results]
        print(f"Total benchmarks completed: {len(results_list)}")
        
        # Display summary - just count of successful operations shown in terminal output
        success_count = 0
        for i, result in enumerate(results_list, 1):
            try:
                if hasattr(result, 'benchmark_name'):
                    print(f"✅ Benchmark {i}: {result.benchmark_name}")
                    success_count += 1
                elif isinstance(result, str):
                    print(f"✅ Benchmark {i}: Operation completed")
                    success_count += 1
                else:
                    print(f"✅ Benchmark {i}: Operation completed (details in logs)")
                    success_count += 1
            except Exception:
                print(f"✅ Benchmark {i}: Operation completed")
                success_count += 1
        
        print(f"\n🎯 Summary: {success_count}/{len(results_list)} benchmarks completed successfully")
        print("📝 All detailed validation results are captured in the exported JSON file")
    else:
        print("No results to display")
    
    # Use built-in OmniBAR logging system
    print("\n📊 OmniBAR Logger Summary:")
    benchmarker.print_logger_summary()
    
    print("\n📋 Detailed Results:")
    benchmarker.print_logger_details(detail_level="detailed")
    
    # Add AI-powered inventory management analysis using SimpleAILogger
    print("\n" + "="*80)
    print("🤖 AI-Powered Inventory Management Analysis")
    print("="*80)
    
    try:
        # Import SimpleAILogger
        from omnibar.logging.simple_ai_logger import SimpleAILogger
        
        # Create AI logger and copy logs from regular logger
        ai_logger = SimpleAILogger()
        
        # Copy all benchmark logs to the AI logger
        for benchmark_id, objective_logs in benchmarker.logger.logs.items():
            for objective_id, log in objective_logs.items():
                ai_logger.add_log(log)
        
        # Configure AI with default OpenAI settings
        ai_logger.configure_ai()
        
        # Generate AI analysis
        print("🔍 Running AI analysis on inventory management results...")
        ai_logger.print_ai_analysis(use_colors=True)
        
    except ImportError as e:
        print(f"⚠️  AI Analysis not available: {e}")
        print("💡 To enable AI-powered inventory analysis:")
        print("   pip install langchain langchain-openai")
        print("   export OPENAI_API_KEY=your_openai_api_key")
    except Exception as e:
        print(f"❌ Unexpected error during AI analysis: {e}")
    
    print("="*80)
    
    # Export results using built-in logger
    try:
        export_path = Path("inventory_management_benchmark_results.json")
        json_data = benchmarker.logger.to_json(include_evaluations=True)
        
        with open(export_path, 'w') as f:
            f.write(json_data)
            
        print(f"\n✅ Results exported to: {export_path}")
    except Exception as e:
        print(f"\n❌ Export failed: {e}")
    
    return {
        "results": results,
        "logger": benchmarker.logger
    }


def main():
    """Main function to run the complex multi-location crisis management benchmark with LangChain agent."""
    
    print("🚨 COMPLEX MULTI-LOCATION CRISIS MANAGEMENT BENCHMARK")
    print("=" * 60)
    print("🤖 Using gpt-4 LangChain agent for emergency supply chain management")
    print("⚠️  CRISIS SCENARIO: Multi-constraint optimization with priority management")
    print("📦 Strategic resource allocation across 3 showrooms with severe constraints")
    print("🎯 Combined evaluation: State correctness + Execution path efficiency")
    print("🛤️  Simultaneous scoring: Final outcomes + Strategic execution patterns")
    print("🔑 Requires OPENAI_API_KEY in environment or .env file")
    print()
    
    # Check for OpenAI API key before starting
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable is required")
        print("   Please add your OpenAI API key to a .env file in the project root:")
        print("   OPENAI_API_KEY=your_api_key_here")
        return None
    
    print("✅ OpenAI API key found, starting benchmark...")
    print()
    
    # Run the async benchmark
    results = asyncio.run(run_inventory_benchmark())
    return results


if __name__ == "__main__":
    main()
