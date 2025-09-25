"""
Transport Order XML Generator Tool

A FastMCP-based tool for generating valid transport order XML files
based on user input. Supports three transport order types:
- Simple/Standard Road Freight
- Complex Road Freight (with parameters)
- Ocean Visibility Transport
"""

from .main_tool import generate_transport_order_xml

__version__ = "1.0.0"
__author__ = "Transport Order Generator"

__all__ = ["generate_transport_order_xml"]
