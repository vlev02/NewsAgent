"""
SimuControl - Backward Compatibility Control Panel

DEPRECATED: Use SimuRequest directly instead.

This module provides convenience functions for the legacy control panel API.
All functions delegate to SimuRequest class methods.

Recommended usage:
    from src.utils.simu_request import SimuRequest

    # Instead of:
    from src.utils.simu_control import enable_simu, disable_simu
    enable_simu()

    # Use:
    SimuRequest.update_behaviors(simu_call=1, update_response=0)
    SimuRequest.status()
"""

from src.utils.simu_request import SimuRequest


def enable_simu(verbose: bool = True) -> None:
    """
    DEPRECATED: Use SimuRequest.update_behaviors() instead.

    Enable simulation mode (use cached responses).
    Sets: simu_call=1, update_response=0

    Args:
        verbose: Print confirmation message
    """
    SimuRequest.update_behaviors(simu_call=1, update_response=0, verbose=verbose)
    if verbose:
        print("✓ Simulation ENABLED (using cached responses)")


def disable_simu(verbose: bool = True) -> None:
    """
    DEPRECATED: Use SimuRequest.update_behaviors() instead.

    Disable simulation mode (use real API).
    Sets: simu_call=0, update_response=0

    Args:
        verbose: Print confirmation message
    """
    SimuRequest.update_behaviors(simu_call=0, update_response=0, verbose=False)
    if verbose:
        print("✓ Simulation DISABLED (calling real API)")


def refresh_cache(verbose: bool = True) -> None:
    """
    DEPRECATED: Use SimuRequest.update_behaviors() instead.

    Enable cache refresh mode (call real API and update cache).
    Sets: simu_call=0, update_response=1

    Args:
        verbose: Print confirmation message
    """
    SimuRequest.update_behaviors(simu_call=0, update_response=1, verbose=False)
    if verbose:
        print("✓ Cache REFRESH mode ENABLED (calling real API and updating cache)")


def capture_cache(verbose: bool = True) -> None:
    """
    DEPRECATED: Use SimuRequest.update_behaviors() instead.

    Enable capture mode (call real API and save to cache, no simulation).
    Sets: simu_call=0, update_response=1

    Same as refresh_cache() - calls real API and saves responses.

    Args:
        verbose: Print confirmation message
    """
    refresh_cache(verbose=verbose)


def quiet(verbose: bool = True) -> None:
    """
    DEPRECATED: Use SimuRequest.update_behaviors() instead.

    Disable logging output.
    Sets: log_calls=0

    Args:
        verbose: Print confirmation message
    """
    SimuRequest.update_behaviors(log_calls=0, verbose=False)
    if verbose:
        print("✓ Logging DISABLED")


def verbose(verbose_param: bool = True) -> None:
    """
    DEPRECATED: Use SimuRequest.update_behaviors() instead.

    Enable logging output.
    Sets: log_calls=1

    Args:
        verbose_param: Print confirmation message
    """
    SimuRequest.update_behaviors(log_calls=1, verbose=False)
    if verbose_param:
        print("✓ Logging ENABLED")


def set_simu_flags(
    simu_call: int = None,
    update_response: int = None,
    log_calls: int = None,
    verbose: bool = True
) -> None:
    """
    DEPRECATED: Use SimuRequest.update_behaviors() instead.

    Set custom SimuCall flags.

    Args:
        simu_call: 1 = use cache, 0 = use API
        update_response: 1 = update cache, 0 = no update
        log_calls: 1 = enable logging, 0 = disable logging
        verbose: Print confirmation message

    Example:
        set_simu_flags(simu_call=1, update_response=0)
    """
    SimuRequest.update_behaviors(
        simu_call=simu_call,
        update_response=update_response,
        log_calls=log_calls,
        verbose=verbose
    )


def show_config() -> None:
    """
    DEPRECATED: Use SimuRequest.status() instead.

    Display current SimuCall configuration.
    """
    SimuRequest.status()


def get_config() -> dict:
    """
    DEPRECATED: Use SimuRequest.status() instead.

    Get current configuration as dictionary (non-verbose).
    """
    return SimuRequest.status()


# Quick aliases for common workflows
def dev():
    """
    DEPRECATED: Use SimuRequest.update_behaviors() instead.

    Start development mode (simulation enabled with logging)
    """
    SimuRequest.update_behaviors(simu_call=1, log_calls=1, verbose=True)


def test():
    """
    DEPRECATED: Use SimuRequest.update_behaviors() instead.

    Start test mode (simulation only, quiet)
    """
    SimuRequest.update_behaviors(simu_call=1, log_calls=0, verbose=True)


def update():
    """
    DEPRECATED: Use SimuRequest.update_behaviors() instead.

    Start update mode (refresh cache from real API)
    """
    SimuRequest.update_behaviors(simu_call=0, update_response=1, verbose=True)


def live():
    """
    DEPRECATED: Use SimuRequest.update_behaviors() instead.

    Start live mode (real API only, no caching)
    """
    SimuRequest.update_behaviors(simu_call=0, update_response=0, verbose=True)
