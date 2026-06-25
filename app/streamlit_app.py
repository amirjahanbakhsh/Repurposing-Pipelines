"""Professional Streamlit interface for pipeline repurposing screening."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

try:
    import pydeck as pdk
    _PYDECK_OK = True
except ImportError:
    _PYDECK_OK = False


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SCREENING_DIR = ROOT / "model_layers" / "06_screening_and_decision"
DATA_DIR = ROOT / "model_layers" / "01_data_foundation"
COST_DIR = ROOT / "model_layers" / "04_cost_economics"
LCA_DIR = ROOT / "model_layers" / "05_lca"
ASSET_DIR = ROOT / "app" / "assets"
ALL_ROUTES_PATH = ASSET_DIR / "nsta_all_routes.json"
CANDIDATE_ROUTES_PATH = ASSET_DIR / "nsta_candidate_routes.json"


st.set_page_config(
    page_title="CO2 Pipeline Repurposing Evaluation Tool",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)


KNOWN_CASES = {
    "Goldeneye - poster assumptions": {
        "selection_id": "goldeneye_poster",
        "map_pipeline_id": "PL1978",
        "screening_scenario": "goldeneye_poster",
        "cost_case": "goldeneye_poster",
        "lca_scenario": "goldeneye_poster",
        "label": "20 in Gas Goldeneye - St. Fergus",
    },
    "Goldeneye - dissertation assumptions": {
        "selection_id": "goldeneye_dissertation",
        "map_pipeline_id": "PL1978",
        "screening_scenario": "goldeneye_dissertation",
        "cost_case": "goldeneye_benchmark",
        "lca_scenario": "goldeneye_dissertation",
        "label": "20 in Gas Goldeneye - St. Fergus",
    },
}


@st.cache_data(show_spinner=False)
def load_csv(path: str) -> pd.DataFrame:
    csv_path = Path(path)
    if not csv_path.exists():
        return pd.DataFrame()
    return pd.read_csv(csv_path)


@st.cache_data(show_spinner=False)
def load_routes(path: str) -> dict[str, Any]:
    route_path = Path(path)
    if not route_path.exists():
        return {"routes": []}
    with route_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@st.cache_data(show_spinner=False)
def load_all_routes() -> dict[str, Any]:
    """Load the full-fleet route JSON if available; fall back to candidate routes."""
    if ALL_ROUTES_PATH.exists():
        with ALL_ROUTES_PATH.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    if CANDIDATE_ROUTES_PATH.exists():
        with CANDIDATE_ROUTES_PATH.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    return {"routes": []}


def find_route_record(all_routes_payload: dict[str, Any], pipeline_id: str) -> dict[str, Any] | None:
    """Return the first route record matching *pipeline_id* (any pipeline, not just candidates)."""
    for record in all_routes_payload.get("routes", []):
        if record.get("pipeline_id") == pipeline_id:
            return record
    return None


def route_summary_table(all_routes_payload: dict[str, Any]) -> pd.DataFrame:
    """Build a unique pipeline-level table from the route-part payload for fallback selection."""
    rows: dict[str, dict[str, Any]] = {}
    for record in all_routes_payload.get("routes", []):
        pipeline_id = str(record.get("pipeline_id") or "").strip().upper()
        if not pipeline_id or pipeline_id in rows:
            continue
        rows[pipeline_id] = {
            "pipeline_id": pipeline_id,
            "pipeline_name": clean_text(record.get("pipeline_name"), pipeline_id),
            "is_candidate": bool(record.get("is_candidate")),
            "status": clean_text(record.get("status"), ""),
            "fluid": clean_text(record.get("fluid"), ""),
            "display": (
                f"{pipeline_id} - {clean_text(record.get('pipeline_name'), pipeline_id)} "
                f"({'candidate' if record.get('is_candidate') else 'all-pipeline'}, "
                f"{clean_text(record.get('status'), 'status n/a').lower()})"
            ),
        }
    if not rows:
        return pd.DataFrame(columns=["pipeline_id", "pipeline_name", "is_candidate", "status", "fluid", "display"])
    return pd.DataFrame(rows.values()).sort_values(["is_candidate", "pipeline_id"], ascending=[False, True]).reset_index(drop=True)


def apply_pipeline_selection_from_map_choice(pipeline_id: str, candidate_pipeline_ids: set[str]) -> None:
    """Apply a selection from the fallback route picker.

    Candidate pipelines switch the source back to the NSTA candidate mode.
    Non-candidates open the preview card.
    """
    if pipeline_id in candidate_pipeline_ids:
        st.session_state["map_selected_pipeline_id"] = pipeline_id
        st.session_state["pending_asset_source"] = "NSTA model-ready pipelines"
        st.session_state.pop("non_candidate_preview", None)
    else:
        st.session_state["non_candidate_preview"] = pipeline_id


def clean_text(value: Any, fallback: str = "Not available") -> str:
    if value is None:
        return fallback
    if isinstance(value, float) and pd.isna(value):
        return fallback
    text = str(value).strip()
    return text if text else fallback


def safe_filename(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = text.strip("_")
    return text or "scenario"


def nsta_scenario_name(pipeline_id: str) -> str:
    return f"nsta_{safe_filename(pipeline_id)}"


def as_float(value: Any) -> float | None:
    try:
        if pd.isna(value):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def fmt_number(value: Any, digits: int = 1, suffix: str = "") -> str:
    number = as_float(value)
    if number is None:
        return "Not available"
    return f"{number:,.{digits}f}{suffix}"


def fmt_money(value: Any) -> str:
    number = as_float(value)
    if number is None:
        return "Not available"
    if abs(number) >= 1_000_000:
        return f"${number / 1_000_000:,.1f} million"
    return f"${number:,.0f}"


def split_items(value: Any) -> list[str]:
    text = clean_text(value, "")
    if not text:
        return []
    return [item.strip() for item in text.split(";") if item.strip()]


def value_is_missing(value: Any, *, zero_invalid: bool = False) -> bool:
    text = clean_text(value, "")
    if not text:
        return True
    if text.upper() in {"N/A", "NA", "NONE", "NULL", "UNKNOWN", "NOT AVAILABLE"}:
        return True
    number = as_float(value)
    if number is None:
        return False
    if number in {-9999, -9999.0, -9997, -9997.0}:
        return True
    return zero_invalid and number <= 0


def availability(value: Any, *, zero_invalid: bool = False) -> str:
    return "Missing - please add a value" if value_is_missing(value, zero_invalid=zero_invalid) else "Available"


def status_colour(status: Any) -> tuple[str, str]:
    text = clean_text(status, "unknown").lower()
    if text in {"pass", "ready", "ready_for_screening", "yes", "active", "favour_reuse", "screening_result"}:
        return "#86EFAC", "#0a1f12"   # green text, dark green panel
    if text in {"marginal", "needs_data", "insufficient_data", "not_supplied", "unknown", "sensitivity_only"}:
        return "#FBBF24", "#1e1500"   # amber text, dark amber panel
    if "blocked" in text:
        return "#FBBF24", "#1e1500"
    if text in {"fail", "no", "high"}:
        return "#F87171", "#1e0a0a"   # coral text, dark red panel
    return "#9CA3B2", "#131826"       # muted text, dark panel


def status_pill(label: str, status: Any) -> None:
    fg, bg = status_colour(status)
    st.markdown(
        f"""
        <div class="status-row">
          <span>{label}</span>
          <strong style="color:{fg}; background:{bg};">{clean_text(status)}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )


