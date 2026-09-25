"""Public API: track / start_tracking / stop_tracking / event.

Every call signature from 0.10 is kept. New keyword-only options:
``store_values`` (record free text, off by default), ``events_path`` (JSONL or
SQLite event log) and ``store`` (your own backend).
"""

from __future__ import annotations

import datetime
import hashlib
import json
import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Union, cast

import streamlit as st
from streamlit import session_state as ss

from . import aggregate, capture, clientinfo, display
from . import events as ev
from . import firestore, storage, utils
from .state import data, reset_data

log = logging.getLogger("streamlit_analytics2")

PathLike = Union[str, Path]

_memory_store = storage.MemoryStore()
_json_loaded: set = set()

_CFG = "_sa2_cfg"
_PENDING = "_sa2_pending"


def update_session_stats(data_dict: Dict[str, Any]) -> None:
    """Legacy per-run counters (pageviews, script runs, time, per day)."""
    today = str(datetime.date.today())
    if data_dict["per_day"]["days"][-1] != today:
        data_dict["per_day"]["days"].append(today)
        data_dict["per_day"]["pageviews"].append(0)
        data_dict["per_day"]["script_runs"].append(0)
    data_dict["total_script_runs"] += 1
    data_dict["per_day"]["script_runs"][-1] += 1
    now = datetime.datetime.now()
    data_dict["total_time_seconds"] += (
        now - st.session_state.last_time
    ).total_seconds()
    st.session_state.last_time = now
    if not st.session_state.user_tracked:
        st.session_state.user_tracked = True
        data_dict["total_pageviews"] += 1
        data_dict["per_day"]["pageviews"][-1] += 1


def _track_user() -> None:
    update_session_stats(data)
    update_session_stats(ss.session_data)


def _visitor_id() -> Optional[str]:
    """Daily-rotating hash of ip + user agent. Never stored raw."""
    try:
        ctx = st.context
        ip = ctx.ip_address or ""
        ua = ctx.headers.get("User-Agent", "") if ctx.headers else ""
    except Exception:
        return None
    if not ip and not ua:
        return None
    salt = datetime.date.today().isoformat()
    return hashlib.sha256(f"{salt}|{ip}|{ua}".encode()).hexdigest()[:16]


def _dashboard_open() -> bool:
    try:
        qp = st.query_params
        return "analytics" in qp and "on" in qp["analytics"]
    except Exception:
        return False


def _session_id() -> str:
    ctx = capture._ctx()
    return ctx.session_id if ctx is not None else "no-session"


def _resolve_store(cfg: Dict[str, Any]) -> storage.Store:
    if cfg.get("store") is not None:
        return cast(storage.Store, cfg["store"])
    path = cfg.get("events_path") or storage.events_path_for(cfg.get("save_to_json"))
    if path is not None:
        return storage.open_store(path)
    return _memory_store


def _load_json_once(path: PathLike, verbose: bool) -> None:
    key = str(Path(path).resolve())
    if key in _json_loaded:
        return
    _json_loaded.add(key)
    try:
        json_data = json.loads(Path(path).read_text())
        data.update({k: json_data[k] for k in json_data if k in data})
        if verbose:
            log.info("Loaded data from %s", path)
    except FileNotFoundError:
        if verbose:
            log.warning("File %s not found, proceeding with empty data", path)
    except Exception as exc:
        log.error("Error loading data from %s: %s", path, exc)


def _use_firestore(cfg: Dict[str, Any]) -> bool:
    return bool(cfg.get("firestore_key_file")) or (
        cfg.get("streamlit_secrets_firestore_key") is not None
        and cfg.get("firestore_project_name") is not None
    )


