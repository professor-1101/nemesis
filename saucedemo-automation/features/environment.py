"""Simplified Behave environment using Nemesis framework."""

# Import Nemesis environment hooks
from nemesis.environment import (
    before_all, after_all, before_feature, after_feature,
    before_scenario, after_scenario, before_step, after_step
)

# CRITICAL FIX: Hooks must be defined in the global scope for Behave to discover them
# The imported functions are now available in the global scope

# AUTO-DISCOVERY RESTORED: Nemesis hooks are now fixed
# Behave will automatically discover step definitions in the steps/ directory
# No manual imports needed - Nemesis hooks are now non-blocking and lazy
