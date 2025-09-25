"""
Main FastMCP tool definitions for Transport Order XML Generator.
"""

from typing import Dict, Any, Optional
import json
import base64
import requests
from fastmcp import FastMCP

from .generators.base_generator import BaseGenerator
from .generators.simple_road import SimpleRoadGenerator
from .generators.complex_road import ComplexRoadGenerator
from .generators.ocean_visibility import OceanVisibilityGenerator
from .validation.structural_validator import StructuralValidator
from .validation.business_validator import BusinessValidator
from .utils.template_loader import TemplateLoader


class TransportOrderFactory:
    """Factory for creating transport order generators."""
    
    def __init__(self, data_path: Optional[str] = None):
        """Initialize factory with optional data path."""
        self.data_path = data_path
        self.generators = {
            "simple_road": SimpleRoadGenerator,
            "complex_road": ComplexRoadGenerator,
            "ocean_visibility": OceanVisibilityGenerator
        }
    
    def create_generator(self, transport_type: str) -> BaseGenerator:
        """Create generator instance for specified transport type."""
        if transport_type not in self.generators:
            raise ValueError(f"Unsupported transport type: {transport_type}")
        
        generator_class = self.generators[transport_type]
        return generator_class(self.data_path)
    
    def get_available_types(self) -> list:
        """Get list of available transport types."""
        return list(self.generators.keys())
    
    def get_transport_type_info(self, transport_type: str) -> Dict[str, Any]:
        """Get information about a specific transport type."""
        generator = self.create_generator(transport_type)
        return generator.get_transport_type_info()


# Initialize FastMCP server
app = FastMCP(
    name="Transport Order XML Generator",
    instructions="Generate valid transport order XML files for Transporeon API. Supports Simple Road, Complex Road, and Ocean Visibility transport types."
)

# Initialize factory
factory = TransportOrderFactory()


@app.tool()
def generate_transport_order_xml(
    transport_type: str,
    order_data: str
) -> Dict[str, Any]:
    """
    Generate valid transport order XML based on user input.
    
    Supports three transport order types:
    - simple_road: Simple/Standard Road Freight
    - complex_road: Complex Road Freight (with parameters and order items)
    - ocean_visibility: Ocean Visibility Transport
    
    Args:
        transport_type: Type of transport order ("simple_road", "complex_road", "ocean_visibility")
        order_data: JSON string containing transport order parameters specific to the transport type
        
    Returns:
        Dict containing success status, XML content, and metadata
    """
    try:
        # Validate transport type
        if transport_type not in factory.get_available_types():
            return {
                "success": False,
                "error_type": "invalid_transport_type",
                "error_message": f"Unsupported transport type: {transport_type}",
                "available_types": factory.get_available_types()
            }
        
        # Parse order data JSON
        try:
            kwargs = json.loads(order_data)
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error_type": "invalid_json",
                "error_message": f"Invalid JSON in order_data: {str(e)}"
            }
        
        # Create generator
        generator = factory.create_generator(transport_type)
        
        # Generate XML
        result = generator.generate_xml(**kwargs)
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error_type": "system_error",
            "error_message": f"System error: {str(e)}"
        }


