# -*- coding: utf-8 -*-
"""
Data Input Page
===============
Allows users to upload their own pipeline database (CSV, Excel, JSON, SQLite)
and map it to the tool's standard template fields.

Workflow:
  1. Upload raw file or pre-filled template
  2. Auto-extract and match columns via string similarity
  3. Review and correct column mapping
  4. Fill gaps manually
  5. Save as standard template and use on Dashboard
"""

from __future__ import annotations

import io
import json
import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# Standard template field definitions
# ---------------------------------------------------------------------------

STANDARD_FIELDS: list[dict[str, Any]] = [
    # Identification
    {"field": "pipeline_id",          "label": "Pipeline ID",              "type": "text",   "required": True,  "group": "Identification",        "description": "Unique identifier for the pipeline (e.g. PL774, CATS-001)"},
    {"field": "pipeline_name",        "label": "Pipeline name",            "type": "text",   "required": True,  "group": "Identification",        "description": "Full descriptive name of the pipeline"},
    {"field": "fluid",                "label": "Fluid type",               "type": "text",   "required": True,  "group": "Identification",        "description": "Current transported fluid: GAS, OIL, WATER, MIXED"},
    {"field": "status",               "label": "Operational status",       "type": "text",   "required": True,  "group": "Identification",        "description": "Pipeline status: ACTIVE, INACTIVE, DECOMMISSIONED"},
    # Geometry
    {"field": "pipeline_length_km",   "label": "Length (km)",              "type": "number", "required": True,  "group": "Geometry",              "description": "Total pipeline length in kilometres"},
    {"field": "inner_diameter_in",    "label": "Inner diameter (in)",      "type": "number", "required": True,  "group": "Geometry",              "description": "Internal diameter in inches"},
    {"field": "outer_diameter_in",    "label": "Outer diameter (in)",      "type": "number", "required": False, "group": "Geometry",              "description": "Outer diameter in inches (derived from inner diameter + 2 x wall if not provided)"},
    {"field": "nominal_wall_thickness_mm", "label": "Wall thickness (mm)", "type": "number", "required": True,  "group": "Geometry",              "description": "Nominal wall thickness in millimetres"},
    # Operating conditions
    {"field": "inlet_pressure_psia",  "label": "Inlet pressure (psia)",    "type": "number", "required": True,  "group": "Operating Conditions",  "description": "Design or operating inlet pressure in psia"},
    {"field": "outlet_pressure_psia", "label": "Outlet pressure (psia)",   "type": "number", "required": True,  "group": "Operating Conditions",  "description": "Design or operating outlet pressure in psia"},
    {"field": "start_operation_year", "label": "Year of first operation",  "type": "number", "required": False, "group": "Operating Conditions",  "description": "Year the pipeline first entered service (for remaining life calculation)"},
    # Material
    {"field": "pipe_grade",           "label": "Pipe material grade",      "type": "text",   "required": True,  "group": "Material",              "description": "Steel grade: X42, X46, X52, X56, X60, X65, X70, X80"},
    {"field": "ili_mfl_available",    "label": "In-line inspection record","type": "text",   "required": False, "group": "Material",              "description": "Whether an in-line inspection (magnetic flux leakage) record exists: yes / no / unknown"},
    {"field": "material_certificates_available", "label": "Material certificates", "type": "text", "required": False, "group": "Material", "description": "Whether original material test certificates are available: yes / no / unknown"},
    {"field": "fracture_toughness_basis", "label": "Fracture toughness evidence", "type": "text", "required": False, "group": "Material", "description": "Basis for fracture toughness assessment: known / unknown"},
    # CO2 suitability
    {"field": "co2_water_content_ppmv",  "label": "CO2 water content (ppmv)", "type": "number", "required": False, "group": "CO2 Suitability", "description": "Water content of the CO2 stream in parts per million by volume"},
    {"field": "co2_composition_known",   "label": "CO2 gas composition known","type": "text",   "required": False, "group": "CO2 Suitability", "description": "Whether the full CO2 stream composition is known: yes / no"},
    {"field": "component_compatibility_screened", "label": "Component compatibility checked", "type": "text", "required": False, "group": "CO2 Suitability", "description": "Whether valves, seals and instruments have been checked for CO2 service: yes / no"},
    # Location (for map)
    {"field": "latitude_start",       "label": "Start latitude",           "type": "number", "required": False, "group": "Location",              "description": "Latitude of pipeline start point (decimal degrees, WGS84)"},
    {"field": "longitude_start",      "label": "Start longitude",          "type": "number", "required": False, "group": "Location",              "description": "Longitude of pipeline start point (decimal degrees, WGS84)"},
    {"field": "latitude_end",         "label": "End latitude",             "type": "number", "required": False, "group": "Location",              "description": "Latitude of pipeline end point (decimal degrees, WGS84)"},
    {"field": "longitude_end",        "label": "End longitude",            "type": "number", "required": False, "group": "Location",              "description": "Longitude of pipeline end point (decimal degrees, WGS84)"},
]

