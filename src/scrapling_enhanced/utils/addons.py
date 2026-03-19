"""Firefox addon validation helpers."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

log = logging.getLogger(__name__)


def validate_addon_paths(addons: Optional[List[str]]) -> Optional[List[str]]:
    """Validate addon file paths, skip invalid ones with warnings.

    Args:
        addons: List of paths to .xpi files, or None.

    Returns:
        Filtered list of valid addon paths, or None if empty/None.
    """
    if not addons:
        return None

    valid: List[str] = []
    for addon_path in addons:
        path = Path(addon_path)
        if not path.exists():
            log.warning(f"Addon not found, skipping: {addon_path}")
            continue
        if path.suffix.lower() != ".xpi":
            log.warning(f"Addon is not a .xpi file, skipping: {addon_path}")
            continue
        valid.append(str(path))

    return valid if valid else None