@app.tool()
def get_transport_type_info(transport_type: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific transport type.
    
    Args:
        transport_type: Type of transport order to get information about
        
    Returns:
        Dict containing transport type specifications and requirements
    """
    try:
        if transport_type not in factory.get_available_types():
            return {
                "success": False,
                "error_message": f"Unknown transport type: {transport_type}",
                "available_types": factory.get_available_types()
            }
        
        info = factory.get_transport_type_info(transport_type)
        
        # Get example input
        generator = factory.create_generator(transport_type)
        if hasattr(generator, 'get_example_input'):
            info["example_input"] = generator.get_example_input()
        
        info["success"] = True
        return info
        
    except Exception as e:
        return {
            "success": False,
            "error_message": f"Error getting transport type info: {str(e)}"
        }


@app.tool()
def validate_transport_order_xml(xml_content: str, transport_type: str) -> Dict[str, Any]:
    """
    Validate transport order XML content.
    
    Args:
        xml_content: XML content to validate
        transport_type: Expected transport type for business rule validation
        
    Returns:
        Dict containing validation results
    """
    try:
        # Initialize validators
        template_loader = TemplateLoader()
        structural_validator = StructuralValidator(template_loader)
        business_validator = BusinessValidator(template_loader)
        
        result = {
            "success": True,
            "is_valid": True,
            "structural_validation": {},
            "business_validation": {},
            "cross_field_validation": {},
            "errors": [],
            "warnings": []
        }
        
        # Structural validation
        structural_result = structural_validator.validate_xml_structure(xml_content)
        result["structural_validation"] = structural_result
        
        if not structural_result["is_valid"]:
            result["is_valid"] = False
            result["errors"].extend(structural_result["errors"])
        
        result["warnings"].extend(structural_result.get("warnings", []))
        
        # Field format validation
        format_result = structural_validator.validate_field_formats(xml_content)
        if not format_result["is_valid"]:
            result["is_valid"] = False
            result["errors"].extend(format_result["errors"])
        
        result["warnings"].extend(format_result.get("warnings", []))
        
        # Stop reference validation
        ref_result = structural_validator.validate_stop_references(xml_content)
        if not ref_result["is_valid"]:
            result["is_valid"] = False
            result["errors"].extend(ref_result["errors"])
        
        result["warnings"].extend(ref_result.get("warnings", []))
        
        # Business rule validation
        business_result = business_validator.validate_transport_type_rules(xml_content, transport_type)
        result["business_validation"] = business_result
        
        if not business_result["is_valid"]:
            result["is_valid"] = False
            result["errors"].extend(business_result["errors"])
        
        result["warnings"].extend(business_result.get("warnings", []))
        
        # Cross-field validation
        cross_field_result = business_validator.validate_cross_field_consistency(xml_content)
        result["cross_field_validation"] = cross_field_result
        
        if not cross_field_result["is_valid"]:
            result["is_valid"] = False
            result["errors"].extend(cross_field_result["errors"])
        
        result["warnings"].extend(cross_field_result.get("warnings", []))
        
        # Ocean-specific validation
        if transport_type == "ocean_visibility":
            ocean_result = business_validator.validate_ocean_completeness(xml_content)
            if not ocean_result["is_valid"]:
                result["is_valid"] = False
                result["errors"].extend(ocean_result["errors"])
            
            result["warnings"].extend(ocean_result.get("warnings", []))
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error_message": f"Validation error: {str(e)}"
        }


@app.tool()
def get_available_transport_types() -> Dict[str, Any]:
    """
    Get list of all available transport types with basic information.
    
    Returns:
        Dict containing available transport types and their descriptions
    """
    try:
        types = factory.get_available_types()
        type_descriptions = {
            "simple_road": "Simple/Standard Road Freight - Basic transport orders with stops, optional pricing and vehicle info",
            "complex_road": "Complex Road Freight - Advanced transport orders with order items, parameters, and carrier information",
            "ocean_visibility": "Ocean Visibility Transport - Maritime shipment tracking with mandatory ocean-specific parameters"
        }
        
        return {
            "success": True,
            "transport_types": types,
            "descriptions": {t: type_descriptions.get(t, "No description available") for t in types},
            "total_count": len(types)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error_message": f"Error getting transport types: {str(e)}"
        }


@app.tool()
def get_transport_order_example(transport_type: str) -> Dict[str, Any]:
    """
    Get example XML and input data for a specific transport type.
    
    Args:
        transport_type: Type of transport order to get example for
        
    Returns:
        Dict containing example XML, input data, and metadata
    """
    try:
        if transport_type not in factory.get_available_types():
            return {
                "success": False,
                "error_message": f"Unknown transport type: {transport_type}",
                "available_types": factory.get_available_types()
            }
        
        generator = factory.create_generator(transport_type)
        
        result = {
            "success": True,
            "transport_type": transport_type,
        }
        
        # Get example input if available
        if hasattr(generator, 'get_example_input'):
            result["example_input"] = generator.get_example_input()
        
        # Load example XML
        try:
            template_loader = TemplateLoader()
            example_xml = template_loader.load_example(transport_type)
            result["example_xml"] = example_xml
        except FileNotFoundError:
            result["example_xml"] = None
            result["warnings"] = ["Example XML file not found"]
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error_message": f"Error getting example: {str(e)}"
        }


@app.tool()
def get_parameter_requirements(transport_type: str) -> Dict[str, Any]:
    """
    Get detailed parameter requirements for a specific transport type.
    
    Args:
        transport_type: Type of transport order to get requirements for
        
    Returns:
        Dict containing parameter requirements and validation rules
    """
    try:
        if transport_type not in factory.get_available_types():
            return {
                "success": False,
                "error_message": f"Unknown transport type: {transport_type}",
                "available_types": factory.get_available_types()
            }
        
        template_loader = TemplateLoader()
        
        result = {
            "success": True,
            "transport_type": transport_type,
            "transport_parameters": template_loader.get_transport_parameters(transport_type),
            "order_parameters": template_loader.get_order_parameters(transport_type),
            "fixed_parameters": template_loader.get_fixed_parameters(transport_type)
        }
        
        # Add item parameters for complex road
        if transport_type == "complex_road":
            result["item_parameters"] = template_loader.get_item_parameters(transport_type)
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error_message": f"Error getting parameter requirements: {str(e)}"
        }


def _format_user_credentials(
    username: str,
    company_id: str,
    password: str
) -> Dict[str, Any]:
    """
    Helper function to format user credentials.
    
    Args:
        username: The user's username/login name
        company_id: The company identifier
        password: The user's password
        
    Returns:
        Dict containing formatted credentials and success status
    """
    try:
        # Validate inputs
        if not username or not username.strip():
            return {
                "success": False,
                "error_type": "invalid_input",
                "error_message": "Username cannot be empty"
            }
        
        if not company_id or not company_id.strip():
            return {
                "success": False,
                "error_type": "invalid_input",
                "error_message": "Company ID cannot be empty"
            }
        
        if not password or not password.strip():
            return {
                "success": False,
                "error_type": "invalid_input",
                "error_message": "Password cannot be empty"
            }
        
        # Clean inputs (strip whitespace)
        username = username.strip()
        company_id = company_id.strip()
        password = password.strip()
        
        # Format credentials
        credentials = f"{username}@{company_id}:{password}"
        
        return {
            "success": True,
            "credentials": credentials,
            "username": username,
            "company_id": company_id,
            "format": "username@company_id:password",
            "message": "Credentials formatted successfully"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error_type": "system_error",
            "error_message": f"Error formatting credentials: {str(e)}"
        }


@app.tool()
def get_user_credentials(
    username: str,
    company_id: str,
    password: str
) -> Dict[str, Any]:
    """
    Format user credentials for API authentication.
    
    This tool collects user credentials and formats them according to the required format:
    username@company_id:password
    
    Args:
        username: The user's username/login name
        company_id: The company identifier
        password: The user's password
        
    Returns:
        Dict containing formatted credentials and success status
    """
    return _format_user_credentials(username, company_id, password)


def _analyze_xml_content(xml_content: str) -> Dict[str, str]:
    """
    Analyze XML content to determine the correct API endpoint.
    
    Args:
        xml_content: XML content to analyze
        
    Returns:
        Dict containing message_type and endpoint_path
    """
    try:
        import xml.etree.ElementTree as ET
        
        # Parse XML to identify message type
        root = ET.fromstring(xml_content)
        
        # Remove namespace for easier matching
        tag = root.tag.split('}')[-1] if '}' in root.tag else root.tag
        
        # Check for transport_orders
        if tag == 'transport_orders' or root.find('.//*[contains(local-name(), "transport_order")]') is not None:
            return {
                "message_type": "transport_orders",
                "endpoint_path": "/v2/transport_orders"
            }
        
        # Future message types can be added here
        # Example:
        # elif tag == 'offers':
        #     return {
        #         "message_type": "offers", 
        #         "endpoint_path": "/v2/offers"
        #     }
        
        # Default fallback - could not determine message type
        return {
            "message_type": "unknown",
            "endpoint_path": None
        }
        
    except Exception as e:
        return {
            "message_type": "error",
            "endpoint_path": None,
            "error": str(e)
        }


@app.tool()
def send_xml_to_transporeon_api(
    xml_content: str,
    environment: str = "test",
    credentials: str = "",
    username: str = "",
    company_id: str = "",
    password: str = ""
) -> Dict[str, Any]:
    """
    Send XML content to the appropriate Transporeon API endpoint.
    
    This unified tool automatically:
    1. Analyzes XML content to determine the correct endpoint
    2. Handles credentials (calls get_user_credentials if needed)
    3. Posts XML to the appropriate API endpoint
    
    Supported message types:
    - transport_orders -> /v2/transport_orders
    - (more message types will be added later)
    
    Args:
        xml_content: Valid XML message (either user-provided or generated by tools like generate_transport_order_xml)
        environment: API environment ("test" or "production"), defaults to "test"
        credentials: Pre-formatted credentials (username@company_id:password). If empty, will use individual credentials
        username: Username (used only if credentials is empty)
        company_id: Company ID (used only if credentials is empty)
        password: Password (used only if credentials is empty)
        
    Returns:
        Dict containing analysis results, API response, and success status
    """
    try:
        # Step 1: Validate XML content
        if not xml_content or not xml_content.strip():
            return {
                "success": False,
                "error_type": "invalid_input",
                "error_message": "XML content cannot be empty"
            }
        
        # Step 2: Analyze XML content to determine endpoint
        print("🔍 Analyzing XML content to determine endpoint...")
        analysis = _analyze_xml_content(xml_content)
        
        if analysis.get("message_type") == "error":
            return {
                "success": False,
                "error_type": "xml_parse_error",
                "error_message": f"Failed to parse XML content: {analysis.get('error')}",
                "analysis": analysis
            }
        
        if analysis.get("message_type") == "unknown" or not analysis.get("endpoint_path"):
            return {
                "success": False,
                "error_type": "unsupported_message_type",
                "error_message": f"Unable to determine API endpoint for XML content. Supported types: transport_orders",
                "analysis": analysis
            }
        
        message_type = analysis["message_type"]
        endpoint_path = analysis["endpoint_path"]
        print(f"✅ Detected message type: {message_type} -> {endpoint_path}")
        
        # Step 3: Handle credentials - call get_user_credentials if needed
        if not credentials or not credentials.strip():
            print("🔑 No credentials provided, collecting user credentials...")
            
            # If individual credentials are provided, use them
            if username and company_id and password:
                cred_result = _format_user_credentials(username, company_id, password)
                if not cred_result.get("success"):
                    return {
                        "success": False,
                        "error_type": "credential_error",
                        "error_message": f"Failed to format credentials: {cred_result.get('error_message')}",
                        "analysis": analysis
                    }
                credentials = cred_result.get("credentials")
                print(f"✅ Credentials automatically formatted: {credentials.split(':')[0]}:***")
            else:
                # No credentials provided at all
                return {
                    "success": False,
                    "error_type": "missing_credentials",
                    "error_message": "Credentials are required. Please provide either 'credentials' parameter or 'username', 'company_id', and 'password' parameters.",
                    "required_format": "username@company_id:password",
                    "suggestion": "Use the get_user_credentials tool first to format your credentials properly.",
                    "analysis": analysis
                }
        else:
            print(f"✅ Pre-formatted credentials provided: {credentials.split(':')[0]}:***")
        
        # Step 4: Determine API base URL
        base_urls = {
            "test": "https://xch.test.transporeon.com/openapi",
            "production": "https://xch.transporeon.com/openapi"
        }
        
        if environment not in base_urls:
            return {
                "success": False,
                "error_type": "invalid_environment",
                "error_message": f"Environment must be 'test' or 'production', got: {environment}",
                "analysis": analysis
            }
        
        base_url = base_urls[environment]
        endpoint = f"{base_url}{endpoint_path}"
        
        # Step 5: Prepare authentication header
        try:
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
        except Exception as e:
            return {
                "success": False,
                "error_type": "credential_encoding_error", 
                "error_message": f"Failed to encode credentials: {str(e)}",
                "analysis": analysis
            }
        
        # Step 6: Prepare headers
        headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/xml',
            'Accept': 'application/xml'
        }
        
        # Step 7: Make API request
        try:
            print(f"🚀 Sending {message_type} XML to {environment} environment...")
            print(f"📍 Endpoint: {endpoint}")
            
            response = requests.post(
                endpoint,
                data=xml_content,
                headers=headers,
                timeout=30
            )
            
            # Step 8: Process response
            api_success = response.status_code == 202  # Expected success code for async processing
            
            result = {
                "success": api_success,
                "analysis": analysis,
                "api_response": {
                    "status_code": response.status_code,
                    "status_text": response.reason,
                    "headers": dict(response.headers),
                    "content": response.text,
                    "environment": environment,
                    "endpoint": endpoint,
                    "expected_success_code": 202
                },
                "credentials_used": credentials.split(':')[0],  # Just show username@company part
                "xml_sent_length": len(xml_content)
            }
            
            if api_success:
                result["message"] = f"✅ {message_type} successfully posted to {endpoint_path} endpoint (HTTP {response.status_code})"
                print(result["message"])
            else:
                result["error_type"] = "api_request_failed"
                result["error_message"] = f"API request failed with status {response.status_code}: {response.reason}"
                if response.status_code == 401:
                    result["error_message"] += " - Check your credentials format (username@company_id:password)"
                elif response.status_code == 413:
                    result["error_message"] += " - Batch size limit exceeded (max 1000)"
            
            return result
            
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error_type": "timeout_error",
                "error_message": "API request timed out after 30 seconds",
                "analysis": analysis
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error_type": "connection_error", 
                "error_message": "Failed to connect to Transporeon API",
                "analysis": analysis
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error_type": "request_error",
                "error_message": f"API request failed: {str(e)}",
                "analysis": analysis
            }
        
    except Exception as e:
        return {
            "success": False,
            "error_type": "system_error",
            "error_message": f"System error: {str(e)}"
        }


# Export the FastMCP app
if __name__ == "__main__":
    # Run with streamable HTTP transport for production deployment
    app.run(
        transport="http",
        host="0.0.0.0", 
        port=8000,
        path="/mcp",
        show_banner=True,
        stateless_http=True  # Enable stateless HTTP for direct POST requests
    )
