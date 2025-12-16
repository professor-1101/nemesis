"""Exception handling utilities to reduce code duplication."""


def handle_keyboard_and_system_exit(func):
    """Decorator to handle KeyboardInterrupt and SystemExit exceptions.

    This decorator ensures that KeyboardInterrupt and SystemExit are always re-raised,
    which is a common pattern throughout the codebase to allow proper program termination.
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (KeyboardInterrupt, SystemExit):
            # Always re-raise these to allow proper program termination
            raise
    return wrapper

