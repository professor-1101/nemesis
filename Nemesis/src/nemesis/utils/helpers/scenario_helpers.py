"""Helper functions for scenario status normalization."""

from typing import Any


def normalize_scenario_status(scenario: Any, status: Any = None) -> str:
    """Normalize scenario status to standard format.
    
    Args:
        scenario: Scenario object from Behave
        status: Optional status string or object
        
    Returns:
        Normalized status string ("passed" or "failed")
    """
    if status is None:
        scenario_status = getattr(scenario, 'status', None)
        if hasattr(scenario_status, 'name'):
            status = scenario_status.name  # "passed" or "failed"
        elif isinstance(scenario_status, str):
            status = scenario_status.lower()
        else:
            status = "passed"

    # Normalize to lowercase
    status_lower = status.lower()
    if status_lower in ("passed", "pass"):
        return "passed"
    elif status_lower in ("failed", "fail"):
        return "failed"
    elif status_lower in ("skipped", "skip"):
        return "skipped"
    else:
        return "passed"  # Default fallback


def normalize_scenario_status_for_rp(scenario: Any, status: Any = None) -> str:
    """Normalize scenario status to ReportPortal format (uppercase).

    Args:
        scenario: Scenario object from Behave
        status: Optional status string or object

    Returns:
        Normalized status string ("PASSED", "FAILED", or "SKIPPED")
    """
    normalized = normalize_scenario_status(scenario, status)
    if normalized == "skipped":
        return "SKIPPED"
    else:
        return normalized.upper()
