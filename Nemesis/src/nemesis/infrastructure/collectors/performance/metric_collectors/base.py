"""Base collector class for performance metrics."""
import traceback
from abc import ABC, abstractmethod
from typing import Any

from playwright.sync_api import Page

from nemesis.infrastructure.logging import Logger


class BaseMetricCollector(ABC):
    """Abstract base class for metric collectors."""

    def __init__(self, page: Page, logger: Logger) -> None:
        """
        Initialize collector.

        :param page: Playwright page object
        :param logger: Logger instance
        """
        self.page = page
        self.logger = logger

    @abstractmethod
    def collect(self) -> Any:
        """
        Collect metrics.

        :return: Collected metrics
        """

    def _safe_evaluate(self, script: str, default: Any = None) -> Any:
        """
        Safely evaluate JavaScript with error handling.

        :param script: JavaScript code to evaluate
        :param default: Default value if evaluation fails
        :return: Evaluation result or default
        """
        try:
            return self.page.evaluate(script)
        except (RuntimeError, AttributeError) as e:
            # Playwright API errors or JavaScript evaluation errors
            self.logger.debug(f"Evaluation failed: {e}", traceback=traceback.format_exc(), module=__name__, class_name="BaseMetricCollector", method="_safe_evaluate")
            return default if default is not None else {}
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from Playwright evaluate
            # NOTE: page.evaluate may raise various exceptions (JavaScript errors, API errors) we cannot predict
            self.logger.debug(f"Evaluation failed: {e}", traceback=traceback.format_exc(), module=__name__, class_name="BaseMetricCollector", method="_safe_evaluate")
            return default if default is not None else {}

    def _round_metric(self, value: float, decimals: int = 2) -> float:
        """Round metric to specified decimal places."""
        return round(value, decimals)
