"""
@ai-metadata {
    "domain": "metadata-schema",
    "description": "Schema definition for ADP metadata format with dynamic customization"
}
"""

import os
import yaml
import json
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
import jsonschema

# Registry for storing multiple schemas
_schema_registry: Dict[str, Dict[str, Any]] = {}
_active_schema_name: str = "default"

@dataclass
class ADPMetadata:
    """Class representing ADP metadata extracted from a file."""
    metadata: dict
    file_path: str
    line_number: int
    scope: str = "file"

@dataclass
class ADPSchema:
    """Schema class for ADP metadata."""
    name: str
    schema: Dict[str, Any]
    description: str = ""
    version: str = "1.0.0"
    validators: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize validators after instance creation."""
        self.validators["jsonschema"] = jsonschema.Draft7Validator(self.schema)
    
    def validate(self, metadata: Dict[str, Any]) -> bool:
        """Validate metadata against this schema."""
        try:
            self.validators["jsonschema"].validate(metadata)
            return True
        except jsonschema.exceptions.ValidationError:
            return False
    
    def get_validation_errors(self, metadata: Dict[str, Any]) -> List[str]:
        """Get detailed validation errors for metadata."""
        errors = []
        for error in self.validators["jsonschema"].iter_errors(metadata):
            errors.append(f"{error.message} at {'/'.join(str(p) for p in error.path)}")
        return errors
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ADPSchema':
        """Create a schema from a dictionary."""
        return cls(
            name=data.get("name", "custom"),
            schema=data.get("schema", {}),
            description=data.get("description", ""),
            version=data.get("version", "1.0.0")
        )
    
    @classmethod
    def from_file(cls, file_path: str) -> 'ADPSchema':
        """Create a schema from a file (YAML or JSON)."""
        with open(file_path, 'r', encoding='utf-8') as f:
            if file_path.endswith('.yaml') or file_path.endswith('.yml'):
                data = yaml.safe_load(f)
            else:
                data = json.load(f)
        return cls.from_dict(data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the schema to a dictionary."""
        return {
            "name": self.name,
            "schema": self.schema,
            "description": self.description,
            "version": self.version
        }
    
    def save_to_file(self, file_path: str) -> None:
        """Save the schema to a file (YAML or JSON)."""
        data = self.to_dict()
        with open(file_path, 'w', encoding='utf-8') as f:
            if file_path.endswith('.yaml') or file_path.endswith('.yml'):
                yaml.dump(data, f, default_flow_style=False)
            else:
                json.dump(data, f, indent=2)


# Default schema definition
_DEFAULT_SCHEMA = {
    "type": "object",
    "properties": {
        # Core fields
        "name": {"type": "string", "description": "Name of the component or entity"},
        "domain": {"type": "string", "description": "Business domain context"},
        "complexity": {"type": "string", "description": "Time/space complexity"},
        "thread-safety": {"type": "boolean", "description": "Thread safety guarantees"},
        "memory-footprint": {"type": "string", "description": "Memory usage characteristics"},
        "dependencies": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Component dependencies"
        },
        "invariants": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Conditions that must be maintained"
        },
        "description": {"type": "string", "description": "Detailed description"},
        
        # Service boundary fields
        "service-boundary": {"type": "string", "description": "Service this component belongs to"},
        "permitted-dependencies": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Services this component is allowed to depend on"
        },
        "prohibited-dependencies": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Services this component must not depend on"
        },
        
        # Tech debt group
        "tech-debt": {
            "type": "object",
            "properties": {
                "severity": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Severity of the technical debt"
                },
                "type": {"type": "string", "description": "Type of technical debt"},
                "threshold": {"type": "string", "description": "Threshold at which this becomes critical"},
                "refactor-ticket": {"type": "string", "description": "Ticket reference for refactoring"},
                "business-impact": {"type": "string", "description": "Impact on business"}
            }
        },
        
        # Performance group
        "performance": {
            "type": "object",
            "properties": {
                "max-latency": {"type": "string", "description": "Maximum allowed latency"},
                "throughput": {"type": "string", "description": "Expected throughput"},
                "hot-path": {"type": "boolean", "description": "Whether this is on the hot path"},
                "optimization-priority": {"type": "string", "description": "What to optimize for"},
                "bottlenecks": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Known bottlenecks"
                }
            }
        },
        
        # Data handling group
        "data-handling": {
            "type": "object",
            "properties": {
                "pii-fields": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Fields containing personally identifiable information"
                },
                "required-anonymization": {"type": "string", "description": "Anonymization requirements"},
                "storage-requirements": {"type": "string", "description": "Data storage requirements"},
                "retention-policy": {"type": "string", "description": "Data retention policy"}
            }
        }
    }
}

# Initialize the registry with the default schema
_schema_registry["default"] = ADPSchema(
    name="default",
    schema=_DEFAULT_SCHEMA,
    description="Default ADP metadata schema",
    version="1.0.0"
)


def register_schema(schema: Union[ADPSchema, Dict[str, Any], str]) -> ADPSchema:
    """
    Register a new schema with the registry.
    
    Args:
        schema: Either an ADPSchema instance, a dictionary with schema definition,
               or a path to a schema file.
    
    Returns:
        The registered schema instance.
    """
    if isinstance(schema, str) and os.path.exists(schema):
        schema_obj = ADPSchema.from_file(schema)
    elif isinstance(schema, dict):
        schema_obj = ADPSchema.from_dict(schema)
    elif isinstance(schema, ADPSchema):
        schema_obj = schema
    else:
        raise ValueError("Invalid schema type. Expected ADPSchema, dict, or file path.")
    
    _schema_registry[schema_obj.name] = schema_obj
    return schema_obj


def get_schema(name: str = None) -> ADPSchema:
    """
    Get a schema from the registry.
    
    Args:
        name: Name of the schema to get. If None, returns the active schema.
    
    Returns:
        The requested schema.
    """
    name = name or _active_schema_name
    if name not in _schema_registry:
        raise ValueError(f"Schema '{name}' not found in registry")
    return _schema_registry[name]


def set_active_schema(name: str) -> None:
    """
    Set the active schema by name.
    
    Args:
        name: Name of the schema to set as active.
    """
    global _active_schema_name
    if name not in _schema_registry:
        raise ValueError(f"Schema '{name}' not found in registry")
    _active_schema_name = name


def get_default_schema() -> ADPSchema:
    """
    Get the default schema.
    
    Returns:
        The default schema.
    """
    return _schema_registry["default"]


def load_schema(file_path: str) -> ADPSchema:
    """
    Load a schema from a file and register it.
    
    Args:
        file_path: Path to the schema file.
    
    Returns:
        The loaded schema.
    """
    schema = ADPSchema.from_file(file_path)
    _schema_registry[schema.name] = schema
    return schema 