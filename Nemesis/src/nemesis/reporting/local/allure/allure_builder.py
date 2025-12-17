"""Allure-style HTML report builder using Allure format."""
import json
import subprocess
import shutil
import traceback
from pathlib import Path
from typing import Any, Optional

from nemesis.infrastructure.logging import Logger
from nemesis.reporting.local.data_model import ExecutionData
from .allure_integration import AllureResultsGenerator
from .allure_cli_manager import AllureCLIManager, AllureCLINotInstalledError


class AllureReportBuilder:
    """Builds Allure-style HTML report using Allure results format."""

    def __init__(self, execution_data: ExecutionData, execution_path: Path):
        """Initialize Allure report builder.
        
        Args:
            execution_data: Execution data from LocalReporter
            execution_path: Path to execution directory
        """
        self.execution_data = execution_data
        self.execution_path = execution_path
        self.logger = Logger.get_instance({})
        
        # Directory for Allure results
        self.allure_results_dir = execution_path / "allure-results"
        self.allure_report_dir = execution_path / "allure-report"
        
        # Allure CLI manager
        self.cli_manager = AllureCLIManager()

    def build_report(self) -> None:
        """Build Allure report (only allure-results and allure-report, no report.html).
        
        This method:
        1. Generates Allure results JSON files
        2. Attempts to use Allure CLI to generate HTML (if available)
        3. If Allure CLI not available, only generates results (no HTML fallback)
        """
        # Step 1: Generate Allure results JSON files
        self.logger.info("Generating Allure results JSON files...")
        results_generator = AllureResultsGenerator(self.allure_results_dir, self.execution_path)
        results_generator.generate_from_execution_data(self.execution_data)
        
        # Step 1.5: Generate environment.json and executor.json
        self._generate_environment_files()
        
        # Step 2: Try to use Allure CLI to generate HTML
        if self._try_allure_cli():
            self.logger.info("Allure report generated using Allure CLI", module=__name__, class_name="AllureReportBuilder", method="build_report")
            return
        
        # Step 3: Allure CLI not available - only results generated
        self.logger.info(
            "Allure CLI not available. Allure results generated: JSON files are available in allure-results/ directory. "
            "To generate HTML report, install Allure CLI and Java 17 LTS.",
            module=__name__,
            class_name="AllureReportBuilder",
            method="build_report"
        )
    
    def _try_allure_cli(self) -> bool:
        """Try to generate report using Allure CLI.
        
        Returns:
            True if Allure CLI was used successfully, False otherwise
        """
        try:
            # Step 1: Check if Allure CLI is installed
            if not self.cli_manager.is_installed():
                self.logger.debug("Allure CLI is not installed", module=__name__, class_name="AllureReportBuilder", method="_try_allure_cli")
                return False
            
            # Step 2: Get version info
            version = self.cli_manager.get_version()
            if version:
                self.logger.info(f"Using Allure CLI version: {version}", module=__name__, class_name="AllureReportBuilder", method="_try_allure_cli")
            
            # Step 3: Validate results directory
            if not self.allure_results_dir.exists():
                self.logger.warning(
                    f"Allure results directory does not exist: {self.allure_results_dir}",
                    module=__name__,
                    class_name="AllureReportBuilder",
                    method="_try_allure_cli"
                )
                return False
            
            result_files = list(self.allure_results_dir.glob("*-result.json"))
            if not result_files:
                self.logger.warning(
                    f"No Allure result files found in: {self.allure_results_dir}",
                    module=__name__,
                    class_name="AllureReportBuilder",
                    method="_try_allure_cli"
                )
                return False
            
            self.logger.info(
                f"Found {len(result_files)} Allure result files, generating report...",
                module=__name__,
                class_name="AllureReportBuilder",
                method="_try_allure_cli"
            )
            
            # Step 4: Generate report using CLI manager
            try:
                success, error_msg = self.cli_manager.generate_report(
                    results_dir=self.allure_results_dir,
                    output_dir=self.allure_report_dir,
                    clean=True
                )
                
                if not success:
                    self.logger.warning(
                        f"Allure CLI report generation failed: {error_msg}",
                        module=__name__,
                        class_name="AllureReportBuilder",
                        method="_try_allure_cli"
                    )
                    return False
            except AllureCLINotInstalledError as e:
                # Re-raise to be handled by caller
                raise
            
            # Step 5: Create a simple redirect HTML file that points to allure-report
            try:
                index_html = self.allure_report_dir / "index.html"
                if not index_html.exists():
                    self.logger.warning(
                        "Allure CLI completed but index.html not found in report directory",
                        module=__name__,
                        class_name="AllureReportBuilder",
                        method="_try_allure_cli"
                    )
                    return False
                
                self.logger.info(
                    f"Allure report generated successfully at: {self.allure_report_dir}",
                    module=__name__,
                    class_name="AllureReportBuilder",
                    method="_try_allure_cli"
                )
                self.logger.info(
                    f"To view the report, run: nemesis open or allure open {self.allure_report_dir}",
                    module=__name__,
                    class_name="AllureReportBuilder",
                    method="_try_allure_cli"
                )
                return True
                
            except (OSError, IOError, shutil.Error) as e:
                # File copy errors
                self.logger.error(
                    f"Failed to copy Allure report: {e}",
                    traceback=traceback.format_exc(),
                    module=__name__,
                    class_name="AllureReportBuilder",
                    method="_try_allure_cli"
                )
                return False
                
        except KeyboardInterrupt:
            # User interrupted - re-raise to allow proper termination
            raise
        except SystemExit:
            # System exit - re-raise to allow proper termination
            raise
        except (AttributeError, RuntimeError) as e:
            # Attribute or runtime errors
            self.logger.error(
                f"Failed to use Allure CLI - runtime error: {e}",
                traceback=traceback.format_exc(),
                module=__name__,
                class_name="AllureReportBuilder",
                method="_try_allure_cli"
            )
            return False
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from Allure CLI
            # NOTE: Allure CLI may raise various exceptions we cannot predict
            self.logger.error(
                f"Failed to use Allure CLI - unexpected error: {e}",
                traceback=traceback.format_exc(),
                module=__name__,
                class_name="AllureReportBuilder",
                method="_try_allure_cli"
            )
            return False

    def _build_custom_html(self, output_path: Path) -> None:
        """Build custom HTML report (fallback when Allure CLI not available).
        
        Args:
            output_path: Path where report.html will be saved
        """
        # Load Allure results
        results = self._load_allure_results()
        
        # Generate HTML
        html_content = self._generate_html_from_results(results)
        
        # Save HTML
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Copy assets (will be implemented)
        self._copy_custom_assets(output_path.parent)

    def _load_allure_results(self) -> list[dict[str, Any]]:
        """Load Allure results JSON files.
        
        Returns:
            List of test result dictionaries
        """
        results = []
        
        if not self.allure_results_dir.exists():
            return results
        
        for result_file in self.allure_results_dir.glob("*-result.json"):
            try:
                with open(result_file, 'r', encoding='utf-8') as f:
                    result = json.load(f)
                    results.append(result)
            except (json.JSONDecodeError, IOError) as e:
                self.logger.warning(f"Failed to load result file {result_file}: {e}")
        
        return results

    def _generate_html_from_results(self, results: list[dict[str, Any]]) -> str:
        """Generate HTML from Allure results.
        
        Args:
            results: List of test result dictionaries
            
        Returns:
            HTML content string
        """
        # Calculate statistics
        total = len(results)
        passed = sum(1 for r in results if r.get("status") == "passed")
        failed = sum(1 for r in results if r.get("status") == "failed")
        broken = sum(1 for r in results if r.get("status") == "broken")
        skipped = sum(1 for r in results if r.get("status") == "skipped")
        
        # This will be replaced with full Allure-style template
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Allure Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .stats {{ display: flex; gap: 20px; margin: 20px 0; }}
        .stat {{ padding: 10px; border: 1px solid #ccc; border-radius: 4px; }}
        .stat.passed {{ background: #d4edda; }}
        .stat.failed {{ background: #f8d7da; }}
        .stat.broken {{ background: #fff3cd; }}
        .stat.skipped {{ background: #d1ecf1; }}
    </style>
</head>
<body>
    <h1>Allure Report</h1>
    <div class="stats">
        <div class="stat passed">Passed: {passed}</div>
        <div class="stat failed">Failed: {failed}</div>
        <div class="stat broken">Broken: {broken}</div>
        <div class="stat skipped">Skipped: {skipped}</div>
        <div class="stat">Total: {total}</div>
    </div>
    <div style="margin-top: 30px; padding: 20px; background: #fff3cd; border-left: 4px solid #ffc107; border-radius: 4px;">
        <h3 style="margin-top: 0; color: #856404;">Allure CLI Not Installed</h3>
        <p>
            <strong>Allure results generated:</strong> JSON files are available in <code>allure-results/</code> directory.<br>
            <strong>Allure CLI not available:</strong> To generate a full Allure report with Dashboard, Charts, and Timeline features, you need to install Allure CLI and Java 17 LTS.
        </p>
        <p><strong>Prerequisites:</strong></p>
        <div style="background: #f8f9fa; padding: 15px; border-radius: 4px; margin: 10px 0;">
            <p style="margin-top: 0; margin-bottom: 10px;"><strong>1. Install Java 17 LTS:</strong></p>
            <ul style="line-height: 1.8; margin-bottom: 15px;">
                <li>Download from <a href="https://adoptium.net/temurin/releases/" target="_blank">Eclipse Temurin JDK 17 LTS</a></li>
                <li>Set <code style="background: #e9ecef; padding: 2px 6px; border-radius: 3px;">JAVA_HOME</code> environment variable</li>
                <li>Verify: <code style="background: #e9ecef; padding: 2px 6px; border-radius: 3px;">java -version</code></li>
            </ul>
            
            <p style="margin-top: 0; margin-bottom: 10px;"><strong>2. Install Allure CLI:</strong></p>
            <ul style="line-height: 1.8; margin-bottom: 10px;">
                <li><strong>npm:</strong> <code style="background: #e9ecef; padding: 2px 6px; border-radius: 3px;">npm install -g allure-commandline</code></li>
                <li><strong>Chocolatey (Windows):</strong> <code style="background: #e9ecef; padding: 2px 6px; border-radius: 3px;">choco install allure</code></li>
                <li><strong>Scoop (Windows):</strong> <code style="background: #e9ecef; padding: 2px 6px; border-radius: 3px;">scoop install allure</code></li>
                <li><strong>Homebrew (macOS):</strong> <code style="background: #e9ecef; padding: 2px 6px; border-radius: 3px;">brew install allure</code></li>
            </ul>
            
            <p style="margin-top: 15px; margin-bottom: 5px;"><strong>After installation, generate the report:</strong></p>
            <ul style="line-height: 1.8; margin-bottom: 0;">
                <li><code style="background: #e9ecef; padding: 2px 6px; border-radius: 3px;">cd {str(self.execution_path)}</code></li>
                <li><code style="background: #e9ecef; padding: 2px 6px; border-radius: 3px;">allure generate allure-results -o allure-report</code></li>
                <li><code style="background: #e9ecef; padding: 2px 6px; border-radius: 3px;">allure open allure-report</code></li>
            </ul>
        </div>
        <p style="margin-bottom: 0; color: #6c757d; font-size: 0.9em;">
            Documentation: <a href="https://docs.qameta.io/allure/" target="_blank">https://docs.qameta.io/allure/</a>
        </p>
    </div>
</body>
</html>"""

    def _copy_custom_assets(self, output_dir: Path) -> None:
        """Copy custom assets for HTML report.
        
        Args:
            output_dir: Output directory
        """
        # This will be implemented with full Allure-style assets
        pass

    def _generate_environment_files(self) -> None:
        """Generate environment.json and executor.json for Allure report.
        
        These files provide environment information and executor details
        for the Allure report's Environment and Trends sections.
        """
        try:
            import platform
            import sys
            
            # Generate environment.json
            environment_data = {
                "execution_id": self.execution_data.execution_id,
                "start_time": self.execution_data.start_time.isoformat() if self.execution_data.start_time else None,
                "end_time": self.execution_data.end_time.isoformat() if self.execution_data.end_time else None,
                "duration": self.execution_data.duration,
                "total_scenarios": len(self.execution_data.scenarios),
                "passed_scenarios": self.execution_data.passed_scenarios,
                "failed_scenarios": self.execution_data.failed_scenarios,
                "total_steps": self.execution_data.total_steps,
                "python_version": sys.version,
                "platform": platform.platform(),
                "system": platform.system(),
                "processor": platform.processor(),
            }
            
            # Add browser info if available
            try:
                from nemesis.infrastructure.browser import BrowserManager
                # Try to get browser info from config or context
                # This is a best-effort attempt
                environment_data["browser"] = "Playwright"
            except (ImportError, AttributeError):
                pass
            
            environment_file = self.allure_results_dir / "environment.json"
            with open(environment_file, 'w', encoding='utf-8') as f:
                json.dump(environment_data, f, indent=2, ensure_ascii=False)
            
            # Generate executor.json
            executor_data = {
                "buildName": f"nemesis-{self.execution_data.execution_id}",
                "buildOrder": 1,
                "type": "local",
                "reportName": "Nemesis Test Execution",
                "reportUrl": "",
            }
            
            executor_file = self.allure_results_dir / "executor.json"
            with open(executor_file, 'w', encoding='utf-8') as f:
                json.dump(executor_data, f, indent=2, ensure_ascii=False)
            
            self.logger.debug(
                "Generated environment.json and executor.json",
                module=__name__,
                class_name="AllureReportBuilder",
                method="_generate_environment_files"
            )
            
        except (OSError, IOError, json.JSONEncodeError) as e:
            self.logger.warning(
                f"Failed to generate environment files: {e}",
                module=__name__,
                class_name="AllureReportBuilder",
                method="_generate_environment_files"
            )


