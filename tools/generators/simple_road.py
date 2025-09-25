"""
Simple Road Freight transport order generator.
"""

from typing import Dict, Any, List
from .base_generator import BaseGenerator


class SimpleRoadGenerator(BaseGenerator):
    """Generator for Simple Road Freight transport orders."""
    
    def __init__(self, data_path=None):
        """Initialize Simple Road generator."""
        super().__init__(data_path)
        self.transport_type = "simple_road"
        self.required_fields = ["number", "status", "scheduling_unit"]
        self.supports_pricing = True
        self.supports_order_items = False
        self.supports_vehicle = True
    
    def generate_xml(self, **kwargs) -> Dict[str, Any]:
        """Generate XML for Simple Road Freight transport order."""
        user_input = kwargs
        
        # Validate input first
        validation = self.validate_input(user_input)
        if not validation["is_valid"]:
            return {
                "success": False,
                "error_type": "validation_error",
                "errors": validation["errors"],
                "missing_required": validation["missing_required"],
                "suggested_optional": validation["suggested_optional"]
            }
        
        try:
            # Collect all parameters
            collected_params = self.collect_all_parameters(user_input)
            
            # Build basic XML structure (will have placeholders)
            xml_content = self.build_basic_structure(collected_params)
            
            # Add simple road specific elements (replaces remaining placeholders)
            xml_content = self._add_simple_road_elements(xml_content, collected_params)
            
            # Finalize XML
            final_xml = self.finalize_xml(xml_content)
            
            return {
                "success": True,
                "xml_content": final_xml,
                "transport_type": self.transport_type,
                "order_number": collected_params["transport_info"]["number"],
                "metadata": {
                    "has_pricing": self._has_pricing(collected_params),
                    "has_vehicle": self._has_vehicle(collected_params),
                    "stop_count": len(collected_params["stops"]),
                    "parameter_count": len(collected_params["custom_parameters"])
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error_type": "generation_error",
                "error_message": str(e)
            }
    
    def _perform_specific_validation(self, user_input: Dict[str, Any], validation_result: Dict[str, Any]) -> None:
        """Perform Simple Road specific validation."""
        # Validate stops
        stops = user_input.get("stops", [])
        if len(stops) < 2:
            validation_result["errors"].append("Simple road freight requires at least 2 stops (loading and unloading)")
            validation_result["is_valid"] = False
        elif len(stops) > 10:
            validation_result["warnings"].append("More than 10 stops is unusual for simple road freight")
        
        # Check for forbidden parameters (ocean-specific)
        forbidden_ocean_params = ["ocean.scac.no", "ocean.bl.no", "ocean.container.no", "visibility.ocean.product"]
        parameters = user_input.get("parameters", [])
        
        for param in parameters:
            if param.get("qualifier") in forbidden_ocean_params:
                validation_result["errors"].append(f"Ocean parameter '{param['qualifier']}' not allowed in simple road freight")
                validation_result["is_valid"] = False
        
        # Validate pricing if provided
        if "price_reference" in user_input and user_input["price_reference"] <= 0:
            validation_result["errors"].append("Price reference must be positive")
            validation_result["is_valid"] = False
        
        # Validate weight values
        if "weight_value" in user_input and user_input["weight_value"] < 0:
            validation_result["errors"].append("Weight value cannot be negative")
            validation_result["is_valid"] = False
    
    def _add_simple_road_elements(self, xml_content: str, collected_params: Dict[str, Any]) -> str:
        """Add Simple Road specific elements to XML."""
        transport_info = collected_params["transport_info"]
        order_details = collected_params["order_details"]
        
        replacements = {}
        
        # Add vehicle element if provided
        if "vehicle" in transport_info:
            replacements["vehicle_element"] = f"<vehicle>{transport_info['vehicle']}</vehicle>"
        else:
            replacements["vehicle_element"] = ""
        
        # Add pricing element if provided
        if self._has_pricing(collected_params):
            pricing_xml = self._build_pricing_xml(transport_info)
            replacements["prices_element"] = pricing_xml
        else:
            replacements["prices_element"] = ""
        
        # Add weight element if provided
        if "weight_value" in order_details:
            replacements["weight_element"] = f'''
                <weight unit="kg">
                    <value>{order_details["weight_value"]}</value>
                </weight>'''
        else:
            replacements["weight_element"] = ""
        
        # Add loading meter element (can be empty)
        replacements["loading_meter_element"] = '<loading_meter unit="m"></loading_meter>'
        
        # Add distance element if provided
        if "distance_value" in order_details:
            replacements["distance_element"] = f'''
                <distance unit="km">
                    <value>{order_details["distance_value"]}</value>
                </distance>'''
        else:
            replacements["distance_element"] = ""
        
        # Add comment element if provided
        if "comment" in order_details:
            # Escape HTML entities in comments
            comment = order_details["comment"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            replacements["comment_element"] = f"<comment>{comment}</comment>"
        else:
            replacements["comment_element"] = ""
        
        # Add parameters if any
        if collected_params["custom_parameters"]:
            replacements["parameters_element"] = self._build_parameters_xml(collected_params["custom_parameters"])
        else:
            replacements["parameters_element"] = ""
        
        # Apply all replacements
        for placeholder, value in replacements.items():
            xml_content = xml_content.replace(f"{{{placeholder}}}", value)
        
        return xml_content
    
    def _has_pricing(self, collected_params: Dict[str, Any]) -> bool:
        """Check if pricing information is available."""
        transport_info = collected_params["transport_info"]
        return "price_reference" in transport_info
    
    def _has_vehicle(self, collected_params: Dict[str, Any]) -> bool:
        """Check if vehicle information is available."""
        transport_info = collected_params["transport_info"]
        return "vehicle" in transport_info
    
    def _build_pricing_xml(self, transport_info: Dict[str, Any]) -> str:
        """Build pricing XML section."""
        reference = transport_info.get("price_reference", 0)
        currency = transport_info.get("price_currency", "EUR")
        mode = transport_info.get("price_mode", "DEFAULT")
        
        pricing_xml = f"<prices>\n            <reference>{reference}</reference>\n            <currency>{currency}</currency>\n            <mode>{mode}</mode>\n        </prices>"
        
        return pricing_xml
    
    def get_example_input(self) -> Dict[str, Any]:
        """Get example input for Simple Road Freight."""
        return {
            "number": "1404338",
            "status": "N",
            "scheduling_unit": "Wörth",
            "vehicle": "MEGA:Stehend",
            "price_reference": 845.0,
            "price_currency": "EUR",
            "weight_value": 23106,
            "distance_value": 1153,
            "comment": "rolls in mm : 2800",
            "loading_stop_ids": ["1"],
            "unloading_stop_ids": ["2"],
            "stops": [
                {
                    "id": "1",
                    "index": 0,
                    "location": {
                        "company_name": "Papierfabrik Palm (PM 6)",
                        "street": "Am Oberwald 2",
                        "zip": "76744",
                        "city": "Wörth",
                        "country": "DE"
                    },
                    "date_time_period": {
                        "start": "2025-09-25T00:00:00+02:00",
                        "end": "2025-09-25T23:59:00+02:00",
                        "timezone": "Europe/Berlin"
                    }
                },
                {
                    "id": "2",
                    "index": 1,
                    "location": {
                        "company_name": "WOK Sp. z o.o.",
                        "street": "Podgórna 104",
                        "zip": "87300",
                        "city": "Brodnica",
                        "country": "PL",
                        "comment": "ZF: 12:00"
                    },
                    "date_time_period": {
                        "start": "2025-09-29T00:00:00+02:00",
                        "end": "2025-09-29T00:00:00+02:00",
                        "timezone": "Europe/Berlin"
                    }
                }
            ],
            "parameters": [
                {
                    "qualifier": "custom.important.info",
                    "value": "<span style=\"color: #ff0000; font-size: 10pt;\"></span>"
                }
            ]
        }