def start_tracking(
    unsafe_password: Optional[str] = None,
    save_to_json: Optional[PathLike] = None,
    load_from_json: Optional[PathLike] = None,
    firestore_project_name: Optional[str] = None,
    firestore_collection_name: Optional[str] = None,
    firestore_document_name: Optional[str] = "counts",
    firestore_key_file: Optional[str] = None,
    streamlit_secrets_firestore_key: Optional[str] = None,
    session_id: Optional[str] = None,
    verbose: bool = False,
    *,
    store_values: bool = False,
    events_path: Optional[PathLike] = None,
    store: Optional[storage.Store] = None,
) -> None:
    """Start tracking user inputs to a streamlit app.

    If you call this function directly, you NEED to call `stop_tracking()` at
    the end of your streamlit script. For a more convenient interface, wrap
    your streamlit calls in `with streamlit_analytics2.track():`.
    """
    cfg = dict(
        unsafe_password=unsafe_password,
        save_to_json=save_to_json,
        load_from_json=load_from_json,
        firestore_project_name=firestore_project_name,
        firestore_collection_name=firestore_collection_name,
        firestore_document_name=firestore_document_name,
        firestore_key_file=firestore_key_file,
        streamlit_secrets_firestore_key=streamlit_secrets_firestore_key,
        session_id=session_id,
        verbose=verbose,
        store_values=store_values,
        events_path=events_path,
        store=store,
    )
    if verbose and not log.handlers:
        log.addHandler(logging.StreamHandler())
        log.setLevel(logging.INFO)

    utils.initialize_session_data()
    if _use_firestore(cfg) and not data["loaded_from_firestore"]:
        firestore.load(
            data,
            firestore_key_file,
            firestore_collection_name,
            firestore_document_name,
            streamlit_secrets_firestore_key,
            firestore_project_name,
            session_id=session_id,
        )
        data["loaded_from_firestore"] = True
    if load_from_json is not None:
        _load_json_once(load_from_json, verbose)

    if "user_tracked" not in st.session_state:
        st.session_state.user_tracked = False
    if "last_time" not in st.session_state:
        st.session_state.last_time = datetime.datetime.now()
    first_run = not st.session_state.user_tracked
    _track_user()

    # Traffic events: no patching involved. A run with the dashboard open is
    # the app owner looking at analytics, not traffic, so it is not recorded.
    ctx = capture._ctx()
    sid = ctx.session_id if ctx is not None else "no-session"
    page = capture.page_of(ctx) if ctx is not None else None
    visitor = _visitor_id()
    now = ev.now_iso()
    pending: List[ev.Event] = []
    if not _dashboard_open():
        if first_run:
            props = clientinfo.session_props()
            pending.append(
                ev.Event(now, ev.SESSION, sid, visitor, page, props=props or None)
            )
        if first_run or st.session_state.get("_sa2_page") != page:
            st.session_state["_sa2_page"] = page
            pending.append(ev.Event(now, ev.PAGEVIEW, sid, visitor, page))
        pending.append(ev.Event(now, ev.RUN, sid, visitor, page))

    st.session_state[_CFG] = cfg
    st.session_state[_PENDING] = pending
    if capture.install():
        capture.begin(sid)


def event(name: str, **props: Any) -> None:
    """Record a custom event from app code, e.g. ``sa2.event("report", rows=12)``.

    Call it inside ``with track():`` (or between start and stop). Outside a
    tracked run the event goes to the in-memory store only.
    """
    e = ev.Event(
        ev.now_iso(),
        ev.CUSTOM,
        _session_id(),
        _visitor_id(),
        st.session_state.get("_sa2_page"),
        name=name,
        props=props or None,
    )
    pending = st.session_state.get(_PENDING)
    if pending is not None:
        pending.append(e)
    else:
        _memory_store.append([e])


