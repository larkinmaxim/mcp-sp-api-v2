"""
Base generator class for transport order XML generation.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from ..utils.template_loader import TemplateLoader
from ..utils.xml_builder import XMLDOMBuilder
from ..utils.parameter_collector import ParameterCollector


class BaseGenerator(ABC):
    """Abstract base class for transport order generators."""
    
    def __init__(self, data_path: Optional[str] = None):
        """Initialize base generator with utilities."""
        self.template_loader = TemplateLoader(data_path)
        self.xml_builder = XMLDOMBuilder()
        self.parameter_collector = ParameterCollector(self.template_loader)
        
        # These should be overridden by subclasses
        self.transport_type = ""
        self.required_fields = []
        self.supports_pricing = False
        self.supports_order_items = False
        self.supports_vehicle = False
    
    @abstractmethod
    def generate_xml(self, **kwargs) -> Dict[str, Any]:
        """Generate XML for the specific transport type."""
        pass
    
    def validate_input(self, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """Validate user input and return validation results."""
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "missing_required": [],
            "suggested_optional": []
        }
        
        try:
            # Check for missing required fields
            missing_prompts = self.parameter_collector.generate_missing_field_prompts(
                self.transport_type, user_input
            )
            validation_result["missing_required"] = missing_prompts
            
            if missing_prompts:
                validation_result["is_valid"] = False
            
            # Get optional field suggestions
            validation_result["suggested_optional"] = self.parameter_collector.suggest_optional_fields(
                self.transport_type
            )
            
            # Perform specific validation based on transport type
            self._perform_specific_validation(user_input, validation_result)
            
        except ValueError as e:
            validation_result["is_valid"] = False
            validation_result["errors"].append(str(e))
        
        return validation_result
    
    def _perform_specific_validation(self, user_input: Dict[str, Any], validation_result: Dict[str, Any]) -> None:
        """Perform transport type specific validation. Override in subclasses."""
        pass
    
    def collect_all_parameters(self, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """Collect all parameters needed for XML generation."""
        collected = {}
        
        # Collect basic transport information
        collected["transport_info"] = self.parameter_collector.collect_basic_transport_info(
            self.transport_type, user_input
        )
        
        # Collect order details
        collected["order_details"] = self.parameter_collector.collect_order_details(
            self.transport_type, user_input
        )
        
        # Collect stops
        collected["stops"] = self.parameter_collector.collect_stops(user_input)
        
        # Collect custom parameters
        collected["custom_parameters"] = self.parameter_collector.collect_custom_parameters(user_input)
        
        return collected
    
    def build_basic_structure(self, collected_params: Dict[str, Any]) -> str:
        """Build basic XML structure using template replacement."""
        template = self.template_loader.load_template(self.transport_type)
        transport_info = collected_params["transport_info"]
        order_details = collected_params["order_details"]
        
        replacements = {}
        
        # Basic transport order fields
        replacements.update({
            "transport_number": transport_info.get("number", ""),
            "status": transport_info.get("status", "N"),
            "scheduling_unit": transport_info.get("scheduling_unit", ""),
            "order_number": order_details.get("order_number", transport_info.get("number", ""))
        })
        
        # Add carrier creditor number if present
        if "carrier_creditor_number" in transport_info:
            replacements["carrier_creditor_number"] = transport_info["carrier_creditor_number"]
        
        # DISCOVERY: Add ALL transport_info fields for potential direct replacement
        for key, value in transport_info.items():
            if key not in replacements:  # Don't override already set replacements
                replacements[key] = value
        
        # Process stops
        replacements.update(self._build_stops_replacements(collected_params["stops"]))
        
        # Process stop IDs
        loading_ids = order_details.get("loading_stop_ids", [])
        unloading_ids = order_details.get("unloading_stop_ids", [])
        
        replacements["loading_stop_ids"] = self._build_stop_ids_xml(loading_ids, "loading_stop_id")
        replacements["unloading_stop_ids"] = self._build_stop_ids_xml(unloading_ids, "unloading_stop_id")
        
        # Apply replacements
        xml_content = self.xml_builder.replace_placeholders(template, replacements)
        
        # Don't clean up placeholders here - let subclasses handle their specific elements first
        return xml_content
    
    def _build_stops_replacements(self, stops: List[Dict[str, Any]]) -> Dict[str, str]:
        """Build XML for stops section."""
        stops_xml = ""
        
        for stop_data in stops:
            stops_xml += self._build_single_stop_xml(stop_data)
        
        return {"stops": stops_xml}
    
    def _build_single_stop_xml(self, stop_data: Dict[str, Any]) -> str:
        """Build XML for a single stop."""
        location = stop_data["location"]
        period = stop_data["date_time_period"]
        
        stop_xml = f"""
        <stop>
            <id>{stop_data["id"]}</id>
            <index>{stop_data["index"]}</index>
            <location>
                <company_name>{location["company_name"]}</company_name>"""
        
        if location.get("street"):
            stop_xml += f"""
                <street>{location["street"]}</street>"""
        
        if location.get("zip"):
            stop_xml += f"""
                <zip>{location["zip"]}</zip>"""
        
        stop_xml += f"""
                <city>{location["city"]}</city>"""
        
        if location.get("state"):
            stop_xml += f"""
                <state>{location["state"]}</state>"""
        
        stop_xml += f"""
                <country>{location["country"]}</country>"""
        
        if location.get("comment"):
            stop_xml += f"""
                <comment>{location["comment"]}</comment>"""
        
        stop_xml += f"""
            </location>
            <date_time_period>
                <start>{period["start"]}</start>
                <end>{period["end"]}</end>"""
        
        if period.get("timezone"):
            stop_xml += f"""
                <timezone>{period["timezone"]}</timezone>"""
        
        stop_xml += """
            </date_time_period>
        </stop>"""
        
        return stop_xml
    
    def _build_stop_ids_xml(self, stop_ids: List[str], tag_name: str) -> str:
        """Build XML for stop IDs list."""
        ids_xml = ""
        for stop_id in stop_ids:
            ids_xml += f"""
                    <{tag_name}>{stop_id}</{tag_name}>"""
        return ids_xml
    
    def _build_parameters_xml(self, parameters: List[Dict[str, Any]]) -> str:
        """Build XML for parameters section."""
        if not parameters:
            return ""
        
        params_xml = """
        <parameters>"""
        
        for param in parameters:
            qualifier = param["qualifier"]
            value = param.get("value", "")
            
            param_xml = f"""
            <parameter qualifier="{qualifier}\""""
            
            if param.get("shipper_visibility"):
                param_xml += f""" shipperVisibility="{param["shipper_visibility"]}\""""
            
            if param.get("export_to_carrier"):
                param_xml += f""" exportToCarrier="{param["export_to_carrier"]}\""""
            
            param_xml += ">"
            
            if value:
                param_xml += f"""
                <value>{value}</value>"""
            
            param_xml += """
            </parameter>"""
            
            params_xml += param_xml
        
        params_xml += """
        </parameters>"""
        
        return params_xml
    
    def finalize_xml(self, xml_content: str) -> str:
        """Finalize XML content with validation and formatting."""
        # Remove any remaining empty placeholders
        xml_content = self.xml_builder.remove_empty_placeholders(xml_content)
        
        # Validate XML structure
        if not self.xml_builder.validate_xml_structure(xml_content):
            raise ValueError("Generated XML is not well-formed")
        
        return xml_content
    
    def get_transport_type_info(self) -> Dict[str, Any]:
        """Get information about this transport type."""
        return {
            "transport_type": self.transport_type,
            "supports_pricing": self.supports_pricing,
            "supports_order_items": self.supports_order_items,
            "supports_vehicle": self.supports_vehicle,
            "required_fields": self.required_fields
        }
