"""Configuration validator for Nemesis CLI."""
from typing import Any, Dict, List

from .schema import (
    BEHAVE_SCHEMA,
    LOGGING_SCHEMA,
    PLAYWRIGHT_SCHEMA,
    REPORTPORTAL_SCHEMA,
    REPORTING_SCHEMA,
)


class ConfigValidator:
    """Validate configuration against schemas."""

    def validate(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate complete configuration.

        Args:
            config: Configuration dictionary

        Returns:
            Validation result with errors
        """
        errors = []

        # Validate each section
        if "playwright" in config:
            errors.extend(self._validate_section(config["playwright"], PLAYWRIGHT_SCHEMA, "playwright"))

        if "reportportal" in config:
            errors.extend(self._validate_section(config["reportportal"], REPORTPORTAL_SCHEMA, "reportportal"))

        if "behave" in config:
            errors.extend(self._validate_section(config["behave"], BEHAVE_SCHEMA, "behave"))

        if "logging" in config:
            errors.extend(self._validate_section(config["logging"], LOGGING_SCHEMA, "logging"))

        if "reporting" in config:
            errors.extend(self._validate_section(config["reporting"], REPORTING_SCHEMA, "reporting"))

        return {
            "valid": len(errors) == 0,
            "errors": errors,
        }

    def _validate_section(
            self,
            config: Dict[str, Any],
            schema: Dict[str, Any],
            section_name: str
    ) -> List[str]:
        """Validate a configuration section against its schema.

        Args:
            config: Configuration section
            schema: Schema definition
            section_name: Name of section for error messages

        Returns:
            List of validation errors
        """
        errors = []

        # Check required fields
        required = schema.get("required", [])
        for field in required:
            if field not in config:
                errors.append(f"{section_name}.{field} is required but missing")

        # Check field types and values
        fields = schema.get("fields", {})
        for field_name, field_schema in fields.items():
            if field_name in config:
                value = config[field_name]
                field_errors = self._validate_field(
                    value,
                    field_schema,
                    f"{section_name}.{field_name}"
                )
                errors.extend(field_errors)

        return errors

    def _validate_field(
            self,
            value: Any,
            schema: Dict[str, Any],
            field_path: str
    ) -> List[str]:
        """Validate a single field.

        Args:
            value: Field value
            schema: Field schema
            field_path: Full path to field for error messages

        Returns:
            List of validation errors
        """
        errors = []

        # Type validation
        expected_type = schema.get("type")
        if expected_type:
            if expected_type == "string" and not isinstance(value, str):
                errors.append(f"{field_path} must be a string")
            elif expected_type == "integer" and not isinstance(value, int):
                errors.append(f"{field_path} must be an integer")
            elif expected_type == "boolean" and not isinstance(value, bool):
                errors.append(f"{field_path} must be a boolean")
            elif expected_type == "dict" and not isinstance(value, dict):
                errors.append(f"{field_path} must be a dictionary")
            elif expected_type == "list" and not isinstance(value, list):
                errors.append(f"{field_path} must be a list")

        # Enum validation
        if "enum" in schema:
            if value not in schema["enum"]:
                valid_values = ", ".join(str(v) for v in schema["enum"])
                errors.append(f"{field_path} must be one of: {valid_values}")

        # Range validation
        if "min" in schema and isinstance(value, (int, float)):
            if value < schema["min"]:
                errors.append(f"{field_path} must be >= {schema['min']}")

        if "max" in schema and isinstance(value, (int, float)):
            if value > schema["max"]:
                errors.append(f"{field_path} must be <= {schema['max']}")

        # Nested object validation
        if expected_type == "dict" and "fields" in schema:
            nested_errors = self._validate_section(value, schema, field_path)
            errors.extend(nested_errors)

        return errors
