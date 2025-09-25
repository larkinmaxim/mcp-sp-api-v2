"""
Ocean Visibility transport order generator.
"""

from typing import Dict, Any, List
from .base_generator import BaseGenerator


class OceanVisibilityGenerator(BaseGenerator):
    """Generator for Ocean Visibility transport orders."""
    
    def __init__(self, data_path=None):
        """Initialize Ocean Visibility generator."""
        super().__init__(data_path)
        self.transport_type = "ocean_visibility"
        self.required_fields = ["number"]
        self.supports_pricing = False
        self.supports_order_items = False
        self.supports_vehicle = False
        
        # Fixed values for ocean visibility
        self.fixed_values = {
            "scheduling_unit": "Ocean Visibility",
            "carrier_creditor_number": "Ocean",
            "status": "NTO"
        }
        
        # Required ocean parameters
        self.required_ocean_parameters = [
            "ocean.scac.no",
            "ocean.bl.no", 
            "ocean.container.no"
        ]
    
    def generate_xml(self, **kwargs) -> Dict[str, Any]:
        """Generate XML for Ocean Visibility transport order."""
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
            
            # Collect ocean-specific parameters
            collected_params["ocean_parameters"] = self.parameter_collector.collect_ocean_parameters(user_input)
            
            # Build basic XML structure
            xml_content = self.build_basic_structure(collected_params)
            
            # Add ocean visibility specific elements
            xml_content = self._add_ocean_visibility_elements(xml_content, collected_params)
            
            # Finalize XML
            final_xml = self.finalize_xml(xml_content)
            
            return {
                "success": True,
                "xml_content": final_xml,
                "transport_type": self.transport_type,
                "order_number": collected_params["transport_info"]["number"],
                "metadata": {
                    "scac_code": collected_params["ocean_parameters"].get("ocean.scac.no"),
                    "bl_number": collected_params["ocean_parameters"].get("ocean.bl.no"),
                    "container_number": collected_params["ocean_parameters"].get("ocean.container.no"),
                    "booking_number": collected_params["ocean_parameters"].get("ocean.booking.no", ""),
                    "stop_count": len(collected_params["stops"])
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error_type": "generation_error",
                "error_message": str(e)
            }
    
    def collect_all_parameters(self, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """Override to apply fixed values for ocean visibility."""
        # Apply fixed values
        modified_input = user_input.copy()
        modified_input.update(self.fixed_values)
        
        # Set order number same as transport number if not provided
        if "order_number" not in modified_input:
            modified_input["order_number"] = modified_input.get("number", "")
        
        # Ensure we have exactly 2 stops for ocean visibility
        if "stops" not in modified_input or len(modified_input["stops"]) != 2:
            if "departure_location" in modified_input and "arrival_location" in modified_input:
                modified_input["stops"] = self._build_ocean_stops(modified_input)
            
        # Set fixed stop IDs
        modified_input["loading_stop_ids"] = ["Departure"]
        modified_input["unloading_stop_ids"] = ["Arrival"]
        
        return super().collect_all_parameters(modified_input)
    
    def _build_ocean_stops(self, user_input: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build the two required stops for ocean visibility."""
        departure_location = user_input.get("departure_location", {})
        arrival_location = user_input.get("arrival_location", {})
        
        departure_date = user_input.get("departure_date", {})
        arrival_date = user_input.get("arrival_date", {})
        
        stops = [
            {
                "id": "Departure",
                "index": 0,
                "location": departure_location,
                "date_time_period": departure_date
            },
            {
                "id": "Arrival",
                "index": 1,
                "location": arrival_location,
                "date_time_period": arrival_date
            }
        ]
        
        return stops
    
    def _perform_specific_validation(self, user_input: Dict[str, Any], validation_result: Dict[str, Any]) -> None:
        """Perform Ocean Visibility specific validation."""
        # Check for exactly 2 stops OR location data
        stops = user_input.get("stops", [])
        has_location_data = "departure_location" in user_input and "arrival_location" in user_input
        
        if len(stops) == 0 and not has_location_data:
            validation_result["errors"].append(
                "Ocean visibility requires either 2 stops OR departure_location and arrival_location data"
            )
            validation_result["is_valid"] = False
        elif len(stops) > 0 and len(stops) != 2:
            validation_result["errors"].append("Ocean visibility requires exactly 2 stops (Departure and Arrival)")
            validation_result["is_valid"] = False
        
        # Validate required ocean parameters
        for param_name in self.required_ocean_parameters:
            if param_name not in user_input:
                validation_result["errors"].append(f"Required ocean parameter '{param_name}' is missing")
                validation_result["is_valid"] = False
        
        # Validate SCAC code format
        scac_code = user_input.get("ocean.scac.no", "")
        if scac_code and len(scac_code) != 4:
            validation_result["errors"].append("SCAC code must be exactly 4 characters")
            validation_result["is_valid"] = False
        elif scac_code and not scac_code.replace("0", "A").replace("1", "A").replace("2", "A").replace("3", "A").replace("4", "A").replace("5", "A").replace("6", "A").replace("7", "A").replace("8", "A").replace("9", "A").isalpha():
            # Check if it's alphanumeric
            import re
            if not re.match(r'^[A-Z0-9]{4}$', scac_code):
                validation_result["errors"].append("SCAC code must contain only uppercase letters and numbers")
                validation_result["is_valid"] = False
        
        # Check for forbidden elements
        forbidden_elements = ["vehicle", "prices", "order_items"]
        for element in forbidden_elements:
            if element in user_input:
                validation_result["warnings"].append(
                    f"'{element}' is not used in ocean visibility transport orders"
                )
        
        # Check for non-ocean parameters
        parameters = user_input.get("parameters", [])
        for param in parameters:
            qualifier = param.get("qualifier", "")
            if not qualifier.startswith("ocean.") and qualifier != "visibility.ocean.product":
                validation_result["warnings"].append(
                    f"Parameter '{qualifier}' is not typically used in ocean visibility orders"
                )
    
    def _add_ocean_visibility_elements(self, xml_content: str, collected_params: Dict[str, Any]) -> str:
        """Add Ocean Visibility specific elements to XML."""
        ocean_params = collected_params.get("ocean_parameters", {})
        
        replacements = {}
        
        # Process stops for ocean visibility template
        stops = collected_params.get("stops", [])
        if len(stops) >= 2:
            departure_stop = stops[0]
            arrival_stop = stops[1]
            
            # Departure location replacements
            dept_loc = departure_stop["location"]
            replacements.update({
                "departure_company_name": dept_loc.get("company_name", ""),
                "departure_street": dept_loc.get("street", ""),
                "departure_zip": dept_loc.get("zip", ""),
                "departure_city": dept_loc.get("city", ""),
                "departure_country": dept_loc.get("country", "")
            })
            
            # Departure date replacements
            dept_period = departure_stop.get("date_time_period", {})
            replacements.update({
                "departure_start_date": dept_period.get("start", ""),
                "departure_end_date": dept_period.get("end", "")
            })
            
            # Arrival location replacements
            arr_loc = arrival_stop["location"]
            replacements.update({
                "arrival_company_name": arr_loc.get("company_name", ""),
                "arrival_street": arr_loc.get("street", ""),
                "arrival_zip": arr_loc.get("zip", ""),
                "arrival_city": arr_loc.get("city", ""),
                "arrival_country": arr_loc.get("country", "")
            })
            
            # Arrival date replacements
            arr_period = arrival_stop.get("date_time_period", {})
            replacements.update({
                "arrival_start_date": arr_period.get("start", ""),
                "arrival_end_date": arr_period.get("end", "")
            })
        
        # Ocean parameter replacements
        replacements.update({
            "scac_code": ocean_params.get("ocean.scac.no", ""),
            "bl_number": ocean_params.get("ocean.bl.no", ""),
            "container_number": ocean_params.get("ocean.container.no", ""),
            "booking_number": ocean_params.get("ocean.booking.no", "")
        })
        
        # Apply all replacements
        for placeholder, value in replacements.items():
            xml_content = xml_content.replace(f"{{{placeholder}}}", str(value))
        
        return xml_content
    
    def get_example_input(self) -> Dict[str, Any]:
        """Get example input for Ocean Visibility."""
        return {
            "number": "4500831479-20",
            "ocean.scac.no": "MAEU",
            "ocean.bl.no": "MAEU258327258",
            "ocean.container.no": "MMAU1291440",
            "ocean.booking.no": "",
            "departure_location": {
                "company_name": "Camimex Joint Stock Company",
                "street": "Cao Thang Street",
                "zip": "",
                "city": "Ca Mau City",
                "country": "VN"
            },
            "arrival_location": {
                "company_name": "Factory Bremerhaven DE",
                "street": "Am Lunedeich",
                "zip": "27572",
                "city": "Bremerhaven",
                "country": "DE"
            },
            "departure_date": {
                "start": "2025-07-13T00:00:00+02:00",
                "end": "2025-07-13T00:00:00+02:00"
            },
            "arrival_date": {
                "start": "2025-10-11T00:00:00+02:00",
                "end": "2025-10-11T00:00:00+02:00"
            }
        }
    
    def get_required_ocean_parameters(self) -> List[str]:
        """Get list of required ocean parameters."""
        return self.required_ocean_parameters.copy()
    
    def get_fixed_values(self) -> Dict[str, str]:
        """Get fixed values for ocean visibility."""
        return self.fixed_values.copy()