def stop_tracking(
    unsafe_password: Optional[str] = None,
    save_to_json: Optional[PathLike] = None,
    load_from_json: Optional[PathLike] = None,
    firestore_project_name: Optional[str] = None,
    firestore_collection_name: Optional[str] = None,
    firestore_document_name: Optional[str] = "counts",
    firestore_key_file: Optional[str] = None,
    streamlit_secrets_firestore_key: Optional[str] = None,
    session_id: Optional[str] = None,
    verbose: bool = False,
    *,
    store_values: Optional[bool] = None,
    events_path: Optional[PathLike] = None,
    store: Optional[storage.Store] = None,
) -> None:
    """Stop tracking user inputs to a streamlit app.

    Should be called after `start_tracking()`. This method also shows the
    analytics results below your app if you attach `?analytics=on` to the URL.
    """
    cfg: Dict[str, Any] = dict(st.session_state.get(_CFG) or {})
    for k, v in dict(
        unsafe_password=unsafe_password,
        save_to_json=save_to_json,
        load_from_json=load_from_json,
        firestore_project_name=firestore_project_name,
        firestore_collection_name=firestore_collection_name,
        firestore_key_file=firestore_key_file,
        streamlit_secrets_firestore_key=streamlit_secrets_firestore_key,
        session_id=session_id,
        store_values=store_values,
        events_path=events_path,
        store=store,
    ).items():
        if v is not None:
            cfg[k] = v
    if firestore_document_name != "counts" or "firestore_document_name" not in cfg:
        cfg["firestore_document_name"] = firestore_document_name
    if verbose:
        cfg["verbose"] = True

    sid = _session_id()
    pending: List[ev.Event] = list(st.session_state.pop(_PENDING, []) or [])
    page = st.session_state.get("_sa2_page")
    visitor = pending[0].visitor if pending else _visitor_id()
    now = ev.now_iso()
    for change in capture.end(sid):
        name = aggregate.widget_name(change.label, change.key, change.widget_id)
        for value in capture.record_values(change, bool(cfg.get("store_values"))):
            aggregate.apply_widget(data, change.widget_type, name, value)
            aggregate.apply_widget(ss.session_data, change.widget_type, name, value)
            pending.append(
                ev.Event(
                    now,
                    ev.WIDGET,
                    sid,
                    visitor,
                    page,
                    name=change.label or None,
                    widget_id=change.widget_id,
                    widget_type=change.widget_type,
                    key=change.key,
                    value=value,
                )
            )

    active_store = _resolve_store(cfg)
    try:
        active_store.append(pending)
    except Exception as exc:
        log.error("streamlit-analytics2: could not store events: %s", exc)

    if cfg.get("verbose"):
        log.info("Finished script execution. New data: %s", data)

    if _use_firestore(cfg):
        firestore.save(
            data,
            cfg.get("firestore_key_file"),
            cfg.get("firestore_collection_name"),
            cfg.get("firestore_document_name"),
            cfg.get("streamlit_secrets_firestore_key"),
            cfg.get("firestore_project_name"),
            session_id=cfg.get("session_id"),
        )

    if cfg.get("save_to_json") is not None:
        file_path = Path(cfg["save_to_json"])
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("w") as f:
            json.dump(data, f)
        if cfg.get("verbose"):
            log.info("Storing results to file: %s", file_path)

    if _dashboard_open():

        @st.dialog("Streamlit-Analytics2", width="large")
        def show_sa2() -> None:
            display.show_results(
                data, reset_data, cfg.get("unsafe_password"), store=active_store
            )

        show_sa2()


@contextmanager
def track(
    unsafe_password: Optional[str] = None,
    save_to_json: Optional[PathLike] = None,
    load_from_json: Optional[PathLike] = None,
    firestore_project_name: Optional[str] = None,
    firestore_collection_name: Optional[str] = None,
    firestore_document_name: Optional[str] = "counts",
    firestore_key_file: Optional[str] = None,
    streamlit_secrets_firestore_key: Optional[str] = None,
    session_id: Optional[str] = None,
    verbose: bool = False,
    *,
    store_values: bool = False,
    events_path: Optional[PathLike] = None,
    store: Optional[storage.Store] = None,
) -> Iterator[None]:
    """Context manager to start and stop tracking user inputs to a streamlit app.

    To use this, make calls to streamlit in `with streamlit_analytics2.track():`.
    This also shows the analytics results below your app if you attach
    `?analytics=on` to the URL.
    """
    start_tracking(
        unsafe_password=unsafe_password,
        save_to_json=save_to_json,
        load_from_json=load_from_json,
        firestore_project_name=firestore_project_name,
        firestore_collection_name=firestore_collection_name,
        firestore_document_name=firestore_document_name,
        firestore_key_file=firestore_key_file,
        streamlit_secrets_firestore_key=streamlit_secrets_firestore_key,
        session_id=session_id,
        verbose=verbose,
        store_values=store_values,
        events_path=events_path,
        store=store,
    )
    yield
    stop_tracking(firestore_document_name=firestore_document_name)


reset_data()
