"""
Template loader utility for loading and caching XML templates.
"""

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path


class TemplateLoader:
    """Loads and caches XML templates and parameter configurations."""
    
    def __init__(self, data_path: Optional[str] = None):
        """Initialize template loader with data directory path."""
        if data_path is None:
            # Default to data directory relative to this file
            current_dir = Path(__file__).parent.parent.parent
            data_path = current_dir / "data"
        
        self.data_path = Path(data_path)
        self._template_cache: Dict[str, str] = {}
        self._parameter_cache: Dict[str, Dict[str, Any]] = {}
        self._validation_cache: Dict[str, Dict[str, Any]] = {}
        
        # Validate data directory exists
        if not self.data_path.exists():
            raise FileNotFoundError(f"Data directory not found: {self.data_path}")
        
        self._validate_templates_on_startup()
    
    def _validate_templates_on_startup(self) -> None:
        """Pre-validate templates at startup to catch errors early."""
        templates_dir = self.data_path / "templates"
        if not templates_dir.exists():
            raise FileNotFoundError(f"Templates directory not found: {templates_dir}")
        
        required_templates = ["simple_road.xml", "complex_road.xml", "ocean_visibility.xml"]
        for template_file in required_templates:
            template_path = templates_dir / template_file
            if not template_path.exists():
                raise FileNotFoundError(f"Required template not found: {template_path}")
    
    def load_template(self, transport_type: str) -> str:
        """Load XML template for the specified transport type."""
        if transport_type not in self._template_cache:
            template_path = self.data_path / "templates" / f"{transport_type}.xml"
            
            if not template_path.exists():
                raise FileNotFoundError(f"Template not found: {template_path}")
            
            with open(template_path, 'r', encoding='utf-8') as f:
                self._template_cache[transport_type] = f.read()
        
        return self._template_cache[transport_type]
    
    def load_parameters(self, parameter_type: str) -> Dict[str, Any]:
        """Load parameter configuration for the specified type."""
        cache_key = f"parameters_{parameter_type}"
        
        if cache_key not in self._parameter_cache:
            param_path = self.data_path / "parameters" / f"{parameter_type}_parameters.json"
            
            if not param_path.exists():
                raise FileNotFoundError(f"Parameter file not found: {param_path}")
            
            with open(param_path, 'r', encoding='utf-8') as f:
                self._parameter_cache[cache_key] = json.load(f)
        
        return self._parameter_cache[cache_key]
    
    def load_validation_rules(self, validation_type: str) -> Dict[str, Any]:
        """Load validation rules for the specified type."""
        cache_key = f"validation_{validation_type}"
        
        if cache_key not in self._validation_cache:
            validation_path = self.data_path / "validation" / f"{validation_type}_rules.json"
            
            if not validation_path.exists():
                raise FileNotFoundError(f"Validation file not found: {validation_path}")
            
            with open(validation_path, 'r', encoding='utf-8') as f:
                self._validation_cache[cache_key] = json.load(f)
        
        return self._validation_cache[cache_key]
    
    def get_transport_parameters(self, transport_type: str) -> Dict[str, Any]:
        """Get transport-specific parameter definitions."""
        transport_params = self.load_parameters("transport")
        return transport_params.get(transport_type, {})
    
    def get_order_parameters(self, transport_type: str) -> Dict[str, Any]:
        """Get order-specific parameter definitions."""
        order_params = self.load_parameters("order")
        return order_params.get(transport_type, {})
    
    def get_fixed_parameters(self, transport_type: str) -> Dict[str, Any]:
        """Get fixed parameter definitions."""
        fixed_params = self.load_parameters("fixed")
        return fixed_params.get(transport_type, {})
    
    def get_item_parameters(self, transport_type: str) -> Dict[str, Any]:
        """Get item-specific parameter definitions."""
        item_params = self.load_parameters("item")
        return item_params.get(transport_type, {})
    
    def load_example(self, transport_type: str) -> str:
        """Load example XML for the specified transport type."""
        example_path = self.data_path / "examples" / f"{transport_type}_example.xml"
        
        if not example_path.exists():
            raise FileNotFoundError(f"Example file not found: {example_path}")
        
        with open(example_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def clear_cache(self) -> None:
        """Clear all cached templates and parameters."""
        self._template_cache.clear()
        self._parameter_cache.clear()
        self._validation_cache.clear()
    
    def get_available_transport_types(self) -> list:
        """Get list of available transport types based on templates."""
        templates_dir = self.data_path / "templates"
        transport_types = []
        
        for template_file in templates_dir.glob("*.xml"):
            transport_type = template_file.stem
            transport_types.append(transport_type)
        
        return sorted(transport_types)
