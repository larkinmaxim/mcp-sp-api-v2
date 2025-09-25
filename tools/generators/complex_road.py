"""
Complex Road Freight transport order generator.
"""

from typing import Dict, Any, List
from .base_generator import BaseGenerator


class ComplexRoadGenerator(BaseGenerator):
    """Generator for Complex Road Freight transport orders."""
    
    def __init__(self, data_path=None):
        """Initialize Complex Road generator."""
        super().__init__(data_path)
        self.transport_type = "complex_road"
        self.required_fields = ["number", "status", "scheduling_unit", "carrier_creditor_number"]
        self.supports_pricing = False
        self.supports_order_items = True
        self.supports_vehicle = False
    
    def generate_xml(self, **kwargs) -> Dict[str, Any]:
        """Generate XML for Complex Road Freight transport order."""
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
            
            # Collect order items
            collected_params["order_items"] = self.parameter_collector.collect_order_items(user_input)
            
            # Build basic XML structure
            xml_content = self.build_basic_structure(collected_params)
            
            # Add complex road specific elements
            xml_content = self._add_complex_road_elements(xml_content, collected_params)
            
            # Finalize XML
            final_xml = self.finalize_xml(xml_content)
            
            return {
                "success": True,
                "xml_content": final_xml,
                "transport_type": self.transport_type,
                "order_number": collected_params["transport_info"]["number"],
                "metadata": {
                    "has_order_items": len(collected_params["order_items"]) > 0,
                    "order_item_count": len(collected_params["order_items"]),
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
        """Perform Complex Road specific validation."""
        # Validate stops
        stops = user_input.get("stops", [])
        if len(stops) < 2:
            validation_result["errors"].append("Complex road freight requires at least 2 stops")
            validation_result["is_valid"] = False
        elif len(stops) > 20:
            validation_result["errors"].append("Complex road freight supports maximum 20 stops")
            validation_result["is_valid"] = False
        
        # Validate carrier creditor number format
        carrier_creditor = user_input.get("carrier_creditor_number")
        if carrier_creditor and not carrier_creditor.isdigit():
            if len(carrier_creditor) != 10:
                validation_result["errors"].append("Carrier creditor number must be 10 digits")
                validation_result["is_valid"] = False
        
        # Check for forbidden ocean parameters
        forbidden_ocean_params = ["ocean.scac.no", "ocean.bl.no", "ocean.container.no", "visibility.ocean.product"]
        parameters = user_input.get("parameters", [])
        
        for param in parameters:
            if param.get("qualifier") in forbidden_ocean_params:
                validation_result["errors"].append(f"Ocean parameter '{param['qualifier']}' not allowed in complex road freight")
                validation_result["is_valid"] = False
        
        # Validate order items if provided
        order_items = user_input.get("order_items", [])
        for i, item in enumerate(order_items):
            self._validate_order_item(item, i, validation_result)
        
        # Check for consistency between transport and order level carrier creditor numbers
        transport_carrier = user_input.get("carrier_creditor_number")
        order_params = user_input.get("parameters", [])
        
        for param in order_params:
            if param.get("qualifier") == "custom.preassignedCarrierCreditorNumber":
                if param.get("value") != transport_carrier:
                    validation_result["warnings"].append(
                        "Carrier creditor number inconsistency between transport and order levels"
                    )
    
    def _validate_order_item(self, item: Dict[str, Any], index: int, validation_result: Dict[str, Any]) -> None:
        """Validate a single order item."""
        required_item_fields = ["number", "short_description", "material_number"]
        
        for field in required_item_fields:
            if field not in item or not item[field]:
                validation_result["errors"].append(
                    f"Order item {index + 1}: Required field '{field}' is missing"
                )
                validation_result["is_valid"] = False
        
        # Validate quantities
        quantities = item.get("quantities", [])
        if not quantities:
            validation_result["warnings"].append(f"Order item {index + 1}: No quantities specified")
        else:
            for qty in quantities:
                if not qty.get("qualifier"):
                    validation_result["errors"].append(
                        f"Order item {index + 1}: Quantity qualifier is required"
                    )
                    validation_result["is_valid"] = False
        
        # Validate item parameters
        item_params = item.get("parameters", [])
        required_param_qualifiers = ["material", "plantCode", "unitOfMeasurement"]
        
        existing_qualifiers = [p.get("qualifier") for p in item_params]
        for required_qualifier in required_param_qualifiers:
            if required_qualifier not in existing_qualifiers:
                validation_result["warnings"].append(
                    f"Order item {index + 1}: Recommended parameter '{required_qualifier}' is missing"
                )
    
    def _add_complex_road_elements(self, xml_content: str, collected_params: Dict[str, Any]) -> str:
        """Add Complex Road specific elements to XML."""
        transport_info = collected_params["transport_info"]
        order_details = collected_params["order_details"]
        
        replacements = {}
        
        # Add weight element with default value
        weight_value = transport_info.get("weight_value", 0.0)
        replacements["weight_element"] = f'''
        <weight>
            <value>{weight_value}</value>
        </weight>'''
        
        # Add volume element with default value
        volume_value = transport_info.get("volume_value", 0.0)
        replacements["volume_element"] = f'''
        <volume>
            <value>{volume_value}</value>
        </volume>'''
        
        # Add incoterms if provided
        if "incoterms" in order_details:
            replacements["incoterms_element"] = f"<incoterms>{order_details['incoterms']}</incoterms>"
        else:
            replacements["incoterms_element"] = ""
        
        # Add order items
        if collected_params.get("order_items"):
            replacements["order_items_element"] = self._build_order_items_xml(collected_params["order_items"])
        else:
            replacements["order_items_element"] = ""
        
        # Add order-level parameters
        order_parameters = self._extract_order_parameters(collected_params["custom_parameters"])
        if order_parameters:
            replacements["order_parameters_element"] = self._build_parameters_xml(order_parameters)
        else:
            replacements["order_parameters_element"] = ""
        
        # Add transport-level parameters
        transport_parameters = self._extract_transport_parameters(collected_params["custom_parameters"])
        if transport_parameters:
            replacements["transport_parameters_element"] = self._build_parameters_xml(transport_parameters)
        else:
            replacements["transport_parameters_element"] = ""
        
        # Apply all replacements
        for placeholder, value in replacements.items():
            xml_content = xml_content.replace(f"{{{placeholder}}}", value)
        
        return xml_content
    
    def _build_order_items_xml(self, order_items: List[Dict[str, Any]]) -> str:
        """Build order items XML section."""
        items_xml = """
                <order_items>"""
        
        for item in order_items:
            items_xml += f"""
                    <order_item>
                        <number>{item['number']}</number>
                        <short_description>{item['short_description']}</short_description>
                        <material_number>{item['material_number']}</material_number>"""
            
            # Add quantities
            if item.get("quantities"):
                items_xml += """
                        <quantities>"""
                
                for qty in item["quantities"]:
                    items_xml += f"""
                            <quantity>
                                <qualifier>{qty['qualifier']}</qualifier>
                                <value>{qty['value']}</value>"""
                    
                    if qty.get("unit"):
                        items_xml += f"""
                                <unit>{qty['unit']}</unit>"""
                    
                    items_xml += """
                            </quantity>"""
                
                items_xml += """
                        </quantities>"""
            
            # Add item parameters
            if item.get("parameters"):
                items_xml += """
                        <parameters>"""
                
                for param in item["parameters"]:
                    items_xml += f"""
                            <parameter qualifier="{param['qualifier']}\""""
                    
                    if param.get("shipper_visibility"):
                        items_xml += f""" shipperVisibility="{param['shipper_visibility']}\""""
                    
                    items_xml += ">"
                    
                    if param.get("value"):
                        items_xml += f"""
                                <value>{param['value']}</value>"""
                    
                    items_xml += """
                            </parameter>"""
                
                items_xml += """
                        </parameters>"""
            
            items_xml += """
                    </order_item>"""
        
        items_xml += """
                </order_items>"""
        
        return items_xml
    
    def _extract_order_parameters(self, all_parameters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract parameters that belong at the order level."""
        order_level_qualifiers = [
            "custom.preassignedCarrierCreditorNumber",
            "salesorderNumber",
            "shuttleTransport",
            "shuttleTransportAuto",
            "CPUrecipient",
            "CSRName",
            "CSREmail",
            "CSRPhone",
            "OrderDate",
            "transportMode",
            "shippingPoint",
            "ShipTo",
            "material",
            "route",
            "purchaseOrderNumber",
            "PGIDate"
        ]
        
        return [param for param in all_parameters if param.get("qualifier") in order_level_qualifiers]
    
    def _extract_transport_parameters(self, all_parameters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract parameters that belong at the transport level."""
        transport_level_qualifiers = [
            "numberofCombinedDeliveries",
            "combinedloadnumber",
            "transport.salesorderNumber",
            "transport.purchaseOrderNumber",
            "transport.customerPONumber",
            "custom.resend.carrierprint",
            "transport.shipperBillTo"
        ]
        
        return [param for param in all_parameters if param.get("qualifier") in transport_level_qualifiers]
    
    def get_example_input(self) -> Dict[str, Any]:
        """Get example input for Complex Road Freight."""
        return {
            "number": "0081310198",
            "status": "D",
            "scheduling_unit": "BCO",
            "carrier_creditor_number": "0000203512",
            "weight_value": 0.0,
            "volume_value": 0.0,
            "incoterms": "DAP",
            "loading_stop_ids": ["BCOT"],
            "unloading_stop_ids": ["0000017649"],
            "stops": [
                {
                    "id": "BCOT",
                    "index": 0,
                    "location": {
                        "company_name": "Bayport CO Truck Terminal",
                        "street": "5761 Underwood, BCO",
                        "zip": "77507",
                        "city": "Pasadena",
                        "state": "TX",
                        "country": "US"
                    },
                    "date_time_period": {
                        "start": "2025-09-25T00:00:00Z",
                        "end": "2025-09-26T23:59:00Z"
                    }
                },
                {
                    "id": "0000017649",
                    "index": 1,
                    "location": {
                        "company_name": "THE SHERWIN WILLIAMS COMPANY",
                        "street": "701 SOUTH SHILOH RD DOCK 42",
                        "zip": "75042",
                        "city": "GARLAND",
                        "state": "TX",
                        "country": "US",
                        "comment": "C/O VALSPAR PACKAGING"
                    },
                    "date_time_period": {
                        "start": "2025-09-26T09:00:00Z",
                        "end": "2025-09-26T09:00:00Z"
                    }
                }
            ],
            "order_items": [
                {
                    "number": "000010",
                    "short_description": "GLYCOL ETHER EB",
                    "material_number": "0205LB",
                    "quantities": [
                        {
                            "qualifier": "weight",
                            "value": 45000.0,
                            "unit": "LBR"
                        },
                        {
                            "qualifier": "custom.unit.of.measurement",
                            "value": 0.0
                        }
                    ],
                    "parameters": [
                        {
                            "qualifier": "technicalDeviation",
                            "shipper_visibility": "YES"
                        },
                        {
                            "qualifier": "material",
                            "value": "0205LB",
                            "shipper_visibility": "YES"
                        },
                        {
                            "qualifier": "plantCode",
                            "value": "US61",
                            "shipper_visibility": "YES"
                        },
                        {
                            "qualifier": "customerMaterial",
                            "value": "0421598"
                        },
                        {
                            "qualifier": "unitOfMeasurement",
                            "value": "LBR",
                            "shipper_visibility": "YES"
                        }
                    ]
                }
            ],
            "parameters": [
                {
                    "qualifier": "custom.preassignedCarrierCreditorNumber",
                    "value": "0000203512"
                },
                {
                    "qualifier": "transportMode",
                    "value": "RO",
                    "shipper_visibility": "YES"
                },
                {
                    "qualifier": "transport.salesorderNumber",
                    "value": "0001076772",
                    "shipper_visibility": "YES"
                }
            ]
        }
