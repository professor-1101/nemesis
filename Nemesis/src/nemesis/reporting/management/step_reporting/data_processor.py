"""Step data processor for placeholder replacement and metadata extraction.

Responsibilities:
- Replace PLACEHOLDER values with actual test data
- Extract feature/scenario/step metadata
- Provide processed step names and metadata
"""
from typing import Any, Dict

from nemesis.infrastructure.logging import Logger


class StepDataProcessor:
    """Processes step data and replaces placeholders with actual values."""

    def __init__(self) -> None:
        """Initialize step data processor."""
        self.logger = Logger.get_instance({})

    def process_step_name(self, step: Any) -> str:
        """
        Process step name by replacing PLACEHOLDER values with actual data.

        Args:
            step: Behave step object

        Returns:
            Processed step name with actual values
        """
        step_name = getattr(step, 'name', str(step))

        # Replace PLACEHOLDER values with actual data for better reporting
        try:
            from nemesis.infrastructure.environment.hooks import _get_env_manager
            env_manager = _get_env_manager()

            if env_manager and hasattr(env_manager, 'context'):
                context = env_manager.context
                if hasattr(context, 'current_user_data') and context.current_user_data:
                    user_data = context.current_user_data
                    username = user_data.get('نام_کاربری', '')
                    password = user_data.get('رمز_عبور', '')

                    if username:
                        step_name = step_name.replace('"PLACEHOLDER"', f'"{username}"')
                    if password and '"رمز_عبور"' in step_name:
                        step_name = step_name.replace('"PLACEHOLDER"', f'"{password}"')

        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e:
            self.logger.debug(
                f"Failed to replace placeholders in step name: {e}",
                module=__name__,
                class_name="StepDataProcessor",
                method="process_step_name"
            )
            # Fallback to original step name

        return step_name

    def extract_metadata(self, step: Any) -> Dict[str, str]:
        """
        Extract feature, scenario, and code reference metadata from step.

        Args:
            step: Behave step object

        Returns:
            Dictionary with feature_name, scenario_name, code_ref
        """
        metadata = {
            "feature_name": "",
            "scenario_name": "",
            "code_ref": ""
        }

        try:
            if hasattr(step, 'scenario') and step.scenario:
                metadata["scenario_name"] = getattr(step.scenario, 'name', '')

                if hasattr(step.scenario, 'feature') and step.scenario.feature:
                    metadata["feature_name"] = getattr(step.scenario.feature, 'name', '')

                    # Extract code reference from feature
                    if hasattr(step.scenario.feature, 'filename'):
                        metadata["code_ref"] = getattr(step.scenario.feature, 'filename', '')

        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e:
            self.logger.debug(
                f"Failed to extract step metadata: {e}",
                module=__name__,
                class_name="StepDataProcessor",
                method="extract_metadata"
            )

        return metadata