def apply_style() -> None:
    css = (
        "<link href='https://fonts.googleapis.com/css2?"
        "family=Fraunces:ital,wght@0,400;0,500;0,600;1,400"
        "&family=Manrope:wght@300;400;500;600"
        "&family=JetBrains+Mono:wght@400;500&display=swap' rel='stylesheet'>"
        "<style>"
        ":root{"
        "--bg:#0A0E1A;--panel:#111827;--panel2:#1a2236;--line:#1e2d47;"
        "--text:#E8E4DC;--mute:#7A8499;--accent:#5EEAD4;"
        "--amber:#FBBF24;--coral:#F87171;--green:#86EFAC;"
        "}"
        ".stApp{background:var(--bg)!important;color:var(--text);font-family:'Manrope',sans-serif;}"
        ".stApp>div{background:var(--bg)!important;}"
        "header[data-testid='stHeader']{background:#0A0E1A!important;border-bottom:1px solid #1e2d47;}"
        ".block-container{padding-top:0!important;padding-bottom:3rem;max-width:1440px;}"
        "h2{font-family:'Fraunces',serif;font-size:22px;font-weight:500;color:var(--text);}"
        "h3{font-family:'Fraunces',serif;font-size:17px;font-weight:500;color:var(--text);margin:0 0 .4rem;}"
        "div[data-testid='stMetric']{background:var(--panel);border:1px solid var(--line);"
        "border-top:2px solid var(--accent);border-radius:10px;padding:.9rem 1.1rem;}"
        "div[data-testid='stMetric'] label{font-size:10px;letter-spacing:.12em;"
        "text-transform:uppercase;color:var(--mute);}"
        "div[data-testid='stMetric'] [data-testid='stMetricValue']{"
        "font-family:'JetBrains Mono',monospace;font-size:20px;color:var(--text);}"
        "div[data-testid='stVerticalBlockBorderWrapper']{"
        "border-color:var(--line)!important;border-radius:12px;background:var(--panel);}"
        "div[data-baseweb='select']>div{"
        "background-color:var(--panel2)!important;border-color:var(--line)!important;"
        "color:var(--text)!important;border-radius:8px!important;}"
        "div[data-baseweb='select'] span,"
        "div[data-baseweb='select'] div[class*='singleValue'],"
        "div[data-baseweb='select'] input{color:var(--text)!important;background:transparent!important;}"
        "div[data-baseweb='popover'] ul{"
        "background-color:var(--panel2)!important;border:1px solid var(--line)!important;}"
        "div[data-baseweb='popover'] li{color:var(--text)!important;background:var(--panel2)!important;}"
        "div[data-baseweb='popover'] li:hover{background-color:var(--line)!important;}"
        "[data-testid='stSelectbox'] label{color:var(--mute)!important;font-size:11px;"
        "letter-spacing:.1em;text-transform:uppercase;}"
        "[data-testid='stSegmentedControl'] div[role='radio']{"
        "background:var(--panel2)!important;color:var(--text)!important;"
        "border-color:var(--line)!important;font-size:12px;}"
        "[data-testid='stSegmentedControl'] div[role='radio'][aria-checked='true']{"
        "border-color:var(--accent)!important;color:var(--accent)!important;"
        "background:#0d2a28!important;}"
        ".stButton>button{font-family:'Manrope',sans-serif;border-radius:8px;"
        "border:1px solid var(--line);background:var(--panel2);color:var(--text);"
        "font-weight:500;font-size:13px;padding:.45rem 1rem;transition:all .15s;}"
        ".stButton>button:hover{background:var(--line);border-color:var(--accent);color:var(--accent);}"
        ".stButton>button[kind='primary']{background:var(--accent);color:#0A0E1A;"
        "border-color:var(--accent);font-weight:600;}"
        "[data-testid='stDataFrame']{border-radius:8px;overflow:hidden;}"
        "[data-testid='stDataFrame'] th{background:var(--panel2)!important;"
        "color:var(--mute)!important;font-size:11px;letter-spacing:.08em;"
        "text-transform:uppercase;border-bottom:1px solid var(--line)!important;}"
        "[data-testid='stDataFrame'] td{background:var(--panel)!important;"
        "color:var(--text)!important;border-bottom:1px solid var(--line)!important;font-size:13px;}"
        ".stCodeBlock,[data-testid='stCode']{background:#080d18!important;"
        "border:1px solid var(--line);border-radius:8px;}"
        "[data-testid='stExpander']{border-color:var(--line)!important;"
        "background:var(--panel);border-radius:10px;}"
        "[data-testid='stExpander'] summary{font-family:'Manrope',sans-serif;"
        "font-weight:500;color:var(--text);}"
        ".nav-bar{background:var(--panel);border-bottom:1px solid var(--line);"
        "padding:.75rem 2rem;display:flex;align-items:center;"
        "justify-content:space-between;margin:-1rem -5rem 1.5rem;"
        "position:sticky;top:0;z-index:100;}"
        ".nav-brand{display:flex;align-items:baseline;gap:.5rem;}"
        ".nav-title{font-family:'Fraunces',serif;font-size:19px;font-weight:500;color:var(--text);}"
        ".nav-title em{color:var(--accent);font-style:italic;}"
        ".nav-badge{font-family:'JetBrains Mono',monospace;font-size:9px;color:var(--mute);"
        "border:1px solid var(--line);border-radius:3px;padding:1px 5px;letter-spacing:.08em;}"
        ".nav-sub{font-size:11px;color:var(--mute);font-family:'Manrope',sans-serif;}"
        ".hero-eyebrow{font-size:10px;letter-spacing:.2em;text-transform:uppercase;"
        "color:var(--accent);font-family:'Manrope',sans-serif;margin-bottom:.5rem;}"
        ".hero-hed{font-family:'Fraunces',serif;font-size:34px;font-weight:500;"
        "line-height:1.2;color:var(--text);margin:0 0 .6rem;}"
        ".hero-hed em{color:var(--accent);font-style:italic;}"
        ".hero-sub{font-size:13px;color:var(--mute);font-family:'Manrope',sans-serif;"
        "line-height:1.65;margin-bottom:1.25rem;max-width:430px;}"
        ".pipe-id{font-family:'JetBrains Mono',monospace;font-size:11px;"
        "color:var(--accent);letter-spacing:.1em;margin-bottom:2px;}"
        ".pipe-name{font-family:'Fraunces',serif;font-size:21px;font-weight:500;"
        "color:var(--text);line-height:1.2;margin-bottom:.8rem;}"
        ".pipe-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:.5rem .75rem;margin-top:.25rem;}"
        ".pi-label{font-size:9px;letter-spacing:.12em;text-transform:uppercase;"
        "color:var(--mute);font-family:'Manrope',sans-serif;}"
        ".pi-value{font-family:'JetBrains Mono',monospace;font-size:13px;color:var(--text);margin-top:1px;}"
        ".sbar{display:flex;gap:.35rem;flex-wrap:wrap;margin:.75rem 0 .5rem;}"
        ".schip{display:inline-flex;align-items:center;gap:.25rem;border-radius:5px;"
        "padding:.22rem .55rem;font-size:11px;font-family:'Manrope',sans-serif;"
        "font-weight:600;letter-spacing:.04em;border:1px solid;}"
        ".schip-lbl{opacity:.6;font-weight:400;margin-right:1px;}"
        ".map-legend{display:flex;gap:1.2rem;align-items:center;"
        "padding:.4rem 0 .5rem;font-size:11px;font-family:'Manrope',sans-serif;color:var(--mute);}"
        ".ldot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:4px;}"
        ".map-cap{font-size:11px;color:var(--mute);font-family:'Manrope',sans-serif;padding:.2rem 0;}"
        ".kpi-row{display:grid;grid-template-columns:repeat(5,1fr);gap:.5rem;margin:1.25rem 0;}"
        ".kpi-tile{background:var(--panel);border:1px solid var(--line);"
        "border-top:2px solid var(--accent);border-radius:10px;padding:.75rem 1rem;}"
        ".kpi-lbl{font-size:9px;letter-spacing:.12em;text-transform:uppercase;"
        "color:var(--mute);font-family:'Manrope',sans-serif;margin-bottom:4px;}"
        ".kpi-val{font-family:'JetBrains Mono',monospace;font-size:19px;"
        "color:var(--text);letter-spacing:-.02em;}"
        ".status-row{display:flex;align-items:center;justify-content:space-between;"
        "gap:.75rem;padding:.5rem 0;border-bottom:1px solid var(--line);"
        "font-size:13px;font-family:'Manrope',sans-serif;color:var(--mute);}"
        ".status-row strong{display:inline-block;border-radius:999px;"
        "padding:.18rem .65rem;font-size:11px;font-weight:600;"
        "letter-spacing:.06em;white-space:nowrap;}"
        ".section-note{background:var(--panel2);border:1px solid var(--line);"
        "border-left:3px solid var(--accent);border-radius:8px;"
        "padding:.7rem 1rem;color:var(--mute);font-size:12px;"
        "font-family:'Manrope',sans-serif;line-height:1.6;margin-bottom:.75rem;}"
        ".missing-note{background:#1a1200;border:1px solid #3a2e00;"
        "border-left:3px solid var(--amber);border-radius:8px;"
        "padding:.7rem 1rem;color:#FCD34D;font-size:12px;"
        "font-family:'Manrope',sans-serif;line-height:1.6;}"
        ".workflow-step{border-left:3px solid var(--accent);padding-left:.8rem;margin-bottom:.6rem;}"
        ".score-card{background:var(--panel);border:1px solid var(--line);"
        "border-radius:12px;padding:16px 20px;margin-bottom:10px;}"
        ".eyebrow{font-family:'Manrope',sans-serif;font-size:10px;letter-spacing:.14em;"
        "text-transform:uppercase;color:var(--mute);margin-bottom:4px;}"
        ".small-muted{color:var(--mute);font-size:12px;font-family:'Manrope',sans-serif;}"
        "hr{border-color:var(--line);margin:1rem 0;}"
        ".score-num-small{font-family:'JetBrains Mono',monospace;font-size:24px;color:var(--text);}"
        "</style>"
    )
    if hasattr(st, "html"):
        st.html(css)
    else:
        st.markdown(css, unsafe_allow_html=True)
def build_candidate_table(ranked_df: pd.DataFrame, screening_df: pd.DataFrame) -> pd.DataFrame:
    """Build the pipeline selector table from ALL NSTA pipelines.

    The list shows every pipeline in the ranked CSV regardless of data completeness.
    Users can upload data for any pipeline. Goldeneye (PL1978) is added manually
    since it has pre-loaded scenario assumptions but does not appear in the ranked CSV
    with full technical data.
    """
    if ranked_df.empty:
        return pd.DataFrame()
    candidates = ranked_df.copy()
    candidates["pipeline_id"] = candidates["NSTAPIPNO"].astype(str).str.strip().str.upper()
    candidates["rank"] = pd.to_numeric(candidates["RANK"], errors="coerce")
    candidates["data_priority_score"] = pd.to_numeric(candidates["SCREENING_SCORE"], errors="coerce")

    # Add Goldeneye (PL1978) if not already present — it has preloaded scenario data
    if "PL1978" not in set(candidates["pipeline_id"]):
        goldeneye_row = pd.DataFrame([{
            "pipeline_id": "PL1978",
            "NSTAPIPNO": "PL1978",
            "PIPE_NAME": "20\" GAS GOLDENEYE - ST. FERGUS",
            "FLUID": "GAS",
            "STATUS": "ACTIVE",
            "RANK": 0,
            "SCREENING_SCORE": 0,
            "data_priority_score": 0,
            "rank": 0,
        }])
        candidates = pd.concat([goldeneye_row, candidates], ignore_index=True)

    if not screening_df.empty:
        screen_cols = [
            "nsta_pipeline_number",
            "pre_lca_decision",
            "repurposing_gate_status",
            "capacity_mtpa",
            "remaining_life_years",
            "lca_proxy_saving_percent",
        ]
        available = [c for c in screen_cols if c in screening_df.columns]
        screen = screening_df[available].copy()
        screen["pipeline_id"] = screen["nsta_pipeline_number"].astype(str).str.strip().str.upper()
        candidates = candidates.merge(
            screen.drop(columns=["nsta_pipeline_number"], errors="ignore"),
            on="pipeline_id",
            how="left",
        )

    candidates = candidates.sort_values("rank", na_position="last")
    candidates = candidates.drop_duplicates(subset=["pipeline_id"], keep="first")
    candidates["display"] = candidates.apply(
        lambda row: (
            f"{row['pipeline_id']} - {clean_text(row.get('PIPE_NAME'), row['pipeline_id'])} "
            f"({clean_text(row.get('FLUID'), 'fluid n/a').lower()}, "
            f"{clean_text(row.get('STATUS'), 'status n/a').lower()})"
        ),
        axis=1,
    )
    return candidates.reset_index(drop=True)


