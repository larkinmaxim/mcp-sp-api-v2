"""
Business Rules Processor for Transport Orders.
Implements business rules defined in transport_parameters.json
"""

from typing import Dict, Any, List, Optional
import re


class BusinessRulesProcessor:
    """Processes and applies business rules to transport order data."""
    
    def __init__(self, template_loader):
        """Initialize with template loader to access business rules."""
        self.template_loader = template_loader
        
    def apply_business_rules(self, transport_type: str, user_input: Dict[str, Any], collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply business rules to collected data.
        
        Args:
            transport_type: Type of transport order
            user_input: Original user input (for field mapping rules)
            collected_data: Already collected transport parameters
            
        Returns:
            Modified collected_data with business rules applied
        """
        # Get business rules from the top level of transport parameters file
        all_transport_params = self.template_loader.load_parameters("transport")
        business_rules = all_transport_params.get("business_rules", [])
        
        # Create a working copy of collected data
        result = collected_data.copy()
        
        # Sort rules by priority (if specified), process mapping rules first (higher priority = later execution)
        sorted_rules = sorted(business_rules, key=lambda x: x.get("priority", 0))
        
        for rule in sorted_rules:
            if transport_type not in rule.get("applies_to", []):
                continue
                
            result = self._apply_single_rule(rule, user_input, result)
            
        return result
        
    def _apply_single_rule(self, rule: Dict[str, Any], user_input: Dict[str, Any], collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a single business rule."""
        rule_id = rule.get("id", "unknown")
        
        if rule_id == "carrier_id_mapping_rule":
            return self._apply_field_mapping_rule(rule, user_input, collected_data)
        elif rule_id == "carrier_creditor_status_rule":
            return self._apply_status_rule(rule, user_input, collected_data)
        else:
            # Generic rule processing can be added here
            return collected_data
            
    def _apply_field_mapping_rule(self, rule: Dict[str, Any], user_input: Dict[str, Any], collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply field mapping rule - maps alternative field names to standard field names.
        Example: carrier_id -> carrier_creditor_number
        """
        result = collected_data.copy()
        condition = rule.get("condition", {})
        action = rule.get("action", {})
        
        field_patterns = condition.get("field_patterns", [])
        target_field = action.get("target_field")
        
        if not target_field:
            return result
            
        # Check if target field is already set
        if target_field in result and result[target_field]:
            # Target field already has a value, don't override
            return result
            
        # Look for any of the pattern fields in user input
        for pattern in field_patterns:
            if pattern in user_input and user_input[pattern]:
                # Map the field value
                result[target_field] = user_input[pattern]
                print(f"Applied field mapping rule: {pattern} -> {target_field} = {user_input[pattern]}")
                break
                
        return result
        
    def _apply_status_rule(self, rule: Dict[str, Any], user_input: Dict[str, Any], collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply status rule - if carrier_creditor_number has value then status is NTO.
        """
        result = collected_data.copy()
        condition = rule.get("condition", {})
        action = rule.get("action", {})
        
        condition_field = condition.get("field")
        condition_operator = condition.get("operator")
        action_field = action.get("field")
        action_value = action.get("value")
        
        if not all([condition_field, condition_operator, action_field, action_value]):
            return result
            
        # Check condition
        if condition_operator == "has_value":
            if condition_field in result and result[condition_field]:
                # Condition met: field has a value
                result[action_field] = action_value
                print(f"Applied status rule: {condition_field} has value -> {action_field} = {action_value}")
                
        return result
        
    def get_business_rules_summary(self, transport_type: str) -> List[Dict[str, str]]:
        """Get a summary of business rules for a transport type."""
        all_transport_params = self.template_loader.load_parameters("transport")
        business_rules = all_transport_params.get("business_rules", [])
        
        summary = []
        for rule in business_rules:
            if transport_type in rule.get("applies_to", []):
                summary.append({
                    "id": rule.get("id", "unknown"),
                    "description": rule.get("description", "No description"),
                    "priority": rule.get("priority", 0)
                })
                
        return summary
