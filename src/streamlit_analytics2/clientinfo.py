"""Coarse, privacy-safe facts about the visiting browser.

Only families are kept (Chrome, macOS, Mobile). The raw User-Agent, the IP
address and the full URL are never stored.
"""

from __future__ import annotations

import contextlib
import re
from typing import Any, Dict, Optional
from urllib.parse import urlsplit

import streamlit as st

UTM_KEYS = ("utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term")


def browser_family(ua: str) -> str:
    if not ua:
        return "Unknown"
    if "Edg/" in ua or "EdgA/" in ua or "EdgiOS/" in ua:
        return "Edge"
    if "OPR/" in ua or "Opera" in ua:
        return "Opera"
    if "SamsungBrowser" in ua:
        return "Samsung Internet"
    if "Firefox/" in ua or "FxiOS/" in ua:
        return "Firefox"
    if "CriOS/" in ua or ("Chrome/" in ua and "Chromium" not in ua):
        return "Chrome"
    if "Chromium" in ua:
        return "Chromium"
    if "Safari/" in ua and "Chrome" not in ua:
        return "Safari"
    if re.search(r"bot|crawl|spider|slurp|headless", ua, re.I):
        return "Bot"
    return "Other"


def os_family(ua: str) -> str:
    if not ua:
        return "Unknown"
    if "iPhone" in ua or "iPad" in ua or "iPod" in ua:
        return "iOS"
    if "Android" in ua:
        return "Android"
    if "Windows" in ua:
        return "Windows"
    if "Mac OS X" in ua or "Macintosh" in ua:
        return "macOS"
    if "CrOS" in ua:
        return "ChromeOS"
    if "Linux" in ua:
        return "Linux"
    return "Other"


def device_family(ua: str) -> str:
    if not ua:
        return "Unknown"
    if "iPad" in ua or "Tablet" in ua or ("Android" in ua and "Mobile" not in ua):
        return "Tablet"
    if "Mobile" in ua or "iPhone" in ua:
        return "Mobile"
    return "Desktop"


def session_props() -> Dict[str, Any]:
    """Facts recorded once per session. Missing values are simply absent."""
    props: Dict[str, Any] = {}
    try:
        ctx = st.context
    except Exception:
        return props
    ua = ""
    try:
        ua = ctx.headers.get("User-Agent", "") if ctx.headers else ""
    except Exception:
        ua = ""
    if ua:
        props["browser"] = browser_family(ua)
        props["os"] = os_family(ua)
        props["device"] = device_family(ua)
    for attr, key in (("locale", "locale"), ("timezone", "timezone")):
        try:
            value = getattr(ctx, attr)
        except Exception:
            value = None
        if value:
            props[key] = value
    with contextlib.suppress(Exception):
        theme = ctx.theme.type if ctx.theme else None
        if theme:
            props["theme"] = theme
    with contextlib.suppress(Exception):
        if ctx.is_embedded:
            props["embedded"] = True
    utm = utm_params()
    if utm:
        props.update(utm)
    return props


def utm_params() -> Dict[str, str]:
    """UTM tags from the current URL, the privacy-safe stand-in for referrers."""
    out: Dict[str, str] = {}
    with contextlib.suppress(Exception):
        qp = st.query_params
        for k in UTM_KEYS:
            v = qp.get(k)
            if v:
                out[k] = str(v)[:100]
    return out


def page_from_url(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    parts = urlsplit(url)
    return parts.path or "/"