# ── Commented out: pydeck utility functions (no longer needed with Folium)
# def route_bounds(routes: list[dict[str, Any]]) -> dict[str, float] | None:
#     if not routes:
#         return None
#     return {
#         "min_lon": min(route["bounds"]["min_lon"] for route in routes),
#         "max_lon": max(route["bounds"]["max_lon"] for route in routes),
#         "min_lat": min(route["bounds"]["min_lat"] for route in routes),
#         "max_lat": max(route["bounds"]["max_lat"] for route in routes),
#     }
#
#
# def route_zoom(bounds: dict[str, float] | None) -> float:
#     if bounds is None:
#         return 4.6
#     span = max(bounds["max_lon"] - bounds["min_lon"], bounds["max_lat"] - bounds["min_lat"])
#     if span < 0.3:
#         return 7.2
#     if span < 0.8:
#         return 6.4
#     if span < 1.8:
#         return 5.5
#     if span < 3.5:
#         return 4.9
#     return 4.2
#
#
# def find_pipeline_id(payload: Any) -> str | None:
#     if isinstance(payload, dict):
#         direct = payload.get("pipeline_id")
#         if direct:
#             return str(direct).strip().upper()
#         for value in payload.values():
#             found = find_pipeline_id(value)
#             if found:
#                 return found
#     if isinstance(payload, list):
#         for item in payload:
#             found = find_pipeline_id(item)
#             if found:
#                 return found
#     return None
#
#
# def extract_map_selection(event: Any) -> str | None:
#     if event is None:
#         return None
#     selection = getattr(event, "selection", None)
#     if selection is None and isinstance(event, dict):
#         selection = event.get("selection")
#     return find_pipeline_id(selection)

def _extract_pydeck_selection(event: Any) -> str | None:
    """Pull pipeline_id out of a pydeck on_select event object."""
    if event is None:
        return None
    selection = getattr(event, "selection", None)
    if selection is None and isinstance(event, dict):
        selection = event.get("selection")
    if not selection:
        return None
    # selection.objects is a dict keyed by layer id → list of picked records
    objects = getattr(selection, "objects", None)
    if objects is None and isinstance(selection, dict):
        objects = selection.get("objects")
    if not objects:
        return None
    for records in (objects.values() if isinstance(objects, dict) else [objects]):
        if isinstance(records, list):
            for rec in records:
                pid = (rec or {}).get("pipeline_id")
                if pid:
                    return str(pid).strip().upper()
    return None


