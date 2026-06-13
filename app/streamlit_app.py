"""Streamlit dashboard for pipeline repurposing screening."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
SCREENING_DIR = ROOT / "model_layers" / "06_screening_and_decision"
DATA_DIR = ROOT / "model_layers" / "01_data_foundation"
COST_DIR = ROOT / "model_layers" / "04_cost_economics"
LCA_DIR = ROOT / "model_layers" / "05_lca"
ASSET_DIR = ROOT / "app" / "assets"


st.set_page_config(
    page_title="Pipeline Repurposing Screening",
    layout="wide",
    initial_sidebar_state="expanded",
)


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


def clean_text(value: Any, fallback: str = "Not available") -> str:
    if value is None:
        return fallback
    if isinstance(value, float) and pd.isna(value):
        return fallback
    text = str(value).strip()
    return text if text else fallback


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


def status_colour(status: Any) -> tuple[str, str]:
    text = clean_text(status, "unknown").lower()
    if text in {"pass", "ready", "ready_for_screening", "yes", "active"}:
        return "#176d52", "#e5f3ee"
    if text in {"marginal", "needs_data", "insufficient_data", "not_supplied", "unknown"}:
        return "#8a5a00", "#fff2d8"
    if "blocked" in text:
        return "#8a5a00", "#fff2d8"
    if text in {"fail", "no"}:
        return "#9c2f2f", "#f7e4e4"
    return "#334155", "#e8edf2"


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
        <style>
        .stApp {
            background: #f6f8f9;
            color: #1f2933;
        }
        h1, h2, h3 {
            letter-spacing: 0;
        }
        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #d8e0e7;
            border-radius: 8px;
            padding: 0.85rem 0.9rem;
        }
        div[data-testid="stMetric"] label {
            color: #52606d;
        }
        .status-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.75rem;
            padding: 0.65rem 0;
            border-bottom: 1px solid #e2e8ee;
        }
        .status-row strong {
            display: inline-block;
            border-radius: 999px;
            padding: 0.25rem 0.65rem;
            font-size: 0.82rem;
            line-height: 1.2;
            white-space: nowrap;
        }
        .note-box {
            background: #ffffff;
            border: 1px solid #d8e0e7;
            border-radius: 8px;
            padding: 0.85rem;
        }
        .small-muted {
            color: #61717f;
            font-size: 0.88rem;
        }
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
            f"{int(row['rank']) if pd.notna(row['rank']) else '-'} | "
            f"{row['pipeline_id']} | {clean_text(row.get('PIPE_NAME'), row['pipeline_id'])}"
        ),
        axis=1,
    )
    return candidates


def route_bounds(routes: list[dict[str, Any]]) -> dict[str, float] | None:
    if not routes:
        return None
    return {
        "min_lon": min(route["bounds"]["min_lon"] for route in routes),
        "max_lon": max(route["bounds"]["max_lon"] for route in routes),
        "min_lat": min(route["bounds"]["min_lat"] for route in routes),
        "max_lat": max(route["bounds"]["max_lat"] for route in routes),
    }


def route_zoom(bounds: dict[str, float] | None) -> float:
    if bounds is None:
        return 4.6
    span = max(bounds["max_lon"] - bounds["min_lon"], bounds["max_lat"] - bounds["min_lat"])
    if span < 0.3:
        return 7.2
    if span < 0.8:
        return 6.4
    if span < 1.8:
        return 5.5
    if span < 3.5:
        return 4.9
    return 4.2


def render_route_map(route_payload: dict[str, Any], selected_pipeline_id: str) -> None:
    try:
        import pydeck as pdk
    except ImportError:
        st.info("Install the dashboard requirements to show the route map.")
        st.code("python -m pip install -r requirements.txt", language="powershell")
        return

    routes = route_payload.get("routes", [])
    selected_routes = [route for route in routes if route.get("pipeline_id") == selected_pipeline_id]
    dim_routes = [
        {
            **route,
            "color": [57, 92, 115, 55],
            "width": 2,
        }
        for route in routes
        if route.get("pipeline_id") != selected_pipeline_id
    ]
    highlighted_routes = [
        {
            **route,
            "color": [223, 82, 38, 230],
            "width": 8,
        }
        for route in selected_routes
    ]
    selected_points = []
    for route in selected_routes:
        selected_points.append({"position": route["start"], "label": "start"})
        selected_points.append({"position": route["end"], "label": "end"})

    bounds = route_bounds(selected_routes) or route_bounds(routes)
    center_lon = -1.5
    center_lat = 56.5
    if bounds is not None:
        center_lon = (bounds["min_lon"] + bounds["max_lon"]) / 2
        center_lat = (bounds["min_lat"] + bounds["max_lat"]) / 2

    layers = [
        pdk.Layer(
            "PathLayer",
            data=dim_routes,
            get_path="path",
            get_color="color",
            get_width="width",
            width_min_pixels=1,
            rounded=True,
            pickable=True,
        ),
        pdk.Layer(
            "PathLayer",
            data=highlighted_routes,
            get_path="path",
            get_color="color",
            get_width="width",
            width_min_pixels=3,
            rounded=True,
            pickable=True,
        ),
        pdk.Layer(
            "ScatterplotLayer",
            data=selected_points,
            get_position="position",
            get_radius=5000,
            get_fill_color=[24, 112, 86, 220],
            pickable=True,
        ),
    ]

    deck = pdk.Deck(
        layers=layers,
        initial_view_state=pdk.ViewState(
            latitude=center_lat,
            longitude=center_lon,
            zoom=route_zoom(bounds),
            pitch=0,
        ),
        tooltip={"text": "{pipeline_id}\n{pipeline_name}"},
        map_style=None,
    )
    st.pydeck_chart(deck, width="stretch", height=520)


def selected_screening_row(screening_df: pd.DataFrame, pipeline_id: str) -> pd.Series | None:
    if screening_df.empty:
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


def render_metric_row(row: pd.Series | None, ranked_row: pd.Series | None) -> None:
    pipeline_id = ranked_row.get("pipeline_id") if ranked_row is not None else None
    rank = ranked_row.get("rank") if ranked_row is not None else None
    length = row.get("length_km") if row is not None else None
    if length is None and ranked_row is not None:
        length = ranked_row.get("LENGTH_KM")

    columns = st.columns(6)
    columns[0].metric("NSTA number", clean_text(pipeline_id))
    columns[1].metric("Rank", clean_text(rank))
    columns[2].metric("Capacity", fmt_number(row.get("capacity_mtpa") if row is not None else None, 1, " Mtpa"))
    columns[3].metric("Remaining life", fmt_number(row.get("remaining_life_years") if row is not None else None, 1, " yr"))
    columns[4].metric("Length", fmt_number(length, 1, " km"))
    columns[5].metric("LCA proxy saving", fmt_number(row.get("lca_proxy_saving_percent") if row is not None else None, 1, "%"))


def render_overview(
    route_payload: dict[str, Any],
    row: pd.Series | None,
    ranked_row: pd.Series | None,
    selected_pipeline_id: str,
) -> None:
    left, right = st.columns([2.1, 1])
    with left:
        render_route_map(route_payload, selected_pipeline_id)
    with right:
        st.subheader(clean_text(ranked_row.get("PIPE_NAME") if ranked_row is not None else None, selected_pipeline_id))
        status_pill("Pre-LCA decision", row.get("pre_lca_decision") if row is not None else "not available")
        status_pill("Repurposing gate", row.get("repurposing_gate_status") if row is not None else "not available")
        status_pill("Capacity suitable", row.get("capacity_suitable") if row is not None else "not available")
        status_pill("Corrosion risk", row.get("corrosion_risk_level") if row is not None else "not available")
        status_pill("NSTA status", ranked_row.get("STATUS") if ranked_row is not None else "not available")
        st.markdown('<div class="small-muted">This is a screening result, not engineering approval.</div>', unsafe_allow_html=True)

    render_metric_row(row, ranked_row)


def render_technical(row: pd.Series | None, ranked_row: pd.Series | None) -> None:
    if row is None:
        st.warning("No screening result was found for this pipeline.")
        return

    left, right = st.columns(2)
    with left:
        st.subheader("Pipeline Data")
        data = {
            "Pipeline name": clean_text(row.get("pipeline_name")),
            "NSTA number": clean_text(row.get("nsta_pipeline_number")),
            "Fluid": clean_text(ranked_row.get("FLUID") if ranked_row is not None else row.get("nsta_fluid")),
            "Status": clean_text(ranked_row.get("STATUS") if ranked_row is not None else row.get("nsta_status")),
            "Start date": clean_text(ranked_row.get("START_DATE") if ranked_row is not None else None),
            "Internal diameter": fmt_number(row.get("inner_diameter_in"), 1, " in"),
            "Wall thickness": fmt_number(row.get("nominal_wall_thickness_mm"), 1, " mm"),
            "Maximum operating pressure": fmt_number(ranked_row.get("MX_OP_PRES") if ranked_row is not None else None, 1, " bar"),
        }
        st.dataframe(pd.DataFrame(data.items(), columns=["Field", "Value"]), hide_index=True, width="stretch")

    with right:
        st.subheader("Main Screening Numbers")
        metrics = {
            "Required design flow": fmt_number(row.get("required_design_mtpa"), 2, " Mtpa"),
            "Estimated CO2 capacity": fmt_number(row.get("capacity_mtpa"), 2, " Mtpa"),
            "Current wall thickness": fmt_number(row.get("current_wall_thickness_mm"), 2, " mm"),
            "Minimum wall thickness": fmt_number(row.get("minimum_wall_thickness_mm"), 2, " mm"),
            "Available wall": fmt_number(row.get("available_wall_thickness_mm"), 2, " mm"),
            "Remaining life base case": fmt_number(row.get("remaining_life_years"), 2, " yr"),
            "Remaining life high case": fmt_number(row.get("remaining_life_high_years"), 2, " yr"),
            "Evidence score": fmt_number(row.get("repurposing_evidence_score"), 1, "/100"),
        }
        st.dataframe(pd.DataFrame(metrics.items(), columns=["Check", "Value"]), hide_index=True, width="stretch")

    st.subheader("Decision Notes")
    notes_left, notes_right = st.columns(2)
    with notes_left:
        st.markdown("**Showstoppers**")
        items = split_items(row.get("repurposing_showstoppers"))
        if items:
            for item in items:
                st.write(f"- {item}")
        else:
            st.write("No showstoppers listed.")
    with notes_right:
        st.markdown("**Next Data To Check**")
        items = split_items(row.get("pre_lca_next_data") or row.get("repurposing_gate_next_data"))
        if items:
            for item in items:
                st.write(f"- {item}")
        else:
            st.write("No next-data list available.")


def render_work_scope(work_scope_df: pd.DataFrame, scenario: str) -> None:
    if work_scope_df.empty:
        st.warning("No work-scope CSV was found.")
        return
    selected = work_scope_df[work_scope_df["scenario"].astype(str) == scenario].copy()
    if selected.empty:
        st.info("No work-scope rows were found for this selected pipeline.")
        return
    duplicate_item_count = selected["work_item_id"].duplicated().sum()
    if duplicate_item_count:
        selected = selected.drop_duplicates(subset=["work_item_id"], keep="first")
        st.info("This NSTA number has more than one source record. The dashboard shows the first ranked/main record.")

    count_cols = st.columns(4)
    replacement_steel = pd.to_numeric(
        selected.loc[selected["work_item_id"] == "replacement_steel_allowance", "quantity_base"],
        errors="coerce",
    ).sum()
    count_cols[0].metric("Work items", f"{len(selected):,}")
    count_cols[1].metric("Cost items", f"{(selected['cost_include'].astype(str).str.lower() == 'yes').sum():,}")
    count_cols[2].metric("LCA items", f"{(selected['lca_include'].astype(str).str.lower() != 'no').sum():,}")
    count_cols[3].metric("Replacement steel", fmt_number(replacement_steel, 0, " kg"))

    stage_counts = selected.groupby("work_stage").size().reset_index(name="item_count")
    if not stage_counts.empty:
        st.bar_chart(stage_counts.set_index("work_stage"))

    visible_columns = [
        "work_item_name",
        "work_stage",
        "quantity_base",
        "unit",
        "cost_driver",
        "lca_mapping_key",
        "data_quality",
        "basis",
    ]
    available = [column for column in visible_columns if column in selected.columns]
    st.dataframe(selected[available], hide_index=True, width="stretch")


def render_cost_lca(row: pd.Series | None, cost_df: pd.DataFrame, scenario: str) -> None:
    left, right = st.columns(2)
    with left:
        st.subheader("Refurbishment Cost")
        cost_row = None
        if not cost_df.empty:
            match = cost_df[cost_df["scenario"].astype(str) == scenario]
            if not match.empty:
                cost_row = match.iloc[0]
        status_pill("Cost status", cost_row.get("refurbishment_cost_status") if cost_row is not None else "not run")
        if cost_row is not None and "blocked" not in clean_text(cost_row.get("refurbishment_cost_status"), "").lower():
            st.metric("Base refurbishment cost", fmt_money(cost_row.get("cost_base_usd_2025")))
        if cost_row is not None:
            st.write("Missing cost drivers")
            missing = split_items(cost_row.get("missing_cost_drivers"))
            if missing:
                for item in missing:
                    st.write(f"- {item}")
            else:
                st.write("No missing cost drivers listed.")
        st.markdown(
            '<div class="small-muted">The dashboard does not display private unit-cost factors.</div>',
            unsafe_allow_html=True,
        )

    with right:
        st.subheader("LCA")
        if row is not None:
            status_pill("Screening LCA", row.get("lca_screening_decision"))
            st.metric("Proxy saving", fmt_number(row.get("lca_proxy_saving_percent"), 1, "%"))
            st.metric("Avoided steel", fmt_number(row.get("lca_avoided_steel_kg"), 0, " kg"))
        lca_path = LCA_DIR / f"lca_results_{scenario}.csv"
        lca_result = load_csv(str(lca_path))
        if not lca_result.empty:
            lca_row = lca_result.iloc[0]
            status_pill("ecoinvent-linked LCA", lca_row.get("lca_status"))
            missing = split_items(lca_row.get("missing_mapping_keys"))
            if missing:
                st.write("Missing LCA factors")
                for item in missing:
                    st.write(f"- {item}")
        else:
            status_pill("ecoinvent-linked LCA", "not run for selected pipeline")
        st.markdown(
            '<div class="small-muted">The dashboard does not display private ecoinvent impact factors.</div>',
            unsafe_allow_html=True,
        )


def render_traceability(row: pd.Series | None, selected_pipeline_id: str, scenario: str) -> None:
    if row is None:
        st.warning("No traceability data was found for this pipeline.")
        return

    left, right = st.columns(2)
    with left:
        st.subheader("Source And Output Files")
        paths = {
            "Ranked candidate table": DATA_DIR / "nsta_candidate_ranked.csv",
            "Batch screening table": SCREENING_DIR / "pipeline_screen_nsta_all.csv",
            "Selected screening report": SCREENING_DIR / f"pipeline_screen_{scenario}.md",
            "Selected trace file": SCREENING_DIR / f"pipeline_screen_{scenario}_trace.json",
            "Selected work scope": SCREENING_DIR / f"refurbishment_work_scope_{scenario}.csv",
        }
        for label, path in paths.items():
            exists = "available" if path.exists() else "not created yet"
            st.write(f"**{label}:** {exists}")
            st.code(str(path), language="text")
        st.write("Run command")
        st.code(f"python scripts\\run_pipeline_screen.py --nsta-id {selected_pipeline_id}", language="powershell")

    with right:
        st.subheader("References Cited By Gate")
        refs = split_items(row.get("repurposing_gate_cited_references"))
        if refs:
            for ref in refs:
                st.write(f"- {ref}")
        else:
            st.write("No references listed for this row.")

        st.subheader("Evidence Gaps")
        gaps = split_items(row.get("repurposing_evidence_gaps"))
        if gaps:
            for gap in gaps:
                st.write(f"- {gap}")
        else:
            st.write("No evidence gaps listed.")


def main() -> None:
    apply_style()

    ranked_df = load_csv(str(DATA_DIR / "nsta_candidate_ranked.csv"))
    screening_df = load_csv(str(SCREENING_DIR / "pipeline_screen_nsta_all.csv"))
    work_scope_df = load_csv(str(SCREENING_DIR / "refurbishment_work_scope_nsta_all.csv"))
    cost_df = load_csv(str(COST_DIR / "refurbishment_cost_summary_nsta_all.csv"))
    route_payload = load_routes(str(ASSET_DIR / "nsta_candidate_routes.json"))

    candidate_df = build_candidate_table(ranked_df, screening_df)
    if candidate_df.empty:
        st.error("No ranked candidate table was found.")
        return

    st.title("Pipeline Repurposing Screening")
    st.caption(
        "NSTA candidate ranking, CO2 screening, repurposing gate, work scope, cost status and LCA status. "
        f"Dashboard selector: {len(candidate_df):,} unique NSTA numbers from {len(ranked_df):,} ranked records."
    )

    with st.sidebar:
        st.header("Pipeline")
        default_index = 0
        if "PL774" in set(candidate_df["pipeline_id"]):
            default_index = candidate_df.index[candidate_df["pipeline_id"] == "PL774"][0]
            default_index = int(candidate_df.index.get_loc(default_index))
        selected_label = st.selectbox(
            "Select NSTA pipeline",
            candidate_df["display"].tolist(),
            index=default_index,
        )
        selected_pipeline_id = selected_label.split("|")[1].strip().upper()
        ranked_row = selected_ranked_row(candidate_df, selected_pipeline_id)
        scenario = f"nsta_{selected_pipeline_id.lower()}"

        decision_filter = st.multiselect(
            "Decision filter",
            sorted([clean_text(value) for value in candidate_df.get("pre_lca_decision", pd.Series()).dropna().unique()]),
            default=[],
        )
        if decision_filter:
            filtered = candidate_df[candidate_df["pre_lca_decision"].isin(decision_filter)]
        else:
            filtered = candidate_df
        st.dataframe(
            filtered[["rank", "pipeline_id", "PIPE_NAME", "FLUID", "STATUS", "LENGTH_KM", "pre_lca_decision"]].head(30),
            hide_index=True,
            width="stretch",
        )

    row = selected_screening_row(screening_df, selected_pipeline_id)

    render_overview(route_payload, row, ranked_row, selected_pipeline_id)

    tabs = st.tabs(["Technical", "Work Scope", "Cost And LCA", "Traceability"])
    with tabs[0]:
        render_technical(row, ranked_row)
    with tabs[1]:
        render_work_scope(work_scope_df, scenario)
    with tabs[2]:
        render_cost_lca(row, cost_df, scenario)
    with tabs[3]:
        render_traceability(row, selected_pipeline_id, scenario)


if __name__ == "__main__":
    main()
