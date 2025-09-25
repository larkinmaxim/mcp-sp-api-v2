"""
Structural validator for XML structure validation.
"""

import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional
import re


class StructuralValidator:
    """Validates XML structure and basic field requirements."""
    
    def __init__(self, template_loader):
        """Initialize structural validator."""
        self.template_loader = template_loader
        self.field_rules = template_loader.load_validation_rules("field")
        self.namespace = "http://xch.transporeon.com/soap/"
        self.ns = "{" + self.namespace + "}"
    
    def validate_xml_structure(self, xml_content: str) -> Dict[str, Any]:
        """Validate XML structure and well-formedness."""
        result = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        try:
            # Parse XML to check well-formedness
            root = ET.fromstring(xml_content)
            
            # Validate namespace
            if not self._validate_namespace(root):
                result["errors"].append("Missing or incorrect namespace")
                result["is_valid"] = False
            
            # Validate root element
            expected_root_tag = f"{self.ns}transport_orders"
            if root.tag != expected_root_tag and root.tag != "transport_orders":
                result["errors"].append("Root element must be 'transport_orders'")
                result["is_valid"] = False
            
            # Find transport_order element
            transport_order = root.find(f".//{self.ns}transport_order")
            if transport_order is None:
                # Try without namespace (for backwards compatibility)
                transport_order = root.find(".//transport_order")
                if transport_order is None:
                    result["errors"].append("No transport_order element found")
                    result["is_valid"] = False
                    return result
            
            # Validate required elements
            self._validate_required_elements(transport_order, result)
            
            # Validate element structure
            self._validate_element_structure(transport_order, result)
            
        except ET.ParseError as e:
            result["is_valid"] = False
            result["errors"].append(f"XML parsing error: {str(e)}")
        
        return result
    
    def _validate_namespace(self, root: ET.Element) -> bool:
        """Validate XML namespace."""
        expected_namespace = "http://xch.transporeon.com/soap/"
        # Check if the tag includes the namespace (this is how ElementTree stores namespace info)
        has_namespace_in_tag = root.tag.startswith("{" + expected_namespace + "}")
        # Or if it's a plain tag (for backwards compatibility)
        is_plain_tag = root.tag == "transport_orders"
        return has_namespace_in_tag or is_plain_tag
    
    def _validate_required_elements(self, transport_order: ET.Element, result: Dict[str, Any]) -> None:
        """Validate presence of required elements."""
        required_elements = ["number", "status", "scheduling_unit", "orders", "stops"]
        
        for element_name in required_elements:
            # Try with namespace first, then without
            element = transport_order.find(f"{self.ns}{element_name}")
            if element is None:
                element = transport_order.find(element_name)
                
            if element is None:
                result["errors"].append(f"Required element '{element_name}' is missing")
                result["is_valid"] = False
            elif element_name in ["number", "status", "scheduling_unit"] and not element.text:
                result["errors"].append(f"Required element '{element_name}' is empty")
                result["is_valid"] = False
    
    def _validate_element_structure(self, transport_order: ET.Element, result: Dict[str, Any]) -> None:
        """Validate internal structure of elements."""
        # Validate orders structure
        orders = transport_order.find(f"{self.ns}orders") or transport_order.find("orders")
        if orders is not None:
            order_details = orders.find(f"{self.ns}order_details") or orders.find("order_details")
            if order_details is None:
                result["errors"].append("orders element must contain order_details")
                result["is_valid"] = False
            else:
                self._validate_order_details(order_details, result)
        
        # Validate stops structure
        stops = transport_order.find(f"{self.ns}stops") or transport_order.find("stops")
        if stops is not None:
            stop_elements = (stops.findall(f"{self.ns}stop") or 
                           stops.findall("stop"))
            if len(stop_elements) == 0:
                result["errors"].append("stops element must contain at least one stop")
                result["is_valid"] = False
            else:
                self._validate_stops(stop_elements, result)
    
    def _validate_order_details(self, order_details: ET.Element, result: Dict[str, Any]) -> None:
        """Validate order_details structure."""
        required_order_elements = ["number", "loading_stop_ids", "unloading_stop_ids"]
        
        for element_name in required_order_elements:
            element = (order_details.find(f"{self.ns}{element_name}") or 
                      order_details.find(element_name))
            if element is None:
                result["errors"].append(f"order_details missing required element: {element_name}")
                result["is_valid"] = False
        
        # Validate stop ID references
        self._validate_stop_id_structure(order_details, result)
    
    def _validate_stop_id_structure(self, order_details: ET.Element, result: Dict[str, Any]) -> None:
        """Validate stop ID elements structure."""
        loading_stop_ids = (order_details.find(f"{self.ns}loading_stop_ids") or 
                           order_details.find("loading_stop_ids"))
        unloading_stop_ids = (order_details.find(f"{self.ns}unloading_stop_ids") or 
                             order_details.find("unloading_stop_ids"))
        
        if loading_stop_ids is not None:
            loading_ids = (loading_stop_ids.findall(f"{self.ns}loading_stop_id") or 
                          loading_stop_ids.findall("loading_stop_id"))
            if len(loading_ids) == 0:
                result["errors"].append("loading_stop_ids must contain at least one loading_stop_id")
                result["is_valid"] = False
        
        if unloading_stop_ids is not None:
            unloading_ids = (unloading_stop_ids.findall(f"{self.ns}unloading_stop_id") or 
                            unloading_stop_ids.findall("unloading_stop_id"))
            if len(unloading_ids) == 0:
                result["errors"].append("unloading_stop_ids must contain at least one unloading_stop_id")
                result["is_valid"] = False
    
    def _validate_stops(self, stop_elements: List[ET.Element], result: Dict[str, Any]) -> None:
        """Validate stops structure."""
        stop_ids = []
        
        for i, stop in enumerate(stop_elements):
            # Validate required stop elements (try with namespace first)
            stop_id = (stop.find(f"{self.ns}id") or stop.find("id"))
            stop_index = (stop.find(f"{self.ns}index") or stop.find("index"))
            location = (stop.find(f"{self.ns}location") or stop.find("location"))
            date_time_period = (stop.find(f"{self.ns}date_time_period") or stop.find("date_time_period"))
            
            if stop_id is None or not stop_id.text:
                result["errors"].append(f"Stop {i+1}: missing or empty id element")
                result["is_valid"] = False
            else:
                # Check for duplicate stop IDs
                if stop_id.text in stop_ids:
                    result["errors"].append(f"Duplicate stop ID: {stop_id.text}")
                    result["is_valid"] = False
                else:
                    stop_ids.append(stop_id.text)
            
            if stop_index is None:
                result["errors"].append(f"Stop {i+1}: missing index element")
                result["is_valid"] = False
            
            if location is None:
                result["errors"].append(f"Stop {i+1}: missing location element")
                result["is_valid"] = False
            else:
                self._validate_location_structure(location, i+1, result)
            
            if date_time_period is None:
                result["errors"].append(f"Stop {i+1}: missing date_time_period element")
                result["is_valid"] = False
            else:
                self._validate_date_time_period(date_time_period, i+1, result)
    
    def _validate_location_structure(self, location: ET.Element, stop_number: int, result: Dict[str, Any]) -> None:
        """Validate location element structure."""
        required_location_elements = ["company_name", "city", "country"]
        
        for element_name in required_location_elements:
            element = (location.find(f"{self.ns}{element_name}") or 
                      location.find(element_name))
            if element is None or not element.text:
                result["errors"].append(f"Stop {stop_number}: location missing required element: {element_name}")
                result["is_valid"] = False
        
        # Validate country code format
        country = (location.find(f"{self.ns}country") or 
                  location.find("country"))
        if country is not None and country.text:
            if not re.match(r'^[A-Z]{2}$', country.text):
                result["errors"].append(f"Stop {stop_number}: country code must be 2 uppercase letters")
                result["is_valid"] = False
    
    def _validate_date_time_period(self, period: ET.Element, stop_number: int, result: Dict[str, Any]) -> None:
        """Validate date_time_period structure."""
        start = (period.find(f"{self.ns}start") or period.find("start"))
        end = (period.find(f"{self.ns}end") or period.find("end"))
        
        if start is None or not start.text:
            result["errors"].append(f"Stop {stop_number}: date_time_period missing start element")
            result["is_valid"] = False
        else:
            if not self._validate_datetime_format(start.text):
                result["errors"].append(f"Stop {stop_number}: invalid start date format")
                result["is_valid"] = False
        
        if end is None or not end.text:
            result["errors"].append(f"Stop {stop_number}: date_time_period missing end element")
            result["is_valid"] = False
        else:
            if not self._validate_datetime_format(end.text):
                result["errors"].append(f"Stop {stop_number}: invalid end date format")
                result["is_valid"] = False
    
    def _validate_datetime_format(self, datetime_str: str) -> bool:
        """Validate ISO datetime format."""
        iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}([+-]\d{2}:\d{2}|Z)$'
        return bool(re.match(iso_pattern, datetime_str))
    
    def validate_field_formats(self, xml_content: str) -> Dict[str, Any]:
        """Validate field formats against field rules."""
        result = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        try:
            root = ET.fromstring(xml_content)
            transport_order = root.find(".//{http://xch.transporeon.com/soap/}transport_order")
            
            if transport_order is None:
                result["errors"].append("No transport_order element found")
                result["is_valid"] = False
                return result
            
            # Validate transport order fields
            self._validate_transport_order_fields(transport_order, result)
            
            # Validate parameter formats
            self._validate_parameter_formats(transport_order, result)
            
        except ET.ParseError as e:
            result["is_valid"] = False
            result["errors"].append(f"XML parsing error: {str(e)}")
        
        return result
    
    def _validate_transport_order_fields(self, transport_order: ET.Element, result: Dict[str, Any]) -> None:
        """Validate transport order field formats."""
        field_rules = self.field_rules.get("field_validation_rules", {}).get("transport_order", {})
        
        for field_name, rules in field_rules.items():
            element = transport_order.find(field_name)
            
            if element is not None and element.text:
                self._apply_field_validation(field_name, element.text, rules, result)
    
    def _validate_parameter_formats(self, transport_order: ET.Element, result: Dict[str, Any]) -> None:
        """Validate parameter field formats."""
        parameters = transport_order.find("parameters")
        if parameters is None:
            return
        
        param_rules = self.field_rules.get("field_validation_rules", {}).get("parameters", {})
        
        for param in parameters.findall("parameter"):
            qualifier = param.get("qualifier")
            value_elem = param.find("value")
            
            if qualifier and value_elem is not None and value_elem.text:
                # Check ocean-specific parameter formats
                if qualifier == "ocean.scac.no":
                    if not re.match(r'^[A-Z0-9]{4}$', value_elem.text):
                        result["errors"].append(f"Invalid SCAC code format: {value_elem.text}")
                        result["is_valid"] = False
    
    def _apply_field_validation(self, field_name: str, value: str, rules: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Apply validation rules to a field value."""
        # Check required
        if rules.get("required", False) and not value:
            result["errors"].append(f"Field '{field_name}' is required but empty")
            result["is_valid"] = False
            return
        
        # Check type
        field_type = rules.get("type")
        if field_type == "number":
            try:
                float(value)
            except ValueError:
                result["errors"].append(f"Field '{field_name}' must be a number: {value}")
                result["is_valid"] = False
                return
        
        # Check length constraints
        min_length = rules.get("min_length")
        max_length = rules.get("max_length")
        
        if min_length and len(value) < min_length:
            result["errors"].append(f"Field '{field_name}' is too short (minimum {min_length} characters)")
            result["is_valid"] = False
        
        if max_length and len(value) > max_length:
            result["errors"].append(f"Field '{field_name}' is too long (maximum {max_length} characters)")
            result["is_valid"] = False
        
        # Check pattern
        pattern = rules.get("pattern")
        if pattern and not re.match(pattern, value):
            error_msg = rules.get("error_message", f"Field '{field_name}' format is invalid")
            result["errors"].append(error_msg)
            result["is_valid"] = False
        
        # Check allowed values
        allowed_values = rules.get("allowed_values")
        if allowed_values and value not in allowed_values:
            result["errors"].append(f"Field '{field_name}' must be one of: {allowed_values}")
            result["is_valid"] = False
    
    def validate_stop_references(self, xml_content: str) -> Dict[str, Any]:
        """Validate that stop ID references are valid."""
        result = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        try:
            root = ET.fromstring(xml_content)
            transport_order = root.find(".//{http://xch.transporeon.com/soap/}transport_order")
            
            if transport_order is None:
                result["errors"].append("No transport_order element found")
                result["is_valid"] = False
                return result
            
            # Get all stop IDs
            stops = transport_order.find("stops")
            stop_ids = set()
            
            if stops is not None:
                for stop in stops.findall("stop"):
                    stop_id_elem = stop.find("id")
                    if stop_id_elem is not None and stop_id_elem.text:
                        stop_ids.add(stop_id_elem.text)
            
            # Check loading stop ID references
            orders = transport_order.find("orders")
            if orders is not None:
                order_details = orders.find("order_details")
                if order_details is not None:
                    self._validate_stop_id_references(order_details, stop_ids, result)
            
        except ET.ParseError as e:
            result["is_valid"] = False
            result["errors"].append(f"XML parsing error: {str(e)}")
        
        return result
    
    def _validate_stop_id_references(self, order_details: ET.Element, stop_ids: set, result: Dict[str, Any]) -> None:
        """Validate stop ID references in order details."""
        # Check loading stop IDs
        loading_stop_ids = order_details.find("loading_stop_ids")
        if loading_stop_ids is not None:
            for loading_id in loading_stop_ids.findall("loading_stop_id"):
                if loading_id.text and loading_id.text not in stop_ids:
                    result["errors"].append(f"Loading stop ID '{loading_id.text}' does not reference an existing stop")
                    result["is_valid"] = False
        
        # Check unloading stop IDs
        unloading_stop_ids = order_details.find("unloading_stop_ids")
        if unloading_stop_ids is not None:
            for unloading_id in unloading_stop_ids.findall("unloading_stop_id"):
                if unloading_id.text and unloading_id.text not in stop_ids:
                    result["errors"].append(f"Unloading stop ID '{unloading_id.text}' does not reference an existing stop")
                    result["is_valid"] = False
