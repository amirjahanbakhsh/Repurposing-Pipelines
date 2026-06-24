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
    st.markdown(
        """
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,wght@0,400;0,500;0,600;1,400&family=Manrope:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root {
    --bg:    #0A0E1A;
    --panel: #131826;
    --line:  #232B42;
    --text:  #F4F1EA;
    --mute:  #9CA3B2;
    --accent:#5EEAD4;
}
.stApp {
    background: #0A0E1A;
    color: #F4F1EA;
    font-family: 'Manrope', sans-serif;
}
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 3rem;
    max-width: 1400px;
}
h1, h2, h3 {
    font-family: 'Fraunces', 'Georgia', serif;
    font-weight: 500;
    letter-spacing: -0.01em;
    color: #F4F1EA;
}
h1 { font-size: 36px; margin-bottom: 0.15rem; }
h2 { font-size: 24px; margin-top: 0.4rem; }
h3 { font-size: 18px; }
div[data-testid="stMetric"] {
    background: #131826;
    border: 1px solid #232B42;
    border-radius: 12px;
    padding: 0.85rem 1rem;
    min-height: 92px;
}
div[data-testid="stMetric"] label {
    font-family: 'Manrope', sans-serif;
    font-size: 11px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #9CA3B2;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    font-family: 'JetBrains Mono', 'Consolas', monospace;
    font-size: 22px;
    color: #F4F1EA;
}
div[data-testid="stVerticalBlockBorderWrapper"] {
    border-color: #232B42;
    border-radius: 14px;
    background: #131826;
}
[data-testid="stSidebar"] {
    background: #131826;
    border-right: 1px solid #232B42;
}
.stButton > button {
    font-family: 'Manrope', sans-serif;
    border-radius: 8px;
    border: 1px solid #232B42;
    background: #131826;
    color: #F4F1EA;
    font-weight: 500;
}
.stButton > button:hover {
    background: #1e263a;
    border-color: #5EEAD4;
    color: #5EEAD4;
}
.tool-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 1rem;
    border-bottom: 1px solid #232B42;
    padding-bottom: 1rem;
    margin-bottom: 1.2rem;
}
.eyebrow {
    font-family: 'Manrope', sans-serif;
    font-size: 11px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #5F6981;
    margin-bottom: 4px;
}
.small-muted {
    color: #9CA3B2;
    font-size: 0.88rem;
    font-family: 'Manrope', sans-serif;
}
.status-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.75rem;
    padding: 0.6rem 0;
    border-bottom: 1px solid #232B42;
}
.status-row strong {
    display: inline-block;
    border-radius: 999px;
    padding: 0.22rem 0.7rem;
    font-size: 0.75rem;
    font-family: 'Manrope', sans-serif;
    font-weight: 600;
    letter-spacing: 0.05em;
    line-height: 1.3;
    white-space: nowrap;
}
.section-note {
    background: #131826;
    border: 1px solid #232B42;
    border-left: 3px solid #5EEAD4;
    border-radius: 10px;
    padding: 0.75rem 1rem;
    color: #9CA3B2;
    font-size: 0.88rem;
    font-family: 'Manrope', sans-serif;
    line-height: 1.6;
}
.missing-note {
    background: #1e1500;
    border: 1px solid #4a3500;
    border-left: 3px solid #FBBF24;
    border-radius: 10px;
    padding: 0.75rem 1rem;
    color: #FCD34D;
    font-size: 0.88rem;
    font-family: 'Manrope', sans-serif;
    line-height: 1.6;
}
.workflow-step {
    border-left: 4px solid #5EEAD4;
    padding-left: 0.85rem;
    margin-bottom: 0.5rem;
}
.score-card {
    background: #131826;
    border: 1px solid #232B42;
    border-radius: 14px;
    padding: 18px 22px;
    margin-bottom: 12px;
}
.score-num {
    font-family: 'JetBrains Mono', 'Consolas', monospace;
    font-size: 52px;
    font-weight: 500;
    line-height: 1;
    color: #F4F1EA;
}
.score-num-small {
    font-family: 'JetBrains Mono', monospace;
    font-size: 26px;
    color: #F4F1EA;
}
hr { border-color: #232B42; }
/* dataframes */
[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }
/* code blocks */
.stCodeBlock { background: #0f1320 !important; border: 1px solid #232B42; border-radius: 8px; }
/* expanders */
[data-testid="stExpander"] summary {
    font-family: 'Manrope', sans-serif;
    font-weight: 500;
    color: #F4F1EA;
}
[data-testid="stExpander"] { border-color: #232B42 !important; background: #131826; border-radius: 10px; }
/* segmented control & select */
[data-testid="stSegmentedControl"] { font-family: 'Manrope', sans-serif; }
</style>
        """,
        unsafe_allow_html=True,
    )


