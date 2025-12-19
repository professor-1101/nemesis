"""Artifact handling service for test execution"""

from pathlib import Path
from typing import List, Optional

from nemesis.domain.entities import Step, Scenario
from nemesis.domain.ports import IBrowserDriver, IReporter


class ArtifactHandler:
    """Handles artifact capture and storage (screenshots, videos, traces)"""

    def __init__(
        self,
        browser_driver: IBrowserDriver,
        reporters: List[IReporter],
        output_dir: Path,
    ):
        """
        Initialize artifact handler

        Args:
            browser_driver: Browser driver for capturing artifacts
            reporters: List of reporters to notify
            output_dir: Base directory for artifacts
        """
        self.browser_driver = browser_driver
        self.reporters = reporters
        self.output_dir = Path(output_dir)

    def capture_screenshot_on_failure(
        self,
        step: Step,
        scenario: Scenario,
    ) -> Optional[Path]:
        """
        Capture screenshot when step fails

        Args:
            step: Failed step entity
            scenario: Parent scenario entity

        Returns:
            Path to saved screenshot, or None if capture failed
        """
        try:
            screenshot_path = (
                self.output_dir
                / "screenshots"
                / f"{scenario.scenario_id}_{step.step_id}.png"
            )
            screenshot_path.parent.mkdir(parents=True, exist_ok=True)

            # Capture screenshot using browser driver interface
            if self.browser_driver and self.browser_driver.is_running():
                screenshot_bytes = self.browser_driver.capture_screenshot()

                if screenshot_bytes:
                    screenshot_path.write_bytes(screenshot_bytes)

                    # Notify reporters about the screenshot
                    for reporter in self.reporters:
                        reporter.attach_file(
                            screenshot_path,
                            description=f"Screenshot at step: {step.name}",
                            attachment_type="image/png"
                        )
                        reporter.log_message(
                            f"Screenshot captured: {screenshot_path}",
                            level="INFO"
                        )

                    return screenshot_path

        except Exception as e:
            # Log error but don't fail the test
            for reporter in self.reporters:
                reporter.log_message(
                    f"Failed to capture screenshot: {str(e)}",
                    level="WARNING"
                )

        return None
