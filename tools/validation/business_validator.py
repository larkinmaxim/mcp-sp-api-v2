"""
Business rule validator for transport order specific business logic.
"""

import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional
from datetime import datetime
import re


class BusinessValidator:
    """Validates business rules and transport-specific logic."""
    
    def __init__(self, template_loader):
        """Initialize business validator."""
        self.template_loader = template_loader
        self.business_rules = template_loader.load_validation_rules("business")
        self.namespace = "http://xch.transporeon.com/soap/"
        self.ns = "{" + self.namespace + "}"
    
    def validate_transport_type_rules(self, xml_content: str, transport_type: str) -> Dict[str, Any]:
        """Validate transport type specific business rules."""
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
            
            transport_rules = self.business_rules.get("business_validation_rules", {}).get("transport_type_rules", {})
            
            if transport_type in transport_rules:
                rules = transport_rules[transport_type]
                self._validate_transport_specific_rules(transport_order, transport_type, rules, result)
            
        except ET.ParseError as e:
            result["is_valid"] = False
            result["errors"].append(f"XML parsing error: {str(e)}")
        
        return result
    
    def _validate_transport_specific_rules(self, transport_order: ET.Element, transport_type: str, 
                                         rules: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Validate specific transport type rules."""
        # Validate required elements
        required_elements = rules.get("required_elements", [])
        for element_name in required_elements:
            element = (transport_order.find(f"{self.ns}{element_name}") or 
                      transport_order.find(element_name))
            if element is None:
                result["errors"].append(f"{transport_type}: Required element '{element_name}' is missing")
                result["is_valid"] = False
        
        # Validate stop counts
        self._validate_stop_counts(transport_order, transport_type, rules, result)
        
        # Validate fixed values for ocean visibility
        if transport_type == "ocean_visibility":
            self._validate_ocean_fixed_values(transport_order, rules, result)
        
        # Validate parameter restrictions
        self._validate_parameter_restrictions(transport_order, transport_type, rules, result)
        
        # Validate complex road specific rules
        if transport_type == "complex_road":
            self._validate_complex_road_rules(transport_order, rules, result)
    
    def _validate_stop_counts(self, transport_order: ET.Element, transport_type: str, 
                            rules: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Validate stop count requirements."""
        stops = transport_order.find("stops")
        if stops is None:
            return
        
        stop_elements = stops.findall("stop")
        stop_count = len(stop_elements)
        
        min_stops = rules.get("minimum_stops", 0)
        max_stops = rules.get("maximum_stops", float('inf'))
        
        if stop_count < min_stops:
            result["errors"].append(f"{transport_type}: Minimum {min_stops} stops required, found {stop_count}")
            result["is_valid"] = False
        
        if stop_count > max_stops:
            result["errors"].append(f"{transport_type}: Maximum {max_stops} stops allowed, found {stop_count}")
            result["is_valid"] = False
    
    def _validate_ocean_fixed_values(self, transport_order: ET.Element, rules: Dict[str, Any], 
                                   result: Dict[str, Any]) -> None:
        """Validate fixed values for ocean visibility."""
        fixed_values = rules.get("fixed_values", {})
        
        for field_name, expected_value in fixed_values.items():
            element = transport_order.find(field_name)
            
            if element is None:
                result["errors"].append(f"Ocean visibility: Missing required field '{field_name}'")
                result["is_valid"] = False
            elif element.text != expected_value:
                result["errors"].append(
                    f"Ocean visibility: Field '{field_name}' must be '{expected_value}', found '{element.text}'"
                )
                result["is_valid"] = False
    
    def _validate_parameter_restrictions(self, transport_order: ET.Element, transport_type: str,
                                       rules: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Validate parameter restrictions for transport type."""
        parameter_restrictions = rules.get("parameter_restrictions", {})
        
        # Check forbidden parameters
        forbidden_qualifiers = parameter_restrictions.get("forbidden_qualifiers", [])
        parameters = transport_order.find("parameters")
        
        if parameters is not None:
            for param in parameters.findall("parameter"):
                qualifier = param.get("qualifier")
                if qualifier in forbidden_qualifiers:
                    result["errors"].append(
                        f"{transport_type}: Forbidden parameter '{qualifier}' is not allowed"
                    )
                    result["is_valid"] = False
        
        # Check required parameters for ocean visibility
        if transport_type == "ocean_visibility":
            required_params = rules.get("required_parameters", [])
            self._validate_required_parameters(transport_order, required_params, result)
        
        # Check mandatory fixed parameters
        mandatory_fixed = parameter_restrictions.get("mandatory_fixed_parameters", {})
        self._validate_mandatory_fixed_parameters(transport_order, mandatory_fixed, result)
    
    def _validate_required_parameters(self, transport_order: ET.Element, required_params: List[str],
                                    result: Dict[str, Any]) -> None:
        """Validate required parameters are present."""
        parameters = transport_order.find("parameters")
        if parameters is None:
            if required_params:
                result["errors"].append("Required parameters section is missing")
                result["is_valid"] = False
            return
        
        existing_qualifiers = [param.get("qualifier") for param in parameters.findall("parameter")]
        
        for required_qualifier in required_params:
            if required_qualifier not in existing_qualifiers:
                result["errors"].append(f"Required parameter '{required_qualifier}' is missing")
                result["is_valid"] = False
    
    def _validate_mandatory_fixed_parameters(self, transport_order: ET.Element, 
                                           mandatory_fixed: Dict[str, str], result: Dict[str, Any]) -> None:
        """Validate mandatory fixed parameter values."""
        parameters = transport_order.find("parameters")
        if parameters is None:
            return
        
        for param in parameters.findall("parameter"):
            qualifier = param.get("qualifier")
            if qualifier in mandatory_fixed:
                value_elem = param.find("value")
                expected_value = mandatory_fixed[qualifier]
                
                if value_elem is None or value_elem.text != expected_value:
                    result["errors"].append(
                        f"Parameter '{qualifier}' must have value '{expected_value}'"
                    )
                    result["is_valid"] = False
    
    def _validate_complex_road_rules(self, transport_order: ET.Element, rules: Dict[str, Any],
                                   result: Dict[str, Any]) -> None:
        """Validate complex road freight specific rules."""
        # Check carrier creditor number requirement
        if rules.get("requires_carrier_creditor", False):
            carrier_elem = transport_order.find("carrier_creditor_number")
            if carrier_elem is None or not carrier_elem.text:
                result["errors"].append("Complex road freight requires carrier_creditor_number")
                result["is_valid"] = False
        
        # Validate order items if present
        if rules.get("allows_order_items", False):
            self._validate_order_items_rules(transport_order, rules, result)
    
    def _validate_order_items_rules(self, transport_order: ET.Element, rules: Dict[str, Any],
                                  result: Dict[str, Any]) -> None:
        """Validate order items business rules."""
        orders = transport_order.find("orders")
        if orders is None:
            return
        
        order_details = orders.find("order_details")
        if order_details is None:
            return
        
        order_items = order_details.find("order_items")
        if order_items is None:
            return
        
        item_rules = rules.get("order_item_rules", {})
        required_fields = item_rules.get("required_fields", [])
        required_quantities = item_rules.get("required_quantities", [])
        required_parameters = item_rules.get("required_parameters", [])
        
        for i, item in enumerate(order_items.findall("order_item")):
            # Validate required item fields
            for field in required_fields:
                element = item.find(field)
                if element is None or not element.text:
                    result["errors"].append(f"Order item {i+1}: Missing required field '{field}'")
                    result["is_valid"] = False
            
            # Validate quantities
            quantities = item.find("quantities")
            if quantities is not None:
                existing_qualifiers = [q.find("qualifier").text for q in quantities.findall("quantity") 
                                     if q.find("qualifier") is not None and q.find("qualifier").text]
                
                for required_qty in required_quantities:
                    if required_qty not in existing_qualifiers:
                        result["warnings"].append(
                            f"Order item {i+1}: Recommended quantity '{required_qty}' is missing"
                        )
            
            # Validate item parameters
            item_params = item.find("parameters")
            if item_params is not None:
                existing_param_qualifiers = [p.get("qualifier") for p in item_params.findall("parameter")]
                
                for required_param in required_parameters:
                    if required_param not in existing_param_qualifiers:
                        result["warnings"].append(
                            f"Order item {i+1}: Recommended parameter '{required_param}' is missing"
                        )
    
    def validate_cross_field_consistency(self, xml_content: str) -> Dict[str, Any]:
        """Validate cross-field consistency rules."""
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
            
            # Validate carrier creditor consistency
            self._validate_carrier_creditor_consistency(transport_order, result)
            
            # Validate date sequence
            self._validate_date_sequence(transport_order, result)
            
            # Validate stop index sequence
            self._validate_stop_index_sequence(transport_order, result)
            
        except ET.ParseError as e:
            result["is_valid"] = False
            result["errors"].append(f"XML parsing error: {str(e)}")
        
        return result
    
    def _validate_carrier_creditor_consistency(self, transport_order: ET.Element, result: Dict[str, Any]) -> None:
        """Validate carrier creditor number consistency."""
        transport_carrier_elem = transport_order.find("carrier_creditor_number")
        if transport_carrier_elem is None or not transport_carrier_elem.text:
            return
        
        transport_carrier = transport_carrier_elem.text
        
        # Check consistency with order-level parameters
        parameters = transport_order.find("parameters")
        if parameters is not None:
            for param in parameters.findall("parameter"):
                if param.get("qualifier") == "custom.preassignedCarrierCreditorNumber":
                    value_elem = param.find("value")
                    if value_elem is not None and value_elem.text != transport_carrier:
                        result["warnings"].append(
                            "Carrier creditor number inconsistency between transport and order levels"
                        )
    
    def _validate_date_sequence(self, transport_order: ET.Element, result: Dict[str, Any]) -> None:
        """Validate logical date sequence across stops."""
        stops = transport_order.find("stops")
        if stops is None:
            return
        
        stop_dates = []
        
        for stop in stops.findall("stop"):
            period = stop.find("date_time_period")
            if period is not None:
                start_elem = period.find("start")
                if start_elem is not None and start_elem.text:
                    try:
                        # Parse ISO datetime
                        date_str = start_elem.text
                        # Remove timezone for comparison
                        if '+' in date_str:
                            date_str = date_str.split('+')[0]
                        elif 'Z' in date_str:
                            date_str = date_str.replace('Z', '')
                        
                        date_obj = datetime.fromisoformat(date_str)
                        stop_dates.append(date_obj)
                    except ValueError:
                        # Skip invalid dates - will be caught by structural validation
                        continue
        
        # Check if dates are in logical sequence (allowing for same dates)
        for i in range(1, len(stop_dates)):
            if stop_dates[i] < stop_dates[i-1]:
                result["warnings"].append(
                    "Stop dates may not be in logical sequence - verify pickup and delivery order"
                )
                break
    
    def _validate_stop_index_sequence(self, transport_order: ET.Element, result: Dict[str, Any]) -> None:
        """Validate stop index sequence."""
        stops = transport_order.find("stops")
        if stops is None:
            return
        
        indices = []
        
        for stop in stops.findall("stop"):
            index_elem = stop.find("index")
            if index_elem is not None and index_elem.text:
                try:
                    index = int(index_elem.text)
                    indices.append(index)
                except ValueError:
                    result["errors"].append("Stop index must be a number")
                    result["is_valid"] = False
        
        # Check if indices start from 0 and are sequential
        if indices:
            indices.sort()
            if indices[0] != 0:
                result["errors"].append("Stop indices should start from 0")
                result["is_valid"] = False
            
            for i in range(1, len(indices)):
                if indices[i] != indices[i-1] + 1:
                    result["errors"].append("Stop indices should be sequential")
                    result["is_valid"] = False
                    break
    
    def validate_ocean_completeness(self, xml_content: str) -> Dict[str, Any]:
        """Validate ocean visibility parameter completeness."""
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
            
            # Check if this is an ocean visibility order
            scheduling_unit = transport_order.find("scheduling_unit")
            if scheduling_unit is None or scheduling_unit.text != "Ocean Visibility":
                return result  # Not an ocean visibility order
            
            # Validate required ocean parameters
            required_ocean_params = ["visibility.ocean.product", "ocean.scac.no", "ocean.bl.no", "ocean.container.no"]
            parameters = transport_order.find("parameters")
            
            if parameters is None:
                result["errors"].append("Ocean visibility orders must have parameters section")
                result["is_valid"] = False
                return result
            
            existing_qualifiers = [param.get("qualifier") for param in parameters.findall("parameter")]
            
            for required_param in required_ocean_params:
                if required_param not in existing_qualifiers:
                    result["errors"].append(f"Ocean visibility: Missing required parameter '{required_param}'")
                    result["is_valid"] = False
            
            # Validate specific ocean parameter values
            for param in parameters.findall("parameter"):
                qualifier = param.get("qualifier")
                value_elem = param.find("value")
                
                if qualifier == "visibility.ocean.product":
                    if value_elem is None or value_elem.text != "true":
                        result["errors"].append("Ocean visibility parameter must be 'true'")
                        result["is_valid"] = False
                
                elif qualifier == "ocean.scac.no":
                    if value_elem is not None and value_elem.text:
                        if not re.match(r'^[A-Z0-9]{4}$', value_elem.text):
                            result["errors"].append(f"Invalid SCAC code format: {value_elem.text}")
                            result["is_valid"] = False
        
        except ET.ParseError as e:
            result["is_valid"] = False
            result["errors"].append(f"XML parsing error: {str(e)}")
        
        return result