def render_route_map(all_routes_payload: dict[str, Any], selected_pipeline_id: str | None) -> str | None:
    """Render the North Sea pipeline map using pydeck (built-in Streamlit).

    Visual layers
    ─────────────
    PathLayer  (all dim)       — dim blue, not pickable (avoids thin-line click issues)
    PathLayer  (candidates)    — teal, not pickable
    PathLayer  (selected)      — coral, not pickable
    ScatterplotLayer (dots)    — one dot per candidate pipeline at its midpoint;
                                 large radius → easy to click; returns pipeline_id.
    """
    if not _PYDECK_OK:
        st.info("Install pydeck: `pip install pydeck`")
        return None

    routes = all_routes_payload.get("routes", [])
    if not routes:
        st.info("No route data available. Run `scripts/build_dashboard_assets.py` first.")
        return None

    # ── Partition routes ───────────────────────────────────────────────────
    dim_routes: list[dict] = []
    cand_routes: list[dict] = []
    sel_routes: list[dict] = []
    # Deduplicated candidate records for clickable dot layer
    seen_cand: dict[str, dict] = {}

    for route in routes:
        path = route.get("path") or []
        if not path:
            continue
        pid = route.get("pipeline_id", "")
        # Routes JSON contains only candidate pipelines (is_candidate field may be absent)
        # A route is a candidate if is_candidate is True OR if is_candidate is not set
        # (legacy JSON without the field — all routes in the file are candidates)
        is_cand = route.get("is_candidate", True)
        if pid == selected_pipeline_id:
            sel_routes.append({**route, "_color": [248, 113, 113, 240], "_width": 6})
        elif is_cand:
            cand_routes.append({**route, "_color": [20, 184, 166, 200], "_width": 3})
            if pid not in seen_cand:
                seen_cand[pid] = route
        else:
            dim_routes.append({**route, "_color": [60, 80, 140, 110], "_width": 2})

    # Also expose selected pipeline via dot layer if it is not a candidate
    if selected_pipeline_id and selected_pipeline_id not in seen_cand:
        for route in routes:
            if route.get("pipeline_id") == selected_pipeline_id:
                seen_cand[selected_pipeline_id] = route
                break

    # ── Dot layer data ─────────────────────────────────────────────────────
    # One point per unique pipeline_id at the route midpoint.
    dot_data: list[dict] = []
    for pid, route in seen_cand.items():
        path = route.get("path") or []
        if not path:
            continue
        mid = path[len(path) // 2]          # [lon, lat]
        is_sel = pid == selected_pipeline_id
        dot_data.append({
            "position": mid,
            "pipeline_id": pid,
            "pipeline_name": route.get("pipeline_name", ""),
            "fluid": route.get("fluid", ""),
            "status": route.get("status", ""),
            "length_km": route.get("length_km", ""),
            "diameter_mm": route.get("diameter_mm", ""),
            "_radius": 9000 if is_sel else 6000,
            "_color": [248, 113, 113, 230] if is_sel else [20, 184, 166, 200],
        })

    # ── View state ─────────────────────────────────────────────────────────
    view = pdk.ViewState(latitude=56.5, longitude=3.0, zoom=5, pitch=0)

    # ── Layers ─────────────────────────────────────────────────────────────
    layers = [
        pdk.Layer("PathLayer", id="dim",       data=dim_routes,  get_path="path", get_color="_color", get_width="_width", width_min_pixels=1,  rounded=True, pickable=False),
        pdk.Layer("PathLayer", id="candidates", data=cand_routes, get_path="path", get_color="_color", get_width="_width", width_min_pixels=2,  rounded=True, pickable=False),
        pdk.Layer("PathLayer", id="selected",   data=sel_routes,  get_path="path", get_color="_color", get_width="_width", width_min_pixels=4,  rounded=True, pickable=False),
        pdk.Layer(
            "ScatterplotLayer",
            id="dots",
            data=dot_data,
            get_position="position",
            get_radius="_radius",
            get_fill_color="_color",
            radius_min_pixels=2,
            stroked=True,
            get_line_color=[255, 255, 255, 120],
            line_width_min_pixels=1,
            pickable=True,
        ),
    ]

    tooltip = {
        "html": "<b>{pipeline_id}</b> {pipeline_name}<br/>"
                "Fluid: {fluid} · {status}<br/>"
                "Length: {length_km} km · ⌀ {diameter_mm} mm",
        "style": {"backgroundColor": "#131826", "color": "#F4F1EA", "fontSize": "12px",
                  "padding": "8px 12px", "borderRadius": "8px"},
    }

    deck = pdk.Deck(
        layers=layers,
        initial_view_state=view,
        tooltip=tooltip,
        map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
    )

    event = st.pydeck_chart(
        deck,
        use_container_width=True,
        height=520,
        selection_mode="single-object",
        on_select="rerun",
        key="pipeline_route_map",
    )
    return _extract_pydeck_selection(event)




def selected_screening_row(screening_df: pd.DataFrame, pipeline_id: str) -> pd.Series | None:
    if screening_df.empty or "nsta_pipeline_number" not in screening_df.columns:
        return None
    match = screening_df[
        screening_df["nsta_pipeline_number"].astype(str).str.strip().str.upper() == pipeline_id
    ]
    if match.empty:
        return None
    return match.iloc[0]


def selected_ranked_row(candidate_df: pd.DataFrame, pipeline_id: str) -> pd.Series | None:
    match = candidate_df[candidate_df["pipeline_id"] == pipeline_id]
    if match.empty:
        return None
    return match.iloc[0]


def load_scenario_row(scenario: str) -> pd.Series | None:
    path = SCREENING_DIR / f"pipeline_screen_{scenario}.csv"
    df = load_csv(str(path))
    if df.empty:
        return None
    return df.iloc[0]


def load_cost_row(case_name: str) -> pd.Series | None:
    path = COST_DIR / f"refurbishment_cost_summary_{case_name}.csv"
    df = load_csv(str(path))
    if not df.empty:
        return df.iloc[0]
    return None


def load_lca_row(scenario: str) -> pd.Series | None:
    path = LCA_DIR / f"lca_results_{scenario}.csv"
    df = load_csv(str(path))
    if not df.empty:
        return df.iloc[0]
    return None


def run_model_command(args: list[str]) -> tuple[bool, str]:
    completed = subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    output = "\n".join(
        part.strip()
        for part in [completed.stdout, completed.stderr]
        if part and part.strip()
    )
    return completed.returncode == 0, output


def run_screening(selection: dict[str, str]) -> tuple[bool, str]:
    if selection["kind"] == "nsta":
        return run_model_command(["scripts\\run_pipeline_screen.py", "--nsta-id", selection["pipeline_id"]])
    return run_model_command(["scripts\\run_pipeline_screen.py", "--scenario", selection["screening_scenario"]])


def run_cost(selection: dict[str, str], factor_mode: str) -> tuple[bool, str]:
    return run_model_command(
        ["scripts\\run_refurbishment_cost.py", "--case", selection["cost_case"], "--factor-mode", factor_mode]
    )


def run_lca(selection: dict[str, str], factor_mode: str) -> tuple[bool, str]:
    if selection["kind"] == "nsta":
        return run_model_command(
            ["scripts\\run_ecoinvent_lca.py", "--nsta-id", selection["pipeline_id"], "--factor-mode", factor_mode]
        )
    return run_model_command(
        ["scripts\\run_ecoinvent_lca.py", "--scenario", selection["lca_scenario"], "--factor-mode", factor_mode]
    )


def run_all(selection: dict[str, str], factor_mode: str) -> list[tuple[str, bool, str]]:
    steps = [
        ("Technical screening", lambda: run_screening(selection)),
        ("Refurbishment cost", lambda: run_cost(selection, factor_mode)),
        ("LCA", lambda: run_lca(selection, factor_mode)),
    ]
    results: list[tuple[str, bool, str]] = []
    for label, command in steps:
        ok, output = command()
        results.append((label, ok, output))
        if not ok:
            break
    st.cache_data.clear()
    return results


def show_run_result(key: str) -> None:
    result = st.session_state.get(key)
    if not result:
        return
    label, ok, output = result
    if ok:
        st.success(f"{label} completed.")
    else:
        st.error(f"{label} failed.")
    with st.expander("Command output"):
        st.code(output or "No output", language="text")


def data_table(rows: list[dict[str, Any]]) -> None:
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")


def input_row(field: str, value: Any, unit: str = "", *, zero_invalid: bool = False, source: str = "") -> dict[str, str]:
    return {
        "Input": field,
        "Value": clean_text(value),
        "Unit": unit,
        "Status": availability(value, zero_invalid=zero_invalid),
        "Source": source or "model input",
    }


def equation_box(lines: list[str]) -> None:
    st.code("\n".join(lines), language="text")


def render_missing_warning(info_rows: list[dict[str, str]]) -> None:
    missing = [row["Input"] for row in info_rows if row["Status"].startswith("Missing")]
    if missing:
        st.markdown(
            f"""
            <div class="missing-note">
            Missing values: {", ".join(missing)}. Please add values or documented assumptions before relying on this result.
            </div>
            """,
            unsafe_allow_html=True,
        )


def profile_rows(row: pd.Series | None, ranked_row: pd.Series | None, selection: dict[str, str]) -> list[dict[str, str]]:
    pipeline_name = clean_text(
        row.get("pipeline_name") if row is not None else ranked_row.get("PIPE_NAME") if ranked_row is not None else selection["label"]
    )
    pipeline_id = selection["pipeline_id"]
    length = row.get("length_km") if row is not None else ranked_row.get("LENGTH_KM") if ranked_row is not None else None
    internal_diameter = row.get("inner_diameter_in") if row is not None else None
    wall = row.get("nominal_wall_thickness_mm") if row is not None else ranked_row.get("THICKNESS") if ranked_row is not None else None
    max_pressure = ranked_row.get("MX_OP_PRES") if ranked_row is not None else None
    if max_pressure is None and row is not None:
        max_pressure = row.get("average_pressure_mpa")

    return [
        input_row("Pipeline name", pipeline_name),
        input_row("Pipeline ID / case", pipeline_id),
        input_row("Fluid", ranked_row.get("FLUID") if ranked_row is not None else "CO2 candidate"),
        input_row("Status", ranked_row.get("STATUS") if ranked_row is not None else selection["kind"]),
        input_row("Length", length, "km", zero_invalid=True),
        input_row("Internal diameter", internal_diameter, "in", zero_invalid=True),
        input_row("Wall thickness", wall, "mm", zero_invalid=True),
        input_row("Maximum operating pressure", max_pressure, "bar or MPa basis", zero_invalid=True),
        input_row("Start date", ranked_row.get("START_DATE") if ranked_row is not None else None),
    ]


def render_header() -> None:
    html = (
        "<div class='nav-bar'>"
        "<div class='nav-brand'>"
        "<span class='nav-title'>CO&#8322; Pipeline Repurposing <em>Evaluation Tool</em></span>"
        "<span class='nav-badge'>v1.0 &middot; NSTA</span>"
        "</div>"
        "<span class='nav-sub'>Screen &middot; Score &middot; Decide</span>"
        "</div>"
    )
    if hasattr(st, "html"):
        st.html(html)
    else:
        st.markdown(html, unsafe_allow_html=True)


def render_selector(candidate_df: pd.DataFrame) -> dict[str, str]:
    pending_asset_source = st.session_state.pop("pending_asset_source", None)
    if pending_asset_source is not None:
        st.session_state["asset_source"] = pending_asset_source

    source = st.segmented_control(
        "Asset source",
        ["NSTA model-ready pipelines", "Known CCS benchmark cases"],
        default=st.session_state.get("asset_source", "NSTA model-ready pipelines"),
        key="asset_source",
    )

    if source == "Known CCS benchmark cases":
        case_label = st.selectbox("Select case", list(KNOWN_CASES), key="known_case_label")
        case = KNOWN_CASES[case_label]
        selection = {
            "kind": "scenario",
            "pipeline_id": case["selection_id"],
            "map_pipeline_id": case["map_pipeline_id"],
            "screening_scenario": case["screening_scenario"],
            "cost_case": case["cost_case"],
            "lca_scenario": case["lca_scenario"],
            "label": case["label"],
        }
        st.session_state["selected_pipeline_id"] = selection["pipeline_id"]
        return selection

    options = candidate_df["display"].tolist()
    map_selected_pipeline_id = st.session_state.get("map_selected_pipeline_id")
    if map_selected_pipeline_id in set(candidate_df["pipeline_id"]):
        default_pipeline_id = str(map_selected_pipeline_id)
        st.session_state["selected_pipeline_id"] = default_pipeline_id
        del st.session_state["map_selected_pipeline_id"]
    else:
        default_pipeline_id = st.session_state.get("selected_pipeline_id", "PL774")
    if default_pipeline_id not in set(candidate_df["pipeline_id"]):
        default_pipeline_id = "PL774" if "PL774" in set(candidate_df["pipeline_id"]) else candidate_df.iloc[0]["pipeline_id"]
    default_index = int(candidate_df.index[candidate_df["pipeline_id"] == default_pipeline_id][0])
    default_label = str(candidate_df.loc[default_index, "display"])
    if st.session_state.get("nsta_pipeline_label") not in options or map_selected_pipeline_id:
        st.session_state["nsta_pipeline_label"] = default_label
    selected_label = st.selectbox("Select pipeline", options, index=default_index, key="nsta_pipeline_label")
    selected_pipeline_id = selected_label.split(" - ", 1)[0].strip().upper()
    st.session_state["selected_pipeline_id"] = selected_pipeline_id
    return {
        "kind": "nsta",
        "pipeline_id": selected_pipeline_id,
        "screening_scenario": nsta_scenario_name(selected_pipeline_id),
        "cost_case": nsta_scenario_name(selected_pipeline_id),
        "lca_scenario": nsta_scenario_name(selected_pipeline_id),
        "label": selected_label,
    }


def render_non_candidate_info(record: dict[str, Any]) -> None:
    pid = record.get("pipeline_id", "")
    name = record.get("pipeline_name", pid)
    fluid = clean_text(record.get("fluid"), "")
    status = clean_text(record.get("status"), "")
    length = record.get("length_km")
    diameter = record.get("diameter_mm")
    pressure = record.get("max_op_pressure")
    operator = clean_text(record.get("operator"), "")

    st.markdown(
        f"""
        <div class="score-card" style="border-top:2px solid #9CA3B2;">
          <div class="eyebrow" style="color:#9CA3B2;">Not in CO₂ candidate set</div>
          <div style="font-family:'Fraunces',serif; font-size:18px; font-weight:500;
                      margin:6px 0 12px; color:#F4F1EA;">{name}</div>
          <div style="color:#5F6981; font-size:12px; font-family:'JetBrains Mono',monospace;
                      margin-bottom:12px;">{pid}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    rows = [
        {"Field": "Fluid", "Value": fluid or "—"},
        {"Field": "Status", "Value": status or "—"},
        {"Field": "Length", "Value": fmt_number(length, 1, " km") if length else "—"},
        {"Field": "Diameter", "Value": fmt_number(diameter, 0, " mm") if diameter else "—"},
        {"Field": "Max op. pressure", "Value": fmt_number(pressure, 1, " bar") if pressure else "—"},
        {"Field": "Operator", "Value": operator or "—"},
    ]
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    st.markdown(
        """<div class="section-note" style="margin-top:10px;">
        This pipeline did not pass the initial data-completeness or geometry screen
        for the CO₂ repurposing candidate set. No engineering model layers are available.
        </div>""",
        unsafe_allow_html=True,
    )


def _html(html: str) -> None:
    """Render HTML reliably across Streamlit versions."""
    if hasattr(st, "html"):
        st.html(html)
    else:
        st.markdown(html, unsafe_allow_html=True)


def _chip(label: str, status: Any) -> str:
    fg, bg = status_colour(status)
    text = clean_text(status)
    return (
        f"<span class='schip' style='color:{fg};background:{bg}22;border-color:{fg}55;'>"
        f"<span class='schip-lbl'>{label}</span>{text}</span>"
    )


def _pipe_info_html(
    row: pd.Series | None,
    ranked_row: pd.Series | None,
    selection: dict[str, str],
) -> str:
    pid   = selection["pipeline_id"]
    name  = clean_text(
        (row.get("pipeline_name") if row is not None else None)
        or (ranked_row.get("PIPE_NAME") if ranked_row is not None else None)
        or selection["label"]
    )
    fluid  = clean_text(ranked_row.get("FLUID")  if ranked_row is not None else None, "N/A")
    status = clean_text(ranked_row.get("STATUS") if ranked_row is not None else None, "N/A")
    length = as_float((row.get("length_km") if row is not None else None) or (ranked_row.get("LENGTH_KM") if ranked_row is not None else None))
    od_in  = as_float(row.get("outer_diameter_in") if row is not None else None)
    id_in  = as_float((row.get("inner_diameter_in") if row is not None else None) or (ranked_row.get("INT_DIAM") if ranked_row is not None else None))
    wall   = as_float((row.get("nominal_wall_thickness_mm") if row is not None else None) or (ranked_row.get("THICKNESS") if ranked_row is not None else None))
    mop    = as_float((ranked_row.get("MX_OP_PRES") if ranked_row is not None else None) or (row.get("average_pressure_mpa") if row is not None else None))
    start  = clean_text(ranked_row.get("START_DATE") if ranked_row is not None else None, "N/A")
    grade  = clean_text(row.get("pipe_grade") if row is not None else None, "N/A")

    def v(val: Any, d: int, u: str) -> str:
        f = as_float(val)
        return fmt_number(f, d, f" {u}") if f is not None else "N/A"

    od_str = v(od_in, 1, "in") if od_in else v(id_in, 1, "in")
    items = [
        ("Fluid",    fluid),
        ("Status",   status),
        ("Length",   v(length, 1, "km")),
        ("OD",       od_str),
        ("Wall",     v(wall, 1, "mm")),
        ("Max P",    v(mop, 0, "bar")),
        ("Start",    start[:10] if start != "N/A" else "N/A"),
        ("Grade",    grade),
    ]
    grid = "".join(
        f"<div><div class='pi-label'>{lbl}</div><div class='pi-value'>{val}</div></div>"
        for lbl, val in items
    )
    return (
        f"<div class='pipe-id'>{pid}</div>"
        f"<div class='pipe-name'>{name}</div>"
        f"<div class='pipe-grid'>{grid}</div>"
    )


def render_top_area(
    all_routes_payload: dict[str, Any],
    row: pd.Series | None,
    ranked_row: pd.Series | None,
    selection: dict[str, str],
    candidate_pipeline_ids: set[str],
) -> None:
    map_active_id = selection["pipeline_id"] if selection["kind"] == "nsta" else selection.get("map_pipeline_id")
    non_candidate_preview = st.session_state.get("non_candidate_preview")
    if non_candidate_preview:
        map_active_id = non_candidate_preview

    left_col, right_col = st.columns([1, 1.85], gap="large")

    with left_col:
        _html(
            "<div class='hero-hed'>Repurpose pipelines<br>for <em>CO&#8322; transport.</em></div>"
            "<div class='hero-sub'>A technical, economic and lifecycle assessment tool "
            "for evaluating whether existing offshore gas pipelines can be reused for CO&#8322; "
            "transport and carbon capture and storage (CCS). "
            "A pass means the pipeline warrants detailed engineering study -- not a construction permit.</div>"
        )

        # Pipeline search dropdown — all pipelines in the database
        route_summary = route_summary_table(all_routes_payload)
        all_pipeline_ids = set(candidate_df["pipeline_id"]) if "candidate_df" in dir() else set()

        # Build combined option list: routes + any candidates not in routes
        if not route_summary.empty:
            active_route_id = (
                map_active_id if map_active_id in set(route_summary["pipeline_id"])
                else route_summary.iloc[0]["pipeline_id"]
            )
            fallback_index = int(route_summary.index[route_summary["pipeline_id"] == active_route_id][0])
            fallback_options = route_summary["display"].tolist()
            if st.session_state.get("route_picker_label") not in fallback_options:
                st.session_state["route_picker_label"] = fallback_options[fallback_index]
            picked_label = st.selectbox(
                "Search pipelines",
                fallback_options,
                index=fallback_index,
                key="route_picker_label",
                label_visibility="collapsed",
            )
            picked_id = str(route_summary.loc[route_summary["display"] == picked_label, "pipeline_id"].iloc[0])
            if picked_id != map_active_id:
                apply_pipeline_selection_from_map_choice(picked_id, candidate_pipeline_ids)
                st.rerun()

        if non_candidate_preview:
            record = find_route_record(all_routes_payload, non_candidate_preview)
            if record:
                render_non_candidate_info(record)
            if st.button("Back to candidate"):
                st.session_state.pop("non_candidate_preview", None)
                st.rerun()
            return

        # Status chips + pipeline info card
        pre_lca = row.get("pre_lca_decision") if row is not None else "not run"
        gate    = row.get("repurposing_gate_status") if row is not None else "not run"
        cap     = row.get("capacity_suitable") if row is not None else "not run"
        _html(
            f"<div class='sbar'>{_chip('Pre-LCA', pre_lca)}"
            f"{_chip('Gate', gate)}{_chip('Capacity', cap)}</div>"
            + _pipe_info_html(row, ranked_row, selection)
        )

    with right_col:
        _html(
            "<div class='map-legend'>"
            "<span><span class='ldot' style='background:#5EEAD4;'></span>CO&#8322; candidate</span>"
            "<span><span class='ldot' style='background:#F87171;'></span>Selected</span>"
            "<span><span class='ldot' style='background:#3C5078;opacity:.7;'></span>All NSTA pipelines</span>"
            "</div>"
        )
        clicked_pipeline_id = render_route_map(all_routes_payload, map_active_id)
        if clicked_pipeline_id and clicked_pipeline_id != map_active_id:
            apply_pipeline_selection_from_map_choice(clicked_pipeline_id, candidate_pipeline_ids)
            st.rerun()
        n_routes     = len(all_routes_payload.get("routes", []))
        n_candidates = all_routes_payload.get("candidate_count", "?")
        _html(
            f"<div class='map-cap'>{n_routes} route segments "
            f"&middot; {n_candidates} CO&#8322; candidates (teal) "
            "&middot; Click any pipeline to inspect it</div>"
        )


def render_key_metrics(row: pd.Series | None, ranked_row: pd.Series | None) -> None:
    cap      = fmt_number(row.get("capacity_mtpa")             if row is not None else None, 1, " Mtpa")
    req      = fmt_number(row.get("required_design_mtpa")      if row is not None else None, 1, " Mtpa")
    life     = fmt_number(row.get("remaining_life_years")      if row is not None else None, 1, " yr")
    evidence = fmt_number(row.get("repurposing_evidence_score") if row is not None else None, 0, "/100")
    lca      = fmt_number(row.get("lca_proxy_saving_percent")  if row is not None else None, 1, "%")

def render_layer_button(label: str, selection: dict[str, str]) -> None:
    result_key = f"last_result_{safe_filename(label)}"
    if st.button(label, key=safe_filename(label + selection["pipeline_id"])):
        ok, output = run_screening(selection)
        st.session_state[result_key] = (label, ok, output)
        st.cache_data.clear()
        st.rerun()
    show_run_result(result_key)


_DQ_TIERS: dict[str, tuple[int, str]] = {
    # quality label -> (tier number, display label)
    "primary_record":       (1, "Primary record"),
    "reported":             (1, "Primary record"),
    "regulatory_record":    (2, "Regulatory record"),
    "measured_inspection":  (3, "ILI / inspection"),
    "pressure_test_derived":(4, "Pressure test derived"),
    "engineering_derived":  (5, "Engineering derived"),
    "derived":              (5, "Engineering derived"),
    "standard_nominal":     (6, "Standard nominal"),
    "assumed_conservative": (7, "Assumption"),
    "assumed":              (7, "Assumption"),
    "assumed_or_standard":  (6, "Standard/assumption"),
    "calculated":           (5, "Calculated"),
    "screening_lca_proxy":  (7, "Assumption"),
}

_DQ_CRITICAL_PARAMS: set[str] = {
    "nominal_wall_thickness_mm",
    "inner_diameter_in",
    "outer_diameter_in",
    "pipe_grade",
    "inlet_pressure_psia",
    "outlet_pressure_psia",
    "length_km",
    "pipeline_length_km",
}

_DQ_SIGNIFICANT_PARAMS: set[str] = {
    "historical_corrosion_rate_mm_per_year",
    "future_co2_corrosion_rate_mm_per_year",
    "transport_temperature_c",
    "required_project_flow_mtpa",
    "start_operation_year",
    "capacity_factor",
}


def _dq_tier(quality: str) -> tuple[int, str]:
    return _DQ_TIERS.get(str(quality).strip().lower(), (7, "Assumption"))


def _dq_tier_colour(tier: int) -> str:
    return {1: "🟢", 2: "🟢", 3: "🟡", 4: "🟡", 5: "🟠", 6: "🟠", 7: "🔴"}.get(tier, "⚪")


def _load_assumption_quality(selection: dict[str, str]) -> dict[str, str]:
    """Load parameter -> quality mapping from the assumptions CSV for this scenario."""
    from pathlib import Path
    import csv

    quality: dict[str, str] = {}
    # Try goldeneye assumptions first, then NSTA defaults
    for path in [
        Path("model_layers/06_screening_and_decision/goldeneye_assumptions.csv"),
        Path("model_layers/06_screening_and_decision/nsta_screening_defaults.csv"),
    ]:
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                sc = row.get("scenario", "")
                param = row.get("parameter", "")
                q = row.get("quality", "assumed")
                scenario = selection.get("screening_scenario", "")
                if sc == scenario or sc == "defaults" or sc == "nsta_defaults":
                    quality[param] = q
    return quality


def render_data_layer(row: pd.Series | None, ranked_row: pd.Series | None, selection: dict[str, str]) -> None:
    with st.container(border=True):
        st.markdown('<div class="workflow-step"><h3>1. Data Completeness &amp; Quality Gate</h3></div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-note">Scores each input parameter against a 7-tier data quality hierarchy '
            '(primary records → regulatory → ILI → pressure test → engineering derivation → standard nominal → assumption). '
            'Basis: Burkinshaw (2024); Mahmoud &amp; Dodds (2022); API TR 1178; API RP 1160.</div>',
            unsafe_allow_html=True,
        )

        # ── equation block ────────────────────────────────────────────────────
        # (equations hidden in UI — see methodology docs)

        # ── build quality table ───────────────────────────────────────────────
        quality_map = _load_assumption_quality(selection)

        critical_params = [
            ("Pipeline length",         "pipeline_length_km",           row.get("length_km") if row is not None else ranked_row.get("LENGTH_KM") if ranked_row is not None else None, "km"),
            ("Outer diameter",          "outer_diameter_in",            row.get("outer_diameter_in") if row is not None else None, "in"),
            ("Inner diameter",          "inner_diameter_in",            row.get("inner_diameter_in") if row is not None else ranked_row.get("INT_DIAM") if ranked_row is not None else None, "in"),
            ("Wall thickness (nominal)","nominal_wall_thickness_mm",    row.get("nominal_wall_thickness_mm") if row is not None else ranked_row.get("THICKNESS") if ranked_row is not None else None, "mm"),
            ("Pipe grade",              "pipe_grade",                   row.get("pipe_grade") if row is not None else None, ""),
            ("Inlet pressure",          "inlet_pressure_psia",          None, "psia"),
            ("Outlet pressure",         "outlet_pressure_psia",         None, "psia"),
        ]

        significant_params = [
            ("Transport temperature",   "transport_temperature_c",      None, "°C"),
            ("Required project flow",   "required_project_flow_mtpa",   row.get("required_design_mtpa") if row is not None else None, "Mtpa"),
            ("Capacity factor",         "capacity_factor",              None, ""),
            ("Start operation year",    "start_operation_year",         row.get("start_operation_year") if row is not None else ranked_row.get("START_DATE") if ranked_row is not None else None, ""),
            ("Historical corrosion rate","historical_corrosion_rate_mm_per_year", row.get("historical_wall_loss_mm") if row is not None else None, "mm/yr"),
            ("Future CO2 corrosion rate","future_co2_corrosion_rate_mm_per_year", row.get("future_co2_corrosion_rate_mm_per_year") if row is not None else None, "mm/yr"),
            ("ILI / MFL available",     "ili_mfl_available",            row.get("ili_mfl_available") if row is not None else None, ""),
            ("Material certificates",   "material_certificates_available", row.get("material_certificates_available") if row is not None else None, ""),
            ("Fracture toughness basis","fracture_toughness_basis",     row.get("fracture_toughness_basis") if row is not None else None, ""),
            ("Component compatibility", "component_compatibility_screened", row.get("component_compatibility_screened") if row is not None else None, ""),
        ]

        def _build_dq_rows(params: list, label: str) -> list[dict]:
            out = []
            for display, param, value, unit in params:
                q = quality_map.get(param, "assumed")
                tier, tier_label = _dq_tier(q)
                icon = _dq_tier_colour(tier)
                val_str = f"{value} {unit}".strip() if value not in (None, "", "nan", float("nan")) else "—"
                try:
                    if value is not None and float(str(value)) != float(str(value)):
                        val_str = "—"
                except (ValueError, TypeError):
                    pass
                out.append({
                    "Criticality": label,
                    "Parameter": display,
                    "Value": val_str,
                    "Source quality": f"{icon} T{tier} — {tier_label}",
                    "Tier": tier,
                })
            return out

        crit_rows = _build_dq_rows(critical_params, "Critical")
        sig_rows  = _build_dq_rows(significant_params, "Significant")
        all_rows  = crit_rows + sig_rows

        # ── completeness score ────────────────────────────────────────────────
        crit_tiers = [r["Tier"] for r in crit_rows]
        score = int(100 * sum(1 for t in crit_tiers if t <= 4) / len(crit_tiers)) if crit_tiers else 0
        score_colour = "🟢" if score >= 75 else ("🟡" if score >= 50 else "🔴")

        col_score, col_table = st.columns([1, 2.5])
        with col_score:
            st.metric("Critical parameter score", f"{score_colour} {score}%")
            st.caption(
                "% of critical parameters sourced from tier 1–4 "
                "(primary, regulatory, ILI, or pressure test records)."
            )
            n_assumed = sum(1 for r in crit_rows if r["Tier"] >= 7)
            if n_assumed:
                st.warning(
                    f"{n_assumed} critical parameter(s) are tier-7 assumptions. "
                    "Results are screening-level only. Do not cite as engineering assessment.",
                    icon="⚠️",
                )
            n_missing = sum(1 for r in all_rows if r["Value"] == "—")
            if n_missing:
                st.info(f"{n_missing} parameter(s) have no value available in current run.", icon="ℹ️")

        with col_table:
            display_df = pd.DataFrame([
                {"Parameter": r["Parameter"], "Value": r["Value"], "Quality": r["Source quality"], "Criticality": r["Criticality"]}
                for r in all_rows
            ])
            st.dataframe(display_df, hide_index=True, use_container_width=True)

        # ── wall thickness conflict warning ───────────────────────────────────
        wall = row.get("nominal_wall_thickness_mm") if row is not None else None
        if wall is not None:
            wall_f = as_float(wall)
            if wall_f is not None:
                od_in = row.get("outer_diameter_in") if row is not None else None
                od_f  = as_float(od_in)
                inlet = row.get("average_pressure_mpa") if row is not None else None
                inlet_f = as_float(inlet)
                if od_f and inlet_f:
                    smys_mpa = 413.7  # X60 default
                    t_min = inlet_f * (od_f * 25.4) / (2 * smys_mpa * 0.72)
                    if wall_f < t_min:
                        st.error(
                            f"⛔ Wall thickness {wall_f:.2f} mm is below the Barlow minimum "
                            f"({t_min:.2f} mm) for {inlet_f:.1f} MPa, X60, DF=0.72. "
                            "This value must be verified before any integrity assessment.",
                            icon="🚨",
                        )
                    elif wall_f < t_min * 1.15:
                        st.warning(
                            f"Wall thickness {wall_f:.2f} mm is close to the Barlow minimum "
                            f"({t_min:.2f} mm, <15% margin). Verify against primary records.",
                            icon="⚠️",
                        )

        render_layer_button("Run / refresh screening", selection)


def render_capacity_layer(row: pd.Series | None, selection: dict[str, str]) -> None:
    with st.container(border=True):
        st.markdown('<div class="workflow-step"><h3>2. CO2 Transport Capacity</h3></div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-note">Weymouth equation for dense-phase CO2 flow. '
            'Cross-validation target: REPACT tool (2024). Ref: hydraulics.py.</div>',
            unsafe_allow_html=True,
        )

        r = row  # shorthand
        length   = as_float(r.get("length_km") if r is not None else None)
        id_in    = as_float(r.get("inner_diameter_in") if r is not None else None)
        id_m     = as_float(r.get("inner_diameter_m") if r is not None else None)
        p_avg    = as_float(r.get("average_pressure_mpa") if r is not None else None)
        friction = as_float(r.get("fanning_friction_factor") if r is not None else None)
        cap_kgs  = as_float(r.get("capacity_kg_per_s") if r is not None else None)
        cap_mtp  = as_float(r.get("capacity_mtpa") if r is not None else None)
        req_flow = as_float(r.get("required_design_mtpa") if r is not None else None)
        reynolds = as_float(r.get("reynolds_number") if r is not None else None)
        rep_cap  = as_float(r.get("reported_capacity_mtpa") if r is not None else None)

        left, right = st.columns([1.2, 1])
        with left:
            # (equations hidden in UI — see methodology docs)
            data_table([
                {"Input": "Length",             "Value": fmt_number(length, 1, " km"),      "Source": "NSTA/scenario"},
                {"Input": "Inner diameter",     "Value": fmt_number(id_in, 3, " in"),       "Source": "NSTA/scenario"},
                {"Input": "Avg pressure",       "Value": fmt_number(p_avg, 2, " MPa"),      "Source": "calculated"},
                {"Input": "Fanning friction f", "Value": fmt_number(friction, 6),           "Source": "Moody/defaults"},
                {"Input": "Reynolds number",    "Value": fmt_number(reynolds, 0),           "Source": "calculated"},
                {"Input": "Required design flow","Value": fmt_number(req_flow, 2, " Mtpa"), "Source": "project requirement"},
            ])

        with right:
            status_pill("Capacity suitable", r.get("capacity_suitable") if r is not None else "not run")
            st.metric("Estimated capacity",  fmt_number(cap_mtp, 2, " MtCO2/yr"))
            st.metric("Required flow",       fmt_number(req_flow, 2, " MtCO2/yr"))
            if cap_mtp is not None and req_flow is not None:
                delta = cap_mtp - req_flow
                st.metric("Capacity margin", fmt_number(delta, 2, " Mtpa"),
                          delta_color="normal" if delta >= 0 else "inverse")
            st.metric("Mass flow", fmt_number(cap_kgs, 1, " kg/s"))
            if rep_cap is not None:
                st.metric("Reported capacity (original gas)", fmt_number(rep_cap, 2, " Mtpa"))
                if cap_mtp is not None:
                    st.caption(f"CO2 capacity / original gas capacity = {cap_mtp/rep_cap*100:.0f}% — dense CO2 is denser than gas so capacity increases")

        render_layer_button("Run / refresh capacity layer", selection)


def render_corrosion_layer(row: pd.Series | None, selection: dict[str, str]) -> None:
    with st.container(border=True):
        st.markdown('<div class="workflow-step"><h3>3. Corrosion Screening</h3></div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-note">Internal corrosion risk from water content; future corrosion rate for remaining life. '
            'Ref: ISO 27913:2024 §8.3 (water limit 500 ppmv for carbon steel); DNV-RP-J202.</div>',
            unsafe_allow_html=True,
        )

        r = row
        corr_rate     = as_float(r.get("future_co2_corrosion_rate_mm_per_year") if r is not None else None)
        corr_low      = as_float(r.get("corrosion_rate_low_mm_per_year") if r is not None else None)
        corr_high     = as_float(r.get("corrosion_rate_high_mm_per_year") if r is not None else None)

        left, right = st.columns([1.2, 1])
        with left:
            # (equations hidden in UI — see methodology docs)
            data_table([
                {"Input": "CO2 water content",      "Value": "see scenario defaults",         "Source": "assumption — replace with stream spec"},
                {"Input": "Water spec limit",        "Value": "500 ppmv",                      "Source": "ISO 27913:2024; DNV-RP-J202"},
                {"Input": "Dew-point margin",        "Value": "see scenario defaults",         "Source": "assumption"},
                {"Input": "Future CO2 corr. rate",   "Value": fmt_number(corr_rate, 3, " mm/yr"), "Source": "scenario/defaults"},
                {"Input": "Low corrosion case",      "Value": fmt_number(corr_low,  3, " mm/yr"), "Source": "sensitivity"},
                {"Input": "High corrosion case",     "Value": fmt_number(corr_high, 3, " mm/yr"), "Source": "sensitivity"},
            ])

        with right:
            status_pill("Corrosion risk", r.get("corrosion_risk_level") if r is not None else "not run")
            if corr_rate is not None:
                st.metric("Future CO2 corrosion rate (base)", fmt_number(corr_rate, 3, " mm/yr"))
            if corr_low is not None and corr_high is not None:
                st.metric("Low case",  fmt_number(corr_low, 3, " mm/yr"))
                st.metric("High case", fmt_number(corr_high, 3, " mm/yr"))
            st.caption(
                "⚠ Corrosion rate is an assumed value for all NSTA pipelines. "
                "Validation requires: CO2 stream composition, water dew-point test, "
                "and ILI metal-loss data [Kass et al. 2023; ISO 27913:2024]."
            )

        render_layer_button("Run / refresh corrosion layer", selection)


def render_integrity_layer(row: pd.Series | None, selection: dict[str, str]) -> None:
    with st.container(border=True):
        st.markdown('<div class="workflow-step"><h3>4. Wall Thickness &amp; Remaining Life</h3></div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-note">Barlow minimum wall check + remaining life from future corrosion rate. '
            'Methodology: Mahmoud &amp; Dodds (2022) survival analysis approach. '
            'Cross-check: ISO 27913:2024 §7; DNV-RP-J202.</div>',
            unsafe_allow_html=True,
        )

        r = row
        nominal_wall  = as_float(r.get("nominal_wall_thickness_mm") if r is not None else None)
        hist_loss     = as_float(r.get("historical_wall_loss_mm") if r is not None else None)
        current_wall  = as_float(r.get("current_wall_thickness_mm") if r is not None else None)
        min_wall      = as_float(r.get("minimum_wall_thickness_mm") if r is not None else None)
        avail_wall    = as_float(r.get("available_wall_thickness_mm") if r is not None else None)
        avail_low     = as_float(r.get("available_wall_low_mm") if r is not None else None)
        avail_high    = as_float(r.get("available_wall_high_mm") if r is not None else None)
        corr_rate     = as_float(r.get("future_co2_corrosion_rate_mm_per_year") if r is not None else None)
        life_base     = as_float(r.get("remaining_life_years") if r is not None else None)
        life_low      = as_float(r.get("remaining_life_low_years") if r is not None else None)
        life_high     = as_float(r.get("remaining_life_high_years") if r is not None else None)
        rep_life      = as_float(r.get("reported_remaining_life_years") if r is not None else None)

        left, right = st.columns([1.2, 1])
        with left:
            # (equations hidden in UI — see methodology docs)
            data_table([
                {"Step": "Nominal wall (t₀)",        "Value": fmt_number(nominal_wall,  2, " mm"),  "Note": "design or NSTA record — verify source tier"},
                {"Step": "− Historical loss",         "Value": fmt_number(hist_loss,     2, " mm"),  "Note": "rate × years"},
                {"Step": "= Current wall (t_now)",    "Value": fmt_number(current_wall,  2, " mm"),  "Note": ""},
                {"Step": "− Barlow minimum (t_min)",  "Value": fmt_number(min_wall,      2, " mm"),  "Note": "P × OD / (2 × SMYS × DF)"},
                {"Step": "= Available wall (t_avail)","Value": fmt_number(avail_wall,    2, " mm"),  "Note": f"low={fmt_number(avail_low,1)} high={fmt_number(avail_high,1)}"},
                {"Step": "÷ Future CO2 corr. rate",   "Value": fmt_number(corr_rate,     3, " mm/yr"),"Note": "from Gate 3"},
                {"Step": "= Remaining life",          "Value": fmt_number(life_base,     1, " years"),"Note": f"low={fmt_number(life_low,1)} high={fmt_number(life_high,1)}"},
            ])

        with right:
            st.metric("Remaining life (base)", fmt_number(life_base, 1, " years"))
            st.metric("Low case",              fmt_number(life_low,  1, " years"))
            st.metric("High case",             fmt_number(life_high, 1, " years"))
            if rep_life is not None:
                st.metric("Reported life (original source)", fmt_number(rep_life, 1, " years"))
                if life_base is not None:
                    delta_life = life_base - rep_life
                    st.metric("Model vs reported", fmt_number(delta_life, 1, " years"),
                              delta_color="normal" if abs(delta_life) < 5 else "inverse")
            if avail_wall is not None and avail_wall < 0:
                st.error("⛔ Available wall is negative — pipeline has exceeded design life at base case.", icon="🚨")
            elif avail_wall is not None and avail_wall < 2:
                st.warning("Available wall < 2 mm — very thin margin. Verify wall thickness source tier.", icon="⚠️")

        render_layer_button("Run / refresh integrity layer", selection)


def render_gate_layer(row: pd.Series | None, selection: dict[str, str]) -> None:
    with st.container(border=True):
        st.markdown('<div class="workflow-step"><h3>5. Repurposing Evidence Gate</h3></div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-note">Structured evidence checklist for CO2 repurposing. '
            'Framework: DNV PTC 2022 (Leinum et al.); Monsma &amp; Murray (2026); '
            'OTC-31457 (Luna-Ortiz 2022). Missing evidence is output, not hidden.</div>',
            unsafe_allow_html=True,
        )

        r = row
        evidence_score = as_float(r.get("repurposing_evidence_score") if r is not None else None)
        gaps   = split_items(r.get("repurposing_evidence_gaps") if r is not None else None)
        stops  = split_items(r.get("repurposing_showstoppers") if r is not None else None)
        refs   = split_items(r.get("repurposing_gate_cited_references") if r is not None else None)
        next_d = split_items(r.get("pre_lca_next_data") if r is not None else None)

        # (equations hidden in UI — see methodology docs)

        col1, col2, col3 = st.columns(3)
        with col1:
            status_pill("Gate status",      r.get("repurposing_gate_status")    if r is not None else "not run")
            status_pill("CO2 phase screen", r.get("repurposing_phase_status")   if r is not None else "not run")
            status_pill("Gate confidence",  r.get("repurposing_gate_confidence") if r is not None else "not run")
            st.metric("Evidence score", fmt_number(evidence_score, 1, "/100"))

        with col2:
            st.markdown("**Evidence gaps**")
            if gaps:
                for g in gaps:
                    st.markdown(f"- {g}")
            else:
                st.markdown("_None listed — run screening_")
            if stops:
                st.error("**Showstoppers:**\n" + "\n".join(f"- {s}" for s in stops), icon="🚨")

        with col3:
            st.markdown("**Next data required**")
            if next_d:
                for nd in next_d:
                    st.markdown(f"- {nd}")
            else:
                st.markdown("_None listed_")
            if refs:
                st.markdown("**References cited**")
                for ref in refs:
                    st.markdown(f"- {ref}")

        if r is not None:
            reason = r.get("repurposing_gate_reason_summary")
            if reason and str(reason).strip() not in ("", "nan"):
                st.caption(f"Summary: {clean_text(reason)}")

        render_layer_button("Run / refresh repurposing gate", selection)


def render_work_scope_layer(row: pd.Series | None, selection: dict[str, str]) -> None:
    scenario = selection["screening_scenario"]
    path = SCREENING_DIR / f"refurbishment_work_scope_{scenario}.csv"
    selected = load_csv(str(path))
    with st.container(border=True):
        st.markdown('<div class="workflow-step"><h3>6. Quantified Work Scope</h3></div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-note">Converts gate findings into quantities for cost and LCA. '
            'Work items are derived from evidence gaps, not invented. '
            'Ref: Saipem PTC 2025 (D\'Alonzo et al.) IMR plan framework; DNV PTC 2025 (Torbergsen).</div>',
            unsafe_allow_html=True,
        )

        r = row
        # (equations hidden in UI — see methodology docs)

        cols = st.columns(4)
        cols[0].metric("Work items",        fmt_number(r.get("refurbishment_work_scope_item_count") if r is not None else None, 0))
        cols[1].metric("Cost items",        fmt_number(r.get("refurbishment_cost_item_count")      if r is not None else None, 0))
        cols[2].metric("LCA items",         fmt_number(r.get("refurbishment_lca_item_count")       if r is not None else None, 0))
        cols[3].metric("Replacement steel", fmt_number(r.get("refurbishment_replacement_steel_kg") if r is not None else None, 0, " kg"))

        if not selected.empty:
            visible = ["work_item_name", "work_stage", "quantity_base", "unit", "cost_driver", "lca_mapping_key", "data_quality"]
            available = [c for c in visible if c in selected.columns]
            st.dataframe(selected[available], hide_index=True, use_container_width=True)
            st.caption(
                "Work scope quantities are derived from pipeline length and evidence gaps. "
                "They are inputs to unit-cost screening (Gate 7) and LCA (Gate 8), "
                "not contractor estimates. Data quality column follows the 7-tier hierarchy from Gate 1."
            )
        else:
            st.info("No work-scope table created yet. Run the screening layer.")


def render_cost_layer(selection: dict[str, str], factor_mode: str) -> None:
    from repurposing_pipelines.costs import calculate_all_models

    cost_row = load_cost_row(selection["cost_case"])
    screen_row = load_scenario_row(selection["screening_scenario"])

    with st.container(border=True):
        st.markdown('<div class="workflow-step"><h3>7. Refurbishment Cost vs New-Build CAPEX</h3></div>', unsafe_allow_html=True)

        # ── equation block ────────────────────────────────────────────────────
        # (equations hidden in UI — see methodology docs)

        # ── run button ────────────────────────────────────────────────────────
        if st.button("Run cost layer", key=f"run_cost_{selection['pipeline_id']}"):
            ok, output = run_cost(selection, factor_mode)
            st.session_state["last_cost_result"] = ("Cost layer", ok, output)
            st.cache_data.clear()
            st.rerun()
        show_run_result("last_cost_result")

        # ── compute new-build if pipeline data available ───────────────────
        nb_results: dict | None = None
        od_in: float | None = None
        length_km: float | None = None
        offshore_factor: float = 1.6

        if screen_row is not None:
            od_in = as_float(screen_row.get("outer_diameter_in"))
            length_km = as_float(screen_row.get("length_km"))

        if od_in is not None and length_km is not None and od_in > 0 and length_km > 0:
            try:
                nb_results = calculate_all_models(
                    diameter_in=od_in,
                    length_km=length_km,
                    project_year=2026,
                    offshore=True,
                    offshore_factor=offshore_factor,
                    contingency_fraction=(
                        cf if (cf := as_float(screen_row.get("contingency_fraction") if screen_row is not None else None)) is not None
                        else 0.10
                    ),
                )
            except Exception:
                nb_results = None

        # ── model selector ────────────────────────────────────────────────────
        model_choice = st.selectbox(
            "New-build model",
            options=["brown", "parker", "mccoy", "rui", "all"],
            format_func=lambda m: {
                "brown": "Brown et al. (2022) — recommended",
                "parker": "Parker (2004)",
                "mccoy": "McCoy & Rubin (2008)",
                "rui": "Rui et al. (2011)",
                "all": "Show all four models",
            }.get(m, m),
            key=f"nb_model_{selection['pipeline_id']}",
        )

        # derive single new-build value for net saving calculation
        nb_total: float | None = None
        if nb_results is not None:
            if model_choice == "all":
                # use Brown as the anchor for net saving when showing all
                nb_total = nb_results["brown"].cost_total_usd
            else:
                nb_total = nb_results[model_choice].cost_total_usd

        # refurbishment values
        refurb_low  = as_float(cost_row.get("cost_low_usd_2025")  if cost_row is not None else None)
        refurb_base = as_float(cost_row.get("cost_base_usd_2025") if cost_row is not None else None)
        refurb_high = as_float(cost_row.get("cost_high_usd_2025") if cost_row is not None else None)

        # ── three-column layout ───────────────────────────────────────────────
        col_nb, col_refurb, col_saving = st.columns(3)

        # Column 1: New-build
        with col_nb:
            st.markdown("**New-build CAPEX**")
            st.caption(f"OD {od_in:.1f}\" · {length_km:.0f} km · offshore {offshore_factor}×" if od_in else "Pipeline dimensions not available")
            if nb_results is None:
                st.info("Run screening to compute new-build cost")
            elif model_choice == "all":
                for m, label in [
                    ("parker", "Parker (2004)"),
                    ("mccoy",  "McCoy & Rubin (2008)"),
                    ("rui",    "Rui et al. (2011)"),
                    ("brown",  "Brown et al. (2022)"),
                ]:
                    st.metric(label, fmt_money(nb_results[m].cost_total_usd))
            else:
                r = nb_results[model_choice]
                st.metric("Total CAPEX", fmt_money(r.cost_total_usd))
                st.metric("Subtotal (pre-contingency)", fmt_money(r.cost_subtotal_usd))
                data_table([
                    {"Component": "Materials",        "Cost": fmt_money(r.cost_mat_usd)},
                    {"Component": "Labour",           "Cost": fmt_money(r.cost_lab_usd)},
                    {"Component": "ROW & damages",    "Cost": fmt_money(r.cost_row_usd)},
                    {"Component": "Miscellaneous",    "Cost": fmt_money(r.cost_misc_usd)},
                    {"Component": "Surge tank",       "Cost": fmt_money(r.cost_surge_tank_usd)},
                    {"Component": "Control system",   "Cost": fmt_money(r.cost_control_system_usd)},
                    {"Component": "Contingency",      "Cost": fmt_money(r.cost_contingency_usd)},
                ])
                if r.warnings:
                    for w in r.warnings:
                        st.caption(f"⚠ {w[:120]}")

        # Column 2: Refurbishment
        with col_refurb:
            st.markdown("**Refurbishment CAPEX**")
            st.caption("Work-scope unit costs — not contractor quotes")
            status_pill("Cost status", cost_row.get("refurbishment_cost_status") if cost_row is not None else "not run")
            st.metric("Base estimate", fmt_money(refurb_base))
            st.metric("Low estimate",  fmt_money(refurb_low))
            st.metric("High estimate", fmt_money(refurb_high))
            if cost_row is not None:
                st.caption(f"Factor quality: {clean_text(cost_row.get('factor_quality_summary'))}")
                n_factors = as_float(cost_row.get("included_factor_count"))
                n_missing = as_float(cost_row.get("missing_factor_count"))
                if n_factors is not None:
                    st.caption(f"Factors: {int(n_factors)} included, {int(n_missing or 0)} missing")

        # Column 3: Net saving
        with col_saving:
            st.markdown("**Net CAPEX Saving**")
            st.caption(f"New-build ({model_choice if model_choice != 'all' else 'Brown'}) − refurbishment")
            if nb_total is None or refurb_base is None:
                st.info("Run screening and cost layer to compute net saving")
            else:
                saving_low  = nb_total - (refurb_high or 0)   # worst case saving
                saving_base = nb_total - (refurb_base or 0)
                saving_high = nb_total - (refurb_low or 0)    # best case saving
                saving_pct  = 100 * saving_base / nb_total if nb_total else None

                st.metric("Base saving",      fmt_money(saving_base))
                st.metric("Low saving",       fmt_money(saving_low))
                st.metric("High saving",      fmt_money(saving_high))
                if saving_pct is not None:
                    st.metric("Saving vs new-build", fmt_number(saving_pct, 1, "%"))

        # ── disclaimer ────────────────────────────────────────────────────────
        st.caption(
            "New-build CAPEX uses US onshore natural gas pipeline regression models (Parker 2004; McCoy & Rubin 2008; "
            "Rui et al. 2011; Brown et al. 2022) per NETL (2024), escalated to 2026 USD using the RSMeans CCI. "
            "An offshore factor of 1.6 is applied (range 1.5–2.0; ZEP 2011; Knoope et al. 2014). "
            "No offshore CO2 pipeline regression model currently exists in the published literature. "
            "See model_layers/04_cost_economics/cost_escalation_basis.md for full methodology."
        )


def render_lca_layer(row: pd.Series | None, selection: dict[str, str], factor_mode: str) -> None:
    lca_row = load_lca_row(selection["lca_scenario"])
    with st.container(border=True):
        st.markdown('<div class="workflow-step"><h3>8. LCA Screening</h3></div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-note">Two-level LCA: (a) proxy screening using steel mass and construction factors; '
            '(b) ecoinvent-linked LCA using Brightway. '
            'Functional unit: transport of 1 tonne CO2 through the selected pipeline route. '
            'Cross-validation target: Re-Stream (2021); HyNet pre-FEED WP6.</div>',
            unsafe_allow_html=True,
        )

        r = row
        nb_steel      = as_float(r.get("lca_steel_mass_new_build_kg")  if r is not None else None)
        refurb_steel  = as_float(r.get("lca_refurbishment_steel_kg")   if r is not None else None)
        avoided_steel = as_float(r.get("lca_avoided_steel_kg")         if r is not None else None)
        nb_proxy      = as_float(r.get("lca_new_build_proxy_kgco2e")   if r is not None else None)
        reuse_proxy   = as_float(r.get("lca_reuse_proxy_kgco2e")       if r is not None else None)
        saving_proxy  = as_float(r.get("lca_proxy_saving_kgco2e")      if r is not None else None)
        saving_pct    = as_float(r.get("lca_proxy_saving_percent")      if r is not None else None)

        # (equations hidden in UI — see methodology docs)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**Steel inventory**")
            data_table([
                {"Item": "New-build steel",      "Value": fmt_number(nb_steel,      0, " kg")},
                {"Item": "Refurbishment steel",  "Value": fmt_number(refurb_steel,  0, " kg")},
                {"Item": "Avoided steel",        "Value": fmt_number(avoided_steel, 0, " kg")},
                {"Item": "Refurb fraction",      "Value": fmt_number(
                    100 * refurb_steel / nb_steel if nb_steel and refurb_steel else None, 1, "%")},
            ])

        with col2:
            st.markdown("**Proxy LCA (screening)**")
            status_pill("LCA screening decision", r.get("lca_screening_decision") if r is not None else "not run")
            st.metric("New-build impact",  fmt_number((nb_proxy or 0)/1000,     1, " tCO2e"))
            st.metric("Reuse impact",      fmt_number((reuse_proxy or 0)/1000,  1, " tCO2e"))
            st.metric("Proxy saving",      fmt_number((saving_proxy or 0)/1000, 1, " tCO2e"))
            st.metric("Saving vs new-build", fmt_number(saving_pct, 1, "%"))

        with col3:
            st.markdown("**ecoinvent-linked LCA**")
            status_pill("ecoinvent LCA status", lca_row.get("lca_status") if lca_row is not None else "not run")
            if lca_row is not None:
                reuse_base = as_float(lca_row.get("reuse_kgco2e_base"))
                reuse_low  = as_float(lca_row.get("reuse_kgco2e_low"))
                reuse_high = as_float(lca_row.get("reuse_kgco2e_high"))
                st.metric("Reuse impact (base)", fmt_number((reuse_base or 0)/1000, 1, " tCO2e"))
                st.metric("Low case",            fmt_number((reuse_low  or 0)/1000, 1, " tCO2e"))
                st.metric("High case",           fmt_number((reuse_high or 0)/1000, 1, " tCO2e"))
                st.caption(f"Factor quality: {clean_text(lca_row.get('factor_quality_summary'))}")
            else:
                st.info("Run LCA layer to generate ecoinvent-linked results.")

        st.caption(
            "Proxy factors are open placeholders (steel: 2.0 kgCO2e/kg; construction: 100 tCO2e/km; refurbishment: 20 tCO2e/km). "
            "These must be replaced with ecoinvent/Brightway outputs before publication. "
            "Cross-validation targets: Re-Stream EU study (2021); HyNet CCUS pre-FEED WP6 (~2020)."
        )

        if st.button("Run LCA layer", key=f"run_lca_{selection['pipeline_id']}"):
            ok, output = run_lca(selection, factor_mode)
            st.session_state["last_lca_result"] = ("LCA layer", ok, output)
            st.cache_data.clear()
            st.rerun()
        show_run_result("last_lca_result")


def render_traceability(row: pd.Series | None, selection: dict[str, str]) -> None:
    with st.container(border=True):
        st.markdown('<div class="workflow-step"><h3>Traceability</h3></div>', unsafe_allow_html=True)
        scenario = selection["screening_scenario"]
        paths = {
            "Screening report": SCREENING_DIR / f"pipeline_screen_{scenario}.md",
            "Trace file": SCREENING_DIR / f"pipeline_screen_{scenario}_trace.json",
            "Work-scope table": SCREENING_DIR / f"refurbishment_work_scope_{scenario}.csv",
            "Cost report": COST_DIR / f"refurbishment_cost_report_{selection['cost_case']}.md",
            "LCA report": LCA_DIR / f"lca_report_{selection['lca_scenario']}.md",
        }
        for label, path in paths.items():
            st.write(f"**{label}:** {'available' if path.exists() else 'not created yet'}")
            st.code(str(path), language="text")
        if row is not None:
            refs = split_items(row.get("repurposing_gate_cited_references"))
            if refs:
                st.markdown("**References cited by gate**")
                st.write("\n".join(f"- {item}" for item in refs))


def render_workflow(row: pd.Series | None, ranked_row: pd.Series | None, selection: dict[str, str], factor_mode: str) -> None:
    st.subheader("Gate-By-Gate Model Layers")
    render_data_layer(row, ranked_row, selection)
    render_capacity_layer(row, selection)
    render_corrosion_layer(row, selection)
    render_integrity_layer(row, selection)
    render_gate_layer(row, selection)
    render_work_scope_layer(row, selection)
    render_cost_layer(selection, factor_mode)
    render_lca_layer(row, selection, factor_mode)
    render_traceability(row, selection)


def main() -> None:
    apply_style()
    render_header()

    ranked_df = load_csv(str(DATA_DIR / "nsta_candidate_ranked.csv"))
    screening_df = load_csv(str(SCREENING_DIR / "pipeline_screen_nsta_all.csv"))
    all_routes_payload = load_all_routes()
    candidate_df = build_candidate_table(ranked_df, screening_df)
    if candidate_df.empty:
        st.error("No NSTA candidate table was found.")
        return
    candidate_pipeline_ids: set[str] = set(candidate_df["pipeline_id"].tolist())

    factor_mode = "screening"

    # Resolve pipeline selection from session state
    map_selected = st.session_state.get("map_selected_pipeline_id")
    if map_selected in candidate_pipeline_ids:
        st.session_state["selected_pipeline_id"] = map_selected
        del st.session_state["map_selected_pipeline_id"]

    default_id = st.session_state.get("selected_pipeline_id", "PL774")
    if default_id not in candidate_pipeline_ids:
        default_id = "PL774" if "PL774" in candidate_pipeline_ids else candidate_df.iloc[0]["pipeline_id"]

    # Goldeneye uses preloaded scenario assumptions; all other pipelines use NSTA screening
    if default_id == "PL1978":
        selection: dict[str, str] = {
            "kind": "nsta",
            "pipeline_id": "PL1978",
            "screening_scenario": "goldeneye_poster",
            "cost_case": "goldeneye_poster",
            "lca_scenario": "goldeneye_poster",
            "label": "20\" GAS GOLDENEYE - ST. FERGUS",
        }
        ranked_row = selected_ranked_row(candidate_df, "PL1978")
        row = load_scenario_row("goldeneye_poster")
    else:
        selection = {
            "kind": "nsta",
            "pipeline_id": default_id,
            "screening_scenario": nsta_scenario_name(default_id),
            "cost_case": nsta_scenario_name(default_id),
            "lca_scenario": nsta_scenario_name(default_id),
            "label": default_id,
        }
        ranked_row = selected_ranked_row(candidate_df, default_id)
        row = selected_screening_row(screening_df, default_id)

    render_top_area(all_routes_payload, row, ranked_row, selection, candidate_pipeline_ids)
    render_key_metrics(row, ranked_row)
    _html("<hr>")
    render_workflow(row, ranked_row, selection, factor_mode)



if __name__ == "__main__":
    main()
