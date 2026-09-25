"""Widget capture through one seam instead of thirty patched functions.

Every element Streamlit renders, in any container, passes through
``DeltaGenerator._enqueue`` with its protobuf (type, id, label, key). We wrap
that one method once per process and, for sessions that are being tracked,
remember which widgets were rendered this run. At the end of the run we ask
Streamlit's own session state which of them changed, the same test it uses to
fire ``on_change`` callbacks.

Both hooks are private Streamlit API. If either is missing the capture is
disabled with one warning and the rest of the library keeps working.
"""

from __future__ import annotations

import logging
import threading
from typing import Any, Dict, List, NamedTuple, Optional

import streamlit as st

log = logging.getLogger("streamlit_analytics2")

TRIGGER_TYPES = frozenset(
    {"button", "form_submit_button", "download_button", "chat_input"}
)
FREE_TEXT_TYPES = frozenset({"text_input", "text_area", "chat_input"})
COUNT_ONLY_TYPES = frozenset(
    {
        "button",
        "form_submit_button",
        "download_button",
        "checkbox",
        "toggle",
        "file_uploader",
        "camera_input",
        "audio_input",
    }
)


class Rendered(NamedTuple):
    widget_type: str
    label: str
    key: Optional[str]


class Change(NamedTuple):
    widget_id: str
    widget_type: str
    label: str
    key: Optional[str]
    value: Any
    old_value: Any


_lock = threading.Lock()
_registry: Dict[str, Dict[str, Rendered]] = {}  # session id -> widget id -> info
_installed = False
_available: Optional[bool] = None


def _ctx() -> Any:
    from streamlit.runtime.scriptrunner import get_script_run_ctx

    return get_script_run_ctx(suppress_warning=True)


def _user_key(element_id: str) -> Optional[str]:
    try:
        from streamlit.runtime.state.common import user_key_from_element_id

        return user_key_from_element_id(element_id)
    except Exception:
        tail = element_id.rsplit("-", 1)[-1]
        return None if tail == "None" else tail


def _observe(delta_type: str, proto: Any) -> None:
    element_id = getattr(proto, "id", None)
    if not element_id:
        return
    ctx = _ctx()
    if ctx is None:
        return
    with _lock:
        reg = _registry.get(ctx.session_id)
    if reg is None:
        return
    widget_type = delta_type
    if delta_type == "checkbox" and getattr(proto, "type", 0) == 1:
        widget_type = "toggle"
    elif delta_type == "button" and getattr(proto, "is_form_submitter", False):
        widget_type = "form_submit_button"
    label = getattr(proto, "label", "") or getattr(proto, "placeholder", "")
    reg[element_id] = Rendered(widget_type, str(label), _user_key(element_id))


def install() -> bool:
    """Wrap the seam once per process. Returns whether capture is available."""
    global _installed, _available
    if _installed:
        return bool(_available)
    _installed = True
    try:
        from streamlit.delta_generator import DeltaGenerator
        from streamlit.runtime.state.session_state import SessionState

        if not callable(getattr(SessionState, "_widget_changed", None)):
            raise AttributeError("SessionState._widget_changed")
        original = DeltaGenerator._enqueue
    except Exception as exc:  # pragma: no cover - depends on streamlit version
        _available = False
        log.warning(
            "streamlit-analytics2: widget capture disabled, this Streamlit "
            "version (%s) lacks %s. Traffic tracking still works.",
            st.__version__,
            exc,
        )
        return False

    def _enqueue(
        self: Any, delta_type: str, element_proto: Any, *a: Any, **kw: Any
    ) -> Any:
        try:
            _observe(delta_type, element_proto)
        except Exception:  # never break the host app
            log.debug("capture: observe failed", exc_info=True)
        return original(self, delta_type, element_proto, *a, **kw)

    DeltaGenerator._enqueue = _enqueue  # type: ignore[method-assign]
    _available = True
    return True


def begin(session_id: str) -> None:
    with _lock:
        _registry[session_id] = {}


def end(session_id: str) -> List[Change]:
    """Return the widgets the user changed during this run."""
    with _lock:
        reg = _registry.pop(session_id, None)
    if not reg:
        return []
    ctx = _ctx()
    if ctx is None:
        return []
    try:
        state = ctx.session_state._state
    except AttributeError:
        return []
    seen = st.session_state.setdefault("_sa2_seen", set())
    changes: List[Change] = []
    for widget_id, info in reg.items():
        first_render = widget_id not in seen
        seen.add(widget_id)
        if first_render:
            # A widget rendering with its default is not an interaction.
            continue
        try:
            if not state._widget_changed(widget_id):
                continue
            value = state[widget_id]
        except Exception:
            log.debug("capture: no state for %s", widget_id, exc_info=True)
            continue
        if info.widget_type in TRIGGER_TYPES and not value:
            continue
        old = state._old_state.get(widget_id)
        changes.append(
            Change(widget_id, info.widget_type, info.label, info.key, value, old)
        )
    return changes


def record_values(change: Change, store_values: bool) -> List[Optional[str]]:
    """Turn a change into the value strings to record.

    Count-only widgets give ``[None]``. Free text gives a placeholder unless
    ``store_values`` is on. Multiselect gives one entry per newly added option.
    """
    t, v = change.widget_type, change.value
    if t in COUNT_ONLY_TYPES:
        return [None]
    if t in FREE_TEXT_TYPES:
        if v in (None, ""):
            return []
        return [_short(v)] if store_values else ["<text>"]
    if isinstance(v, (list, tuple, set)) and t == "multiselect":
        old = set(map(_short, change.old_value or []))
        added: List[Optional[str]] = [_short(x) for x in v if _short(x) not in old]
        return added
    if v is None or v == "":
        return []
    if isinstance(v, tuple) and len(v) == 2:
        return [f"{v[0]} - {v[1]}"]
    return [_short(v)]


def _short(v: Any) -> str:
    s = v if isinstance(v, str) else str(v)
    return s if len(s) <= 200 else s[:200]


def page_of(ctx: Any) -> Optional[str]:
    """Best-effort page name for the current run."""
    try:
        page_hash = ctx.page_script_hash
        pages = ctx.pages_manager.get_pages()
        info = pages.get(page_hash) or {}
        name = info.get("url_pathname") or info.get("page_name")
        if name is not None:
            return "/" + str(name).strip("/") if name != "" else "/"
    except Exception:
        log.debug("capture: pages_manager lookup failed", exc_info=True)
    try:
        url = st.context.url
        if url:
            from urllib.parse import urlsplit

            return urlsplit(url).path or "/"
    except Exception:
        log.debug("capture: st.context.url unavailable", exc_info=True)
    return None
