"""Fingerprint generation and rotation for Camoufox sessions."""

from __future__ import annotations

from typing import Any, Optional, Tuple, Union

from camoufox.utils import generate_fingerprint  # type: ignore[attr-defined]


def generate_rotated_fingerprint(
    *,
    os: Optional[Union[str, Tuple[str, ...]]] = None,
    window: Optional[Tuple[int, int]] = None,
    **kwargs: Any,
) -> Any:
    """Generate a fresh BrowserForge fingerprint for context rotation.

    Args:
        os: Target OS filter (e.g., "windows", "macos", "linux").
        window: Window size as (width, height).
        **kwargs: Additional kwargs passed to generate_fingerprint.

    Returns:
        A BrowserForge Fingerprint object.
    """
    gen_kwargs: dict[str, Any] = {}
    if os is not None:
        gen_kwargs["os"] = os
    if window is not None:
        gen_kwargs["window"] = window
    gen_kwargs.update(kwargs)
    return generate_fingerprint(**gen_kwargs)