def build_candidate_table(ranked_df: pd.DataFrame, screening_df: pd.DataFrame) -> pd.DataFrame:
    if ranked_df.empty:
        return pd.DataFrame()
    candidates = ranked_df.copy()
    candidates["pipeline_id"] = candidates["NSTAPIPNO"].astype(str).str.strip().str.upper()
    candidates["rank"] = pd.to_numeric(candidates["RANK"], errors="coerce")
    candidates["data_priority_score"] = pd.to_numeric(candidates["SCREENING_SCORE"], errors="coerce")

    if not screening_df.empty:
        screen_cols = [
            "nsta_pipeline_number",
            "pre_lca_decision",
            "repurposing_gate_status",
            "capacity_mtpa",
            "remaining_life_years",
            "lca_proxy_saving_percent",
        ]
        available = [column for column in screen_cols if column in screening_df.columns]
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
            f"({clean_text(row.get('FLUID'), 'fluid n/a').lower()}, {clean_text(row.get('STATUS'), 'status n/a').lower()})"
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
        if pid == selected_pipeline_id:
            sel_routes.append({**route, "_color": [248, 113, 113, 240], "_width": 6})
        elif route.get("is_candidate"):
            cand_routes.append({**route, "_color": [20, 184, 166, 200], "_width": 3})
            if pid not in seen_cand:
                seen_cand[pid] = route
        else:
            dim_routes.append({**route, "_color": [59, 106, 181, 40], "_width": 1})

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
    st.markdown(
        """
        <div class="tool-header">
          <div>
            <div class="eyebrow">Screening &amp; Evidence Workflow</div>
            <h1>CO<sub style="font-size:0.7em;">2</sub> Pipeline Repurposing
              <em style="font-style:italic; color:#5EEAD4;">Evaluation Tool</em></h1>
            <div class="small-muted" style="max-width:680px; line-height:1.6; margin-top:6px;">
              Select an asset, inspect the data, then run each model layer gate by gate.
              A pass or marginal result means &#8220;worth deeper study&#8221;,
              not engineering approval.
            </div>
          </div>
          <div class="score-card" style="min-width:160px; text-align:center; border-top:2px solid #5EEAD4;">
            <div class="eyebrow">Model version</div>
            <div class="score-num-small" style="color:#5EEAD4;">1.0</div>
            <div style="color:#5F6981; font-size:11px; margin-top:4px;">NSTA pipeline dataset</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


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


def render_top_area(
    all_routes_payload: dict[str, Any],
    row: pd.Series | None,
    ranked_row: pd.Series | None,
    selection: dict[str, str],
    candidate_pipeline_ids: set[str],
) -> None:
    map_col, profile_col = st.columns([1.65, 1], gap="large")

    map_active_id = selection["pipeline_id"] if selection["kind"] == "nsta" else selection.get("map_pipeline_id")
    non_candidate_preview = st.session_state.get("non_candidate_preview")
    if non_candidate_preview:
        map_active_id = non_candidate_preview

    with map_col:
        st.markdown(
            """
            <div style="display:flex; gap:18px; margin-bottom:6px; font-size:12px;
                        font-family:'Manrope',sans-serif; color:#9CA3B2;">
              <span><span style="display:inline-block; width:10px; height:10px;
                    border-radius:50%; background:#5EEAD4; margin-right:5px;"></span>CO₂ candidate</span>
              <span><span style="display:inline-block; width:10px; height:10px;
                    border-radius:50%; background:#F87171; margin-right:5px;"></span>Selected</span>
              <span><span style="display:inline-block; width:10px; height:10px;
                    border-radius:50%; background:#3C5078; margin-right:5px;"></span>All NSTA pipelines</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        clicked_pipeline_id = render_route_map(all_routes_payload, map_active_id)
        if clicked_pipeline_id and clicked_pipeline_id != map_active_id:
            apply_pipeline_selection_from_map_choice(clicked_pipeline_id, candidate_pipeline_ids)
            st.rerun()
        st.caption(
            f"Showing {len(all_routes_payload.get('routes', []))} route segments · "
            f"{all_routes_payload.get('candidate_count', '?')} CO₂ candidates (teal) · "
            "Click any pipeline to inspect it."
        )

        route_summary = route_summary_table(all_routes_payload)
        if not route_summary.empty:
            active_route_id = map_active_id if map_active_id in set(route_summary["pipeline_id"]) else route_summary.iloc[0]["pipeline_id"]
            fallback_index = int(route_summary.index[route_summary["pipeline_id"] == active_route_id][0])
            fallback_options = route_summary["display"].tolist()
            fallback_default = fallback_options[fallback_index]
            if st.session_state.get("route_picker_label") not in fallback_options:
                st.session_state["route_picker_label"] = fallback_default

            picked_label = st.selectbox(
                "Fallback selector",
                fallback_options,
                index=fallback_index,
                key="route_picker_label",
                help="Use this if map clicks do not register reliably.",
            )
            picked_pipeline_id = str(route_summary.loc[route_summary["display"] == picked_label, "pipeline_id"].iloc[0])
            if picked_pipeline_id != map_active_id:
                apply_pipeline_selection_from_map_choice(picked_pipeline_id, candidate_pipeline_ids)
                st.rerun()

    with profile_col:
        if non_candidate_preview:
            record = find_route_record(all_routes_payload, non_candidate_preview)
            if record:
                render_non_candidate_info(record)
            if st.button("← Back to candidate", width="stretch"):
                st.session_state.pop("non_candidate_preview", None)
                st.rerun()
        else:
            st.markdown(
                "<div class='eyebrow' style='margin-bottom:8px;'>Pipeline Information</div>",
                unsafe_allow_html=True,
            )
            status_pill("Pre-LCA decision", row.get("pre_lca_decision") if row is not None else "not run")
            status_pill("Repurposing gate", row.get("repurposing_gate_status") if row is not None else "not run")
            status_pill("Capacity suitable", row.get("capacity_suitable") if row is not None else "not run")
            info = profile_rows(row, ranked_row, selection)
            data_table(info)
            render_missing_warning(info)
            if ranked_row is not None:
                st.caption(
                    "Data priority score is a data-screening helper only — not an engineering suitability ranking."
                )


def render_key_metrics(row: pd.Series | None, ranked_row: pd.Series | None) -> None:
    cols = st.columns(5)
    cols[0].metric("Capacity", fmt_number(row.get("capacity_mtpa") if row is not None else None, 2, " Mtpa"))
    cols[1].metric("Required flow", fmt_number(row.get("required_design_mtpa") if row is not None else None, 2, " Mtpa"))
    cols[2].metric("Remaining life", fmt_number(row.get("remaining_life_years") if row is not None else None, 1, " yr"))
    cols[3].metric("Evidence score", fmt_number(row.get("repurposing_evidence_score") if row is not None else None, 1, "/100"))
    cols[4].metric("LCA proxy saving", fmt_number(row.get("lca_proxy_saving_percent") if row is not None else None, 1, "%"))
    if ranked_row is not None:
        st.caption(
            f"Data priority score: {fmt_number(ranked_row.get('data_priority_score'), 1, '/100')}."
            " This score only orders records for first-pass review."
        )


def render_layer_button(label: str, selection: dict[str, str]) -> None:
    result_key = f"last_result_{safe_filename(label)}"
    if st.button(label, key=safe_filename(label + selection["pipeline_id"])):
        ok, output = run_screening(selection)
        st.session_state[result_key] = (label, ok, output)
        st.cache_data.clear()
        st.rerun()
    show_run_result(result_key)


def render_data_layer(row: pd.Series | None, ranked_row: pd.Series | None, selection: dict[str, str]) -> None:
    with st.container(border=True):
        st.markdown('<div class="workflow-step"><h3>1. Data Completeness Gate</h3></div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-note">Purpose: confirm that the minimum data needed for screening are available or clearly labelled as assumptions.</div>',
            unsafe_allow_html=True,
        )
        info = profile_rows(row, ranked_row, selection)
        data_table(info)
        render_missing_warning(info)
        render_layer_button("Run / refresh data gate", selection)


def render_capacity_layer(row: pd.Series | None, selection: dict[str, str]) -> None:
    with st.container(border=True):
        st.markdown('<div class="workflow-step"><h3>2. CO2 Transport Capacity</h3></div>', unsafe_allow_html=True)
        inputs = [
            input_row("Pipeline length", row.get("length_km") if row is not None else None, "km", zero_invalid=True),
            input_row("Internal diameter", row.get("inner_diameter_in") if row is not None else None, "in", zero_invalid=True),
            input_row("Average pressure", row.get("average_pressure_mpa") if row is not None else None, "MPa", zero_invalid=True),
            input_row("CO2 compressibility factor", "see screening defaults", "-", source="assumption file"),
            input_row("Fanning friction factor", row.get("fanning_friction_factor") if row is not None else None, "-", zero_invalid=True),
            input_row("Required project flow", row.get("required_design_mtpa") if row is not None else None, "Mtpa", zero_invalid=True),
        ]
        left, right = st.columns([1.1, 1])
        with left:
            data_table(inputs)
            render_missing_warning(inputs)
        with right:
            equation_box(
                [
                    "P_average = (2/3) * (P_in + P_out - (P_in * P_out) / (P_in + P_out))",
                    "required_design_flow = project_flow / capacity_factor",
                    "capacity_suitable = estimated_capacity >= required_design_flow",
                ]
            )
            status_pill("Capacity suitable", row.get("capacity_suitable") if row is not None else "not run")
            st.metric("Estimated capacity", fmt_number(row.get("capacity_mtpa") if row is not None else None, 2, " MtCO2/year"))
        render_layer_button("Run / refresh capacity layer", selection)


def render_corrosion_layer(row: pd.Series | None, selection: dict[str, str]) -> None:
    with st.container(border=True):
        st.markdown('<div class="workflow-step"><h3>3. Corrosion Screening</h3></div>', unsafe_allow_html=True)
        inputs = [
            input_row("Water content", "see scenario/defaults", "ppmv", source="assumption file"),
            input_row("Water specification limit", "see scenario/defaults", "ppmv", source="assumption file"),
            input_row("Dew-point margin", "see scenario/defaults", "degC", source="assumption file"),
            input_row("Future CO2 corrosion rate", row.get("future_co2_corrosion_rate_mm_per_year") if row is not None else None, "mm/year"),
            input_row("Low corrosion case", row.get("corrosion_rate_low_mm_per_year") if row is not None else None, "mm/year"),
            input_row("High corrosion case", row.get("corrosion_rate_high_mm_per_year") if row is not None else None, "mm/year"),
        ]
        left, right = st.columns([1.1, 1])
        with left:
            data_table(inputs)
        with right:
            equation_box(
                [
                    "if water_content > water_limit: corrosion_risk = high",
                    "if dew_point_margin < 0: corrosion_risk = high",
                    "if water/dew-point evidence is missing: corrosion_risk at least medium",
                ]
            )
            status_pill("Corrosion risk", row.get("corrosion_risk_level") if row is not None else "not run")
        render_layer_button("Run / refresh corrosion layer", selection)


def render_integrity_layer(row: pd.Series | None, selection: dict[str, str]) -> None:
    with st.container(border=True):
        st.markdown('<div class="workflow-step"><h3>4. Wall Thickness And Remaining Life</h3></div>', unsafe_allow_html=True)
        inputs = [
            input_row("Nominal wall thickness", row.get("nominal_wall_thickness_mm") if row is not None else None, "mm", zero_invalid=True),
            input_row("Historical wall loss", row.get("historical_wall_loss_mm") if row is not None else None, "mm"),
            input_row("Current wall thickness", row.get("current_wall_thickness_mm") if row is not None else None, "mm"),
            input_row("Minimum wall thickness", row.get("minimum_wall_thickness_mm") if row is not None else None, "mm", zero_invalid=True),
            input_row("Future CO2 corrosion rate", row.get("future_co2_corrosion_rate_mm_per_year") if row is not None else None, "mm/year"),
        ]
        left, right = st.columns([1.1, 1])
        with left:
            data_table(inputs)
            render_missing_warning(inputs)
        with right:
            equation_box(
                [
                    "current_wall = nominal_wall - historical_wall_loss",
                    "available_wall = current_wall - minimum_wall",
                    "remaining_life = available_wall / future_CO2_corrosion_rate",
                ]
            )
            st.metric("Available wall", fmt_number(row.get("available_wall_thickness_mm") if row is not None else None, 2, " mm"))
            st.metric("Remaining life", fmt_number(row.get("remaining_life_years") if row is not None else None, 1, " years"))
        render_layer_button("Run / refresh integrity layer", selection)


def render_gate_layer(row: pd.Series | None, selection: dict[str, str]) -> None:
    with st.container(border=True):
        st.markdown('<div class="workflow-step"><h3>5. Repurposing Evidence Gate</h3></div>', unsafe_allow_html=True)
        left, right = st.columns([1, 1])
        with left:
            status_pill("Gate status", row.get("repurposing_gate_status") if row is not None else "not run")
            status_pill("CO2 phase screen", row.get("repurposing_phase_status") if row is not None else "not run")
            st.metric("Evidence score", fmt_number(row.get("repurposing_evidence_score") if row is not None else None, 1, "/100"))
            equation_box(
                [
                    "gate_status = function(capacity, integrity, CO2 phase evidence, inspection evidence, material evidence)",
                    "missing evidence is reported as an output, not hidden in a final score",
                ]
            )
        with right:
            st.markdown("**Evidence gaps**")
            gaps = split_items(row.get("repurposing_evidence_gaps") if row is not None else None)
            st.write("\n".join(f"- {item}" for item in gaps) if gaps else "No evidence gaps listed.")
            st.markdown("**Next data to add**")
            next_data = split_items(row.get("pre_lca_next_data") if row is not None else None)
            st.write("\n".join(f"- {item}" for item in next_data) if next_data else "No next-data list available.")
        render_layer_button("Run / refresh repurposing gate", selection)


def render_work_scope_layer(row: pd.Series | None, selection: dict[str, str]) -> None:
    scenario = selection["screening_scenario"]
    path = SCREENING_DIR / f"refurbishment_work_scope_{scenario}.csv"
    selected = load_csv(str(path))
    with st.container(border=True):
        st.markdown('<div class="workflow-step"><h3>6. Quantified Work Scope</h3></div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-note">Purpose: convert gate findings into quantities that cost and LCA can use.</div>',
            unsafe_allow_html=True,
        )
        cols = st.columns(4)
        cols[0].metric("Work items", fmt_number(row.get("refurbishment_work_scope_item_count") if row is not None else None, 0))
        cols[1].metric("Cost items", fmt_number(row.get("refurbishment_cost_item_count") if row is not None else None, 0))
        cols[2].metric("LCA items", fmt_number(row.get("refurbishment_lca_item_count") if row is not None else None, 0))
        cols[3].metric("Replacement steel", fmt_number(row.get("refurbishment_replacement_steel_kg") if row is not None else None, 0, " kg"))
        equation_box(
            [
                "work_item_quantity = rule(work_item_type, pipeline_length, steel_mass, evidence_gap)",
                "replacement_steel = new_build_steel_mass * recommended_refurbishment_fraction",
            ]
        )
        if not selected.empty:
            visible = [
                "work_item_name",
                "work_stage",
                "quantity_base",
                "unit",
                "cost_driver",
                "lca_mapping_key",
                "data_quality",
            ]
            available = [column for column in visible if column in selected.columns]
            st.dataframe(selected[available], hide_index=True, width="stretch")
        else:
            st.info("No work-scope table has been created yet for this selection.")


def render_cost_layer(selection: dict[str, str], factor_mode: str) -> None:
    cost_row = load_cost_row(selection["cost_case"])
    with st.container(border=True):
        st.markdown('<div class="workflow-step"><h3>7. Refurbishment Cost</h3></div>', unsafe_allow_html=True)
        left, right = st.columns([1.1, 1])
        with left:
            equation_box(
                [
                    "item_cost_low/base/high = quantity_low/base/high * unit_cost_low/base/high",
                    "total_refurbishment_cost = sum(item_costs)",
                    "screening factors are not contractor quotes",
                ]
            )
            if st.button("Run cost layer", key=f"run_cost_{selection['pipeline_id']}"):
                ok, output = run_cost(selection, factor_mode)
                st.session_state["last_cost_result"] = ("Cost layer", ok, output)
                st.cache_data.clear()
                st.rerun()
            show_run_result("last_cost_result")
        with right:
            status_pill("Cost status", cost_row.get("refurbishment_cost_status") if cost_row is not None else "not run")
            st.metric("Base cost", fmt_money(cost_row.get("cost_base_usd_2025") if cost_row is not None else None))
            st.metric("Low case", fmt_money(cost_row.get("cost_low_usd_2025") if cost_row is not None else None))
            st.metric("High case", fmt_money(cost_row.get("cost_high_usd_2025") if cost_row is not None else None))
            if cost_row is not None:
                st.caption(f"Factor quality: {clean_text(cost_row.get('factor_quality_summary'))}")


def render_lca_layer(row: pd.Series | None, selection: dict[str, str], factor_mode: str) -> None:
    lca_row = load_lca_row(selection["lca_scenario"])
    with st.container(border=True):
        st.markdown('<div class="workflow-step"><h3>8. Conventional LCA Screening</h3></div>', unsafe_allow_html=True)
        left, right = st.columns([1.1, 1])
        with left:
            equation_box(
                [
                    "functional_unit = transport 1 tonne CO2 through selected route",
                    "new_build_impact = steel_impact + construction_impact",
                    "reuse_impact = refurbishment_steel_impact + refurbishment_activity_impact",
                    "saving = new_build_impact - reuse_impact",
                ]
            )
            if st.button("Run LCA layer", key=f"run_lca_{selection['pipeline_id']}"):
                ok, output = run_lca(selection, factor_mode)
                st.session_state["last_lca_result"] = ("LCA layer", ok, output)
                st.cache_data.clear()
                st.rerun()
            show_run_result("last_lca_result")
        with right:
            status_pill("Screening LCA", row.get("lca_screening_decision") if row is not None else "not run")
            status_pill("ecoinvent-linked LCA", lca_row.get("lca_status") if lca_row is not None else "not run")
            st.metric("Proxy saving", fmt_number(row.get("lca_proxy_saving_percent") if row is not None else None, 1, "%"))
            st.metric("Avoided steel", fmt_number(row.get("lca_avoided_steel_kg") if row is not None else None, 0, " kg"))
            if lca_row is not None:
                st.metric("Base reuse impact", fmt_number(as_float(lca_row.get("reuse_kgco2e_base")) / 1000 if as_float(lca_row.get("reuse_kgco2e_base")) is not None else None, 1, " tCO2e"))
                st.caption(f"Factor quality: {clean_text(lca_row.get('factor_quality_summary'))}")


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

    # Simple selector and controls
    controls = st.columns([1.1, 1.8, 0.8, 0.8], gap="medium")
    with controls[0]:
        selection = render_selector(candidate_df)
    with controls[1]:
        st.markdown(
            """
            <div class="section-note">
            Select a pipeline from the map or dropdown below.
            The map shows all NSTA pipelines — click to select, or use the fallback selector.
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── Commented out: Model layers & formulations (commented per user request)
    # with controls[2]:
    #     factor_mode = st.radio("Cost/LCA factors", ["screening", "private"], horizontal=True)
    # with controls[3]:
    #     st.write("")
    #     st.write("")
    #     if st.button("Run all layers", type="primary", width="stretch"):
    #         st.session_state["last_all_results"] = run_all(selection, factor_mode)
    #         st.rerun()

    # if "last_all_results" in st.session_state:
    #     with st.expander("Last full run"):
    #         for label, ok, output in st.session_state["last_all_results"]:
    #             st.write(f"**{label}:** {'completed' if ok else 'failed'}")
    #             st.code(output or "No output", language="text")

    if selection["kind"] == "nsta":
        ranked_row = selected_ranked_row(candidate_df, selection["pipeline_id"])
        row = selected_screening_row(screening_df, selection["pipeline_id"])
    else:
        ranked_row = None
        row = load_scenario_row(selection["screening_scenario"])

    render_top_area(all_routes_payload, row, ranked_row, selection, candidate_pipeline_ids)
    render_key_metrics(row, ranked_row)
    
    # ── Commented out: Display workflow with formulations (per user request)
    # render_workflow(row, ranked_row, selection, factor_mode)



if __name__ == "__main__":
    main()
