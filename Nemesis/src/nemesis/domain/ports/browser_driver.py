"""Browser automation interface"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Protocol, Any, Optional, Dict, List
from pathlib import Path


class IPage(Protocol):
    """Browser page interface"""

    @abstractmethod
    def goto(self, url: str, **options) -> None: ...

    @abstractmethod
    def click(self, selector: str, **options) -> None: ...

    @abstractmethod
    def fill(self, selector: str, value: str, **options) -> None: ...

    @abstractmethod
    def get_text(self, selector: str) -> str: ...

    @abstractmethod
    def is_visible(self, selector: str) -> bool: ...

    @abstractmethod
    def screenshot(self, **options) -> bytes: ...

    @abstractmethod
    def evaluate(self, script: str) -> Any: ...

    @abstractmethod
    def close(self) -> None: ...


class IBrowser(Protocol):
    """Browser instance interface"""

    @abstractmethod
    def new_page(self) -> IPage: ...

    @abstractmethod
    def close(self) -> None: ...

    @abstractmethod
    def contexts(self) -> List[Any]: ...


class IBrowserDriver(ABC):
    """Browser driver port"""

    @abstractmethod
    def launch(
        self,
        headless: bool = False,
        args: Optional[List[str]] = None,
        **options
    ) -> IBrowser:
        """
        Launch browser

        Args:
            headless: Run in headless mode
            args: Browser launch arguments
            **options: Additional browser options

        Returns:
            IBrowser instance
        """
        ...

    @abstractmethod
    def close(self) -> None:

        ...

    @abstractmethod
    def is_running(self) -> bool:

        ...

    @abstractmethod
    def get_browser_type(self) -> str:

        ...

    @abstractmethod
    def create_context(
        self,
        browser: IBrowser,
        record_video: bool = False,
        record_har: bool = False,
        **options
    ) -> Any:
        """
        Create browser context with optional recording

        Args:
            browser: Browser instance
            record_video: Enable video recording
            record_har: Enable HAR recording
            **options: Additional context options

        Returns:
            Browser context
        """
        ...

    @abstractmethod
    def save_trace(self, trace_path: Path) -> None:

        ...

    @abstractmethod
    def save_video(self, video_path: Path) -> Optional[Path]:

        ...
