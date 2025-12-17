"""Screenshot attachment management."""

from nemesis.infrastructure.logging import Logger


class ScreenshotManager:
    """Manages screenshot attachments."""

    def __init__(self, reporter_manager, execution_manager):
        """Initialize screenshot manager."""
        self.logger = Logger.get_instance({})
        self.reporter_manager = reporter_manager
        self.execution_manager = execution_manager

    def attach_screenshot(self, screenshot: bytes, name: str) -> None:
        """Attach screenshot to reports."""
        try:
            # Save to disk
            screenshot_path = self.execution_manager.get_execution_path() / "screenshots" / f"{name}.png"
            screenshot_path.parent.mkdir(parents=True, exist_ok=True)

            with open(screenshot_path, "wb") as f:
                f.write(screenshot)

            self.logger.debug(f"Screenshot saved: {screenshot_path.name}")

            # Attach to LocalReporter
            if self.reporter_manager.is_local_enabled():
                try:
                    self.reporter_manager.get_local_reporter().add_screenshot(screenshot_path, f"Screenshot: {name}")
                except (AttributeError, RuntimeError) as e:
                    # Local reporter API errors - non-critical
                    self.logger.debug(f"Failed to add screenshot to local reporter - API error: {e}", exc_info=True)
                except (OSError, IOError) as e:
                    # File I/O errors from screenshot_path access - non-critical
                    self.logger.debug(f"Failed to add screenshot to local reporter - I/O error: {e}", exc_info=True)
                except (KeyboardInterrupt, SystemExit):
                    # Allow program interruption to propagate
                    raise
                except Exception as e:  # pylint: disable=broad-exception-caught
                    # Catch-all for unexpected errors from local reporter
                    # NOTE: LocalReporter.add_screenshot may raise various exceptions we cannot predict
                    self.logger.debug(f"Failed to add screenshot to local reporter: {e}", exc_info=True)

            # Attach to ReportPortal
            if self.reporter_manager.is_rp_enabled():
                try:
                    self.reporter_manager.get_rp_client().attach_file(screenshot_path, f"Screenshot: {name}", "screenshot")
                except (AttributeError, RuntimeError) as e:
                    # ReportPortal attachment API errors - non-critical
                    self.logger.debug(f"Failed to attach screenshot to RP - API error: {e}", exc_info=True)
                except (OSError, IOError) as e:
                    # File I/O errors from screenshot_path access - non-critical
                    self.logger.debug(f"Failed to attach screenshot to RP - I/O error: {e}", exc_info=True)
                except (KeyboardInterrupt, SystemExit):
                    # Allow program interruption to propagate
                    raise
                except Exception as e:  # pylint: disable=broad-exception-caught
                    # Catch-all for unexpected errors from ReportPortal SDK
                    # NOTE: ReportPortal SDK may raise various exceptions we cannot predict
                    self.logger.debug(f"Failed to attach screenshot to RP: {e}", exc_info=True)

        except (OSError, IOError, PermissionError) as e:
            # File I/O errors - directory creation or file write failed
            self.logger.error(f"Failed to save screenshot - I/O error: {e}", exc_info=True)
        except (KeyboardInterrupt, SystemExit):
            # Allow program interruption to propagate
            raise
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from file operations
            # NOTE: File operations or directory creation may raise various exceptions we cannot predict
            self.logger.error(f"Failed to save screenshot: {e}", exc_info=True)
