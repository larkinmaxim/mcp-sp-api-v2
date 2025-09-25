# Transport Order XML Generator Tool

A FastMCP-based tool that generates valid transport order XML files based on user input. Supports three transport order types: Simple/Standard Road Freight, Complex Road Freight (with parameters), and Ocean Visibility Transport.

## Features

- **Three Transport Types**: Simple Road, Complex Road, and Ocean Visibility
- **Smart Parameter Collection**: Context-aware user input collection
- **XML DOM Manipulation**: Reliable and valid XML generation
- **Hybrid Validation**: Structural and business rule validation
- **Factory Pattern Architecture**: Clean, extensible code organization

## Architecture

```
/tools/
├── __init__.py
├── main_tool.py                 # FastMCP tool definitions
├── generators/
│   ├── __init__.py
│   ├── base_generator.py        # Base generator class
│   ├── simple_road.py           # Simple road freight generator
│   ├── complex_road.py          # Complex road freight generator
│   └── ocean_visibility.py      # Ocean transport generator
├── validation/
│   ├── __init__.py
│   ├── structural_validator.py  # XML structure validation
│   └── business_validator.py    # Business rule validation
├── utils/
│   ├── __init__.py
│   ├── template_loader.py       # Template loading utilities
│   ├── xml_builder.py          # XML DOM manipulation
│   └── parameter_collector.py   # Smart parameter collection
└── data/                        # Configuration and templates
    ├── templates/               # XML templates
    ├── parameters/             # Parameter definitions
    ├── validation/             # Validation rules
    └── examples/              # Reference examples
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the FastMCP server:

**Development (stdio transport):**
```bash
python tools/main_tool.py
```

**Production (streamable HTTP transport):**
```bash
python server.py
```

**ASGI deployment with Uvicorn:**
```bash
uvicorn asgi_app:asgi_app --host 0.0.0.0 --port 8000
```

**ASGI deployment with Gunicorn:**
```bash
gunicorn asgi_app:asgi_app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Available Tools

### 1. generate_transport_order_xml
Generate valid transport order XML based on user input.

**Parameters:**
- `transport_type`: "simple_road", "complex_road", or "ocean_visibility"
- Additional parameters specific to transport type

### 2. validate_transport_order_xml
Validate existing transport order XML content.

**Parameters:**
- `xml_content`: XML string to validate
- `transport_type`: Expected transport type

### 3. get_transport_type_info
Get detailed information about a specific transport type.

**Parameters:**
- `transport_type`: Transport type to get info for

### 4. get_available_transport_types
Get list of all available transport types.

### 5. get_transport_order_example
Get example XML and input data for a transport type.

**Parameters:**
- `transport_type`: Transport type to get example for

### 6. get_parameter_requirements
Get detailed parameter requirements for a transport type.

**Parameters:**
- `transport_type`: Transport type to get requirements for

## Transport Types

### Simple Road Freight
Basic transport orders with stops, optional pricing, and vehicle information.

**Required Fields:**
- number, status, scheduling_unit
- At least 2 stops (loading and unloading)

**Optional Fields:**
- vehicle, pricing, weight, distance, comments, custom parameters

### Complex Road Freight  
Advanced transport orders with order items, parameters, and carrier information.

**Required Fields:**
- number, status, scheduling_unit, carrier_creditor_number
- Order items with quantities and parameters

**Features:**
- Hierarchical parameters (transport, order, item levels)
- Carrier creditor number validation
- Extensive parameter support

### Ocean Visibility Transport
Maritime shipment tracking with mandatory ocean-specific parameters.

**Fixed Values:**
- scheduling_unit: "Ocean Visibility"
- carrier_creditor_number: "Ocean"  
- status: "NTO"

**Required Parameters:**
- ocean.scac.no (4-character SCAC code)
- ocean.bl.no (Bill of Lading number)
- ocean.container.no (Container number)
- visibility.ocean.product: "true"

## Example Usage

### Simple Road Freight
```python
result = generate_transport_order_xml(
    transport_type="simple_road",
    number="1404338",
    status="N", 
    scheduling_unit="Wörth",
    vehicle="MEGA:Stehend",
    price_reference=845.0,
    loading_stop_ids=["1"],
    unloading_stop_ids=["2"],
    stops=[
        {
            "id": "1",
            "location": {
                "company_name": "Loading Company",
                "city": "Loading City",
                "country": "DE"
            },
            "date_time_period": {
                "start": "2025-09-25T00:00:00+02:00",
                "end": "2025-09-25T23:59:00+02:00"
            }
        },
        # ... unloading stop
    ]
)
```

### Ocean Visibility
```python
result = generate_transport_order_xml(
    transport_type="ocean_visibility",
    number="4500831479-20",
    **{
        "ocean.scac.no": "MAEU",
        "ocean.bl.no": "MAEU258327258", 
        "ocean.container.no": "MMAU1291440",
        "departure_location": {
            "company_name": "Port of Origin",
            "city": "Origin City",
            "country": "VN"
        },
        "arrival_location": {
            "company_name": "Port of Destination", 
            "city": "Destination City",
            "country": "DE"
        },
        # ... date periods
    }
)
```

## Validation

The tool includes comprehensive validation:

- **Structural Validation**: XML well-formedness, required elements, format validation
- **Business Rule Validation**: Transport-specific rules, parameter restrictions
- **Cross-field Validation**: Consistency checks, date sequences, stop references

## Error Handling

All tools return structured responses with:
- `success`: Boolean indicating operation success
- `error_type`: Category of error if any
- `errors`: List of error messages
- `warnings`: List of warning messages
- `missing_required`: Required fields that need to be provided

## Development

### Adding New Transport Types

1. Create generator class extending `BaseGenerator`
2. Add templates and parameter configurations
3. Update factory registration
4. Add validation rules

### Extending Validation

1. Update validation rule JSON files
2. Implement custom validation methods
3. Add business-specific logic

## License

This tool is part of the Transport Order Management system.