REQUIRED_FIELDS = [f["field"] for f in STANDARD_FIELDS if f["required"]]
ALL_FIELDS      = [f["field"] for f in STANDARD_FIELDS]

# Known aliases for auto-matching
FIELD_ALIASES: dict[str, list[str]] = {
    "pipeline_id":               ["id", "pipe_id", "nstapipno", "pipeline_number", "pipeno", "asset_id"],
    "pipeline_name":             ["name", "pipe_name", "description", "pipeline", "asset_name", "pipe_name"],
    "fluid":                     ["fluid_type", "product", "medium", "contents", "substance"],
    "status":                    ["operational_status", "condition", "state", "pipe_status"],
    "pipeline_length_km":        ["length_km", "length", "length_kilometers", "pipe_length", "dist_km", "distance_km"],
    "inner_diameter_in":         ["id", "int_diam", "inner_diam", "internal_diameter", "bore", "id_in", "int_diameter"],
    "outer_diameter_in":         ["od", "od_in", "outer_diam", "ext_diam", "external_diameter", "outside_diameter"],
    "nominal_wall_thickness_mm": ["wall", "thickness", "wall_mm", "wt_mm", "wall_thickness", "nominal_wall"],
    "inlet_pressure_psia":       ["pressure_in", "upstream_pressure", "inlet_p", "p_inlet", "max_pressure", "mx_op_pres"],
    "outlet_pressure_psia":      ["pressure_out", "downstream_pressure", "outlet_p", "p_outlet"],
    "start_operation_year":      ["year", "commission_year", "start_year", "commissioned", "start_date", "install_year"],
    "pipe_grade":                ["grade", "steel_grade", "material_grade", "spec", "api_grade"],
    "ili_mfl_available":         ["ili", "mfl", "inspection", "inline_inspection", "pig_run"],
    "material_certificates_available": ["certs", "certificates", "mtc", "material_certs", "traceability"],
    "fracture_toughness_basis":  ["fracture", "toughness", "cvn", "charpy", "fracture_basis"],
    "co2_water_content_ppmv":    ["water_content", "h2o_ppm", "water_ppm", "moisture_ppm"],
    "co2_composition_known":     ["composition", "co2_spec", "gas_composition"],
    "component_compatibility_screened": ["compatibility", "component_check", "valve_check"],
    "latitude_start":            ["lat_start", "start_lat", "lat1", "y_start"],
    "longitude_start":           ["lon_start", "start_lon", "long_start", "lng_start", "x_start"],
    "latitude_end":              ["lat_end", "end_lat", "lat2", "y_end"],
    "longitude_end":             ["lon_end", "end_lon", "long_end", "lng_end", "x_end"],
}


# ---------------------------------------------------------------------------
# File loading
# ---------------------------------------------------------------------------

def _load_file(uploaded_file: Any) -> pd.DataFrame | None:
    """Load uploaded file into a DataFrame. Returns None on failure."""
    name = uploaded_file.name.lower()
    try:
        if name.endswith(".csv"):
            return pd.read_csv(uploaded_file)
        elif name.endswith((".xlsx", ".xls")):
            return pd.read_excel(uploaded_file)
        elif name.endswith(".json"):
            data = json.load(uploaded_file)
            if isinstance(data, list):
                return pd.DataFrame(data)
            elif isinstance(data, dict):
                # Try common JSON structures
                for key in ("pipelines", "data", "records", "features"):
                    if key in data and isinstance(data[key], list):
                        return pd.DataFrame(data[key])
                return pd.DataFrame([data])
        elif name.endswith((".db", ".sqlite", ".sqlite3")):
            raw = uploaded_file.read()
            conn = sqlite3.connect(":memory:")
            conn.execute("PRAGMA page_size=4096")
            conn.executescript("".join(chr(b) for b in raw[:16]))
            # Write to temp file
            tmp = Path("/tmp/_upload.db")
            tmp.write_bytes(raw)
            conn2 = sqlite3.connect(str(tmp))
            tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn2)
            if tables.empty:
                st.error("No tables found in the SQLite database.")
                return None
            table = tables.iloc[0]["name"]
            df = pd.read_sql(f"SELECT * FROM {table}", conn2)
            conn2.close()
            return df
    except Exception as e:
        st.error(f"Could not read file: {e}")
        return None
    return None


