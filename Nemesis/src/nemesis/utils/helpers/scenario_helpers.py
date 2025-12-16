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
    return "passed" if status.lower() in ("passed", "pass") else "failed"


def normalize_scenario_status_for_rp(scenario: Any, status: Any = None) -> str:
    """Normalize scenario status to ReportPortal format (uppercase).
    
    Args:
        scenario: Scenario object from Behave
        status: Optional status string or object
        
    Returns:
        Normalized status string ("PASSED" or "FAILED")
    """
    normalized = normalize_scenario_status(scenario, status)
    return normalized.upper()
