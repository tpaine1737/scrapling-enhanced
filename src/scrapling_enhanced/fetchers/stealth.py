"""Enhanced StealthyFetcher backed by Camoufox instead of Patchright/Chromium."""

from __future__ import annotations

from typing import Any, Optional

from scrapling import StealthyFetcher as _OriginalStealthyFetcher
from scrapling.engines.toolbelt.custom import Response

from scrapling_enhanced.config import CamoufoxConfig
from scrapling_enhanced.engine._stealth import CamoufoxStealthySession


class StealthyFetcher(_OriginalStealthyFetcher):
    """Drop-in replacement for Scrapling's StealthyFetcher using Camoufox.

    All ``configure()`` kwargs (``huge_tree``, ``adaptive``, etc.) work
    identically to the parent class. Pass an optional ``camoufox_config``
    to control Camoufox-specific behaviour.
    """

    _camoufox_config: Optional[CamoufoxConfig] = None

    @classmethod
    def configure(cls, **kwargs: Any) -> None:
        """Configure parser and Camoufox options.

        Accepts all keyword arguments that the parent ``BaseFetcher.configure()``
        supports (``huge_tree``, ``adaptive``, ``storage``, ``storage_args``,
        ``keep_cdata``, ``keep_comments``, ``adaptive_domain``) plus the
        additional keyword ``camoufox_config``.

        :param camoufox_config: A :class:`~scrapling_enhanced.config.CamoufoxConfig`
            instance to use for all subsequent ``fetch()`` calls.  When
            ``None`` (the default) the existing stored config (or Camoufox's
            own defaults) is used.
        """
        camoufox_config = kwargs.pop("camoufox_config", None)
        if camoufox_config is not None:
            cls._camoufox_config = camoufox_config
        if kwargs:
            super().configure(**kwargs)  # type: ignore[no-untyped-call]

    @classmethod
    def fetch(cls, url: str, **kwargs: Any) -> Response:
        """Fetch *url* using a Camoufox-backed stealthy browser session.

        Accepts all keyword arguments that Scrapling's ``StealthyFetcher.fetch()``
        accepts — they are forwarded unchanged to
        :class:`~scrapling_enhanced.engine._stealth.CamoufoxStealthySession`.

        :param url: Target URL.
        :return: A Scrapling ``Response`` object.
        """
        selector_config = kwargs.pop("selector_config", None) or kwargs.pop("custom_config", {})
        if not isinstance(selector_config, dict):
            raise TypeError("Argument `selector_config` must be a dictionary.")

        kwargs["selector_config"] = {**cls._generate_parser_arguments(), **selector_config}

        with CamoufoxStealthySession(camoufox_config=cls._camoufox_config, **kwargs) as session:
            return session.fetch(url)  # type: ignore[no-any-return]

    @classmethod
    async def async_fetch(cls, url: str, **kwargs: Any) -> "Response":
        """Async variant — not yet implemented.

        :raises NotImplementedError: Always.
        """
        raise NotImplementedError("Async fetch is not yet implemented.")
