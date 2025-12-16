"""ReportPortal launch management module.

This module manages ReportPortal launch lifecycle, handling starting and finishing
launches, managing launch attributes, and coordinating the overall test execution.
"""
import time
import traceback
from datetime import datetime
from typing import Any, Dict, List

from reportportal_client import RPClient

from nemesis.core.exceptions import ReportPortalError
from nemesis.core.logging import Logger
from nemesis.utils.decorators import retry
from .rp_client_base import RPClientBase


class RPLaunchManager:
    """
    Manager for ReportPortal launches.

    Responsibilities:
    - Start launch with retry and logging
    - Finish launch safely
    - Provide launch ID and URL
    - Fully compatible with RPClient
    """

    def __init__(
        self,
        rp_client_base: RPClientBase,
        launch_name: str,
        launch_description: str | None = None,
        launch_attributes: List[Dict[str, Any]] | None = None,
    ) -> None:
        self.rp_client_base = rp_client_base
        self.client: RPClient = rp_client_base.client
        self.logger = Logger.get_instance({})
        self.launch_id: str | None = None
        self.launch_name = launch_name
        self.launch_description = launch_description
        self.launch_attributes = self._normalize_attributes(launch_attributes)

    @staticmethod
    def _normalize_attributes(attrs: List[Dict[str, Any]] | None) -> List[Dict[str, Any]]:
        """Ensure all attributes have 'key', 'value', and 'system' fields."""
        normalized = []
        for attr in attrs or []:
            normalized.append({
                "key": attr.get("key") or "tag",
                "value": attr.get("value") or "",
                "system": attr.get("system", False)
            })
        return normalized

    @staticmethod
    def _current_timestamp_ms() -> str:
        """Return current timestamp in milliseconds as string."""
        return str(int(datetime.now().timestamp() * 1000))

    @retry(max_attempts=3, delay=1.0)
    def start_launch(self) -> None:
        """
        Start a new launch in ReportPortal using RPClient.
        Sets self.launch_id for future operations.
        """
        # If launch is already active, don't start a new one
        if self.launch_id:
            self.logger.warning(f"Launch already active: {self.launch_id}, skipping start")
            return

        try:
            launch_id = self.client.start_launch(
                name=self.launch_name,
                start_time=self._current_timestamp_ms(),
                description=self.launch_description,
                attributes=self.launch_attributes,
                mode="DEFAULT",
                rerun=False,
            )

            # RPClient may not return launch_id; fallback to internal state
            self.launch_id = launch_id or getattr(self.client, "launch_id", None)

            if not self.launch_id:
                raise ReportPortalError(
                    "Launch ID not set by RPClient",
                    "RPClient did not return launch_id after start_launch",
                )

            self.logger.info(f"ReportPortal launch started: {self.launch_id}")

            # Store launch_id in EnvironmentManager for cross-process access
            try:
                from nemesis.environment.hooks import _get_env_manager  # pylint: disable=import-outside-toplevel
                env_manager = _get_env_manager()
                if env_manager:
                    # Store launch_id in EnvironmentManager instance
                    if not hasattr(env_manager, 'rp_launch_id'):
                        env_manager.rp_launch_id = None
                    env_manager.rp_launch_id = self.launch_id
                    self.logger.debug(f"Stored launch_id in EnvironmentManager: {self.launch_id}")
            except (AttributeError, ImportError) as store_error:
                # Non-critical: failed to store launch_id in EnvironmentManager
                self.logger.debug(f"Failed to store launch_id in EnvironmentManager (non-critical): {store_error}", module=__name__, class_name="RPLaunchManager", method="start_launch")
            except Exception as store_error:  # pylint: disable=broad-exception-caught
                # Catch-all for unexpected errors from EnvironmentManager access
                # NOTE: EnvironmentManager import or access may raise various exceptions
                self.logger.debug(f"Failed to store launch_id in EnvironmentManager (non-critical): {store_error}", module=__name__, class_name="RPLaunchManager", method="start_launch")

        except (AttributeError, RuntimeError, TypeError) as e:
            # ReportPortal SDK errors
            raise ReportPortalError("Failed to start launch", str(e)) from e
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from ReportPortal SDK
            # NOTE: ReportPortal SDK may raise various exceptions we cannot predict
            raise ReportPortalError("Failed to start launch", str(e)) from e

    def get_launch_id(self) -> str | None:
        """Return the current launch ID."""
        return self.launch_id

    def is_launch_active(self) -> bool:
        """Check if a launch is currently active."""
        return self.launch_id is not None

    def get_launch_url(self) -> str | None:
        """Return the UI URL for the current launch."""
        if not self.launch_id:
            return None
        return self.rp_client_base.get_launch_url(self.launch_id)

    @retry(max_attempts=2, delay=0.5)
    def finish_launch(self, status: str = "FINISHED", launch_id: str | None = None) -> None:
        """
        Finish the current launch in ReportPortal.
        Uses RPClient.finish_launch and clears self.launch_id.

        Args:
            status: Launch status ("FINISHED", "FAILED", etc.)
            launch_id: Optional launch_id to finish (if not provided, uses self.launch_id)

        Note: This should be called after all tests and attachments are done.
        """
        # Use provided launch_id or fall back to self.launch_id
        target_launch_id = launch_id or self.launch_id

        if not target_launch_id:
            self.logger.warning("No active launch to finish")
            return

        try:
            # Give a small delay to ensure all attachments are sent
            time.sleep(1.0)

            # Save launch_id before clearing
            finished_launch_id = target_launch_id

            # If client.launch_id is not set or different, we need to use direct API call
            # RPClient.finish_launch() uses client.launch_id internally
            # So we need to ensure client.launch_id matches our target_launch_id
            current_client_launch_id = getattr(self.client, 'launch_id', None)

            # Log the launch IDs for debugging
            self.logger.info(f"Finishing launch: target={target_launch_id}, client.launch_id={current_client_launch_id}")

            if current_client_launch_id != target_launch_id:
                # Try to set it via internal state (if possible)
                try:
                    # Try to set _launch_id attribute if it exists
                    if hasattr(self.client, '_launch_id'):
                        self.client._launch_id = target_launch_id
                        self.logger.info(f"Set client._launch_id to {target_launch_id}")
                    # Try to access internal _item_stack to set launch_id
                    elif hasattr(self.client, '_item_stack') and self.client._item_stack:
                        # RPClient stores launch_id in _item_stack[0]['uuid']
                        if len(self.client._item_stack) > 0 and 'uuid' in self.client._item_stack[0]:
                            self.client._item_stack[0]['uuid'] = target_launch_id
                            self.logger.info(f"Set client._item_stack[0]['uuid'] to {target_launch_id}")

                    # Call finish_launch - it should now use the correct launch_id
                    self.client.finish_launch(
                        end_time=self._current_timestamp_ms(),
                        status=status,
                    )
                except (AttributeError, RuntimeError, TypeError) as finish_error:
                    # If finish_launch failed, re-raise the error
                    self.logger.error(f"Failed to finish launch via RPClient: {finish_error}", traceback=traceback.format_exc(), module=__name__, class_name="RPLaunchManager", method="finish_launch")
                    raise
                except Exception as finish_error:  # pylint: disable=broad-exception-caught
                    # Catch-all for unexpected errors from RPClient
                    # NOTE: ReportPortal SDK may raise various exceptions we cannot predict
                    self.logger.error(f"Failed to finish launch via RPClient: {finish_error}", traceback=traceback.format_exc(), module=__name__, class_name="RPLaunchManager", method="finish_launch")
                    raise
            else:
                # Client already has the correct launch_id
                self.client.finish_launch(
                    end_time=self._current_timestamp_ms(),
                    status=status,
                )

            # IMPORTANT: reportportal-client uses async queue
            # finish_launch() adds request to queue, but doesn't guarantee immediate send
            # We need to wait a bit for the request to be sent, or use terminate() to flush
            # For now, add a delay to ensure request is processed
            time.sleep(0.5)

            self.logger.info(f"Launch finished: {finished_launch_id}")

            # Clear launch_id after successful finish (only if it was self.launch_id)
            if target_launch_id == self.launch_id:
                self.launch_id = None

            # Clear launch_id from EnvironmentManager
            try:
                from nemesis.environment.hooks import _get_env_manager  # pylint: disable=import-outside-toplevel
                env_manager = _get_env_manager()
                if env_manager and hasattr(env_manager, 'rp_launch_id'):
                    if env_manager.rp_launch_id == finished_launch_id:
                        env_manager.rp_launch_id = None
                    self.logger.debug("Cleared launch_id from EnvironmentManager")
            except (AttributeError, ImportError) as cleanup_error:
                # Non-critical: failed to clear launch_id from EnvironmentManager
                self.logger.debug(f"Failed to clear launch_id from EnvironmentManager (non-critical): {cleanup_error}", module=__name__, class_name="RPLaunchManager", method="finish_launch")
            except Exception as cleanup_error:  # pylint: disable=broad-exception-caught
                # Catch-all for unexpected errors from EnvironmentManager access
                # NOTE: EnvironmentManager import or access may raise various exceptions
                self.logger.debug(f"Failed to clear launch_id from EnvironmentManager (non-critical): {cleanup_error}", module=__name__, class_name="RPLaunchManager", method="finish_launch")

            self.logger.debug(f"Launch {finished_launch_id} finalized and cleared")

        except (AttributeError, RuntimeError, TypeError) as e:
            # ReportPortal SDK errors
            self.logger.error(f"Failed to finish launch: {e}", traceback=traceback.format_exc(), module=__name__, class_name="RPLaunchManager", method="finish_launch")
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from ReportPortal SDK
            # NOTE: ReportPortal SDK may raise various exceptions we cannot predict
            self.logger.error(f"Failed to finish launch: {e}", traceback=traceback.format_exc(), module=__name__, class_name="RPLaunchManager", method="finish_launch")

    @retry(max_attempts=2, delay=0.5)
    def rerun_launch(self, launch_id: str) -> None:
        """
        Optional helper to mark a launch as rerun.
        """
        try:
            self.client.rerun_launch(
                launch_id=launch_id,
                end_time=self._current_timestamp_ms(),
            )
            self.logger.info(f"Launch rerun marked: {launch_id}")
        except (AttributeError, RuntimeError, TypeError) as e:
            # ReportPortal SDK errors
            self.logger.error(f"Failed to mark rerun launch: {e}", traceback=traceback.format_exc(), module=__name__, class_name="RPLaunchManager", method="rerun_launch")
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from ReportPortal SDK
            # NOTE: ReportPortal SDK may raise various exceptions we cannot predict
            self.logger.error(f"Failed to mark rerun launch: {e}", traceback=traceback.format_exc(), module=__name__, class_name="RPLaunchManager", method="rerun_launch")
