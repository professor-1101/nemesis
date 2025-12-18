"""Finalization management for reporting."""
import time
import traceback
from datetime import datetime

import requests
from rich.console import Console

from nemesis.infrastructure.logging import Logger


class FinalizationManager:
    """Manages report finalization."""

    def __init__(self, reporter_manager, execution_manager):
        """Initialize finalization manager."""
        self.logger = Logger.get_instance({})
        self.reporter_manager = reporter_manager
        self.execution_manager = execution_manager

    def finalize(self) -> None:
        """Finalize all reporting."""
        console = Console()
        
        self.logger.info("FinalizationManager.finalize() called")
        Logger.get_instance({}).info("[DEBUG] FinalizationManager.finalize() called")

        # Print step message in CLI style (independent of CLI module)
        console.Logger.get_instance({}).info("[dark_orange]→[/dark_orange] Finalizing reports...")

        # Finalize local reporter - ONLY if enabled
        is_local = self.reporter_manager.is_local_enabled()
        self.logger.info(f"Local reporting enabled: {is_local}")
        Logger.get_instance({}).info(f"[DEBUG] Local reporting enabled: {is_local}")
        
        if is_local:
            try:
                # Print HTML generation message in CLI style
                console.Logger.get_instance({}).info("[dark_orange]→[/dark_orange] Generating HTML report...")

                local_reporter = self.reporter_manager.get_local_reporter()
                self.logger.info(f"Local reporter object: {local_reporter is not None}")
                Logger.get_instance({}).info(f"[DEBUG] Local reporter object: {local_reporter is not None}")
                
                if local_reporter:
                    self.logger.info(f"Calling generate_report() with {len(local_reporter.execution_data.scenarios)} scenarios")
                    Logger.get_instance({}).info(f"[DEBUG] Calling generate_report() with {len(local_reporter.execution_data.scenarios)} scenarios")
                    local_reporter.generate_report()
                    # Clean console output is handled by LocalReporter._print_report_success()
                else:
                    self.logger.warning("Local reporter is None, cannot generate report")
                    Logger.get_instance({}).info("[DEBUG] Local reporter is None, cannot generate report")
            except (AttributeError, RuntimeError, OSError, IOError) as e:
                # Local report generation errors
                self.logger.error(f"Failed to generate local report: {e}", traceback=traceback.format_exc(), module=__name__, class_name="FinalizationManager", method="finalize")
            except Exception as e:  # pylint: disable=broad-exception-caught
                # Catch-all for unexpected errors from local reporter
                # NOTE: Local reporter may raise various exceptions we cannot predict
                self.logger.error(f"Failed to generate local report: {e}", traceback=traceback.format_exc(), module=__name__, class_name="FinalizationManager", method="finalize")
        else:
            self.logger.info("Local reporting disabled, skipping HTML report generation")

        # Finalize ReportPortal
        if self.reporter_manager.is_rp_enabled():
            try:
                rp_client = self.reporter_manager.get_rp_client()
                if rp_client:
                    # Get launch_id from rp_client or EnvironmentCoordinator
                    launch_id = rp_client.launch_id
                    if not launch_id:
                        # Try to get from EnvironmentCoordinator (for cross-process access)
                        try:
                            from nemesis.infrastructure.environment.hooks import _get_env_manager  # pylint: disable=import-outside-toplevel
                            env_manager = _get_env_manager()
                            if env_manager and hasattr(env_manager, 'rp_launch_id') and env_manager.rp_launch_id:
                                launch_id = env_manager.rp_launch_id
                                self.logger.info(f"Retrieved launch_id from EnvironmentCoordinator: {launch_id}")
                        except (AttributeError, ImportError) as get_error:
                            # Non-critical: failed to get launch_id from EnvironmentCoordinator
                            self.logger.debug(f"Could not get launch_id from EnvironmentCoordinator: {get_error}", module=__name__, class_name="FinalizationManager", method="finalize")
                        except Exception as get_error:  # pylint: disable=broad-exception-caught
                            # Catch-all for unexpected errors from EnvironmentCoordinator access
                            # NOTE: EnvironmentCoordinator import or access may raise various exceptions
                            self.logger.debug(f"Could not get launch_id from EnvironmentCoordinator: {get_error}", module=__name__, class_name="FinalizationManager", method="finalize")

                    if launch_id:
                        launch_url = rp_client.get_launch_url()
                        if launch_url:
                            self.logger.info(f"ReportPortal launch: {launch_url}")

                        # Finish launch with explicit launch_id (for cross-process support)
                        self.logger.info(f"Finishing ReportPortal launch: {launch_id}")
                        rp_client.finish_launch("FINISHED", launch_id=launch_id)

                        # CRITICAL: reportportal-client uses async queue
                        # finish_launch() adds request to queue, but doesn't guarantee immediate send
                        # terminate() flushes the queue and ensures all requests are sent
                        # We must call terminate() after finish_launch() to ensure the finish request is sent
                        time.sleep(1.0)  # Give time for finish_launch request to be added to queue
                    else:
                        self.logger.warning("No launch_id available to finish ReportPortal launch")

                    # Terminate the RP client properly - this flushes the async queue
                    if hasattr(rp_client, 'rp_client_base') and rp_client.rp_client_base and hasattr(rp_client.rp_client_base, 'client'):
                        try:
                            self.logger.info("Terminating ReportPortal client to flush async queue...")
                            rp_client.rp_client_base.client.terminate()
                            self.logger.info("ReportPortal client terminated successfully")
                            # Additional delay after terminate to ensure queue is fully flushed
                            time.sleep(0.5)

                            # CRITICAL: Make a direct API call as final fallback to ensure launch is finished
                            # This ensures the finish request is sent even if async queue doesn't flush properly
                            self._finish_launch_direct_api(rp_client.rp_client_base, launch_id)
                        except (AttributeError, RuntimeError) as terminate_error:
                            # ReportPortal client termination errors
                            self.logger.error(f"Error terminating RP client: {terminate_error}", traceback=traceback.format_exc(), module=__name__, class_name="FinalizationManager", method="finalize")
                            # Even if terminate fails, try direct API call as fallback
                            try:
                                self._finish_launch_direct_api(rp_client.rp_client_base, launch_id)
                            except (requests.RequestException, OSError, IOError) as direct_api_error:
                                # Direct API call network errors
                                self.logger.warning(f"Direct API finish_launch also failed: {direct_api_error}", traceback=traceback.format_exc(), module=__name__, class_name="FinalizationManager", method="finalize")
                            except Exception as direct_api_error:  # pylint: disable=broad-exception-caught
                                # Catch-all for unexpected errors from direct API call
                                # NOTE: Direct API call may raise various exceptions we cannot predict
                                self.logger.warning(f"Direct API finish_launch also failed: {direct_api_error}", traceback=traceback.format_exc(), module=__name__, class_name="FinalizationManager", method="finalize")
                        except Exception as terminate_error:  # pylint: disable=broad-exception-caught
                            # Catch-all for unexpected errors from RP client termination
                            # NOTE: ReportPortal SDK may raise various exceptions we cannot predict
                            self.logger.error(f"Error terminating RP client: {terminate_error}", traceback=traceback.format_exc(), module=__name__, class_name="FinalizationManager", method="finalize")
                            # Even if terminate fails, try direct API call as fallback
                            try:
                                self._finish_launch_direct_api(rp_client.rp_client_base, launch_id)
                            except (requests.RequestException, OSError, IOError) as direct_api_error:
                                # Direct API call network errors
                                self.logger.warning(f"Direct API finish_launch also failed: {direct_api_error}", traceback=traceback.format_exc(), module=__name__, class_name="FinalizationManager", method="finalize")
                            except Exception as direct_api_error:  # pylint: disable=broad-exception-caught
                                # Catch-all for unexpected errors from direct API call
                                # NOTE: Direct API call may raise various exceptions we cannot predict
                                self.logger.warning(f"Direct API finish_launch also failed: {direct_api_error}", traceback=traceback.format_exc(), module=__name__, class_name="FinalizationManager", method="finalize")

                    self.logger.info("ReportPortal finalized")
            except (AttributeError, RuntimeError) as e:
                # ReportPortal finalization errors
                self.logger.error(f"ReportPortal finalization failed: {e}", traceback=traceback.format_exc(), module=__name__, class_name="FinalizationManager", method="finalize")
            except Exception as e:  # pylint: disable=broad-exception-caught
                # Catch-all for unexpected errors from ReportPortal finalization
                # NOTE: ReportPortal SDK may raise various exceptions we cannot predict
                self.logger.error(f"ReportPortal finalization failed: {e}", traceback=traceback.format_exc(), module=__name__, class_name="FinalizationManager", method="finalize")

        if self.execution_manager:
            self.logger.info(f"Reports saved to: {self.execution_manager.get_execution_path()}")
        else:
            self.logger.info("Reports finalized (no execution manager)")

    def _finish_launch_direct_api(self, rp_client_base, launch_id: str) -> None:
        """
        Make a direct API call to finish launch as a final fallback.
        This ensures the request is sent even if RPClient async queue fails.

        Args:
            rp_client_base: RPClientBase instance
            launch_id: Launch ID to finish
        """
        try:
            # Prepare API endpoint
            endpoint = rp_client_base.endpoint.rstrip("/")
            if not endpoint.endswith("/api/v1"):
                if endpoint.endswith("/api"):
                    endpoint = endpoint[:-4]
                endpoint = f"{endpoint}/api/v1"

            url = f"{endpoint}/{rp_client_base.project}/launch/{launch_id}/finish"

            # Prepare request data - ReportPortal API for finish launch only needs endTime
            # Status is determined automatically based on test results
            end_time = str(int(datetime.now().timestamp() * 1000))
            data = {
                "endTime": end_time
            }

            # Prepare headers - ReportPortal uses Bearer token
            headers = {
                "Authorization": f"Bearer {rp_client_base.api_key}",
                "Content-Type": "application/json"
            }

            # Make the API call
            self.logger.info(f"Making direct API call to finish launch (final fallback): {launch_id}")
            response = requests.put(
                url,
                json=data,
                headers=headers,
                verify=rp_client_base.verify_ssl,
                timeout=10
            )

            if response.status_code in (200, 204):
                self.logger.info(f"Direct API finish_launch succeeded for launch: {launch_id} (status: {response.status_code})")
            elif response.status_code == 400:
                # 400 might mean launch is already finished or invalid request
                # This is not necessarily an error - launch might already be finished
                self.logger.info(f"Direct API finish_launch returned 400 (launch may already be finished): {response.text[:200]}")
            else:
                self.logger.warning(f"Direct API finish_launch returned status {response.status_code}: {response.text[:200]}")

        except (requests.RequestException, OSError, IOError, ValueError) as e:
            # Network or request errors - don't raise, this is a fallback method
            self.logger.warning(f"Direct API finish_launch failed (non-critical): {e}", traceback=traceback.format_exc(), module=__name__, class_name="FinalizationManager", method="_finish_launch_direct_api")
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from direct API call
            # NOTE: This is a fallback method, so we don't raise
            # Direct API call may raise various exceptions we cannot predict
            self.logger.warning(f"Direct API finish_launch failed (non-critical): {e}", traceback=traceback.format_exc(), module=__name__, class_name="FinalizationManager", method="_finish_launch_direct_api")

    def is_healthy(self) -> bool:
        """Check if at least one reporter is active."""
        local_ok = self.reporter_manager.is_local_enabled()
        rp_ok = self.reporter_manager.is_rp_enabled()
        return local_ok or rp_ok
