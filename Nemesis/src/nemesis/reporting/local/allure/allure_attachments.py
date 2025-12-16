"""Allure attachments handling."""
import shutil
from pathlib import Path
from typing import Any

from nemesis.reporting.local.data_model import ScenarioData, StepData


class AllureAttachmentsBuilder:
    """Builds Allure attachments from scenario data and execution directory."""

    def __init__(self, results_dir: Path, execution_path: Path):
        """Initialize attachments builder.
        
        Args:
            results_dir: Directory where Allure results will be saved
            execution_path: Execution directory path (for finding attachments)
        """
        self.results_dir = results_dir
        self.execution_path = execution_path
        self._copied_videos: set[str] = set()  # Track copied videos to avoid duplicates

    def build_attachments(self, scenario: ScenarioData) -> list[dict[str, str]]:
        """Build attachments list from scenario attachments and execution directory.
        
        Args:
            scenario: Scenario data
            
        Returns:
            List of attachment dictionaries
        """
        attachments = []
        
        # Add attachments from scenario.attachments
        for att in scenario.attachments:
            source = self._get_attachment_source(att)
            if source:
                attachments.append({
                    "name": att.get("description", "Attachment"),
                    "type": self._get_mime_type(att.get("type", "text/plain")),
                    "source": source
                })
        
        # Add attachments from execution directory (videos, console, network)
        # Pass scenario to help match videos to specific scenarios
        execution_attachments = self._find_execution_attachments(scenario)
        attachments.extend(execution_attachments)
        
        return attachments
    
    def build_step_attachments(self, step: StepData) -> list[dict[str, str]]:
        """Build attachments for a step.
        
        Args:
            step: Step data
            
        Returns:
            List of attachment dictionaries
        """
        attachments = []
        
        for screenshot in step.screenshots:
            source = self._get_screenshot_source(screenshot)
            if source:
                attachments.append({
                    "name": screenshot.get("description", "Screenshot"),
                    "type": "image/png",
                    "source": source
                })
        
        return attachments
    
    def _find_execution_attachments(self, scenario: ScenarioData = None) -> list[dict[str, str]]:
        """Find and attach files from execution directory.
        
        Args:
            scenario: Optional scenario data to match videos to specific scenarios
        
        Returns:
            List of attachment dictionaries
        """
        attachments = []
        
        if not self.execution_path.exists():
            return attachments
        
        # Find videos - only add one video per scenario (prefer scenario-specific, else first available)
        videos_dir = self.execution_path / "videos"
        if videos_dir.exists():
            video_files = list(videos_dir.glob("*.mp4"))
            
            # Try to match video to scenario by name (if scenario provided)
            matched_video = None
            if scenario:
                scenario_name_clean = scenario.name.lower().replace(" ", "_").replace("-", "_")
                for video_file in video_files:
                    video_name_lower = video_file.stem.lower()
                    # Check if scenario name appears in video filename
                    if scenario_name_clean in video_name_lower or video_name_lower in scenario_name_clean:
                        matched_video = video_file
                        break
            
            # If no match, use first video (one video per scenario)
            if not matched_video and video_files:
                matched_video = video_files[0]
            
            # Copy video if found and not already copied
            if matched_video:
                video_key = matched_video.name
                if video_key not in self._copied_videos:
                    source = self._copy_attachment_to_results(matched_video, "video/mp4")
                    if source:
                        self._copied_videos.add(video_key)
                        attachments.append({
                            "name": f"Test Execution Video ({matched_video.name})",
                            "type": "video/mp4",
                            "source": source
                        })
        
        # Find console logs
        console_file = self.execution_path / "console" / "console.jsonl"
        if console_file.exists():
            source = self._copy_attachment_to_results(console_file, "text/plain")
            if source:
                attachments.append({
                    "name": "Console Logs",
                    "type": "text/plain",
                    "source": source
                })
        
        # Find network data (HAR or JSON)
        network_dir = self.execution_path / "network"
        if network_dir.exists():
            for network_file in network_dir.glob("*.har"):
                source = self._copy_attachment_to_results(network_file, "application/json")
                if source:
                    attachments.append({
                        "name": f"Network Data ({network_file.name})",
                        "type": "application/json",
                        "source": source
                    })
            for network_file in network_dir.glob("*.json"):
                source = self._copy_attachment_to_results(network_file, "application/json")
                if source:
                    attachments.append({
                        "name": f"Network Metrics ({network_file.name})",
                        "type": "application/json",
                        "source": source
                    })
        
        return attachments
    
    def _copy_attachment_to_results(self, file_path: Path, mime_type: str) -> str:
        """Copy attachment file to results directory.
        
        Args:
            file_path: Path to source file
            mime_type: MIME type of the file
            
        Returns:
            Relative path to copied file (or empty string if failed)
        """
        try:
            if not file_path.exists():
                return ""
            
            # Copy to results directory
            dest_file = self.results_dir / file_path.name
            shutil.copy2(file_path, dest_file)
            
            # Return just the filename (Allure expects relative to results_dir)
            return file_path.name
            
        except (OSError, IOError, shutil.Error):
            return ""
    
    def _get_attachment_source(self, attachment: dict[str, Any]) -> str:
        """Get attachment source path.
        
        Args:
            attachment: Attachment dictionary
            
        Returns:
            Source path string (relative to results directory)
        """
        path = attachment.get("path", "")
        if not path:
            return ""
        
        # Convert to Path if string
        if isinstance(path, str):
            path = Path(path)
        
        # If absolute path, try to make relative to results_dir parent
        if path.is_absolute():
            try:
                # Try to make relative to execution directory (parent of allure-results)
                execution_dir = self.results_dir.parent
                relative_path = path.relative_to(execution_dir)
                return str(relative_path).replace('\\', '/')
            except ValueError:
                # If can't make relative, just use filename
                return path.name
        
        # Already relative, return as-is
        return str(path).replace('\\', '/')
    
    def _get_screenshot_source(self, screenshot: dict[str, Any]) -> str:
        """Get screenshot source path.
        
        Args:
            screenshot: Screenshot dictionary
            
        Returns:
            Source path string (relative to results directory)
        """
        path = screenshot.get("path", "")
        if not path:
            return ""
        
        # Convert to Path if string
        if isinstance(path, str):
            path = Path(path)
        
        # If absolute path, try to make relative to results_dir parent
        if path.is_absolute():
            try:
                # Try to make relative to execution directory (parent of allure-results)
                execution_dir = self.results_dir.parent
                relative_path = path.relative_to(execution_dir)
                return str(relative_path).replace('\\', '/')
            except ValueError:
                # If can't make relative, just use filename
                return path.name
        
        # Already relative, return as-is
        return str(path).replace('\\', '/')
    
    def _get_mime_type(self, file_type: str) -> str:
        """Get MIME type from file type string.
        
        Args:
            file_type: File type string
            
        Returns:
            MIME type string
        """
        mime_map = {
            "video": "video/mp4",
            "mp4": "video/mp4",
            "webm": "video/webm",
            "image": "image/png",
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "json": "application/json",
            "har": "application/json",
            "text": "text/plain",
            "txt": "text/plain",
            "jsonl": "text/plain",
        }
        return mime_map.get(file_type.lower(), "application/octet-stream")

