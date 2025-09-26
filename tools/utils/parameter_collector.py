"""
Smart parameter collection utility for context-aware user input collection.
"""

from typing import Dict, Any, List, Optional, Union
import re
from datetime import datetime
from .business_rules_processor import BusinessRulesProcessor


class ParameterCollector:
    """Collects and processes user input parameters for transport orders."""
    
    def __init__(self, template_loader):
        """Initialize parameter collector with template loader."""
        self.template_loader = template_loader
        self.business_rules_processor = BusinessRulesProcessor(template_loader)
    
    def collect_basic_transport_info(self, transport_type: str, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """Collect basic transport order information."""
        transport_params = self.template_loader.get_transport_parameters(transport_type)
        fixed_params = self.template_loader.get_fixed_parameters(transport_type)
        
        result = {}
        
        # Apply fixed values first
        if "fixed_values" in fixed_params:
            result.update(fixed_params["fixed_values"])
        
        # Collect required fields
        if "required_fields" in transport_params:
            for field in transport_params["required_fields"]:
                field_name = field["name"]
                
                if field_name in user_input:
                    result[field_name] = user_input[field_name]
                elif "default" in field:
                    result[field_name] = field["default"]
                else:
                    # Field is required but not provided
                    raise ValueError(f"Required field '{field_name}' not provided for {transport_type}")
        
        # Collect optional fields if provided
        if "optional_fields" in transport_params:
            for field in transport_params["optional_fields"]:
                field_name = field["name"]
                
                if field_name in user_input:
                    result[field_name] = user_input[field_name]
                elif "default" in field:
                    result[field_name] = field["default"]
        
        # Apply business rules
        result = self.business_rules_processor.apply_business_rules(transport_type, user_input, result)
        
        return result
    
    def collect_order_details(self, transport_type: str, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """Collect order details information."""
        order_params = self.template_loader.get_order_parameters(transport_type)
        result = {}
        
        # Apply fixed values for orders
        if "fixed_values" in order_params:
            result.update(order_params["fixed_values"])
        
        # Collect required order fields
        if "required_fields" in order_params:
            for field in order_params["required_fields"]:
                field_name = field["name"]
                
                if field_name in user_input:
                    result[field_name] = user_input[field_name]
                else:
                    raise ValueError(f"Required order field '{field_name}' not provided")
        
        # Collect optional order fields
        if "optional_fields" in order_params:
            for field in order_params["optional_fields"]:
                field_name = field["name"]
                
                if field_name in user_input:
                    result[field_name] = user_input[field_name]
        
        return result
    
    def collect_stops(self, user_input: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Collect stop information."""
        stops = user_input.get("stops", [])
        processed_stops = []
        
        for i, stop_data in enumerate(stops):
            processed_stop = {
                "id": stop_data.get("id", f"stop_{i+1}"),
                "index": stop_data.get("index", i),
                "location": self._process_location(stop_data.get("location", {})),
                "date_time_period": self._process_date_time_period(stop_data.get("date_time_period", {}))
            }
            processed_stops.append(processed_stop)
        
        return processed_stops
    
    def _process_location(self, location_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and validate location data."""
        required_fields = ["company_name", "city", "country"]
        processed = {}
        
        for field in required_fields:
            if field not in location_data or not location_data[field]:
                raise ValueError(f"Required location field '{field}' is missing")
            processed[field] = location_data[field]
        
        # Add optional fields
        optional_fields = ["street", "zip", "state", "comment"]
        for field in optional_fields:
            if field in location_data and location_data[field]:
                processed[field] = location_data[field]
        
        # Validate country code format
        if not re.match(r'^[A-Z]{2}$', processed["country"]):
            raise ValueError(f"Country code must be 2 uppercase letters, got: {processed['country']}")
        
        return processed
    
    def _process_date_time_period(self, period_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and validate date time period data."""
        required_fields = ["start", "end"]
        processed = {}
        
        for field in required_fields:
            if field not in period_data:
                raise ValueError(f"Required date field '{field}' is missing")
            
            # Validate ISO datetime format
            datetime_str = period_data[field]
            if not self._validate_iso_datetime(datetime_str):
                raise ValueError(f"Invalid datetime format for '{field}': {datetime_str}")
            
            processed[field] = datetime_str
        
        # Add timezone if provided
        if "timezone" in period_data:
            processed["timezone"] = period_data["timezone"]
        
        return processed
    
    def _validate_iso_datetime(self, datetime_str: str) -> bool:
        """Validate ISO 8601 datetime format."""
        iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}([+-]\d{2}:\d{2}|Z)$'
        return bool(re.match(iso_pattern, datetime_str))
    
    def collect_ocean_parameters(self, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """Collect ocean-specific parameters."""
        ocean_params = self.template_loader.get_transport_parameters("ocean_visibility")
        result = {}
        
        if "ocean_parameters" not in ocean_params:
            return result
        
        for param in ocean_params["ocean_parameters"]:
            param_name = param["name"]
            
            if param.get("required", False) and param_name not in user_input:
                raise ValueError(f"Required ocean parameter '{param_name}' not provided")
            
            if param_name in user_input:
                value = user_input[param_name]
                
                # Validate SCAC code format
                if param_name == "ocean.scac.no":
                    if not re.match(r'^[A-Z0-9]{4}$', value):
                        raise ValueError(f"SCAC code must be 4 alphanumeric characters: {value}")
                
                result[param_name] = value
            elif param_name == "ocean.booking.no":
                # Booking number can be empty
                result[param_name] = ""
        
        return result
    
    def collect_order_items(self, user_input: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Collect order items for complex road freight."""
        items = user_input.get("order_items", [])
        processed_items = []
        
        for item_data in items:
            processed_item = {
                "number": item_data.get("number", ""),
                "short_description": item_data.get("short_description", ""),
                "material_number": item_data.get("material_number", ""),
                "quantities": self._process_quantities(item_data.get("quantities", [])),
                "parameters": self._process_item_parameters(item_data.get("parameters", []))
            }
            
            # Validate required fields
            required_fields = ["number", "short_description", "material_number"]
            for field in required_fields:
                if not processed_item[field]:
                    raise ValueError(f"Required item field '{field}' is missing")
            
            processed_items.append(processed_item)
        
        return processed_items
    
    def _process_quantities(self, quantities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process quantity information."""
        processed = []
        
        for qty in quantities:
            processed_qty = {
                "qualifier": qty.get("qualifier", ""),
                "value": qty.get("value", 0.0),
                "unit": qty.get("unit", "")
            }
            processed.append(processed_qty)
        
        return processed
    
    def _process_item_parameters(self, parameters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process item-level parameters."""
        processed = []
        
        for param in parameters:
            processed_param = {
                "qualifier": param.get("qualifier", ""),
                "value": param.get("value", ""),
            }
            
            # Add optional attributes
            if "shipper_visibility" in param:
                processed_param["shipper_visibility"] = param["shipper_visibility"]
            
            if "export_to_carrier" in param:
                processed_param["export_to_carrier"] = param["export_to_carrier"]
            
            processed.append(processed_param)
        
        return processed
    
    def collect_custom_parameters(self, user_input: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Collect custom parameters."""
        parameters = user_input.get("parameters", [])
        processed = []
        
        for param in parameters:
            if not param.get("qualifier"):
                continue
            
            processed_param = {
                "qualifier": param["qualifier"],
                "value": param.get("value", "")
            }
            
            # Add optional attributes
            if "shipper_visibility" in param:
                processed_param["shipper_visibility"] = param["shipper_visibility"]
            
            if "export_to_carrier" in param:
                processed_param["export_to_carrier"] = param["export_to_carrier"]
            
            processed.append(processed_param)
        
        return processed
    
    def generate_missing_field_prompts(self, transport_type: str, provided_data: Dict[str, Any]) -> List[str]:
        """Generate prompts for missing required fields."""
        prompts = []
        
        # Check transport-level required fields
        transport_params = self.template_loader.get_transport_parameters(transport_type)
        if "required_fields" in transport_params:
            for field in transport_params["required_fields"]:
                field_name = field["name"]
                if field_name not in provided_data:
                    prompt = f"Please provide {field['description']} ({field_name})"
                    if "example" in field:
                        prompt += f" - Example: {field['example']}"
                    prompts.append(prompt)
        
        # Check order-level required fields
        order_params = self.template_loader.get_order_parameters(transport_type)
        if "required_fields" in order_params:
            for field in order_params["required_fields"]:
                field_name = field["name"]
                if field_name not in provided_data:
                    prompt = f"Please provide {field['description']} ({field_name})"
                    if "example" in field:
                        prompt += f" - Example: {field['example']}"
                    prompts.append(prompt)
        
        # Check ocean-specific parameters
        if transport_type == "ocean_visibility":
            ocean_params = self.template_loader.get_transport_parameters("ocean_visibility")
            if "ocean_parameters" in ocean_params:
                for param in ocean_params["ocean_parameters"]:
                    param_name = param["name"]
                    if param.get("required", False) and param_name not in provided_data:
                        prompt = f"Please provide {param['description']} ({param_name})"
                        if "example" in param:
                            prompt += f" - Example: {param['example']}"
                        prompts.append(prompt)
        
        return prompts
    
    def suggest_optional_fields(self, transport_type: str) -> List[str]:
        """Generate suggestions for optional fields that might be useful."""
        suggestions = []
        
        transport_params = self.template_loader.get_transport_parameters(transport_type)
        if "optional_fields" in transport_params:
            for field in transport_params["optional_fields"]:
                suggestion = f"Optional: {field['description']} ({field['name']})"
                if "example" in field:
                    suggestion += f" - Example: {field['example']}"
                suggestions.append(suggestion)
        
        return suggestions
