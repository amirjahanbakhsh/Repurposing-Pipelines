"""
New-build CO2 pipeline CAPEX model.

Implements four regression-based cost equations for natural gas pipelines,
adjusted to CO2 service, following the methodology of the FECM/NETL CO2
Transport Cost Model (2024) [NETL-2024].

References
----------
[NETL-2024]
    National Energy Technology Laboratory. (2024). FECM/NETL CO2 Transport
    Cost Model (2024): Description and User's Manual. DOE/NETL-2024/4860.
    https://www.osti.gov/biblio/2473642

[PARKER-2004]
    Parker, N. (2004). Using Natural Gas Transmission Pipeline Costs to
    Estimate Hydrogen Pipeline Costs. UCD-ITS-RR-04-35. UC Davis.

[MCCOY-2008]
    McCoy, S. T., & Rubin, E. S. (2008). An engineering-economic model of
    pipeline transport of CO2 with application to carbon capture and storage.
    International Journal of Greenhouse Gas Control, 2(2), 219–229.
    https://doi.org/10.1016/S1750-5836(07)00119-3

[RUI-2011]
    Rui, Z., Metz, P., Reynolds, D., Chen, G., & Zhou, X. (2011). Regression
    models estimate pipeline construction costs. Oil and Gas Journal,
    109(27), 120–127.

[BROWN-2022]
    Brown, D., Reddi, K., & Elgowainy, A. (2022). The development of natural
    gas and hydrogen pipeline capital cost estimating equations. International
    Journal of Hydrogen Energy, 47(50), 33813–33826.
    https://doi.org/10.1016/j.ijhydene.2022.07.270

[RSMEANS-2026]
    RSMeans. (2026). RSMeans Construction Cost Index. Gordian Group.
    https://www.rsmeans.com/landing-pages/2025-rsmeans-cost-index

[MAXWELL-2026]
    Maxwell, C. (2026). Cost Indices: Free Sources for Engineering Cost
    Estimation. Towering Skills.
    https://toweringskills.com/financial-analysis/cost-indices/

Escalation methodology
----------------------
All four models are first normalised to 2011 USD using published index
ratios [NETL-2024, Exhibit 3-7]:

    Component       Index used                     2000    2004    2008    2011    2018
    Materials/Lab   Handy-Whitman gas transmission  261     400     604     525     629
    ROW             GDP chain-type price index       88.7    96.8   108.5   113.8   ~124.6
    Miscellaneous   US Producer Price Index          122.3  139.6   196.3   190.9   ~199.0

Costs in 2011 USD are then escalated to the project year using the
RSMeans Construction Cost Index [RSMEANS-2026], with 191.2 as the 2011
reference value.

CO2 adjustment factor (eCO2) [NETL-2024, Eq. 3-15]
    D ≤ 12 in.       eCO2 = 1.00
    12 < D ≤ 16 in.  eCO2 = 1.12
    16 < D ≤ 20 in.  eCO2 = 1.18
    D > 20 in.       eCO2 = 1.25
    Applied to materials and labour only (not ROW or miscellaneous).

Offshore factor
    Central estimate: 1.6 (range 1.5–2.0)
    Applied to all four cost components.
    Basis: USAID (2002) offshore ≈ 1.96× onshore; 1.6 is a conservative
    estimate for shallow-to-medium North Sea conditions (50–200 m depth).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Literal

MODEL_VERSION = "newbuild_cost_v1.0"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# RSMeans CCI annual values (Jul reference where available).
# Base year 2011 = 191.2. Source: [RSMEANS-2026] via [MAXWELL-2026].
RSMEANS_CCI: dict[int, float] = {
    2011: 191.2,
    2012: 194.6,
    2013: 201.2,
    2014: 204.9,
    2015: 206.2,
    2016: 207.3,
    2017: 213.6,
    2018: 222.9,
    2019: 232.2,
    2020: 235.6,   # average of quarterly data
    2021: 251.0,   # average
    2022: 290.6,   # average; post-COVID steel/labour spike
    2023: 295.8,   # average
    2024: 295.6,   # average
    2025: 298.7,   # average
    2026: 306.5,   # estimate from Jan–Apr data only
}
RSMEANS_BASE_YEAR = 2011
RSMEANS_BASE_VALUE = 191.2

# Handy-Whitman gas transmission pipeline index [NETL-2024, Exhibit 3-7]
HW_INDEX: dict[int, float] = {
    2000: 261.0,
    2004: 400.0,
    2008: 604.0,
    2011: 525.0,
    2018: 629.0,   # used to de-escalate Brown et al. to 2011
}

# GDP chain-type price index [NETL-2024, Exhibit 3-7]
GDP_INDEX: dict[int, float] = {
    2000: 88.7,
    2004: 96.8,
    2008: 108.5,
    2011: 113.8,
    2018: 124.6,
}

# US Producer Price Index — Industrial Commodities [NETL-2024, Exhibit 3-7]
PPI_INDEX: dict[int, float] = {
    2000: 122.3,
    2004: 139.6,
    2008: 196.3,
    2011: 190.9,
    2018: 199.0,
}

# Surge tank and control system costs [NETL-2024, Sub-part 2.2]
# Both in 2000 USD, escalated to 2011 using CEPCI sub-indices.
# CEPCI heat exchangers/tanks ratio 2011/2000 = 1.774
# CEPCI process instruments ratio 2011/2000 = 1.191
SURGE_TANK_USD_2000 = 701_600.0
CONTROL_SYSTEM_USD_2000 = 94_000.0
CEPCI_RATIO_TANKS_2011_2000 = 1.774
CEPCI_RATIO_INSTRUMENTS_2011_2000 = 1.191

SURGE_TANK_USD_2011 = SURGE_TANK_USD_2000 * CEPCI_RATIO_TANKS_2011_2000
CONTROL_SYSTEM_USD_2011 = CONTROL_SYSTEM_USD_2000 * CEPCI_RATIO_INSTRUMENTS_2011_2000

# Pump costs [McCollum & Ogden 2004, as cited in NETL-2024, Eq. 3-16]
# In 2005 USD; CEPCI ratio 2011/2005 ≈ 1.154 (approx.)
PUMP_FIXED_USD_2005 = 70_000.0
PUMP_VARIABLE_USD_PER_KW_2005 = 1_110.0
CEPCI_RATIO_2011_2005 = 1.154   # approximate

PUMP_FIXED_USD_2011 = PUMP_FIXED_USD_2005 * CEPCI_RATIO_2011_2005
PUMP_VARIABLE_USD_PER_KW_2011 = PUMP_VARIABLE_USD_PER_KW_2005 * CEPCI_RATIO_2011_2005

# ---------------------------------------------------------------------------
# Parker (2004) coefficients [NETL-2024, Exhibit 3-1]
# Equation form: C_i = a_i0 + L * (a_i1 * D² + a_i2 * D + a_i3)
# Units: L in miles, D in inches, cost in 2000 USD
# ---------------------------------------------------------------------------
PARKER_COEFFS: dict[str, dict[str, float]] = {
    "mat":  {"a0": 35_000,  "a1": 330.5,  "a2": 687,     "a3": 26_960},
    "lab":  {"a0": 185_000, "a1": 343.0,  "a2": 2_074,   "a3": 170_013},
    "row":  {"a0": 40_000,  "a1": 0.0,    "a2": 577,     "a3": 29_788},
    "misc": {"a0": 95_000,  "a1": 0.0,    "a2": 8_417,   "a3": 7_324},
}

# ---------------------------------------------------------------------------
# McCoy & Rubin (2008) coefficients [NETL-2024, Exhibit 3-3]
# Equation form: C_i = 10^(a_i0 + a_i_reg) * L^a_i1 * D^a_i2
# Units: L in km, D in inches, cost in 2004 USD
# ---------------------------------------------------------------------------
MCCOY_COEFFS: dict[str, dict[str, float]] = {
    "mat": {
        "a0": 3.112, "a1": 0.901, "a2": 1.590,
        "NE": 0.0, "SE": 0.074, "MW": 0.0,
        "Cen": 0.0, "SW": 0.0, "West": 0.0,
    },
    "lab": {
        "a0": 4.487, "a1": 0.820, "a2": 0.940,
        "NE": 0.075, "SE": 0.0, "MW": 0.0,
        "Cen": -0.187, "SW": -0.216, "West": 0.0,
    },
    "row": {
        "a0": 3.950, "a1": 1.049, "a2": 0.403,
        "NE": 0.0, "SE": 0.0, "MW": 0.0,
        "Cen": -0.382, "SW": 0.0, "West": 0.0,
    },
    "misc": {
        "a0": 4.390, "a1": 0.783, "a2": 0.791,
        "NE": 0.145, "SE": 0.132, "MW": 0.0,
        "Cen": -0.369, "SW": 0.0, "West": -0.377,
    },
}

# ---------------------------------------------------------------------------
# Rui et al. (2011) coefficients [NETL-2024, Exhibit 3-4]
# Equation form: C_i = exp(a_i0 + a_i_reg) * L^a_i1 * SA^a_i2
# Units: L in feet, SA = π*D²/4 in ft², cost in 2008 USD
# ---------------------------------------------------------------------------
RUI_COEFFS: dict[str, dict[str, float]] = {
    "mat": {
        "a0": 4.814, "a1": 0.873, "a2": 0.734,
        "NE": 0.0, "SE": 0.176, "MW": -0.098,
        "Cen": 0.0, "SW": 0.0, "West": 0.0, "Can": -0.196,
    },
    "lab": {
        "a0": 5.697, "a1": 0.808, "a2": 0.459,
        "NE": 0.784, "SE": 0.772, "MW": 0.541,
        "Cen": 0.0, "SW": 0.498, "West": 0.653, "Can": 0.0,
    },
    "row": {
        "a0": 1.259, "a1": 1.027, "a2": 0.191,
        "NE": 0.645, "SE": 0.798, "MW": 1.064,
        "Cen": 0.0, "SW": 0.981, "West": 0.778, "Can": -0.830,
    },
    "misc": {
        "a0": 5.580, "a1": 0.765, "a2": 0.458,
        "NE": 0.704, "SE": 0.967, "MW": 0.547,
        "Cen": 0.0, "SW": 0.699, "West": 0.0, "Can": 0.0,
    },
}

# ---------------------------------------------------------------------------
# Brown et al. (2022) coefficients [NETL-2024, Exhibit 3-6]
# Equation form (per inch-mile): C_i = a_i0 * D^a_i1 * L^a_i2
# Units: D in inches, L in MILES, cost in 2018 USD per inch-mile
# Total cost = C_i * D * L_mi
# Note: NETL-2024 states L in feet, but the student notebook (CpBrown1) and
# the coefficient magnitudes confirm the equation gives $/in-mi with L in miles.
# The NETL Excel model internally converts; we follow the student implementation
# which matches NETL Exhibit 4-3 validation data within screening accuracy.
# Regions: 9 US regions, some sharing coefficients per [NETL-2024, Exhibit 3-6]:
#   GP and RM share coefficients; PN and SE share coefficients; SW and CA share.
# ---------------------------------------------------------------------------
BROWN_COEFFS: dict[str, dict[str, dict[str, float]]] = {
    # 9 individual regions (GP/RM share; SE/PN share; SW/CA share per NETL-2024)
    "NE": {
        "mat":  {"a0": 10_409,   "a1": 0.296847,  "a2": -0.07257},
        "lab":  {"a0": 249_131,  "a1": -0.33162,  "a2": -0.17892},
        "row":  {"a0": 83_124,   "a1": -0.66357,  "a2": -0.07544},
        "misc": {"a0": 65_990,   "a1": -0.29673,  "a2": -0.06856},
    },
    "MA": {
        "mat":  {"a0": 9_113,    "a1": 0.279875,  "a2": -0.00840},
        "lab":  {"a0": 43_692,   "a1": 0.05683,   "a2": -0.10108},
        "row":  {"a0": 1_942,    "a1": 0.17394,   "a2": -0.01555},
        "misc": {"a0": 14_616,   "a1": 0.16354,   "a2": -0.16186},
    },
    "SE": {
        "mat":  {"a0": 6_207,    "a1": 0.38224,   "a2": -0.05211},
        "lab":  {"a0": 32_094,   "a1": 0.06110,   "a2": -0.14828},
        "row":  {"a0": 9_531,    "a1": -0.37284,  "a2":  0.02616},
        "misc": {"a0": 11_270,   "a1": 0.19077,   "a2": -0.13669},
    },
    "GL": {
        "mat":  {"a0": 8_971,    "a1": 0.255012,  "a2": -0.03138},
        "lab":  {"a0": 58_154,   "a1": -0.14821,  "a2": -0.10596},
        "row":  {"a0": 14_259,   "a1": -0.65318,  "a2":  0.06865},
        "misc": {"a0": 41_238,   "a1": -0.34751,  "a2": -0.11104},
    },
    "GP": {
        "mat":  {"a0": 5_813,    "a1": 0.31599,   "a2": -0.00376},
        "lab":  {"a0": 10_406,   "a1": 0.20953,   "a2": -0.08419},
        "row":  {"a0": 2_751,    "a1": -0.28294,  "a2":  0.00731},
        "misc": {"a0": 4_944,    "a1": 0.17351,   "a2": -0.07621},
    },
    "RM": {
        "mat":  {"a0": 5_813,    "a1": 0.31599,   "a2": -0.00376},
        "lab":  {"a0": 10_406,   "a1": 0.20953,   "a2": -0.08419},
        "row":  {"a0": 2_751,    "a1": -0.28294,  "a2":  0.00731},
        "misc": {"a0": 4_944,    "a1": 0.17351,   "a2": -0.07621},
    },
    "PN": {
        "mat":  {"a0": 6_207,    "a1": 0.38224,   "a2": -0.05211},
        "lab":  {"a0": 32_094,   "a1": 0.06110,   "a2": -0.14828},
        "row":  {"a0": 9_531,    "a1": -0.37284,  "a2":  0.02616},
        "misc": {"a0": 11_270,   "a1": 0.19077,   "a2": -0.13669},
    },
    "SW": {
        "mat":  {"a0": 5_605,    "a1": 0.41642,   "a2": -0.06441},
        "lab":  {"a0": 95_295,   "a1": -0.53848,  "a2":  0.03070},
        "row":  {"a0": 72_634,   "a1": -1.07566,  "a2":  0.05284},
        "misc": {"a0": 19_211,   "a1": -0.14178,  "a2": -0.04697},
    },
    "CA": {
        "mat":  {"a0": 5_605,    "a1": 0.41642,   "a2": -0.06441},
        "lab":  {"a0": 95_295,   "a1": -0.53848,  "a2":  0.03070},
        "row":  {"a0": 72_634,   "a1": -1.07566,  "a2":  0.05284},
        "misc": {"a0": 19_211,   "a1": -0.14178,  "a2": -0.04697},
    },
}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def rsmeans_escalation_factor(target_year: int, flat_rate_beyond: float = 0.03) -> float:
    """
    Escalation factor from 2011 to *target_year* using RSMeans CCI.

    For years within the table, the factor is CCI(target) / CCI(2011).
    For years beyond the last known data point, a flat annual rate is
    applied beyond the last known year, with a warning flag returned
    via the docstring. Source: [RSMEANS-2026], [MAXWELL-2026].
    """
    if target_year in RSMEANS_CCI:
        return RSMEANS_CCI[target_year] / RSMEANS_BASE_VALUE
    last_known_year = max(RSMEANS_CCI.keys())
    last_known_value = RSMEANS_CCI[last_known_year]
    years_beyond = target_year - last_known_year
    extrapolated = last_known_value * ((1 + flat_rate_beyond) ** years_beyond)
    return extrapolated / RSMEANS_BASE_VALUE


def co2_adjustment_factor(diameter_in: float) -> float:
    """
    CO2 pipeline cost adjustment factor relative to natural gas pipeline.

    Applied to materials and labour components only.
    Source: [NETL-2024, Eq. 3-15], citing ICF International data.
    """
    if diameter_in <= 12:
        return 1.00
    elif diameter_in <= 16:
        return 1.12
    elif diameter_in <= 20:
        return 1.18
    else:
        return 1.25


def _normalise_to_2011(
    mat: float, lab: float, row: float, misc: float, base_year: int
) -> dict[str, float]:
    """
    Normalise cost components from *base_year* USD to 2011 USD.

    Uses index ratios from [NETL-2024, Exhibit 3-7].
    """
    hw_ratio  = HW_INDEX[2011]  / HW_INDEX[base_year]
    gdp_ratio = GDP_INDEX[2011] / GDP_INDEX[base_year]
    ppi_ratio = PPI_INDEX[2011] / PPI_INDEX[base_year]
    return {
        "mat":  mat  * hw_ratio,
        "lab":  lab  * hw_ratio,
        "row":  row  * gdp_ratio,
        "misc": misc * ppi_ratio,
    }


# ---------------------------------------------------------------------------
# Individual model functions (return costs in 2011 USD)
# ---------------------------------------------------------------------------

def _parker_2011(length_mi: float, diameter_in: float) -> dict[str, float]:
    """
    Parker (2004) natural gas pipeline cost components in 2011 USD.

    [PARKER-2004], [NETL-2024, Eq. 3-11, Exhibit 3-1].
    Note: ROW uses linear diameter term (not squared) per NETL-2024 correction.
    """
    c = PARKER_COEFFS
    L, D = length_mi, diameter_in
    mat  = c["mat"]["a0"]  + L * (c["mat"]["a1"]  * D**2 + c["mat"]["a2"]  * D + c["mat"]["a3"])
    lab  = c["lab"]["a0"]  + L * (c["lab"]["a1"]  * D**2 + c["lab"]["a2"]  * D + c["lab"]["a3"])
    row  = c["row"]["a0"]  + L * (c["row"]["a1"]  * D**2 + c["row"]["a2"]  * D + c["row"]["a3"])
    misc = c["misc"]["a0"] + L * (c["misc"]["a1"] * D**2 + c["misc"]["a2"] * D + c["misc"]["a3"])
    return _normalise_to_2011(mat, lab, row, misc, base_year=2000)


def _mccoy_2011(length_mi: float, diameter_in: float,
                region: str = "Avg") -> dict[str, float]:
    """
    McCoy & Rubin (2008) natural gas pipeline cost components in 2011 USD.

    [MCCOY-2008], [NETL-2024, Eq. 3-12, Exhibit 3-3].
    L in km, D in inches; cost in 2004 USD before normalisation.
    """
    length_km = length_mi * 1.60934
    c = MCCOY_COEFFS
    valid_regions = ["NE", "SE", "MW", "Cen", "SW", "West", "Avg"]
    if region not in valid_regions:
        raise ValueError(f"McCoy region must be one of {valid_regions}")

    def _component(comp: str) -> float:
        reg_adj = 0.0 if region == "Avg" else c[comp].get(region, 0.0)
        if region == "Avg":
            # Average across all six regions
            reg_adjs = [c[comp].get(r, 0.0) for r in ["NE", "SE", "MW", "Cen", "SW", "West"]]
            reg_adj = sum(reg_adjs) / 6
        exponent = c[comp]["a0"] + reg_adj
        return (10 ** exponent) * (length_km ** c[comp]["a1"]) * (diameter_in ** c[comp]["a2"])

    mat  = _component("mat")
    lab  = _component("lab")
    row  = _component("row")
    misc = _component("misc")
    return _normalise_to_2011(mat, lab, row, misc, base_year=2004)


def _rui_2011(length_mi: float, diameter_in: float,
              region: str = "Avg") -> dict[str, float]:
    """
    Rui et al. (2011) natural gas pipeline cost components in 2011 USD.

    [RUI-2011], [NETL-2024, Eq. 3-13, Exhibit 3-4].
    L in feet, SA = π*D²/4 in ft²; cost in 2008 USD before normalisation.
    """
    length_ft = length_mi * 5280.0
    diameter_ft = diameter_in / 12.0
    sa_ft2 = math.pi * (diameter_ft ** 2) / 4.0
    c = RUI_COEFFS
    valid_regions = ["NE", "SE", "MW", "Cen", "SW", "West", "Can", "Avg"]
    if region not in valid_regions:
        raise ValueError(f"Rui region must be one of {valid_regions}")

    def _component(comp: str) -> float:
        if region == "Avg":
            reg_adjs = [c[comp].get(r, 0.0) for r in ["NE", "SE", "MW", "Cen", "SW", "West"]]
            reg_adj = sum(reg_adjs) / 6
        else:
            reg_adj = c[comp].get(region, 0.0)
        exponent = c[comp]["a0"] + reg_adj
        return math.exp(exponent) * (length_ft ** c[comp]["a1"]) * (sa_ft2 ** c[comp]["a2"])

    mat  = _component("mat")
    lab  = _component("lab")
    row  = _component("row")
    misc = _component("misc")
    return _normalise_to_2011(mat, lab, row, misc, base_year=2008)


def _brown_2011(length_mi: float, diameter_in: float,
                region: str = "Avg") -> dict[str, float]:
    """
    Brown et al. (2022) natural gas pipeline cost components in 2011 USD.

    [BROWN-2022], [NETL-2024, Eq. 3-14, Exhibit 3-6].
    Equation gives cost in $/in-mile; total = C * D_in * L_mi.
    De-escalated from 2018 to 2011 using Handy-Whitman index ratio 525/629.

    Note on units: The NETL-2024 manual states L in feet, but cross-validation
    against NETL Exhibit 4-3 confirms the equation is in $/in-mi with L in miles.
    This follows the student implementation (CpBrown1, cost_model.ipynb) which
    matches Exhibit 4-3 values within screening accuracy (~23% for Avg region).
    """
    valid_regions = list(BROWN_COEFFS.keys()) + ["Avg"]
    if region not in valid_regions:
        raise ValueError(f"Brown region must be one of {valid_regions}")

    if region == "Avg":
        all_regions = list(BROWN_COEFFS.keys())  # all 9
    else:
        all_regions = [region]

    totals: dict[str, float] = {"mat": 0.0, "lab": 0.0, "row": 0.0, "misc": 0.0}
    for reg in all_regions:
        coeffs = BROWN_COEFFS[reg]
        for comp in ("mat", "lab", "row", "misc"):
            c = coeffs[comp]
            # Cost per inch-mile, total = C * D * L_mi
            cost_per_in_mi_2018 = c["a0"] * (diameter_in ** c["a1"]) * (length_mi ** c["a2"])
            total_2018 = cost_per_in_mi_2018 * diameter_in * length_mi
            totals[comp] += total_2018
    if region == "Avg":
        for comp in totals:
            totals[comp] /= len(all_regions)

    # De-escalate from 2018 to 2011 using average Handy-Whitman indices
    # [NETL-2024]: "average values of Handy-Whitman indices from 2011 and 2018"
    hw_avg_ratio = (HW_INDEX[2011] + HW_INDEX[2018]) / 2 / HW_INDEX[2018]
    # For screening simplicity we use a single HW ratio for all components
    # (NETL applies HW for mat/lab, GDP for ROW, PPI for misc; here we note
    # that NETL uses the avg HW ratio for Brown de-escalation, not component-specific)
    return {
        "mat":  totals["mat"]  * hw_avg_ratio,
        "lab":  totals["lab"]  * hw_avg_ratio,
        "row":  totals["row"]  * hw_avg_ratio,
        "misc": totals["misc"] * hw_avg_ratio,
    }


# ---------------------------------------------------------------------------
# Main public function
# ---------------------------------------------------------------------------

@dataclass
class NewBuildCostResult:
    """
    Result of a new-build CO2 pipeline CAPEX calculation.

    All cost values are in USD for the specified project year.
    """
    model: str
    region: str
    diameter_in: float
    length_mi: float
    length_km: float
    project_year: int
    offshore: bool
    offshore_factor: float

    # Components in project-year USD (after CO2 and offshore adjustment)
    cost_mat_usd: float
    cost_lab_usd: float
    cost_row_usd: float
    cost_misc_usd: float
    cost_surge_tank_usd: float
    cost_control_system_usd: float
    cost_pump_usd: float

    # Totals
    cost_subtotal_usd: float
    cost_contingency_usd: float
    cost_total_usd: float
    contingency_fraction: float

    # Escalation info
    escalation_factor: float
    co2_factor: float
    rsmeans_cci_year: float
    base_year: int = 2011

    # Warnings
    warnings: list[str] = field(default_factory=list)

    # Audit trace
    trace: dict = field(default_factory=dict)


def calculate_newbuild_cost(
    diameter_in: float,
    length_km: float,
    project_year: int = 2026,
    model: Literal["parker", "mccoy", "rui", "brown"] = "brown",
    region: str = "Avg",
    offshore: bool = True,
    offshore_factor: float = 1.6,
    contingency_fraction: float = 0.10,
    n_booster_pumps: int = 0,
    pump_power_kw: float = 0.0,
    flat_rate_beyond_table: float = 0.03,
) -> NewBuildCostResult:
    """
    Calculate new-build CO2 pipeline CAPEX.

    Parameters
    ----------
    diameter_in : float
        Pipeline outer diameter in inches.
    length_km : float
        Pipeline length in kilometres.
    project_year : int
        Target year for cost escalation (default 2026).
    model : str
        Regression model: 'parker', 'mccoy', 'rui', or 'brown'.
        Default is 'brown' (most recent data, per NETL-2024 recommendation).
    region : str
        US region for regional models. Use 'Avg' for US average (default).
        Not applicable for Parker (national model only).
    offshore : bool
        Apply offshore location factor (default True for North Sea).
    offshore_factor : float
        Offshore multiplier on all cost components (default 1.6).
        Range 1.5–2.0; see cost_escalation_basis.md for justification.
    contingency_fraction : float
        Fraction of subtotal added as contingency (default 0.10 = 10%).
    n_booster_pumps : int
        Number of booster pumps (default 0 for short offshore pipelines).
    pump_power_kw : float
        Required pump power in kW per pump (default 0.0).
    flat_rate_beyond_table : float
        Annual escalation rate applied if project_year > last RSMeans year.

    Returns
    -------
    NewBuildCostResult
        Full cost breakdown with trace and warnings.

    Notes
    -----
    Methodology follows [NETL-2024] throughout. All equations, coefficient
    tables, index values, and adjustment factors are directly sourced from
    [NETL-2024] and the references it cites.
    """
    length_mi = length_km / 1.60934
    warnings: list[str] = []

    # 1. Get natural gas pipeline components in 2011 USD
    if model == "parker":
        components_2011 = _parker_2011(length_mi, diameter_in)
    elif model == "mccoy":
        components_2011 = _mccoy_2011(length_mi, diameter_in, region)
    elif model == "rui":
        components_2011 = _rui_2011(length_mi, diameter_in, region)
    elif model == "brown":
        components_2011 = _brown_2011(length_mi, diameter_in, region)
    else:
        raise ValueError(f"Unknown model '{model}'. Choose: parker, mccoy, rui, brown.")

    # 2. Apply CO2 adjustment factor to mat + lab [NETL-2024, Eq. 3-15]
    eco2 = co2_adjustment_factor(diameter_in)
    mat_co2  = components_2011["mat"]  * eco2
    lab_co2  = components_2011["lab"]  * eco2
    row_co2  = components_2011["row"]   # no CO2 factor on ROW
    misc_co2 = components_2011["misc"]  # no CO2 factor on misc

    # 3. Escalate from 2011 to project year using RSMeans CCI
    if project_year > max(RSMEANS_CCI.keys()):
        warnings.append(
            f"Project year {project_year} is beyond the last known RSMeans CCI data point "
            f"({max(RSMEANS_CCI.keys())}). Costs extrapolated at {flat_rate_beyond_table*100:.1f}%/yr. "
            "Update RSMEANS_CCI when new data becomes available. [RSMEANS-2026]"
        )
    esc = rsmeans_escalation_factor(project_year, flat_rate_beyond_table)
    rsmeans_cci_year = RSMEANS_CCI.get(
        project_year,
        RSMEANS_CCI[max(RSMEANS_CCI.keys())] * ((1 + flat_rate_beyond_table) ** (project_year - max(RSMEANS_CCI.keys())))
    )

    mat_esc  = mat_co2  * esc
    lab_esc  = lab_co2  * esc
    row_esc  = row_co2  * esc
    misc_esc = misc_co2 * esc

    # 4. Apply offshore factor to all components
    if offshore:
        if offshore_factor < 1.5 or offshore_factor > 2.0:
            warnings.append(
                f"Offshore factor {offshore_factor} is outside the expected range 1.5–2.0. "
                "Literature suggests 1.96× for offshore vs onshore (USAID 2002). "
                "Central estimate for North Sea screening is 1.6."
            )
        mat_f  = mat_esc  * offshore_factor
        lab_f  = lab_esc  * offshore_factor
        row_f  = row_esc  * offshore_factor
        misc_f = misc_esc * offshore_factor
    else:
        mat_f, lab_f, row_f, misc_f = mat_esc, lab_esc, row_esc, misc_esc

    # 5. Additional pipeline-related costs (surge tank, control system)
    surge_tank_usd = SURGE_TANK_USD_2011 * esc * (offshore_factor if offshore else 1.0)
    control_usd    = CONTROL_SYSTEM_USD_2011 * esc * (offshore_factor if offshore else 1.0)

    # 6. Booster pump costs [NETL-2024, Eq. 3-16, citing McCollum & Ogden]
    pump_cost_per_pump = (
        PUMP_FIXED_USD_2011 + PUMP_VARIABLE_USD_PER_KW_2011 * pump_power_kw
    ) * esc
    pump_usd = n_booster_pumps * pump_cost_per_pump

    # 7. Subtotal and contingency
    subtotal = mat_f + lab_f + row_f + misc_f + surge_tank_usd + control_usd + pump_usd
    contingency = contingency_fraction * subtotal
    total = subtotal + contingency

    # Warnings
    if model == "parker":
        warnings.append(
            "Parker (2004) uses US national data (1991–2003) with no regional variation. "
            "It typically gives the highest estimates. [PARKER-2004]"
        )
    if diameter_in < 8 or diameter_in > 48:
        warnings.append(
            f"Diameter {diameter_in} in. is outside the 8–48 in. range of the NETL model. "
            "Cost estimates may be unreliable. [NETL-2024]"
        )
    if length_mi > 1000:
        warnings.append(
            f"Pipeline length {length_mi:.0f} mi ({length_km:.0f} km) is very long for a "
            "single-segment offshore pipeline. Verify that no intermediate compression is required."
        )

    trace = {
        "model": model,
        "equations": {
            "parker":  "[NETL-2024 Eq. 3-11]: C_i = a_i0 + L_mi*(a_i1*D² + a_i2*D + a_i3), 2000$",
            "mccoy":   "[NETL-2024 Eq. 3-12]: C_i = 10^(a_i0+a_i_reg) * L_km^a_i1 * D^a_i2, 2004$",
            "rui":     "[NETL-2024 Eq. 3-13]: C_i = exp(a_i0+a_i_reg) * L_ft^a_i1 * SA_ft2^a_i2, 2008$",
            "brown":   "[NETL-2024 Eq. 3-14]: C_i = a_i0 * D^a_i1 * L_ft^a_i2, 2018$",
        }.get(model, ""),
        "step1_ng_components_2011usd": components_2011,
        "step2_co2_factor": eco2,
        "step2_co2_adjusted_2011usd": {"mat": mat_co2, "lab": lab_co2, "row": row_co2, "misc": misc_co2},
        "step3_rsmeans_factor": esc,
        "step3_project_year_usd_before_offshore": {"mat": mat_esc, "lab": lab_esc, "row": row_esc, "misc": misc_esc},
        "step4_offshore_factor": offshore_factor if offshore else 1.0,
        "step4_final_components_usd": {"mat": mat_f, "lab": lab_f, "row": row_f, "misc": misc_f},
        "step5_surge_tank_usd": surge_tank_usd,
        "step5_control_system_usd": control_usd,
        "step6_pump_usd": pump_usd,
        "normalisation_indices": {
            "HW_2011": HW_INDEX[2011],
            "HW_base": HW_INDEX.get({"parker": 2000, "mccoy": 2004, "rui": 2008, "brown": 2018}.get(model, 2011)),
            "RSMeans_2011": RSMEANS_BASE_VALUE,
            f"RSMeans_{project_year}": rsmeans_cci_year,
        },
    }

    return NewBuildCostResult(
        model=model,
        region=region,
        diameter_in=diameter_in,
        length_mi=length_mi,
        length_km=length_km,
        project_year=project_year,
        offshore=offshore,
        offshore_factor=offshore_factor if offshore else 1.0,
        cost_mat_usd=mat_f,
        cost_lab_usd=lab_f,
        cost_row_usd=row_f,
        cost_misc_usd=misc_f,
        cost_surge_tank_usd=surge_tank_usd,
        cost_control_system_usd=control_usd,
        cost_pump_usd=pump_usd,
        cost_subtotal_usd=subtotal,
        cost_contingency_usd=contingency,
        cost_total_usd=total,
        contingency_fraction=contingency_fraction,
        escalation_factor=esc,
        co2_factor=eco2,
        rsmeans_cci_year=rsmeans_cci_year,
        warnings=warnings,
        trace=trace,
    )


def calculate_all_models(
    diameter_in: float,
    length_km: float,
    project_year: int = 2026,
    offshore: bool = True,
    offshore_factor: float = 1.6,
    contingency_fraction: float = 0.10,
) -> dict[str, NewBuildCostResult]:
    """
    Run all four models and return results keyed by model name.

    Useful for showing the range of estimates in the UI.
    """
    return {
        model: calculate_newbuild_cost(
            diameter_in=diameter_in,
            length_km=length_km,
            project_year=project_year,
            model=model,
            offshore=offshore,
            offshore_factor=offshore_factor,
            contingency_fraction=contingency_fraction,
        )
        for model in ("parker", "mccoy", "rui", "brown")
    }


# ---------------------------------------------------------------------------
# Legacy compatibility: evaluate_cost()
# ---------------------------------------------------------------------------
# The original costs.py provided evaluate_cost() which sums pre-calculated
# cost components supplied as scenario parameters. This is still used by
# goldeneye.py and validation.py for the known-case benchmarks where
# component values are supplied directly.
# The new regression-based model (calculate_newbuild_cost) is used for
# computing new-build CAPEX from first principles.

try:
    from .assumptions import ScenarioAssumptions
    from .trace import ModuleResult, OutputRecord, TraceStep, WarningRecord
    _HAS_TRACE = True
except ImportError:
    _HAS_TRACE = False

COST_COMPONENT_PARAMETERS = [
    "cost_material_usd_2025",
    "cost_labor_usd_2025",
    "cost_row_damages_usd_2025",
    "cost_misc_usd_2025",
    "cost_surge_tank_usd_2025",
    "cost_control_system_usd_2025",
    "cost_booster_station_usd_2025",
]

_LEGACY_MODEL_VERSION = "cost_screening_v0.2"


def evaluate_cost(scenario: "ScenarioAssumptions") -> "ModuleResult":
    """
    Legacy cost evaluation: sums pre-calculated component parameters.

    Used by goldeneye.py and validation.py for known-case benchmarks.
    For regression-based new-build CAPEX, use calculate_newbuild_cost().
    """
    subtotal = sum(scenario.number(name) for name in COST_COMPONENT_PARAMETERS)
    contingency = scenario.number("contingency_fraction") * subtotal
    total = subtotal + contingency
    reported_total = scenario.optional_number("reported_total_capex_usd_2025")
    cost_delta = total - reported_total if reported_total is not None else None
    netl_reference_total = scenario.optional_number("netl_reference_total_capex_usd_2025")
    netl_delta = total - netl_reference_total if netl_reference_total is not None else None
    netl_delta_percent = (
        100 * netl_delta / netl_reference_total
        if netl_reference_total not in {None, 0}
        else None
    )
    netl_status = "not_supplied"
    if netl_reference_total is not None and netl_delta_percent is not None:
        netl_status = "pass" if abs(netl_delta_percent) <= 20 else "review_required"

    warnings = []
    if netl_reference_total is None:
        warnings.append(
            WarningRecord(
                level="medium",
                message=(
                    "No NETL CO2_T_COM reference total is supplied for this scenario, "
                    "so cost is internally checked but not externally validated."
                ),
                affected_modules=["cost", "validation"],
            )
        )

    return ModuleResult(
        module="cost",
        model_version=_LEGACY_MODEL_VERSION,
        status="pass" if total > 0 else "fail",
        inputs=scenario.input_records(
            COST_COMPONENT_PARAMETERS
            + ["contingency_fraction"]
            + (
                ["reported_total_capex_usd_2025"]
                if "reported_total_capex_usd_2025" in scenario.records
                else []
            )
            + (
                ["netl_reference_total_capex_usd_2025"]
                if "netl_reference_total_capex_usd_2025" in scenario.records
                else []
            ),
            used_by=["cost"],
        ),
        assumptions=[
            scenario.assumption_record("contingency_fraction", sensitivity_required=True),
        ],
        outputs=[
            OutputRecord("cost_subtotal_usd_2025", subtotal, "USD 2025", used_by=["cost", "pre_lca_gate"]),
            OutputRecord("cost_contingency_usd_2025", contingency, "USD 2025", used_by=["cost", "pre_lca_gate"]),
            OutputRecord("cost_total_usd_2025", total, "USD 2025", used_by=["pre_lca_gate", "final_gate"]),
            OutputRecord("reported_total_capex_usd_2025", reported_total, "USD 2025", quality="reported", used_by=["validation"]),
            OutputRecord("cost_delta_usd_2025", cost_delta, "USD 2025", used_by=["validation"]),
            OutputRecord("netl_reference_total_capex_usd_2025", netl_reference_total, "USD 2025", quality="reported", used_by=["validation"]),
            OutputRecord("netl_cost_delta_usd_2025", netl_delta, "USD 2025", used_by=["validation"]),
            OutputRecord("netl_cost_delta_percent", netl_delta_percent, "%", used_by=["validation"]),
            OutputRecord("netl_cost_validation_status", netl_status, "status", used_by=["validation", "report"]),
        ],
        warnings=warnings,
        trace=[
            TraceStep(
                name="cost_subtotal",
                formula="sum(material, labor, ROW damages, misc, surge tank, control system, booster station)",
                inputs=COST_COMPONENT_PARAMETERS,
                result_name="cost_subtotal_usd_2025",
            ),
            TraceStep(
                name="contingency",
                formula="contingency_fraction * cost_subtotal_usd_2025",
                inputs=["contingency_fraction", "cost_subtotal_usd_2025"],
                result_name="cost_contingency_usd_2025",
            ),
            TraceStep(
                name="total_cost",
                formula="cost_subtotal_usd_2025 + cost_contingency_usd_2025",
                inputs=["cost_subtotal_usd_2025", "cost_contingency_usd_2025"],
                result_name="cost_total_usd_2025",
            ),
        ],
    )
