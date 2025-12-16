"""Shipping manager for multi-channel log delivery."""
import logging
from typing import Any, Dict, List

from ..config.settings import LoggingConfig
from .channels.local import LocalChannel


class ShippingManager:
    """Manages log shipping to multiple channels."""

    def __init__(self, config: LoggingConfig):
        """Initialize shipping manager."""
        self.config = config
        self._channels = self._initialize_channels()

    def _initialize_channels(self) -> Dict[str, Any]:
        """Initialize shipping channels."""
        channels = {}

        # Local channel
        if "local" in self.config.enabled_channels:
            channels["local"] = LocalChannel(self.config.local_config)

        # SigNoz channel - TODO: implement when needed
        # if "signoz" in self.config.enabled_channels:
        #     channels["signoz"] = SigNozChannel(self.config.signoz_config)

        return channels


    def send_log(self, log_data: Dict[str, Any], channel_names: List[str]) -> bool:
        """Send log to specified channels with direct sending only."""
        if not log_data:
            return True

        # Filter channels
        target_channels = [
            name for name in channel_names
            if name in self._channels
        ]

        if not target_channels:
            return True

        # Direct sending only for reliability
        return self._send_directly(log_data, target_channels)


    def _send_directly(self, log_data: Dict[str, Any], target_channels: List[str]) -> bool:
        """Send log directly to channels."""
        success_count = 0
        for channel_name in target_channels:
            try:
                channel = self._channels.get(channel_name)
                if channel and self._send_to_channel(channel, log_data):
                    success_count += 1
            except (OSError, IOError) as e:
                # Channel file I/O errors
                logger = logging.getLogger("nemesis.shipping")
                logger.error("Channel %s failed - I/O error: %s", channel_name, e, exc_info=True)
            except (AttributeError, RuntimeError) as e:
                # Channel API errors
                logger = logging.getLogger("nemesis.shipping")
                logger.error("Channel %s failed - API error: %s", channel_name, e, exc_info=True)
            except Exception as e:  # pylint: disable=broad-exception-caught
                # Catch-all for unexpected errors from channel operations
                # NOTE: Channel.send_log may raise various exceptions we cannot predict
                logger = logging.getLogger("nemesis.shipping")
                logger.error("Channel %s failed: %s", channel_name, e, exc_info=True)
        return success_count > 0

    def _send_to_channel(self, channel: Any, log_data: Dict[str, Any]) -> bool:
        """Send log to a single channel."""
        try:
            return channel.send_log(log_data)
        except (OSError, IOError) as e:
            # Channel file I/O errors
            logger = logging.getLogger("nemesis.shipping")
            logger.error("Channel send failed - I/O error: %s", e, exc_info=True)
            print(f"Channel send failed: {e}")
            return False
        except (AttributeError, RuntimeError) as e:
            # Channel API errors
            logger = logging.getLogger("nemesis.shipping")
            logger.error("Channel send failed - API error: %s", e, exc_info=True)
            print(f"Channel send failed: {e}")
            return False
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for unexpected errors from channel.send_log
            # NOTE: channel.send_log may raise various exceptions we cannot predict
            logger = logging.getLogger("nemesis.shipping")
            logger.error("Channel send failed: %s", e, exc_info=True)
            print(f"Channel send failed: {e}")
            return False
