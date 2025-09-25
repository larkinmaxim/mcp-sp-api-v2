"""
XML DOM builder for programmatic XML construction and manipulation.
"""

import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import re


class XMLDOMBuilder:
    """Builds and manipulates XML using DOM operations."""
    
    def __init__(self):
        """Initialize XML DOM builder."""
        self.namespaces = {
            '': 'http://xch.transporeon.com/soap/',
            'soap': 'http://xch.transporeon.com/soap/'
        }
        
        # Register namespaces
        for prefix, uri in self.namespaces.items():
            ET.register_namespace(prefix, uri)
    
    def create_transport_orders_root(self) -> ET.Element:
        """Create the root transport_orders element with proper namespace."""
        root = ET.Element("transport_orders")
        root.set("xmlns", self.namespaces[''])
        return root
    
    def create_transport_order_element(self, root: ET.Element) -> ET.Element:
        """Create transport_order element under root."""
        transport_order = ET.SubElement(root, "transport_order")
        transport_order.set("xmlns", self.namespaces[''])
        return transport_order
    
    def add_simple_element(self, parent: ET.Element, tag: str, text: str = "") -> ET.Element:
        """Add a simple text element to parent."""
        element = ET.SubElement(parent, tag)
        element.text = text
        return element
    
    def add_weight_element(self, parent: ET.Element, value: float, unit: str = "kg") -> Optional[ET.Element]:
        """Add weight element with value and unit."""
        if value is None:
            return None
        
        weight = ET.SubElement(parent, "weight")
        if unit != "kg":  # Only add unit attribute if not default
            weight.set("unit", unit)
        
        value_elem = ET.SubElement(weight, "value")
        value_elem.text = str(value)
        return weight
    
    def add_volume_element(self, parent: ET.Element, value: float) -> Optional[ET.Element]:
        """Add volume element with value."""
        if value is None:
            return None
        
        volume = ET.SubElement(parent, "volume")
        value_elem = ET.SubElement(volume, "value")
        value_elem.text = str(value)
        return volume
    
    def add_distance_element(self, parent: ET.Element, value: float, unit: str = "km") -> Optional[ET.Element]:
        """Add distance element with value and unit."""
        if value is None:
            return None
        
        distance = ET.SubElement(parent, "distance")
        distance.set("unit", unit)
        
        value_elem = ET.SubElement(distance, "value")
        value_elem.text = str(value)
        return distance
    
    def add_loading_meter_element(self, parent: ET.Element, value: Optional[float] = None, unit: str = "m") -> ET.Element:
        """Add loading_meter element with optional value and unit."""
        loading_meter = ET.SubElement(parent, "loading_meter")
        loading_meter.set("unit", unit)
        
        if value is not None:
            value_elem = ET.SubElement(loading_meter, "value")
            value_elem.text = str(value)
        
        return loading_meter
    
    def add_prices_element(self, parent: ET.Element, reference: float, currency: str = "EUR", mode: str = "DEFAULT") -> ET.Element:
        """Add prices element with reference, currency, and mode."""
        prices = ET.SubElement(parent, "prices")
        
        ref_elem = ET.SubElement(prices, "reference")
        ref_elem.text = str(reference)
        
        curr_elem = ET.SubElement(prices, "currency")
        curr_elem.text = currency
        
        mode_elem = ET.SubElement(prices, "mode")
        mode_elem.text = mode
        
        return prices
    
    def add_stop_ids(self, parent: ET.Element, tag_name: str, stop_ids: List[str]) -> ET.Element:
        """Add loading_stop_ids or unloading_stop_ids elements."""
        container = ET.SubElement(parent, tag_name)
        
        for stop_id in stop_ids:
            id_elem = ET.SubElement(container, tag_name.rstrip('s')[:-5] + "_id")  # Convert plural to singular
            id_elem.text = stop_id
        
        return container
    
    def add_stop_element(self, parent: ET.Element, stop_data: Dict[str, Any]) -> ET.Element:
        """Add a stop element with location and date_time_period."""
        stop = ET.SubElement(parent, "stop")
        
        # Add stop ID and index
        self.add_simple_element(stop, "id", stop_data["id"])
        self.add_simple_element(stop, "index", str(stop_data.get("index", 0)))
        
        # Add location
        location = ET.SubElement(stop, "location")
        location_data = stop_data["location"]
        
        self.add_simple_element(location, "company_name", location_data["company_name"])
        
        if location_data.get("street"):
            self.add_simple_element(location, "street", location_data["street"])
        
        if location_data.get("zip"):
            self.add_simple_element(location, "zip", location_data["zip"])
        
        self.add_simple_element(location, "city", location_data["city"])
        
        if location_data.get("state"):
            self.add_simple_element(location, "state", location_data["state"])
        
        self.add_simple_element(location, "country", location_data["country"])
        
        if location_data.get("comment"):
            self.add_simple_element(location, "comment", location_data["comment"])
        
        # Add date_time_period
        if "date_time_period" in stop_data:
            self.add_date_time_period(stop, stop_data["date_time_period"])
        
        return stop
    
    def add_date_time_period(self, parent: ET.Element, period_data: Dict[str, str]) -> ET.Element:
        """Add date_time_period element."""
        period = ET.SubElement(parent, "date_time_period")
        
        self.add_simple_element(period, "start", period_data["start"])
        self.add_simple_element(period, "end", period_data["end"])
        
        if period_data.get("timezone"):
            self.add_simple_element(period, "timezone", period_data["timezone"])
        
        return period
    
    def add_parameter(self, parent: ET.Element, qualifier: str, value: str = "", 
                     shipper_visibility: Optional[str] = None, 
                     export_to_carrier: Optional[str] = None) -> ET.Element:
        """Add parameter element with attributes."""
        param = ET.SubElement(parent, "parameter")
        param.set("qualifier", qualifier)
        
        if shipper_visibility:
            param.set("shipperVisibility", shipper_visibility)
        
        if export_to_carrier:
            param.set("exportToCarrier", export_to_carrier)
        
        if value:
            value_elem = ET.SubElement(param, "value")
            value_elem.text = value
        
        return param
    
    def add_order_item(self, parent: ET.Element, item_data: Dict[str, Any]) -> ET.Element:
        """Add order_item element with quantities and parameters."""
        item = ET.SubElement(parent, "order_item")
        
        self.add_simple_element(item, "number", item_data["number"])
        self.add_simple_element(item, "short_description", item_data["short_description"])
        self.add_simple_element(item, "material_number", item_data["material_number"])
        
        # Add quantities
        if "quantities" in item_data:
            quantities_elem = ET.SubElement(item, "quantities")
            for quantity_data in item_data["quantities"]:
                self.add_quantity(quantities_elem, quantity_data)
        
        # Add parameters
        if "parameters" in item_data:
            params_elem = ET.SubElement(item, "parameters")
            for param_data in item_data["parameters"]:
                self.add_parameter(
                    params_elem,
                    param_data["qualifier"],
                    param_data.get("value", ""),
                    param_data.get("shipper_visibility"),
                    param_data.get("export_to_carrier")
                )
        
        return item
    
    def add_quantity(self, parent: ET.Element, quantity_data: Dict[str, Any]) -> ET.Element:
        """Add quantity element."""
        quantity = ET.SubElement(parent, "quantity")
        
        self.add_simple_element(quantity, "qualifier", quantity_data["qualifier"])
        self.add_simple_element(quantity, "value", str(quantity_data["value"]))
        
        if quantity_data.get("unit"):
            self.add_simple_element(quantity, "unit", quantity_data["unit"])
        
        return quantity
    
    def replace_placeholders(self, template: str, replacements: Dict[str, str]) -> str:
        """Replace placeholders in template with actual values."""
        result = template
        
        for placeholder, value in replacements.items():
            pattern = f"{{{placeholder}}}"
            result = result.replace(pattern, str(value))
        
        return result
    
    def remove_empty_placeholders(self, xml_string: str) -> str:
        """Remove elements that still contain unreplaced placeholders."""
        # Remove standalone placeholders on their own lines
        xml_string = re.sub(r'^\s*\{[^}]*\}\s*$', '', xml_string, flags=re.MULTILINE)
        
        # Remove elements that contain only placeholders (single line)
        xml_string = re.sub(r'<([^>]+)>\s*\{[^}]*\}\s*</\1>', '', xml_string)
        
        # Remove self-closing elements with placeholder attributes
        xml_string = re.sub(r'<[^>]*\{[^}]*\}[^>]*/>\s*', '', xml_string)
        
        # Remove any remaining standalone placeholders
        xml_string = re.sub(r'\{[^}]*\}', '', xml_string)
        
        return xml_string
    
    def to_xml_string(self, element: ET.Element, encoding: str = "UTF-8") -> str:
        """Convert element tree to formatted XML string."""
        # Add XML declaration
        rough_string = ET.tostring(element, encoding='unicode')
        
        # Add proper XML declaration
        xml_declaration = f'<?xml version="1.0" encoding="{encoding}"?>\n'
        
        return xml_declaration + rough_string
    
    def validate_xml_structure(self, xml_string: str) -> bool:
        """Validate that XML string is well-formed."""
        try:
            ET.fromstring(xml_string)
            return True
        except ET.ParseError:
            return False
    
    def pretty_print_xml(self, element: ET.Element) -> str:
        """Return a pretty-printed XML string."""
        from xml.dom import minidom
        
        rough_string = ET.tostring(element, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        
        # Get pretty printed string and remove the first line (XML declaration)
        pretty = reparsed.toprettyxml(indent="    ", encoding=None)
        lines = pretty.split('\n')
        
        # Remove empty lines and the XML declaration line
        cleaned_lines = [line for line in lines[1:] if line.strip()]
        
        return '<?xml version="1.0" encoding="UTF-8"?>\n' + '\n'.join(cleaned_lines)
