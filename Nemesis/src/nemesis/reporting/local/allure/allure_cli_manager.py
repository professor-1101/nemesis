"""Allure CLI manager for installation and execution."""
import os
import subprocess
import traceback
import shutil
from pathlib import Path
from typing import Optional, Tuple

from nemesis.infrastructure.logging import Logger


class AllureCLINotInstalledError(Exception):
    """Exception raised when Allure CLI is not installed."""
    
    def __init__(self, message: str = "Allure CLI is not installed. Please install it from https://adoptium.net/temurin/releases/ and set JAVA_HOME."):
        self.message = message
        super().__init__(self.message)


class AllureCLIManager:
    """Manages Allure CLI installation and execution."""
    
    def __init__(self):
        """Initialize Allure CLI manager."""
        self.logger = Logger.get_instance({})
        self._allure_binary: Optional[str] = None
        self._ensure_java_in_path()
    
    def _ensure_java_in_path(self) -> None:
        """Ensure Java is in PATH by finding it and setting JAVA_HOME if needed."""
        import platform
        
        # Check if JAVA_HOME is already set
        java_home = os.environ.get('JAVA_HOME')
        if java_home and Path(java_home).exists():
            java_exe = Path(java_home) / "bin" / "java.exe"
            if java_exe.exists():
                # Add to PATH if not already there
                current_path = os.environ.get('PATH', '')
                if str(Path(java_home) / "bin") not in current_path:
                    os.environ['PATH'] = f"{Path(java_home) / 'bin'}{os.pathsep}{current_path}"
                return
        
        # Check if java is already in PATH
        if shutil.which("java"):
            return
        
        # Try to find Java in common Windows locations
        if platform.system() == "Windows":
            common_java_paths = [
                Path("C:/Program Files/Java"),
                Path("C:/Program Files (x86)/Java"),
                Path("C:/Program Files/Eclipse Adoptium"),
                Path("C:/Program Files/Microsoft"),
                Path(os.environ.get('ProgramFiles', 'C:/Program Files')) / "Java",
                Path(os.environ.get('ProgramFiles', 'C:/Program Files')) / "Eclipse Adoptium",
                Path(os.environ.get('ProgramFiles(x86)', 'C:/Program Files (x86)')) / "Java",
            ]
            
            for java_base in common_java_paths:
                if not java_base.exists():
                    continue
                
                # Look for JDK/JRE directories
                for jdk_dir in java_base.iterdir():
                    if not jdk_dir.is_dir():
                        continue
                    
                    java_exe = jdk_dir / "bin" / "java.exe"
                    if java_exe.exists():
                        # Found Java! Set JAVA_HOME
                        java_home = str(jdk_dir)
                        os.environ['JAVA_HOME'] = java_home
                        # Add to PATH
                        current_path = os.environ.get('PATH', '')
                        java_bin = str(jdk_dir / "bin")
                        if java_bin not in current_path:
                            os.environ['PATH'] = f"{java_bin}{os.pathsep}{current_path}"
                        self.logger.debug(f"Found Java at {java_home} and added to PATH", module=__name__, class_name="AllureCLIManager", method="_ensure_java_in_path")
                        return
    
    def is_installed(self) -> bool:
        """Check if Allure CLI is installed and available.
        
        Returns:
            True if Allure CLI is available, False otherwise
        """
        try:
            # Prepare environment with inherited PATH and JAVA_HOME
            env = os.environ.copy()
            java_home = env.get('JAVA_HOME')
            if java_home and java_home not in env.get('PATH', ''):
                env['PATH'] = f"{java_home}{os.pathsep}{java_home}/bin{os.pathsep}{env.get('PATH', '')}"
            
            # Try to find allure command in PATH (with updated environment)
            # Note: shutil.which doesn't accept env parameter, so we need to check manually
            import platform
            is_windows = platform.system() == "Windows"
            
            path_dirs = env.get('PATH', '').split(os.pathsep)
            for path_dir in path_dirs:
                if not path_dir:
                    continue
                # On Windows, check for .cmd, .bat, and .exe files
                if is_windows:
                    for ext in ['', '.cmd', '.bat', '.exe']:
                        allure_bin = Path(path_dir) / f"allure{ext}"
                        if allure_bin.exists() and allure_bin.is_file():
                            self._allure_binary = str(allure_bin)
                            return True
                else:
                    allure_bin = Path(path_dir) / "allure"
                    if allure_bin.exists() and allure_bin.is_file():
                        self._allure_binary = str(allure_bin)
                        return True
            
            # Also try shutil.which with current environment
            allure_path = shutil.which("allure")
            if allure_path:
                self._allure_binary = allure_path
                return True
            
            # Check common installation locations
            common_paths = [
                Path.home() / ".local" / "bin" / "allure",
                Path.home() / ".npm" / "global" / "node_modules" / ".bin" / "allure",
                Path("/usr/local/bin/allure"),
                Path("/usr/bin/allure"),
            ]
            
            for path in common_paths:
                if path.exists() and path.is_file():
                    self._allure_binary = str(path)
                    return True
            
            return False
            
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors during check
            self.logger.debug(f"Error checking Allure CLI: {e}", module=__name__, class_name="AllureCLIManager", method="is_installed")
            return False
    
    def get_version(self) -> Optional[str]:
        """Get Allure CLI version.
        
        Returns:
            Version string if available, None otherwise
        """
        if not self.is_installed():
            return None
        
        # Use environment with inherited PATH
        import platform
        is_windows = platform.system() == "Windows"
        
        env = os.environ.copy()
        java_home = env.get('JAVA_HOME')
        if java_home and java_home not in env.get('PATH', ''):
            env['PATH'] = f"{java_home}{os.pathsep}{java_home}/bin{os.pathsep}{env.get('PATH', '')}"
        
        allure_cmd = self._allure_binary or "allure"
        
        # On Windows, if it's a .cmd or .bat file, we need shell=True
        if is_windows and allure_cmd and (allure_cmd.endswith('.cmd') or allure_cmd.endswith('.bat')):
            command = f"{allure_cmd} --version"
            use_shell = True
        else:
            command = [allure_cmd, "--version"]
            use_shell = False
        
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
                env=env,
                shell=use_shell
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            
            # Check for Java-related errors
            error_output = result.stderr or result.stdout or ""
            if "JAVA_HOME" in error_output or "java" in error_output.lower():
                self.logger.warning(
                    "Allure CLI requires Java 17 LTS to be installed. Please install from https://adoptium.net/temurin/releases/ and set JAVA_HOME environment variable.",
                    module=__name__,
                    class_name="AllureCLIManager",
                    method="get_version"
                )
            
            return None
            
        except FileNotFoundError:
            self.logger.debug("Allure CLI command not found", module=__name__, class_name="AllureCLIManager", method="get_version")
            return None
        except subprocess.TimeoutExpired:
            self.logger.warning("Allure CLI version check timed out", module=__name__, class_name="AllureCLIManager", method="get_version")
            return None
        except (OSError, IOError) as e:
            self.logger.warning(f"Allure CLI version check failed - I/O error: {e}", traceback=traceback.format_exc(), module=__name__, class_name="AllureCLIManager", method="get_version")
            return None
        except Exception as e:  # pylint: disable=broad-exception-caught
            self.logger.warning(f"Allure CLI version check failed: {e}", traceback=traceback.format_exc(), module=__name__, class_name="AllureCLIManager", method="get_version")
            return None
    
    def generate_report(self, results_dir: Path, output_dir: Path, clean: bool = True) -> Tuple[bool, Optional[str]]:
        """Generate Allure report using CLI.
        
        Args:
            results_dir: Directory containing Allure results JSON files
            output_dir: Directory where report will be generated
            clean: If True, clean output directory before generation
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
            
        Raises:
            AllureCLINotInstalledError: If Allure CLI is not installed
        """
        if not self.is_installed():
            raise AllureCLINotInstalledError(
                "Allure CLI is not installed. Please install from https://adoptium.net/temurin/releases/ "
                "and set JAVA_HOME. Then install Allure CLI: npm install -g allure-commandline"
            )
        
        try:
            # Validate results directory
            if not results_dir.exists():
                return False, f"Results directory does not exist: {results_dir}"
            
            result_files = list(results_dir.glob("*-result.json"))
            if not result_files:
                return False, f"No Allure result files found in: {results_dir}"
            
            # Ensure output directory exists
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Build command - on Windows, use shell=True for .cmd/.bat files
            import platform
            is_windows = platform.system() == "Windows"
            
            allure_cmd = self._allure_binary or "allure"
            
            # On Windows, check if the file exists and add .cmd extension if needed
            if is_windows and allure_cmd:
                allure_path = Path(allure_cmd)
                # On Windows, if path doesn't have extension, try .cmd
                if not allure_path.suffix:
                    allure_cmd_cmd = Path(f"{allure_cmd}.cmd")
                    if allure_cmd_cmd.exists():
                        allure_cmd = str(allure_cmd_cmd)
                    elif allure_path.exists():
                        # If file without extension exists, it might be a script wrapper
                        # Try to use it with shell=True anyway
                        pass
            
            # On Windows, if it's a .cmd or .bat file (or no extension on Windows), we need shell=True
            if is_windows and allure_cmd:
                # Check if it's a .cmd/.bat file, or if it's a file without extension (likely a script)
                allure_path = Path(allure_cmd)
                if (allure_cmd.endswith('.cmd') or allure_cmd.endswith('.bat') or 
                    (not allure_path.suffix and allure_path.exists())):
                    # Use shell=True for Windows batch files
                    command_str = f"{allure_cmd} generate {results_dir} -o {output_dir}"
                    if clean:
                        command_str += " --clean"
                    command = command_str
                    use_shell = True
                else:
                    # Direct executable (unlikely on Windows for npm packages)
                    command = [
                        allure_cmd,
                        "generate",
                        str(results_dir),
                        "-o", str(output_dir)
                    ]
                    if clean:
                        command.append("--clean")
                    use_shell = False
            else:
                # Unix-like systems or direct executable
                command = [
                    allure_cmd,
                    "generate",
                    str(results_dir),
                    "-o", str(output_dir)
                ]
                if clean:
                    command.append("--clean")
                use_shell = False
            
            self.logger.info(f"Generating Allure report: {command if isinstance(command, str) else ' '.join(command)}", module=__name__, class_name="AllureCLIManager", method="generate_report")
            
            # Execute command with environment variables
            env = os.environ.copy()
            # Ensure PATH is inherited (important for venv)
            if 'PATH' in env:
                # Add common Java/Allure paths if not already present
                java_home = env.get('JAVA_HOME')
                if java_home and java_home not in env.get('PATH', ''):
                    env['PATH'] = f"{java_home}{os.pathsep}{java_home}/bin{os.pathsep}{env.get('PATH', '')}"
            
            try:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=120,  # 2 minutes timeout
                    check=False,
                    env=env,
                    shell=use_shell
                )
                
                if result.returncode != 0:
                    error_msg = result.stderr or result.stdout or "Unknown error"
                    
                    # Check for Java-related errors
                    if "JAVA_HOME" in error_msg or ("java" in error_msg.lower() and "not found" in error_msg.lower()):
                        java_error = "Allure CLI requires Java 17 LTS to be installed. Please install from https://adoptium.net/temurin/releases/ and set JAVA_HOME environment variable."
                        self.logger.warning(
                            f"Allure CLI generation failed - Java not found: {error_msg}",
                            traceback=None,
                            module=__name__,
                            class_name="AllureCLIManager",
                            method="generate_report"
                        )
                        return False, java_error
                    
                    self.logger.warning(
                        f"Allure CLI generation failed (exit code: {result.returncode}): {error_msg}",
                        traceback=None,
                        module=__name__,
                        class_name="AllureCLIManager",
                        method="generate_report"
                    )
                    return False, f"Allure CLI failed: {error_msg}"
                
                # Verify report was generated
                index_html = output_dir / "index.html"
                if not index_html.exists():
                    return False, f"Report generated but index.html not found in: {output_dir}"
                
                self.logger.info(f"Allure report generated successfully at: {output_dir}", module=__name__, class_name="AllureCLIManager", method="generate_report")
                return True, None
                
            except subprocess.TimeoutExpired:
                self.logger.warning(
                    "Allure CLI report generation timed out (timeout: 120s)",
                    traceback=None,
                    module=__name__,
                    class_name="AllureCLIManager",
                    method="generate_report"
                )
                return False, "Report generation timed out (timeout: 120s)"
            except (OSError, IOError) as e:
                self.logger.error(
                    f"Allure CLI report generation failed - I/O error: {e}",
                    traceback=traceback.format_exc(),
                    module=__name__,
                    class_name="AllureCLIManager",
                    method="generate_report"
                )
                return False, f"I/O error: {e}"
                
        except KeyboardInterrupt:
            # User interrupted - re-raise to allow proper termination
            raise
        except SystemExit:
            # System exit - re-raise to allow proper termination
            raise
        except (AttributeError, RuntimeError) as e:
            self.logger.error(
                f"Allure CLI report generation failed - runtime error: {e}",
                traceback=traceback.format_exc(),
                module=__name__,
                class_name="AllureCLIManager",
                method="generate_report"
            )
            return False, f"Runtime error: {e}"
        except Exception as e:  # pylint: disable=broad-exception-caught
            self.logger.error(
                f"Allure CLI report generation failed - unexpected error: {e}",
                traceback=traceback.format_exc(),
                module=__name__,
                class_name="AllureCLIManager",
                method="generate_report"
            )
            return False, f"Unexpected error: {e}"
    
    def open_report(self, report_dir: Path) -> Tuple[bool, Optional[str]]:
        """Open Allure report in browser using Allure CLI.
        
        Args:
            report_dir: Directory containing the Allure report.
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
            
        Raises:
            AllureCLINotInstalledError: If Allure CLI is not installed
        """
        if not self.is_installed():
            raise AllureCLINotInstalledError(
                "Allure CLI is not installed. Please install from https://adoptium.net/temurin/releases/ "
                "and set JAVA_HOME. Then install Allure CLI: npm install -g allure-commandline"
            )
        
        try:
            if not report_dir.exists():
                return False, f"Report directory does not exist: {report_dir}"
            
            index_html = report_dir / "index.html"
            if not index_html.exists():
                return False, f"Allure report not found in: {report_dir}. Run 'allure generate' first."
            
            import platform
            is_windows = platform.system() == "Windows"
            
            allure_cmd = self._allure_binary or "allure"
            
            # On Windows, check if the file exists and add .cmd extension if needed
            if is_windows and allure_cmd:
                allure_path = Path(allure_cmd)
                # On Windows, if path doesn't have extension, try .cmd
                if not allure_path.suffix:
                    allure_cmd_cmd = Path(f"{allure_cmd}.cmd")
                    if allure_cmd_cmd.exists():
                        allure_cmd = str(allure_cmd_cmd)
                    elif allure_path.exists():
                        # If file without extension exists, use shell=True anyway
                        pass
            
            # On Windows, if it's a .cmd or .bat file (or no extension on Windows), we need shell=True
            if is_windows and allure_cmd:
                allure_path = Path(allure_cmd)
                if (allure_cmd.endswith('.cmd') or allure_cmd.endswith('.bat') or 
                    (not allure_path.suffix and allure_path.exists())):
                    command = f"{allure_cmd} open {report_dir}"
                    use_shell = True
                else:
                    command = [
                        allure_cmd,
                        "open",
                        str(report_dir)
                    ]
                    use_shell = False
            else:
                command = [
                    allure_cmd,
                    "open",
                    str(report_dir)
                ]
                use_shell = False
            
            self.logger.info(f"Opening Allure report: {command if isinstance(command, str) else ' '.join(command)}", module=__name__, class_name="AllureCLIManager", method="open_report")
            
            # Use environment with inherited PATH
            env = os.environ.copy()
            java_home = env.get('JAVA_HOME')
            if java_home and java_home not in env.get('PATH', ''):
                env['PATH'] = f"{java_home}{os.pathsep}{java_home}/bin{os.pathsep}{env.get('PATH', '')}"
            
            # Open report in background (non-blocking)
            try:
                result = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=env,
                    shell=use_shell
                )
                
                # Don't wait for the process - let it run in background
                self.logger.info(f"Allure report opened in browser", module=__name__, class_name="AllureCLIManager", method="open_report")
                return True, None
                
            except (OSError, IOError) as e:
                self.logger.error(
                    f"Allure CLI open failed - I/O error: {e}",
                    traceback=traceback.format_exc(),
                    module=__name__,
                    class_name="AllureCLIManager",
                    method="open_report"
                )
                return False, f"I/O error: {e}"
                
        except KeyboardInterrupt:
            raise
        except SystemExit:
            raise
        except (AttributeError, RuntimeError) as e:
            self.logger.error(
                f"Allure CLI open failed - runtime error: {e}",
                traceback=traceback.format_exc(),
                module=__name__,
                class_name="AllureCLIManager",
                method="open_report"
            )
            return False, f"Runtime error: {e}"
        except Exception as e:  # pylint: disable=broad-exception-caught
            self.logger.error(
                f"Allure CLI open failed - unexpected error: {e}",
                traceback=traceback.format_exc(),
                module=__name__,
                class_name="AllureCLIManager",
                method="open_report"
            )
            return False, f"Unexpected error: {e}"