# ---------------------------------------------------------------------------
# Column auto-matching
# ---------------------------------------------------------------------------

def _normalise(s: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _match_columns(user_cols: list[str]) -> dict[str, dict]:
    """
    For each standard field, find the best matching user column.
    Returns dict: field -> {column, confidence, score}
    """
    try:
        from rapidfuzz import fuzz
    except ImportError:
        fuzz = None

    result: dict[str, dict] = {}
    norm_user = {_normalise(c): c for c in user_cols}

    for field_info in STANDARD_FIELDS:
        field = field_info["field"]
        candidates = [field] + FIELD_ALIASES.get(field, [])
        best_col   = None
        best_score = 0.0

        for candidate in candidates:
            norm_cand = _normalise(candidate)
            # Exact match
            if norm_cand in norm_user:
                best_col   = norm_user[norm_cand]
                best_score = 1.0
                break
            # Fuzzy match
            if fuzz:
                for norm_c, orig_c in norm_user.items():
                    score = fuzz.ratio(norm_cand, norm_c) / 100
                    if score > best_score:
                        best_score = score
                        best_col   = orig_c

        if best_score >= 0.85:
            confidence = "High"
        elif best_score >= 0.60:
            confidence = "Medium"
        elif best_score >= 0.35:
            confidence = "Low"
        else:
            confidence = "No match"
            best_col   = None

        result[field] = {
            "column":     best_col,
            "confidence": confidence,
            "score":      best_score,
        }

    return result


# ---------------------------------------------------------------------------
# Template download
# ---------------------------------------------------------------------------

def _template_csv() -> str:
    df = pd.DataFrame(columns=ALL_FIELDS)
    # Add one example row for Goldeneye
    example = {
        "pipeline_id": "PL1978",
        "pipeline_name": "20in GAS GOLDENEYE - ST. FERGUS",
        "fluid": "GAS",
        "status": "ACTIVE",
        "pipeline_length_km": 101.68,
        "inner_diameter_in": 18.876,
        "outer_diameter_in": 20.0,
        "nominal_wall_thickness_mm": 14.28,
        "inlet_pressure_psia": 1740,
        "outlet_pressure_psia": 1100,
        "start_operation_year": 2004,
        "pipe_grade": "X60",
        "ili_mfl_available": "unknown",
        "material_certificates_available": "unknown",
        "fracture_toughness_basis": "unknown",
        "co2_water_content_ppmv": 50,
        "co2_composition_known": "no",
        "component_compatibility_screened": "no",
        "latitude_start": 57.59,
        "longitude_start": -1.83,
        "latitude_end": 57.02,
        "longitude_end": -2.08,
    }
    df = pd.concat([df, pd.DataFrame([example])], ignore_index=True)
    return df.to_csv(index=False)


# ---------------------------------------------------------------------------
# HTML helpers (self-contained, not importing from main app)
# ---------------------------------------------------------------------------

def _h(html: str) -> None:
    if hasattr(st, "html"):
        st.html(html)
    else:
        st.markdown(html, unsafe_allow_html=True)


def _section(title: str, subtitle: str = "") -> None:
    sub = f"<div style='font-size:12px;color:#7A8499;font-family:Manrope,sans-serif;margin-top:2px;'>{subtitle}</div>" if subtitle else ""
    _h(
        f"<div style='border-left:4px solid #5EEAD4;padding:.3rem .8rem;margin:1.25rem 0 .75rem;'>"
        f"<div style='font-family:Fraunces,serif;font-size:17px;font-weight:500;color:#E8E4DC;'>{title}</div>"
        f"{sub}</div>"
    )


def _badge(text: str, colour: str) -> str:
    bg = colour + "22"
    return (
        f"<span style='background:{bg};border:1px solid {colour}55;color:{colour};"
        f"border-radius:4px;padding:1px 7px;font-size:11px;"
        f"font-family:Manrope,sans-serif;font-weight:600;'>{text}</span>"
    )


CONF_COLOUR = {"High": "#86EFAC", "Medium": "#FBBF24", "Low": "#F97316", "No match": "#F87171"}


# ---------------------------------------------------------------------------
# Main page render function
# ---------------------------------------------------------------------------

def render_data_input_page() -> None:
    """Main render function for the Data Input page."""

    _h(
        "<div style='padding:1.5rem 0 .5rem;'>"
        "<div style='font-family:Fraunces,serif;font-size:28px;font-weight:500;"
        "color:#E8E4DC;margin-bottom:.35rem;'>Data Input</div>"
        "<div style='font-size:13px;color:#7A8499;font-family:Manrope,sans-serif;"
        "line-height:1.6;max-width:640px;'>"
        "Upload your own pipeline database or fill in the standard template. "
        "The tool will automatically match your data fields to the required format "
        "and show you what is available for each assessment.</div>"
        "</div>"
    )

    # ── Step 1: Download template or upload file ──────────────────────────
    _section("Step 1 — Upload your data",
             "Accepted formats: CSV, Excel (.xlsx), JSON, SQLite (.db)")

    col_up, col_tpl = st.columns([2, 1], gap="large")

    with col_tpl:
        _h(
            "<div style='background:#111827;border:1px solid #1e2d47;"
            "border-radius:10px;padding:1rem;'>"
            "<div style='font-size:13px;font-family:Manrope,sans-serif;"
            "color:#E8E4DC;font-weight:600;margin-bottom:.5rem;'>"
            "Don't have your data ready?</div>"
            "<div style='font-size:12px;color:#7A8499;font-family:Manrope,sans-serif;"
            "line-height:1.5;margin-bottom:.75rem;'>"
            "Download our standard template, fill it in with your pipeline data, "
            "then upload it here.</div>"
            "</div>"
        )
        tpl_csv = _template_csv()
        st.download_button(
            "Download standard template (CSV)",
            data=tpl_csv,
            file_name="pipeline_repurposing_template.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col_up:
        uploaded = st.file_uploader(
            "Upload pipeline data file",
            type=["csv", "xlsx", "xls", "json", "db", "sqlite", "sqlite3"],
            key="data_input_upload",
            label_visibility="collapsed",
        )

    if uploaded is None:
        _h(
            "<div style='background:#111827;border:1px dashed #1e2d47;"
            "border-radius:10px;padding:2rem;text-align:center;margin:1rem 0;'>"
            "<div style='font-size:32px;margin-bottom:.5rem;'>&#x1F4C2;</div>"
            "<div style='font-size:14px;color:#7A8499;font-family:Manrope,sans-serif;'>"
            "Drag and drop your file above, or click to browse.</div>"
            "</div>"
        )
        return

    # Load file
    df = _load_file(uploaded)
    if df is None or df.empty:
        st.error("Could not read the file or it is empty.")
        return

    st.success(f"Loaded {len(df):,} rows and {len(df.columns)} columns from {uploaded.name}")

    # ── Step 2: Auto-match columns ────────────────────────────────────────
    _section("Step 2 — Column matching",
             "We automatically matched your column names to our standard fields. "
             "Review and correct any mismatches below.")

    mapping = _match_columns(list(df.columns))

    # Allow user to override mapping via session state
    if "user_mapping" not in st.session_state:
        st.session_state["user_mapping"] = {}

    col_options = ["(not mapped)"] + list(df.columns)

    # Group by category
    groups: dict[str, list[dict]] = {}
    for f in STANDARD_FIELDS:
        g = f["group"]
        groups.setdefault(g, []).append(f)

    for gname, fields in groups.items():
        _h(
            f"<div style='font-size:11px;letter-spacing:.12em;text-transform:uppercase;"
            f"color:#5EEAD4;font-family:Manrope,sans-serif;margin:.9rem 0 .4rem;'>"
            f"{gname}</div>"
        )
        for finfo in fields:
            field = finfo["field"]
            label = finfo["label"]
            required = finfo["required"]
            description = finfo["description"]
            match = mapping[field]
            current = st.session_state["user_mapping"].get(field, match["column"])
            conf  = match["confidence"]
            conf_colour = CONF_COLOUR[conf]

            req_star = "<span style='color:#F87171;'>*</span> " if required else ""

            col_label, col_match, col_select = st.columns([1.5, 1, 2])
            with col_label:
                _h(
                    f"<div style='padding:.3rem 0;'>"
                    f"<div style='font-size:13px;color:#E8E4DC;"
                    f"font-family:Manrope,sans-serif;'>{req_star}{label}</div>"
                    f"<div style='font-size:11px;color:#7A8499;"
                    f"font-family:Manrope,sans-serif;line-height:1.4;'>{description}</div>"
                    f"</div>"
                )
            with col_match:
                    score_str = f"{match['score']*100:.0f}% match" if match["column"] else "No match found"
                    _h(
                    f"<div style='padding:.55rem 0;'>"
                    + _badge(conf, conf_colour)
                    + f"<div style='font-size:11px;color:#7A8499;"
                    f"font-family:Manrope,sans-serif;margin-top:3px;'>"
                    f"{score_str}"
                    f"</div></div>"
                )
            with col_select:
                default_idx = col_options.index(current) if current in col_options else 0
                selected = st.selectbox(
                    f"map_{field}",
                    col_options,
                    index=default_idx,
                    key=f"colmap_{field}",
                    label_visibility="collapsed",
                )
                st.session_state["user_mapping"][field] = selected if selected != "(not mapped)" else None

    # ── Step 3: Apply mapping and show preview ────────────────────────────
    _section("Step 3 — Preview and fill gaps",
             "Review the mapped data below. Fill in any missing required fields manually.")

    # Build mapped DataFrame
    mapped: dict[str, Any] = {}
    for field in ALL_FIELDS:
        col = st.session_state["user_mapping"].get(field)
        if col and col in df.columns:
            mapped[field] = df[col].tolist()
        else:
            mapped[field] = [None] * len(df)

    mapped_df = pd.DataFrame(mapped)

    # Show missing required fields
    missing_required = []
    for field in REQUIRED_FIELDS:
        col = st.session_state["user_mapping"].get(field)
        if not col or col not in df.columns:
            missing_required.append(field)

    if missing_required:
        finfo_map = {f["field"]: f for f in STANDARD_FIELDS}
        missing_labels = [finfo_map[f]["label"] for f in missing_required]
        _h(
            "<div style='background:#2a0d0d;border:1px solid #F8717144;"
            "border-left:4px solid #F87171;border-radius:8px;"
            "padding:.75rem 1rem;margin:.5rem 0;'>"
            "<div style='font-size:13px;color:#F87171;font-family:Manrope,sans-serif;"
            "font-weight:600;margin-bottom:.4rem;'>Required fields not yet mapped:</div>"
            "<div style='font-size:12px;color:#E8E4DC;font-family:Manrope,sans-serif;'>"
            + " &nbsp;&bull;&nbsp; ".join(missing_labels)
            + "</div></div>"
        )

        _h("<div style='font-size:13px;color:#E8E4DC;font-family:Manrope,sans-serif;"
           "margin:.75rem 0 .4rem;font-weight:600;'>Enter values manually:</div>")

        finfo_map2 = {f["field"]: f for f in STANDARD_FIELDS}
        for field in missing_required:
            fi = finfo_map2[field]
            if fi["type"] == "number":
                val = st.number_input(
                    fi["label"],
                    value=0.0,
                    key=f"manual_{field}",
                    help=fi["description"],
                )
                mapped_df[field] = val
            else:
                val = st.text_input(
                    fi["label"],
                    value="",
                    key=f"manual_{field}",
                    help=fi["description"],
                )
                mapped_df[field] = val if val else None

    # Data preview
    preview_cols = [f for f in REQUIRED_FIELDS if f in mapped_df.columns]
    if preview_cols:
        st.dataframe(
            mapped_df[preview_cols].head(10),
            hide_index=True,
            use_container_width=True,
        )
        if len(mapped_df) > 10:
            st.caption(f"Showing 10 of {len(mapped_df):,} rows.")

    # Coverage summary
    n_pipelines = len(mapped_df)
    n_with_geometry = mapped_df["pipeline_length_km"].notna().sum() if "pipeline_length_km" in mapped_df else 0
    n_with_location = (
        mapped_df["latitude_start"].notna() & mapped_df["longitude_start"].notna()
    ).sum() if "latitude_start" in mapped_df and "longitude_start" in mapped_df else 0

    _h(
        f"<div style='display:grid;grid-template-columns:repeat(3,1fr);"
        f"gap:.6rem;margin:.75rem 0;'>"
        f"<div style='background:#111827;border:1px solid #1e2d47;"
        f"border-top:2px solid #5EEAD4;border-radius:8px;padding:.6rem .85rem;'>"
        f"<div style='font-size:9px;letter-spacing:.12em;text-transform:uppercase;"
        f"color:#7A8499;font-family:Manrope,sans-serif;'>Pipelines loaded</div>"
        f"<div style='font-family:JetBrains Mono,monospace;font-size:22px;"
        f"color:#E8E4DC;'>{n_pipelines:,}</div></div>"
        f"<div style='background:#111827;border:1px solid #1e2d47;"
        f"border-top:2px solid #5EEAD4;border-radius:8px;padding:.6rem .85rem;'>"
        f"<div style='font-size:9px;letter-spacing:.12em;text-transform:uppercase;"
        f"color:#7A8499;font-family:Manrope,sans-serif;'>With geometry data</div>"
        f"<div style='font-family:JetBrains Mono,monospace;font-size:22px;"
        f"color:#E8E4DC;'>{n_with_geometry:,}</div></div>"
        f"<div style='background:#111827;border:1px solid #1e2d47;"
        f"border-top:2px solid {'#86EFAC' if n_with_location > 0 else '#F87171'};"
        f"border-radius:8px;padding:.6rem .85rem;'>"
        f"<div style='font-size:9px;letter-spacing:.12em;text-transform:uppercase;"
        f"color:#7A8499;font-family:Manrope,sans-serif;'>With map coordinates</div>"
        f"<div style='font-family:JetBrains Mono,monospace;font-size:22px;"
        f"color:{'#86EFAC' if n_with_location > 0 else '#F87171'};'>"
        f"{n_with_location:,}</div></div>"
        f"</div>"
    )

    if n_with_location == 0:
        _h(
            "<div style='background:#1a1200;border:1px solid #3a2e00;"
            "border-left:4px solid #FBBF24;border-radius:8px;"
            "padding:.6rem 1rem;font-size:12px;color:#FCD34D;"
            "font-family:Manrope,sans-serif;margin:.25rem 0;'>"
            "&#9888; No map coordinates found. Pipelines will not appear on the dashboard map. "
            "Add latitude/longitude start and end points to enable the map.</div>"
        )

    # ── Step 4: Save and use ──────────────────────────────────────────────
    _section("Step 4 — Save and use on Dashboard",
             "Save your mapped data as the standard template and load it on the Dashboard.")

    col_save, col_use = st.columns(2, gap="medium")

    with col_save:
        csv_out = mapped_df.to_csv(index=False)
        st.download_button(
            "Download mapped data (CSV)",
            data=csv_out,
            file_name="my_pipeline_data_mapped.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col_use:
        can_use = not missing_required or all(
            st.session_state.get(f"manual_{f}", "") not in ("", None, 0.0)
            for f in missing_required
        )
        if st.button(
            "Use this data on the Dashboard",
            use_container_width=True,
            type="primary",
            disabled=not can_use,
        ):
            # Store mapped data in session state for Dashboard to pick up
            st.session_state["custom_pipeline_data"] = mapped_df.to_dict(orient="records")
            st.session_state["custom_data_source"]   = uploaded.name
            st.session_state["use_custom_data"]      = True
            st.success(
                f"Data loaded: {n_pipelines:,} pipelines from '{uploaded.name}'. "
                "Go to the Dashboard to run assessments."
            )
            if hasattr(st, "switch_page"):
                st.switch_page("streamlit_app.py")

    if not can_use and missing_required:
        finfo_map3 = {f["field"]: f for f in STANDARD_FIELDS}
        missing_labels2 = [finfo_map3[f]["label"] for f in missing_required]
        st.caption(
            f"Fill in the required fields above before using on the Dashboard: "
            + ", ".join(missing_labels2)
        )
