"""Base class for report-related utilities with shared initialization."""

import traceback
from pathlib import Path

from nemesis.infrastructure.logging import Logger
from nemesis.utils import get_path_manager


class ReportBase:
    """Base class for report utilities with shared path management."""

    def __init__(self, reports_dir: Path | None = None):
        """Initialize with reports directory.

        Args:
            reports_dir: Optional custom reports directory, otherwise uses PathManager
        """
        if reports_dir:
            self.reports_dir = reports_dir
        else:
            # Use PathManager for centralized path management
            try:
                path_manager = get_path_manager()
                self.reports_dir = path_manager.get_reports_dir()
            except (KeyboardInterrupt, SystemExit):  # pylint: disable=try-except-raise
                # Always re-raise these to allow proper program termination
                # NOTE: KeyboardInterrupt and SystemExit must propagate to allow graceful shutdown
                raise
            except (AttributeError, KeyError, RuntimeError) as e:
                # PathManager initialization errors - fallback to default
                logger = Logger.get_instance({})
                logger.debug(
                    f"PathManager failed, using default reports dir: {e}",
                    traceback=traceback.format_exc(),
                    module=__name__,
                    class_name=self.__class__.__name__,
                    method="__init__"
                )
                self.reports_dir = Path("reports")
