"""Element Formatter for Playwright adapters.

Responsibilities:
- Format element information for readable logging
- Create structured element descriptions
"""
from typing import Any, Dict


class ElementFormatter:
    """Handles element information formatting for logs."""

    def format_element_info(self, element_info: Dict[str, Any]) -> str:
        """
        Format element information for readable logging.

        Args:
            element_info: Dictionary with element details

        Returns:
            Formatted string with key element attributes
        """
        if not element_info:
            return ""

        parts = []

        # Tag name with type (most important)
        tag = element_info.get('tag', 'unknown')
        elem_type = element_info.get('type', '')

        if elem_type:
            parts.append(f"<{tag}[type={elem_type}]>")
        else:
            parts.append(f"<{tag}>")

        # ID (very useful for identification)
        elem_id = element_info.get('id', '')
        if elem_id:
            parts.append(f"id=\"{elem_id}\"")

        # Name attribute (common for forms)
        elem_name = element_info.get('name', '')
        if elem_name:
            parts.append(f"name=\"{elem_name}\"")

        # ARIA label (accessibility & identification)
        aria_label = element_info.get('aria_label', '')
        if aria_label:
            parts.append(f"aria-label=\"{aria_label}\"")

        # Role (accessibility context)
        role = element_info.get('role', '')
        if role:
            parts.append(f"role=\"{role}\"")

        # Text content (what user sees)
        text = element_info.get('text', '')
        if text:
            parts.append(f"text=\"{text}\"")

        # Placeholder (for inputs)
        placeholder = element_info.get('placeholder', '')
        if placeholder:
            parts.append(f"placeholder=\"{placeholder}\"")

        return " | ".join(parts)
