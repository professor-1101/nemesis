"""Test execution orchestrator with real-time output."""
import os
import subprocess
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console

from nemesis.infrastructure.logging import Logger
from nemesis.utils import get_path_manager

console = Console()
LOGGER = Logger.get_instance({})
class TestExecutor:
    """Orchestrates test execution with Behave."""

    def __init__(
            self,
            tags: List[str],
            feature: Optional[str],
            env: str,
            report_mode: str,
            parallel: int,
            headless: bool,
            dry_run: bool,
            debug: bool,
            verbose: bool,
            config: Dict[str, Any],
    ):
        self.tags = tags
        self.feature = feature
        self.env = env
        self.report_mode = report_mode
        self.parallel = parallel
        self.headless = headless
        self.dry_run = dry_run
        self.debug = debug
        self.verbose = verbose
        self.config = config

    def execute(self) -> int:
        """Execute tests and return exit code."""
        self._setup_environment()
        command = self._build_command()

        LOGGER.info(f"[dim]$ {' '.join(command)}[/dim]\n")

        return self._execute_realtime(command)

    def _setup_environment(self) -> None:
        """Setup environment variables for test execution."""
        os.environ["TEST_ENV"] = self.env
        os.environ["HEADLESS"] = str(self.headless).lower()
        os.environ["DEBUG"] = str(self.debug).lower()

        if self.report_mode in ["reportportal", "all"]:
            rp_config = self.config.get("reportportal", {})
            if rp_config.get("enabled", True):
                os.environ["RP_ENABLED"] = "true"
                os.environ["RP_ENDPOINT"] = rp_config.get("endpoint", "")
                os.environ["RP_PROJECT"] = rp_config.get("project", "")
                os.environ["RP_API_KEY"] = rp_config.get("api_key", "")

    def _build_command(self) -> List[str]:
        """Build behave command with all options."""
        cmd = ["behave"]

        # Add tags
        for tag in self.tags:
            cmd.extend(["--tags", tag])

        # Add feature
        if self.feature:
            # Use PathHelper for centralized path management
            try:
                path_manager = get_path_manager(self.config)
                features_dir = path_manager.get_features_dir()
            except (AttributeError, KeyError, RuntimeError) as e:
                # PathHelper initialization errors - fallback to config or default
                LOGGER.debug(f"PathHelper failed, using fallback: {e}", traceback=traceback.format_exc(), module=__name__, class_name="TestExecutor", method="_build_command")
                features_dir = self.config.get("features_dir", Path.cwd() / "features")
                if isinstance(features_dir, str):
                    features_dir = Path(features_dir)
            except (KeyboardInterrupt, SystemExit):  # pylint: disable=try-except-raise
                # Always re-raise these to allow proper program termination
                # NOTE: KeyboardInterrupt and SystemExit must propagate to allow graceful shutdown
                raise

            cmd.append(str(features_dir / self.feature))

        # Add dry-run
        if self.dry_run:
            cmd.append("--dry-run")

        # Add parallel execution
        if self.parallel and self.parallel > 1:
            cmd.extend(["--processes", str(self.parallel)])
            cmd.append("--parallel-element=feature")

        # Add verbose
        if self.verbose:
            cmd.append("--verbose")

        # Add custom formatter for local HTML reports
        # if self.report_mode in ["local", "all"]:
        #     reports_dir = self.config.get("reports_dir", Path.cwd() / "reports")
        #     cmd.extend(["-f", "html", "-o", str(reports_dir / "report.html")])

        return cmd

    def _execute_realtime(self, command: List[str]) -> int:
        """Execute command with real-time output streaming."""
        process = None
        try:
            process = subprocess.Popen(
                command,
                cwd=Path.cwd(),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )

            # Stream output in real-time
            if process.stdout:
                for line in process.stdout:
                    try:
                        print(line, end="")
                        sys.stdout.flush()

                        # Check for EPIPE or browser crash indicators with HAR-specific handling
                        if "EPIPE" in line or "broken pipe" in line.lower():
                            console.print(f"\n[red]✗ Browser crash detected: {line.strip()}[/red]")
                            # Check if it's HAR-related crash
                            if "har" in line.lower() or "network" in line.lower():
                                console.print("[yellow]⚠ HAR recording may have caused this crash[/yellow]")
                                console.print("[yellow]💡 Consider disabling HAR or using minimal HAR settings[/yellow]")

                            if process:
                                process.terminate()
                                try:
                                    process.wait(timeout=5)
                                except subprocess.TimeoutExpired:
                                    process.kill()
                            return 1

                    except UnicodeEncodeError:
                        # Handle encoding issues on Windows
                        try:
                            print(line.encode('utf-8', errors='replace').decode('utf-8'), end="")
                            sys.stdout.flush()
                        except (KeyboardInterrupt, SystemExit):  # pylint: disable=try-except-raise
                            # Always re-raise these to allow proper program termination
                            # NOTE: KeyboardInterrupt and SystemExit must propagate to allow graceful shutdown
                            raise
                        except (UnicodeDecodeError, OSError) as encode_error:
                            # Skip problematic lines that cannot be encoded
                            LOGGER.debug(f"Skipping unencodable line: {encode_error}", module=__name__, class_name="TestExecutor", method="_execute_realtime")

            exit_code = process.wait()

            # Check if process crashed with EPIPE
            if exit_code != 0:
                console.print(f"\n[red]✗ Process exited with code: {exit_code}[/red]")
                return exit_code

            return exit_code

        except SystemExit:  # pylint: disable=try-except-raise
            # Re-raise SystemExit to allow proper program termination
            # NOTE: SystemExit must propagate to allow proper exit code handling
            raise
        except KeyboardInterrupt:
            if process:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
            console.print("\n[yellow]⚠ Test execution interrupted[/yellow]")
            return 130
        except (OSError, subprocess.SubprocessError) as e:
            # Process/subprocess errors
            LOGGER.error(f"Execution error - subprocess failed: {e}", traceback=traceback.format_exc(), module=__name__, class_name="TestExecutor", method="_execute_realtime")
            console.print(f"\n[red]✗ Execution error: {e}[/red]")
            if process:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
            return 1
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from subprocess or stdout handling
            # NOTE: subprocess and stdout handling may raise various exceptions we cannot predict
            LOGGER.error(f"Execution error: {e}", traceback=traceback.format_exc(), module=__name__, class_name="TestExecutor", method="_execute_realtime")
            console.print(f"\n[red]✗ Execution error: {e}[/red]")
            if process:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
            return 1
