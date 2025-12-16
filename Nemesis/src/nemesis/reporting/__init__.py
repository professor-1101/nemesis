"""Reporting module for Nemesis test automation framework.

This module provides integration with various reporting systems including
ReportPortal for centralized test result management.
"""
from .reportportal import ReportPortalClient  # noqa: F401

__all__ = ['ReportPortalClient']
